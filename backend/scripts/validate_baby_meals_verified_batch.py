from __future__ import annotations

import csv
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.gtin_service import normalise_barcode, validate_gtin


STAGED_DIR = BACKEND_DIR / "imports" / "staged"
SOURCE_QUEUE_CSV = STAGED_DIR / "baby_meals_source_queue.csv"
PRODUCTS_CSV = STAGED_DIR / "baby_meals_verified_products.csv"
OFFERS_CSV = STAGED_DIR / "baby_meals_verified_offers.csv"
DB_PATH = BACKEND_DIR / "safebite.db"
REPORT_PATH = PROJECT_DIR / "docs" / "data" / "baby_meals_verified_batch_report.md"

QUEUE_HEADERS = [
    "retailer",
    "product_url",
    "brand",
    "product_name",
    "gtin",
    "gtin_source_url",
    "ingredients",
    "ingredients_source_url",
    "allergens",
    "allergens_source_url",
    "price",
    "price_source_url",
    "checked_at",
    "status",
    "notes",
]
PRODUCT_HEADERS = [
    "barcode",
    "name",
    "brand",
    "category",
    "subcategory",
    "ingredients",
    "allergens",
    "source_url",
]
OFFER_HEADERS = [
    "barcode",
    "retailer",
    "price",
    "product_url",
    "stock_status",
    "source_url",
    "checked_at",
]

ALLOWED_RETAILERS = {"Tesco", "Asda", "Sainsbury's"}
ALLOWED_QUEUE_STATUSES = {"needs_review", "verified", "rejected"}
ALLOWED_STOCK_STATUSES = {"in_stock", "out_of_stock", "unknown"}
UNKNOWN_VALUES = {"", "unknown", "data unavailable", "unavailable", "null", "none"}
MIN_VERIFIED_PRODUCTS_FOR_PROMOTION = 6


@dataclass
class LiveState:
    baby_meals_count: int
    product_barcodes: Set[str]
    offer_keys: Set[Tuple[str, str]]


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def lower_clean(value: object) -> str:
    return clean(value).lower()


def is_unknown(value: object) -> bool:
    return lower_clean(value) in UNKNOWN_VALUES


def valid_url(value: object, require_https: bool = False) -> bool:
    text = clean(value)
    parsed = urlparse(text)
    if require_https and parsed.scheme != "https":
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_price(value: object) -> Optional[float]:
    try:
        text = clean(value)
        if not text:
            return None
        price = float(text)
        if price <= 0:
            return None
        return price
    except Exception:
        return None


def load_csv(path: Path, headers: Sequence[str]) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], ["missing CSV: {0}".format(path)]

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if fieldnames != list(headers):
            return [], [
                "header mismatch in {0}: expected {1}, found {2}".format(
                    path,
                    ",".join(headers),
                    ",".join(fieldnames),
                )
            ]
        return list(reader), []


def load_source_queue(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], ["missing CSV: {0}".format(path)]

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if fieldnames != QUEUE_HEADERS:
            return [], [
                "source queue header mismatch in {0}: expected {1}, found {2}".format(
                    path,
                    ",".join(QUEUE_HEADERS),
                    ",".join(fieldnames),
                )
            ]
        return list(reader), []


def write_csv(path: Path, headers: Sequence[str], rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers))
        writer.writeheader()
        for row in rows:
            writer.writerow({header: clean(row.get(header)) for header in headers})


