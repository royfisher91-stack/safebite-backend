import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from database import DatabaseManager
from import_utils import (
    build_offer_payload,
    build_product_payload,
    clean_url,
    normalise_product_row,
    parse_price,
    parse_stock,
    safe_str,
)
from services.analysis_service import analyse_product
from services.gtin_service import normalise_barcode, validate_gtin


ACTIVE_RETAILERS = {
    "Tesco": ["tesco"],
    "Asda": ["asda"],
    "Sainsbury's": ["sainsburys", "sainsbury's", "sainsbury", "sainsburys supermarket"],
    "Waitrose": ["waitrose"],
    "Ocado": ["ocado"],
    "Iceland": ["iceland"],
}

FUTURE_COMPATIBLE_RETAILERS = {
    "M&S": ["m&s", "marks and spencer", "marks & spencer", "marks_spencer", "marks-spencer"],
    "Aldi": ["aldi"],
    "Lidl": ["lidl"],
    "Farmfoods": ["farmfoods"],
    "Home Bargains": ["home bargains", "home_bargains", "home-bargains"],
    "B&M": ["b&m", "b and m", "bm", "b_m"],
    "Heron": ["heron", "heron foods"],
}

TARGET_RETAILERS = dict(ACTIVE_RETAILERS)
SUPPORTED_RETAILERS = dict(ACTIVE_RETAILERS)
SUPPORTED_RETAILERS.update(FUTURE_COMPATIBLE_RETAILERS)

ALLOWED_SOURCE_TYPES = {
    "manual_csv",
    "licensed_feed",
    "approved_api",
    "affiliate_feed",
    "supplier_feed",
    "local_business",
}

BLOCKED_SOURCE_TYPES = {
    "scrape",
    "scraper",
    "web_scrape",
    "webscrape",
    "unapproved_scrape",
}

PLACEHOLDER_BARCODES = {
    "0000000000000",
    "1111111111111",
    "1234567890",
    "1234567891",
    "1234567890123",
    "9999999999999",
}

MAX_STAGE_ROWS = 5000
UNKNOWN_SAFETY_REASON = (
    "Bulk intake staged this product without enough verified ingredient/allergen data for a reliable safety decision."
)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    text = safe_str(value)
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _clean_source_type(value: Any) -> str:
    return safe_str(value).lower().replace(" ", "_").replace("-", "_")


def canonical_retailer(value: Any, source_type: str = "") -> str:
    text = safe_str(value)
    if not text:
        return ""

    key = text.lower().replace("_", " ").replace("-", " ").strip()
    for canonical, aliases in SUPPORTED_RETAILERS.items():
        if key == canonical.lower() or key in aliases:
            return canonical

    if _clean_source_type(source_type) == "local_business":
        return text

    return ""


def target_retailer_names() -> List[str]:
    return sorted(TARGET_RETAILERS.keys())


def supported_retailer_names() -> List[str]:
    return sorted(SUPPORTED_RETAILERS.keys())


def _is_placeholder_barcode(barcode: str) -> bool:
    if barcode in PLACEHOLDER_BARCODES:
        return True
    if barcode.startswith("9000000000"):
        return True
    if barcode and len(set(barcode)) == 1:
        return True
    return False


def _valid_url_or_blank(value: Any) -> str:
    text = safe_str(value)
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return text
    return ""


