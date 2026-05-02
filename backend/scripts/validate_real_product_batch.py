from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.gtin_service import normalise_barcode, validate_gtin


EXPECTED_HEADERS = [
    "barcode",
    "name",
    "brand",
    "category",
    "subcategory",
    "ingredients",
    "allergens",
    "retailer",
    "price",
    "promo_price",
    "original_price",
    "promo_text",
    "stock_status",
    "product_url",
    "image_url",
    "source_type",
    "source_url",
]

ALLOWED_SOURCE_TYPES = {
    "manual_csv",
    "licensed_feed",
    "approved_api",
    "supplier_feed",
    "affiliate_feed",
    "local_business",
}

ALLOWED_STOCK_STATUSES = {"in_stock", "out_of_stock", "unknown"}

RETAILER_ALIASES = {
    "tesco": "Tesco",
    "asda": "Asda",
    "sainsburys": "Sainsbury's",
    "sainsbury": "Sainsbury's",
    "sainsbury's": "Sainsbury's",
    "waitrose": "Waitrose",
    "ocado": "Ocado",
    "morrisons": "Morrisons",
    "morrison": "Morrisons",
    "marks_spencer": "M&S",
    "marks spencer": "M&S",
    "marks and spencer": "M&S",
    "marks & spencer": "M&S",
    "m&s": "M&S",
    "iceland": "Iceland",
    "aldi": "Aldi",
    "lidl": "Lidl",
    "farmfoods": "Farmfoods",
    "home_bargains": "Home Bargains",
    "home bargains": "Home Bargains",
    "b&m": "B&M",
    "bm": "B&M",
    "b and m": "B&M",
    "heron": "Heron",
    "heron foods": "Heron",
}

SUPPORTED_RETAILERS = {
    "Tesco",
    "Asda",
    "Sainsbury's",
    "Waitrose",
    "Ocado",
    "Morrisons",
    "M&S",
    "Iceland",
    "Aldi",
    "Lidl",
    "Farmfoods",
    "Home Bargains",
    "B&M",
    "Heron",
}

CATEGORY_SUBCATEGORIES = {
    "Baby & Toddler": {
        "Baby Formula",
        "Baby Meals",
        "Baby Porridge",
        "Fruit Puree",
        "Toddler Yoghurt",
        "Toddler Milk",
        "Formula Milk",
        "Porridge",
    },
    "Baby Snacks": {
        "Baby Snacks",
        "Baby Crisps & Puffs",
        "Oat Snacks",
    },
    "SafeHome": {
        "Household Cleaning",
        "Laundry",
        "Dishwasher",
        "Surface Cleaners",
    },
    "Household": {
        "Household Cleaning",
        "Laundry",
        "Dishwasher",
        "Surface Cleaners",
    },
}

PLACEHOLDER_BARCODES = {
    "0000000000000",
    "1111111111111",
    "1234567890123",
    "9999999999999",
}


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalise_key(value: object) -> str:
    return clean(value).lower().replace("-", " ").replace("_", " ")


def normalise_retailer(value: object) -> str:
    key = normalise_key(value)
    return RETAILER_ALIASES.get(key, clean(value))


def valid_url_or_blank(value: object) -> bool:
    text = clean(value)
    if not text:
        return True
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_missing_unknown(value: object) -> bool:
    text = clean(value).lower()
    return text in {"", "unknown", "data unavailable", "unavailable", "null", "none"}


def find_csv_files(
    base: Path,
    explicit_files: Sequence[str],
    include_raw: bool,
    include_legacy: bool,
) -> List[Path]:
    if explicit_files:
        return [Path(item) for item in explicit_files]
    files = sorted(path for path in base.glob("*/*.csv") if path.is_file())
    if not include_raw:
        files = [path for path in files if path.name != "raw.csv"]
    if not include_legacy:
        files = [path for path in files if path.parent.name != "baby_toddler"]
    return files


def validate_headers(path: Path, headers: Optional[List[str]]) -> List[str]:
    if headers is None:
        return ["missing CSV header"]
    if headers != EXPECTED_HEADERS:
        return [
            "header mismatch in {0}; expected exactly: {1}".format(
                path,
                ",".join(EXPECTED_HEADERS),
            )
        ]
    return []


def validate_category(category: str, subcategory: str) -> Optional[str]:
    if category not in CATEGORY_SUBCATEGORIES:
        return "category is not approved: {0}".format(category or "missing")
    if subcategory not in CATEGORY_SUBCATEGORIES[category]:
        return "subcategory is not approved for {0}: {1}".format(category, subcategory or "missing")
    return None