def load_live_state() -> LiveState:
    if not DB_PATH.exists():
        return LiveState(0, set(), set())

    conn = sqlite3.connect(str(DB_PATH))
    try:
        product_barcodes = {
            clean(row[0])
            for row in conn.execute("SELECT barcode FROM products")
            if row and clean(row[0])
        }

        baby_meals_count = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM products
                WHERE lower(coalesce(category, '')) = lower('Baby & Toddler')
                  AND lower(coalesce(subcategory, '')) = lower('Baby Meals')
                """
            ).fetchone()[0]
        )

        offer_keys: Set[Tuple[str, str]] = set()
        for table in ("offers", "retailer_offers"):
            table_exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not table_exists:
                continue
            for row in conn.execute(
                "SELECT barcode, retailer FROM {0}".format(table)
            ):
                barcode = clean(row[0])
                retailer = clean(row[1])
                if barcode and retailer:
                    offer_keys.add((barcode, retailer))

        return LiveState(baby_meals_count, product_barcodes, offer_keys)
    finally:
        conn.close()


def base_stats() -> Dict[str, int]:
    return {
        "baby_meals_before": 0,
        "baby_meals_after": 0,
        "source_rows": 0,
        "source_verified": 0,
        "source_needs_review": 0,
        "source_rejected": 0,
        "products_staged": 0,
        "products_verified": 0,
        "products_rejected": 0,
        "offers_staged": 0,
        "offers_verified": 0,
        "offers_rejected": 0,
        "duplicate_barcodes": 0,
        "duplicate_barcode_retailers": 0,
        "checksum_failures": 0,
        "missing_ingredients": 0,
        "missing_allergens": 0,
        "missing_source_urls": 0,
        "blocked_rows": 0,
    }


def build_verified_queue_index(
    queue_rows: List[Dict[str, str]],
    stats: Dict[str, int],
    errors: List[str],
) -> Dict[Tuple[str, str], Dict[str, str]]:
    verified: Dict[Tuple[str, str], Dict[str, str]] = {}
    seen_queue_keys: Set[Tuple[str, str]] = set()

    for index, row in enumerate(queue_rows, start=2):
        retailer = clean(row.get("retailer"))
        barcode = normalise_barcode(row.get("gtin"))
        status = lower_clean(row.get("status"))
        key = (barcode, retailer)
        row_errors: List[str] = []

        if status == "verified":
            stats["source_verified"] += 1
        elif status == "needs_review":
            stats["source_needs_review"] += 1
            continue
        elif status == "rejected":
            stats["source_rejected"] += 1
            continue
        else:
            row_errors.append("status must be needs_review, verified, or rejected")

        if retailer not in ALLOWED_RETAILERS:
            row_errors.append("retailer must be Tesco, Asda, or Sainsbury's")

        ok, detail = validate_gtin(barcode)
        if not ok:
            stats["checksum_failures"] += 1
            row_errors.append(detail)

        if key in seen_queue_keys:
            stats["duplicate_barcode_retailers"] += 1
            row_errors.append("duplicate barcode+retailer in source queue")
        seen_queue_keys.add(key)

        if not clean(row.get("brand")):
            row_errors.append("missing brand")
        if not clean(row.get("product_name")):
            row_errors.append("missing product_name")
        if is_unknown(row.get("ingredients")):
            stats["missing_ingredients"] += 1
            row_errors.append("ingredients value is missing or unknown")
        if is_unknown(row.get("allergens")):
            stats["missing_allergens"] += 1
            row_errors.append("allergens value is missing or unknown")
        if not valid_url(row.get("product_url"), require_https=True):
            row_errors.append("product_url must start with https://")
        if parse_price(row.get("price")) is None:
            row_errors.append("price is missing or invalid")
        if not clean(row.get("checked_at")):
            row_errors.append("checked_at is missing")

        for source_field in (
            "gtin_source_url",
            "ingredients_source_url",
            "allergens_source_url",
            "price_source_url",
        ):
            if not valid_url(row.get(source_field), require_https=True):
                stats["missing_source_urls"] += 1
                row_errors.append("{0} is missing or invalid".format(source_field))

        if status == "verified" and not row_errors:
            verified[key] = row
        elif row_errors:
            stats["blocked_rows"] += 1
            errors.append(
                "source queue row {0} {1}/{2}: {3}".format(
                    index,
                    barcode or "missing-gtin",
                    retailer or "missing-retailer",
                    "; ".join(row_errors),
                )
            )

    return verified


def build_rows_from_verified_queue(
    verified_queue: Dict[Tuple[str, str], Dict[str, str]]
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    product_rows_by_barcode: Dict[str, Dict[str, str]] = {}
    offer_rows: List[Dict[str, str]] = []

    for key in sorted(verified_queue):
        barcode, retailer = key
        source_row = verified_queue[key]

        if barcode not in product_rows_by_barcode:
            product_rows_by_barcode[barcode] = {
                "barcode": barcode,
                "name": clean(source_row.get("product_name")),
                "brand": clean(source_row.get("brand")),
                "category": "Baby & Toddler",
                "subcategory": "Baby Meals",
                "ingredients": clean(source_row.get("ingredients")),
                "allergens": clean(source_row.get("allergens")),
                "source_url": clean(source_row.get("ingredients_source_url")),
            }

        stock_status = lower_clean(source_row.get("stock_status")) or "unknown"
        if stock_status not in ALLOWED_STOCK_STATUSES:
            stock_status = "unknown"

        offer_rows.append(
            {
                "barcode": barcode,
                "retailer": retailer,
                "price": clean(source_row.get("price")),
                "product_url": clean(source_row.get("product_url")),
                "stock_status": stock_status,
                "source_url": clean(source_row.get("price_source_url")),
                "checked_at": clean(source_row.get("checked_at")),
            }
        )

    return list(product_rows_by_barcode.values()), offer_rows


def validate_products(
    product_rows: List[Dict[str, str]],
    verified_queue: Dict[Tuple[str, str], Dict[str, str]],
    live_state: LiveState,
    stats: Dict[str, int],
    errors: List[str],
) -> Set[str]:
    seen_barcodes: Set[str] = set()
    valid_barcodes: Set[str] = set()
    queue_barcodes = {barcode for barcode, _retailer in verified_queue.keys()}

    for index, row in enumerate(product_rows, start=2):
        barcode = normalise_barcode(row.get("barcode"))
        row_errors: List[str] = []

        ok, detail = validate_gtin(barcode)
        if not ok:
            stats["checksum_failures"] += 1
            row_errors.append(detail)
        if barcode in seen_barcodes:
            stats["duplicate_barcodes"] += 1
            row_errors.append("duplicate barcode inside verified products CSV")
        seen_barcodes.add(barcode)
        if barcode in live_state.product_barcodes:
            stats["duplicate_barcodes"] += 1
            row_errors.append("barcode already exists in live products")
        if barcode not in queue_barcodes:
            row_errors.append("barcode has no verified source queue row")
        if not clean(row.get("name")):
            row_errors.append("missing product name")
        if not clean(row.get("brand")):
            row_errors.append("missing brand")
        if clean(row.get("category")) != "Baby & Toddler":
            row_errors.append("category must be Baby & Toddler")
        if clean(row.get("subcategory")) != "Baby Meals":
            row_errors.append("subcategory must be Baby Meals")
        if is_unknown(row.get("ingredients")):
            stats["missing_ingredients"] += 1
            row_errors.append("ingredients must be verified and not unknown")
        if is_unknown(row.get("allergens")):
            stats["missing_allergens"] += 1
            row_errors.append("allergens must be verified and not unknown")
        if not valid_url(row.get("source_url"), require_https=True):
            stats["missing_source_urls"] += 1
            row_errors.append("source_url is missing or invalid")

        if row_errors:
            stats["products_rejected"] += 1
            stats["blocked_rows"] += 1
            errors.append(
                "verified product row {0} {1}: {2}".format(
                    index,
                    barcode or "missing-barcode",
                    "; ".join(row_errors),
                )
            )
        else:
            stats["products_verified"] += 1
            valid_barcodes.add(barcode)

    return valid_barcodes


def validate_offers(
    offer_rows: List[Dict[str, str]],
    verified_queue: Dict[Tuple[str, str], Dict[str, str]],
    valid_product_barcodes: Set[str],
    live_state: LiveState,
    stats: Dict[str, int],
    errors: List[str],
) -> Set[str]:
    seen_offer_keys: Set[Tuple[str, str]] = set()
    valid_offer_barcodes: Set[str] = set()

    for index, row in enumerate(offer_rows, start=2):
        barcode = normalise_barcode(row.get("barcode"))
        retailer = clean(row.get("retailer"))
        key = (barcode, retailer)
        row_errors: List[str] = []

        ok, detail = validate_gtin(barcode)
        if not ok:
            stats["checksum_failures"] += 1
            row_errors.append(detail)
        if barcode not in valid_product_barcodes:
            row_errors.append("offer barcode has no valid verified product row")
        if retailer not in ALLOWED_RETAILERS:
            row_errors.append("retailer must be Tesco, Asda, or Sainsbury's")
        if key not in verified_queue:
            row_errors.append("offer has no verified source queue row")
        if key in live_state.offer_keys:
            stats["duplicate_barcode_retailers"] += 1
            row_errors.append("retailer+barcode already exists in live offers")
        if key in seen_offer_keys:
            stats["duplicate_barcode_retailers"] += 1
            row_errors.append("duplicate barcode+retailer inside verified offers CSV")
        seen_offer_keys.add(key)
        if parse_price(row.get("price")) is None:
            row_errors.append("price is missing or invalid")
        if not valid_url(row.get("product_url"), require_https=True):
            row_errors.append("product_url must start with https://")
        if clean(row.get("stock_status")) not in ALLOWED_STOCK_STATUSES:
            row_errors.append("stock_status must be in_stock, out_of_stock, or unknown")
        if not valid_url(row.get("source_url"), require_https=True):
            stats["missing_source_urls"] += 1
            row_errors.append("source_url is missing or invalid")
        if not clean(row.get("checked_at")):
            row_errors.append("checked_at is missing")

        source_row = verified_queue.get(key)
        if source_row:
            source_price = parse_price(source_row.get("price"))
            offer_price = parse_price(row.get("price"))
            if source_price is None or offer_price is None or abs(source_price - offer_price) > 0.001:
                row_errors.append("offer price does not match verified source queue price")
            if clean(source_row.get("product_url")) != clean(row.get("product_url")):
                row_errors.append("offer product_url does not match verified source queue product_url")

        if row_errors:
            stats["offers_rejected"] += 1
            stats["blocked_rows"] += 1
            errors.append(
                "verified offer row {0} {1}/{2}: {3}".format(
                    index,
                    barcode or "missing-barcode",
                    retailer or "missing-retailer",
                    "; ".join(row_errors),
                )
            )
        else:
            stats["offers_verified"] += 1
            valid_offer_barcodes.add(barcode)

    return valid_offer_barcodes


def write_report(
    stats: Dict[str, int],
    errors: List[str],
    promoted: bool,
    validation_results: Optional[List[Tuple[str, str]]] = None,
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    decision = "PROMOTED" if promoted else "BLOCKED"
    reached_25 = "yes" if stats["baby_meals_after"] >= 25 else "no"
    validation_results = validation_results or [
        ("scripts/validate_baby_meals_verified_batch.py", "BLOCKED" if errors else "PASS"),
        ("run_imports.py", "pending external run"),
        ("coverage_summary_report.py", "pending external run"),
        ("alternatives_quality_report.py", "pending external run"),
        ("validate_backend.py", "pending external run"),
    ]

    lines = [
        "# SafeBite Baby Meals Verified Batch Report",
        "",
        "Generated: {0}".format(date.today().isoformat()),
        "",
        "## Source Workflow",
        "",
        "Use `backend/imports/staged/baby_meals_source_queue.csv` to record source evidence before any live import. Example rows belong in review notes, not as fake CSV rows. A row can move to `verified` only when the GTIN, ingredients, allergens, price, and product URL are all backed by source URLs.",
        "",
        "## Counts",
        "",
        "- Baby Meals count before: {0}".format(stats["baby_meals_before"]),
        "- Baby Meals count after: {0}".format(stats["baby_meals_after"]),
        "- Products staged: {0}".format(stats["products_staged"]),
        "- Products verified: {0}".format(stats["products_verified"]),
        "- Products rejected: {0}".format(stats["products_rejected"]),
        "- Offers staged: {0}".format(stats["offers_staged"]),
        "- Offers verified: {0}".format(stats["offers_verified"]),
        "- Offers rejected: {0}".format(stats["offers_rejected"]),
        "- Source rows: {0}".format(stats["source_rows"]),
        "- Source rows verified: {0}".format(stats["source_verified"]),
        "- Source rows needs_review: {0}".format(stats["source_needs_review"]),
        "- Source rows rejected: {0}".format(stats["source_rejected"]),
        "",
        "## Blockers",
        "",
        "- Duplicate barcodes: {0}".format(stats["duplicate_barcodes"]),
        "- Duplicate barcode + retailer rows: {0}".format(stats["duplicate_barcode_retailers"]),
        "- Rows blocked due to checksum failure: {0}".format(stats["checksum_failures"]),
        "- Rows blocked due to missing ingredients: {0}".format(stats["missing_ingredients"]),
        "- Rows blocked due to missing allergens: {0}".format(stats["missing_allergens"]),
        "- Rows blocked due to missing source URLs: {0}".format(stats["missing_source_urls"]),
        "- Total blocked rows: {0}".format(stats["blocked_rows"]),
        "- Baby Meals reached 25+: {0}".format(reached_25),
        "",
        "## Validation Command Results",
        "",
    ]

    for command, result in validation_results:
        lines.append("- `{0}`: {1}".format(command, result))

    lines.extend(
        [
            "",
            "## Decision",
            "",
            decision,
            "",
        ]
    )

    if errors:
        lines.extend(["## Error Detail", ""])
        for error in errors[:100]:
            lines.append("- {0}".format(error))
        if len(errors) > 100:
            lines.append("- ... {0} more errors omitted".format(len(errors) - 100))
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def validate() -> Tuple[int, List[str], Dict[str, int]]:
    errors: List[str] = []
    stats = base_stats()
    live_state = load_live_state()
    stats["baby_meals_before"] = live_state.baby_meals_count

    queue_rows, queue_errors = load_source_queue(SOURCE_QUEUE_CSV)
    errors.extend(queue_errors)

    stats["source_rows"] = len(queue_rows)

    if errors:
        stats["blocked_rows"] += len(errors)
        stats["baby_meals_after"] = live_state.baby_meals_count
        write_report(stats, errors, promoted=False)
        return 1, errors, stats

    verified_queue = build_verified_queue_index(queue_rows, stats, errors)
    product_rows, offer_rows = build_rows_from_verified_queue(verified_queue)
    stats["products_staged"] = len(product_rows)
    stats["offers_staged"] = len(offer_rows)

    # The staged import CSVs are generated from source queue rows only. When no
    # rows pass, this intentionally leaves header-only files behind.
    write_csv(PRODUCTS_CSV, PRODUCT_HEADERS, product_rows)
    write_csv(OFFERS_CSV, OFFER_HEADERS, offer_rows)

    valid_product_barcodes = validate_products(product_rows, verified_queue, live_state, stats, errors)
    valid_offer_barcodes = validate_offers(
        offer_rows,
        verified_queue,
        valid_product_barcodes,
        live_state,
        stats,
        errors,
    )

    for barcode in sorted(valid_product_barcodes):
        if barcode not in valid_offer_barcodes:
            stats["blocked_rows"] += 1
            errors.append("verified product {0} has no valid verified offer".format(barcode))

    if stats["products_verified"] < MIN_VERIFIED_PRODUCTS_FOR_PROMOTION:
        errors.append(
            "promotion requires at least {0} verified source-backed Baby Meals products; found {1}".format(
                MIN_VERIFIED_PRODUCTS_FOR_PROMOTION,
                stats["products_verified"],
            )
        )

    if not errors:
        # Guarded rewrite keeps generated import CSVs limited to rows that passed this validator.
        write_csv(PRODUCTS_CSV, PRODUCT_HEADERS, product_rows)
        write_csv(OFFERS_CSV, OFFER_HEADERS, offer_rows)

    promoted = not errors and stats["products_verified"] >= MIN_VERIFIED_PRODUCTS_FOR_PROMOTION
    stats["baby_meals_after"] = (
        live_state.baby_meals_count + stats["products_verified"] if promoted else live_state.baby_meals_count
    )
    write_report(stats, errors, promoted=promoted)
    return (0 if promoted else 1), errors, stats


def main() -> int:
    status, errors, stats = validate()
    print("SafeBite Baby Meals verified source batch validation")
    for key in sorted(stats):
        print("- {0}: {1}".format(key, stats[key]))
    if errors:
        print("Validation result: BLOCKED")
        for error in errors:
            print("- {0}".format(error))
    else:
        print("Validation result: PASS")
        print("Promotion gate: READY")
    print("Report: {0}".format(REPORT_PATH))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