def _first_non_empty(row: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = row.get(key)
        if safe_str(value):
            return safe_str(value)

    lower_lookup = {str(key).strip().lower(): key for key in row.keys()}
    for key in keys:
        source_key = lower_lookup.get(str(key).strip().lower())
        if source_key and safe_str(row.get(source_key)):
            return safe_str(row.get(source_key))
    return ""


def _parse_list_field(value: Any) -> List[str]:
    if isinstance(value, list):
        return [safe_str(item) for item in value if safe_str(item)]

    text = safe_str(value)
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [safe_str(item) for item in parsed if safe_str(item)]
    except Exception:
        pass

    text = text.replace("|", ";")
    if ";" in text:
        parts = text.split(";")
    else:
        parts = text.split(",")
    return [part.strip() for part in parts if part.strip()]


def _source_name(source_name: Any, source_type: str, retailer: str) -> str:
    text = safe_str(source_name)
    if text:
        return text
    if retailer:
        return "{0}_{1}".format(retailer.lower().replace("&", "and").replace(" ", "_"), source_type)
    return source_type or "bulk_intake"


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_bulk_intake_schema(db_path: str) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bulk_intake_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                retailer TEXT,
                status TEXT NOT NULL DEFAULT 'staged',
                file_name TEXT,
                row_count INTEGER DEFAULT 0,
                accepted_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                promoted_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bulk_intake_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                row_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                row_type TEXT NOT NULL DEFAULT 'product_offer',
                barcode TEXT,
                retailer TEXT,
                name TEXT,
                brand TEXT,
                category TEXT,
                subcategory TEXT,
                ingredients_json TEXT DEFAULT '[]',
                allergens_json TEXT DEFAULT '[]',
                price REAL,
                promo_price REAL,
                original_price REAL,
                promo_text TEXT,
                stock_status TEXT DEFAULT 'unknown',
                product_url TEXT,
                image_url TEXT,
                source_url TEXT,
                data_quality_json TEXT DEFAULT '{}',
                warnings_json TEXT DEFAULT '[]',
                errors_json TEXT DEFAULT '[]',
                raw_json TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                promoted_at TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES bulk_intake_batches(id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bulk_intake_rows_batch
            ON bulk_intake_rows (batch_id, status, barcode)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bulk_intake_batches_created
            ON bulk_intake_batches (created_at DESC, id DESC)
            """
        )
        conn.commit()
    finally:
        conn.close()


def product_exists(conn: sqlite3.Connection, barcode: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM products WHERE barcode = ? LIMIT 1",
        (barcode,),
    ).fetchone()
    return row is not None


def _shape_row(
    row: Dict[str, Any],
    row_number: int,
    source_type: str,
    source_name: str,
    retailer: str,
) -> Dict[str, Any]:
    warnings: List[str] = []
    errors: List[str] = []

    row_source_type = _clean_source_type(_first_non_empty(row, ["source_type"]) or source_type)
    row_retailer = canonical_retailer(_first_non_empty(row, ["retailer", "source_retailer"]) or retailer, row_source_type)

    if row_source_type in BLOCKED_SOURCE_TYPES:
        errors.append("source_type is not allowed: {0}".format(row_source_type))
    elif row_source_type not in ALLOWED_SOURCE_TYPES:
        errors.append("source_type must be one of: {0}".format(", ".join(sorted(ALLOWED_SOURCE_TYPES))))

    if not row_retailer:
        errors.append("retailer is not in the approved target list")

    barcode = normalise_barcode(
        _first_non_empty(row, ["barcode", "gtin", "ean", "upc", "product_barcode"])
    )
    if not barcode:
        errors.append("barcode is required; SafeBite does not guess product identifiers")
    else:
        ok, detail = validate_gtin(barcode)
        if not ok:
            errors.append("{0} ({1})".format(detail, barcode))
        if _is_placeholder_barcode(barcode):
            errors.append("placeholder barcode is not allowed ({0})".format(barcode))

    mapped = normalise_product_row(dict(row), retailer=row_retailer) or {}
    name = safe_str(mapped.get("name") or _first_non_empty(row, ["name", "product_name", "title"]))
    brand = safe_str(mapped.get("brand") or _first_non_empty(row, ["brand", "manufacturer"]))
    category = safe_str(mapped.get("category"))
    subcategory = safe_str(mapped.get("subcategory"))
    ingredients = mapped.get("ingredients") or _parse_list_field(_first_non_empty(row, ["ingredients", "ingredient_list"]))
    allergens = mapped.get("allergens") or _parse_list_field(_first_non_empty(row, ["allergens", "allergen_info"]))

    price = parse_price(_first_non_empty(row, ["price", "current_price", "sale_price"]))
    promo_price = parse_price(_first_non_empty(row, ["promo_price", "promotional_price", "offer_price"]))
    original_price = parse_price(_first_non_empty(row, ["original_price", "was_price"]))
    stock_status = parse_stock(
        _first_non_empty(row, ["stock_status", "stock", "availability"]),
        _first_non_empty(row, ["in_stock", "available", "available_for_delivery"]) or None,
    )
    product_url = clean_url(_first_non_empty(row, ["product_url", "url", "link"]))
    image_url = _valid_url_or_blank(_first_non_empty(row, ["image_url", "image", "thumbnail"]))
    source_url = _valid_url_or_blank(_first_non_empty(row, ["source_url", "feed_url", "supplier_url"]))
    promo_text = _first_non_empty(row, ["promo_text", "promotion", "offer_text"])

    if safe_str(_first_non_empty(row, ["product_url", "url", "link"])) and not product_url:
        errors.append("product_url must be a valid http or https URL when provided")

    if not name:
        warnings.append("missing product name; row will remain staged until verified")
    if not brand:
        warnings.append("missing brand")
    if not category or not subcategory:
        warnings.append("missing or unsupported SafeBite category/subcategory")
    if not ingredients:
        warnings.append("missing verified ingredients; safety must remain Unknown")
    allergens_unknown = not allergens or any(str(item).strip().lower() in {"unknown", "null"} for item in allergens)
    if price is None:
        warnings.append("missing price; offer cannot be promoted to live offers")
    if not product_url:
        warnings.append("missing product_url; offer cannot be promoted to live offers")

    if promo_price is not None and price is not None and promo_price > price:
        errors.append("promo_price cannot be greater than price")
    if original_price is not None and original_price < 0:
        errors.append("original_price cannot be negative")

    product_ready = bool(barcode and name and category and subcategory and ingredients)
    offer_ready = bool(barcode and row_retailer and price is not None and price > 0 and product_url)

    if not product_ready:
        warnings.append("product is staged only until required verified product fields are present")
    if not offer_ready:
        warnings.append("retailer availability is staged only until required offer fields are present")

    return {
        "row_number": row_number,
        "status": "rejected" if errors else "accepted",
        "row_type": "product_offer",
        "barcode": barcode,
        "retailer": row_retailer,
        "name": name,
        "brand": brand,
        "category": category,
        "subcategory": subcategory,
        "ingredients": ingredients,
        "allergens": allergens,
        "price": price,
        "promo_price": promo_price,
        "original_price": original_price,
        "promo_text": promo_text,
        "stock_status": stock_status,
        "product_url": product_url,
        "image_url": image_url,
        "source_url": source_url,
        "data_quality": {
            "source_name": source_name,
            "source_type": row_source_type,
            "product_ready": product_ready,
            "offer_ready": offer_ready,
            "safety_source": "verified_product_fields" if ingredients else "unknown",
            "allergen_source": "unknown" if allergens_unknown else "verified_product_fields",
            "availability_source": row_source_type,
        },
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "raw": row,
    }


def stage_bulk_csv(
    db_path: str,
    csv_path: str,
    source_type: str,
    retailer: str,
    source_name: str = "",
    notes: str = "",
    max_rows: int = MAX_STAGE_ROWS,
) -> Dict[str, Any]:
    ensure_bulk_intake_schema(db_path)
    source_type = _clean_source_type(source_type)
    canonical = canonical_retailer(retailer, source_type)
    clean_source_name = _source_name(source_name, source_type, canonical or safe_str(retailer))

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(csv_path)

    shaped_rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            if len(shaped_rows) >= max_rows:
                raise ValueError("bulk intake limit exceeded: max_rows={0}".format(max_rows))
            if not any(safe_str(value) for value in row.values()):
                continue
            shaped_rows.append(
                _shape_row(row, row_number, source_type, clean_source_name, canonical or safe_str(retailer))
            )

    conn = _connect(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO bulk_intake_batches (
                    source_name, source_type, retailer, status, file_name,
                    row_count, accepted_count, rejected_count, warning_count, error_count, notes
                ) VALUES (?, ?, ?, 'staged', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_source_name,
                    source_type,
                    canonical or safe_str(retailer),
                    str(path),
                    len(shaped_rows),
                    sum(1 for row in shaped_rows if row["status"] == "accepted"),
                    sum(1 for row in shaped_rows if row["status"] == "rejected"),
                    sum(len(row["warnings"]) for row in shaped_rows),
                    sum(len(row["errors"]) for row in shaped_rows),
                    notes,
                ),
            )
            batch_id = int(cursor.lastrowid)

            for row in shaped_rows:
                conn.execute(
                    """
                    INSERT INTO bulk_intake_rows (
                        batch_id, row_number, status, row_type, barcode, retailer, name, brand,
                        category, subcategory, ingredients_json, allergens_json, price, promo_price,
                        original_price, promo_text, stock_status, product_url, image_url, source_url,
                        data_quality_json, warnings_json, errors_json, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch_id,
                        row["row_number"],
                        row["status"],
                        row["row_type"],
                        row["barcode"],
                        row["retailer"],
                        row["name"],
                        row["brand"],
                        row["category"],
                        row["subcategory"],
                        _json_dumps(row["ingredients"]),
                        _json_dumps(row["allergens"]),
                        row["price"],
                        row["promo_price"],
                        row["original_price"],
                        row["promo_text"],
                        row["stock_status"],
                        row["product_url"],
                        row["image_url"],
                        row["source_url"],
                        _json_dumps(row["data_quality"]),
                        _json_dumps(row["warnings"]),
                        _json_dumps(row["errors"]),
                        _json_dumps(row["raw"]),
                    ),
                )
        return get_batch_summary(db_path, batch_id)
    finally:
        conn.close()


def get_batch_summary(db_path: str, batch_id: int) -> Dict[str, Any]:
    ensure_bulk_intake_schema(db_path)
    conn = _connect(db_path)
    try:
        batch = conn.execute(
            "SELECT * FROM bulk_intake_batches WHERE id = ?",
            (batch_id,),
        ).fetchone()
        if batch is None:
            raise ValueError("bulk intake batch not found: {0}".format(batch_id))

        rows = conn.execute(
            """
            SELECT status, data_quality_json, warnings_json, errors_json
            FROM bulk_intake_rows
            WHERE batch_id = ?
            """,
            (batch_id,),
        ).fetchall()

        product_ready = 0
        offer_ready = 0
        for row in rows:
            quality = _json_loads(row["data_quality_json"], {})
            if quality.get("product_ready"):
                product_ready += 1
            if quality.get("offer_ready"):
                offer_ready += 1

        payload = dict(batch)
        payload["product_ready_count"] = product_ready
        payload["offer_ready_count"] = offer_ready
        return payload
    finally:
        conn.close()


def list_batch_summaries(db_path: str, limit: int = 20) -> List[Dict[str, Any]]:
    ensure_bulk_intake_schema(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM bulk_intake_batches
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [get_batch_summary(db_path, int(row["id"])) for row in rows]
    finally:
        conn.close()


def _row_to_product_payload(row: sqlite3.Row) -> Dict[str, Any]:
    ingredients = _json_loads(row["ingredients_json"], [])
    allergens = _json_loads(row["allergens_json"], [])
    analysis = analyse_product(
        {
            "name": row["name"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "ingredients": ingredients,
            "allergens": allergens,
        }
    )
    payload = build_product_payload(
        {
            "barcode": row["barcode"],
            "name": row["name"],
            "brand": row["brand"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "ingredients": ingredients,
            "allergens": allergens,
            "image_url": row["image_url"] or "",
            "source": "bulk_intake_verified_product",
            "source_retailer": row["retailer"],
        },
        retailer=row["retailer"],
    )
    payload["safety_score"] = analysis.get("safety_score")
    payload["safety_result"] = analysis.get("safety_result")
    payload["ingredient_reasoning"] = analysis.get("ingredient_reasoning") or UNKNOWN_SAFETY_REASON
    payload["allergen_warnings"] = _json_dumps(analysis.get("allergen_warnings") or [])
    return payload


def _row_to_offer_payload(row: sqlite3.Row) -> Dict[str, Any]:
    cleaned = {
        "barcode": row["barcode"],
        "retailer": row["retailer"],
        "price": row["price"],
        "promo_price": row["promo_price"],
        "original_price": row["original_price"],
        "promo_text": row["promo_text"] or "",
        "stock_status": row["stock_status"] or "unknown",
        "product_url": row["product_url"] or "",
        "image_url": row["image_url"] or "",
        "source": "bulk_intake_retailer_availability",
        "source_retailer": row["retailer"],
    }
    return build_offer_payload(cleaned, retailer=row["retailer"])


def promote_batch(
    db_path: str,
    batch_id: int,
    apply: bool = False,
    update_existing_products: bool = False,
) -> Dict[str, Any]:
    ensure_bulk_intake_schema(db_path)
    manager = DatabaseManager(db_path)
    conn = _connect(db_path)
    stats = {
        "batch_id": batch_id,
        "apply": apply,
        "products_created": 0,
        "products_skipped": 0,
        "offers_upserted": 0,
        "offers_skipped": 0,
        "blocked_rows": 0,
        "messages": [],
    }

    try:
        batch = conn.execute(
            "SELECT * FROM bulk_intake_batches WHERE id = ?",
            (batch_id,),
        ).fetchone()
        if batch is None:
            raise ValueError("bulk intake batch not found: {0}".format(batch_id))

        rows = conn.execute(
            """
            SELECT *
            FROM bulk_intake_rows
            WHERE batch_id = ?
            ORDER BY row_number, id
            """,
            (batch_id,),
        ).fetchall()

        for row in rows:
            if row["status"] != "accepted":
                stats["blocked_rows"] += 1
                continue

            quality = _json_loads(row["data_quality_json"], {})
            barcode = safe_str(row["barcode"])
            exists = product_exists(conn, barcode)

            if quality.get("product_ready"):
                if exists and not update_existing_products:
                    stats["products_skipped"] += 1
                else:
                    if apply:
                        manager.upsert_product(_row_to_product_payload(row))
                        conn.execute(
                            "UPDATE bulk_intake_rows SET promoted_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (row["id"],),
                        )
                    stats["products_created"] += 1 if not exists else 0
                    exists = True
            else:
                stats["products_skipped"] += 1

            if quality.get("offer_ready") and (exists or quality.get("product_ready")):
                if apply:
                    manager.upsert_offer(_row_to_offer_payload(row))
                    conn.execute(
                        "UPDATE bulk_intake_rows SET promoted_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (row["id"],),
                    )
                stats["offers_upserted"] += 1
            else:
                stats["offers_skipped"] += 1

        if apply:
            conn.execute(
                """
                UPDATE bulk_intake_batches
                SET status = 'promoted', promoted_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (batch_id,),
            )
            conn.commit()

        if not apply:
            stats["messages"].append("dry run only; pass --apply to write products/offers")
        return stats
    finally:
        conn.close()
