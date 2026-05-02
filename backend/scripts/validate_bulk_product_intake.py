import os
import sqlite3
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_product_intake_service import (
    ALLOWED_SOURCE_TYPES,
    FUTURE_COMPATIBLE_RETAILERS,
    canonical_retailer,
    ensure_bulk_intake_schema,
    supported_retailer_names,
    target_retailer_names,
)


def main() -> int:
    errors = []
    warnings = []

    expected = {
        "Tesco",
        "Asda",
        "Sainsbury's",
        "Waitrose",
        "Ocado",
        "Iceland",
    }

    registered = set(target_retailer_names())
    missing = sorted(expected - registered)
    extra = sorted(registered - expected)
    if missing:
        errors.append("missing target retailers: {0}".format(", ".join(missing)))
    if extra:
        errors.append("unexpected target retailers: {0}".format(", ".join(extra)))

    if "scrape" in ALLOWED_SOURCE_TYPES or "web_scrape" in ALLOWED_SOURCE_TYPES:
        errors.append("scrape source types must not be allowed")

    supported = set(supported_retailer_names())
    missing_future = sorted(set(FUTURE_COMPATIBLE_RETAILERS.keys()) - supported)
    if missing_future:
        errors.append("missing future-compatible retailers: {0}".format(", ".join(missing_future)))

    alias_checks = {
        "sainsburys": "Sainsbury's",
        "marks and spencer": "M&S",
        "home_bargains": "Home Bargains",
        "bm": "B&M",
    }
    for raw, expected_name in alias_checks.items():
        actual = canonical_retailer(raw, "manual_csv")
        if actual != expected_name:
            errors.append("retailer alias failed: {0} -> {1}".format(raw, actual))

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT UNIQUE)")
        conn.execute("CREATE TABLE offers (id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT)")
        conn.commit()
    finally:
        conn.close()

    ensure_bulk_intake_schema(":memory:")

    print("Bulk product intake validation")
    print("- current_target_retailers: {0}".format(", ".join(target_retailer_names())))
    print("- future_compatible_retailers: {0}".format(", ".join(sorted(FUTURE_COMPATIBLE_RETAILERS.keys()))))
    print("- supported_retailers: {0}".format(len(supported_retailer_names())))
    print("- allowed_source_types: {0}".format(", ".join(sorted(ALLOWED_SOURCE_TYPES))))
    print("- warnings: {0}".format(len(warnings)))
    print("- errors: {0}".format(len(errors)))

    if warnings:
        print("\nWarnings")
        for item in warnings:
            print("- {0}".format(item))

    if errors:
        print("\nErrors")
        for item in errors:
            print("- {0}".format(item))
        return 1

    print("Bulk product intake validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
