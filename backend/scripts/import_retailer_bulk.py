import argparse
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_import_service import DB_DEFAULT, import_retailer_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a retailer CSV through the Phase 12 SafeBite bulk importer.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--retailer", required=True)
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    summary = import_retailer_csv(
        csv_path=args.csv,
        retailer=args.retailer,
        db_path=args.db,
        dry_run=args.dry_run,
    )

    print("Phase 12 retailer bulk import")
    print("Batch id: {0}".format(summary["batch_id"]))
    print("Retailer: {0}".format(summary["retailer"]))
    print("Status: {0}".format(summary["status"]))
    print("Rows total: {0}".format(summary["rows_total"]))
    print("Rows imported: {0}".format(summary["rows_imported"]))
    print("Rows skipped: {0}".format(summary["rows_skipped"]))
    print("Errors: {0}".format(summary["errors_count"]))
    if summary["errors"]:
        print("Error preview:")
        for item in summary["errors"][:10]:
            print("- {0}".format(item))
    return 1 if summary["errors_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

