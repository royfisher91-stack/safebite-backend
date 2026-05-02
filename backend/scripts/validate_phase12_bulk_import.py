import os
import sqlite3
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_import_service import (
    ACTIVE_COVERAGE_RETAILERS,
    ADAPTER_MODULES,
    DB_DEFAULT,
    FUTURE_COMPATIBLE_RETAILERS,
    ensure_phase12_schema,
    load_adapter,
)


REQUIRED_PRODUCT_COLUMNS = {
    "barcode",
    "name",
    "brand",
    "category",
    "subcategory",
    "ingredients",
    "allergens",
    "image_url",
    "source",
    "data_quality_status",
    "last_verified_at",
}

REQUIRED_RETAILER_OFFER_COLUMNS = {
    "barcode",
    "retailer",
    "price",
    "promo_price",
    "multibuy_text",
    "stock_status",
    "product_url",
    "source",
    "last_checked_at",
}

REQUIRED_BATCH_COLUMNS = {
    "id",
    "retailer",
    "source_file",
    "status",
    "rows_total",
    "rows_imported",
    "rows_skipped",
    "errors_count",
    "created_at",
}

REQUIRED_ERROR_COLUMNS = {
    "batch_id",
    "row_number",
    "retailer",
    "barcode",
    "reason",
    "raw_row_preview",
}


def table_columns(conn: sqlite3.Connection, table: str) -> set:
    return {row[1] for row in conn.execute("PRAGMA table_info({0})".format(table)).fetchall()}


def main() -> int:
    errors = []
    warnings = []
    ensure_phase12_schema(DB_DEFAULT)

    conn = sqlite3.connect(DB_DEFAULT)
    try:
        checks = [
            ("products", REQUIRED_PRODUCT_COLUMNS),
            ("retailer_offers", REQUIRED_RETAILER_OFFER_COLUMNS),
            ("product_import_batches", REQUIRED_BATCH_COLUMNS),
            ("product_import_errors", REQUIRED_ERROR_COLUMNS),
        ]
        for table, required in checks:
            missing = sorted(required - table_columns(conn, table))
            if missing:
                errors.append("{0} missing columns: {1}".format(table, ", ".join(missing)))
    finally:
        conn.close()

    for retailer in sorted(ADAPTER_MODULES.keys()):
        adapter = load_adapter(retailer)
        mapped = adapter(
            {
                "barcode": "5056000505910",
                "name": "Example Product",
                "brand": "Example Brand",
                "category": "Baby & Toddler",
                "subcategory": "Formula Milk",
                "ingredients": "Milk",
                "allergens": "Milk",
                "price": "1.23",
                "stock_status": "in stock",
                "product_url": "https://example.com/product",
            }
        )
        expected = {
            "barcode",
            "name",
            "brand",
            "category",
            "subcategory",
            "ingredients",
            "allergens",
            "image_url",
            "retailer",
            "price",
            "promo_price",
            "multibuy_text",
            "stock_status",
            "product_url",
            "source",
        }
        missing = sorted(expected - set(mapped.keys()))
        if missing:
            errors.append("{0} adapter missing standard keys: {1}".format(retailer, ", ".join(missing)))

    print("Phase 12 bulk import validation")
    print("- adapters: {0}".format(len(ADAPTER_MODULES)))
    print("- active_coverage_retailers: {0}".format(", ".join(ACTIVE_COVERAGE_RETAILERS)))
    print("- future_compatible_retailers: {0}".format(", ".join(FUTURE_COMPATIBLE_RETAILERS)))
    print("- warnings: {0}".format(len(warnings)))
    print("- errors: {0}".format(len(errors)))
    if errors:
        print("\nErrors")
        for item in errors:
            print("- {0}".format(item))
        return 1
    print("Phase 12 bulk import validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