def validate_row(row: Dict[str, str], row_number: int, path: Path) -> Tuple[List[str], List[str], Tuple[str, str]]:
    errors: List[str] = []
    warnings: List[str] = []

    barcode = normalise_barcode(row.get("barcode"))
    name = clean(row.get("name"))
    retailer = normalise_retailer(row.get("retailer"))
    category = clean(row.get("category"))
    subcategory = clean(row.get("subcategory"))
    stock_status = clean(row.get("stock_status")).lower() or "unknown"
    source_type = clean(row.get("source_type")).lower().replace("-", "_").replace(" ", "_")

    if not barcode:
        errors.append("barcode is required")
    else:
        ok, detail = validate_gtin(barcode)
        if not ok:
            errors.append(detail)
        if barcode in PLACEHOLDER_BARCODES or (barcode and len(set(barcode)) == 1):
            errors.append("placeholder barcode is not allowed")

    if not name:
        errors.append("product name is required")

    if retailer not in SUPPORTED_RETAILERS:
        errors.append("retailer is not supported: {0}".format(retailer or "missing"))

    category_error = validate_category(category, subcategory)
    if category_error:
        errors.append(category_error)

    if stock_status not in ALLOWED_STOCK_STATUSES:
        errors.append("stock_status must be one of: {0}".format(", ".join(sorted(ALLOWED_STOCK_STATUSES))))

    if not source_type:
        errors.append("source_type is required")
    elif source_type not in ALLOWED_SOURCE_TYPES:
        errors.append("source_type must be one of: {0}".format(", ".join(sorted(ALLOWED_SOURCE_TYPES))))

    for field in ["product_url", "image_url", "source_url"]:
        if not valid_url_or_blank(row.get(field)):
            errors.append("{0} must be a valid http(s) URL when present".format(field))

    if is_missing_unknown(row.get("ingredients")):
        warnings.append("missing ingredients; safety must remain unknown/data unavailable")

    if is_missing_unknown(row.get("allergens")):
        warnings.append("missing allergens; allergen safety must remain unknown/data unavailable")

    return errors, warnings, (barcode, retailer)


def validate_file(path: Path, seen: Dict[Tuple[str, str], Path]) -> Dict[str, int]:
    stats = {
        "total_rows": 0,
        "valid_rows": 0,
        "warnings": 0,
        "errors": 0,
        "blocked_rows": 0,
        "duplicates": 0,
        "malformed_rows": 0,
    }
    messages: List[str] = []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header_errors = validate_headers(path, reader.fieldnames)
            if header_errors:
                for error in header_errors:
                    print("ERROR {0}: {1}".format(path, error))
                stats["errors"] += len(header_errors)
                stats["blocked_rows"] += 1
                return stats

            for row_number, row in enumerate(reader, start=2):
                stats["total_rows"] += 1
                if None in row:
                    stats["malformed_rows"] += 1
                    stats["errors"] += 1
                    stats["blocked_rows"] += 1
                    print("ERROR {0}:{1}: malformed row has too many columns".format(path, row_number))
                    continue

                errors, warnings, duplicate_key = validate_row(row, row_number, path)
                if duplicate_key[0] and duplicate_key[1]:
                    if duplicate_key in seen:
                        errors.append(
                            "duplicate barcode+retailer also seen in {0}".format(seen[duplicate_key])
                        )
                        stats["duplicates"] += 1
                    else:
                        seen[duplicate_key] = path

                if warnings:
                    stats["warnings"] += len(warnings)
                    for warning in warnings:
                        messages.append("WARNING {0}:{1}: {2}".format(path, row_number, warning))

                if errors:
                    stats["errors"] += len(errors)
                    stats["blocked_rows"] += 1
                    for error in errors:
                        messages.append("ERROR {0}:{1}: {2}".format(path, row_number, error))
                else:
                    stats["valid_rows"] += 1
    except csv.Error as exc:
        stats["errors"] += 1
        stats["blocked_rows"] += 1
        stats["malformed_rows"] += 1
        messages.append("ERROR {0}: malformed CSV: {1}".format(path, exc))
    except OSError as exc:
        stats["errors"] += 1
        stats["blocked_rows"] += 1
        messages.append("ERROR {0}: could not read file: {1}".format(path, exc))

    for message in messages:
        print(message)
    return stats


def add_stats(total: Dict[str, int], part: Dict[str, int]) -> None:
    for key, value in part.items():
        total[key] = total.get(key, 0) + value


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate real SafeBite product batch CSV files before promotion.")
    parser.add_argument(
        "--base-dir",
        default=str(BACKEND_DIR / "imports" / "bulk"),
        help="Bulk import directory to scan when --csv is not supplied.",
    )
    parser.add_argument("--csv", action="append", default=[], help="Specific CSV file to validate. May be repeated.")
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Include legacy retailer raw.csv files in the default bulk-folder scan.",
    )
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Include legacy combined category folders such as imports/bulk/baby_toddler.",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    files = find_csv_files(base_dir, args.csv, args.include_raw, args.include_legacy)
    seen: Dict[Tuple[str, str], Path] = {}
    totals = {
        "total_rows": 0,
        "valid_rows": 0,
        "warnings": 0,
        "errors": 0,
        "blocked_rows": 0,
        "duplicates": 0,
        "malformed_rows": 0,
    }

    if not files:
        print("No CSV files found for validation.")
        totals["errors"] = 1
    else:
        for path in files:
            add_stats(totals, validate_file(path, seen))

    print("SafeBite real product batch validation")
    print("- files_checked: {0}".format(len(files)))
    print("- total rows: {0}".format(totals["total_rows"]))
    print("- valid rows: {0}".format(totals["valid_rows"]))
    print("- warnings: {0}".format(totals["warnings"]))
    print("- errors: {0}".format(totals["errors"]))
    print("- blocked rows: {0}".format(totals["blocked_rows"]))
    print("- duplicates: {0}".format(totals["duplicates"]))
    print("- malformed rows: {0}".format(totals["malformed_rows"]))

    if totals["errors"] > 0:
        print("Real product batch validation: BLOCKED")
        return 1

    print("Real product batch validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
