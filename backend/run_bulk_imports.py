import argparse
import os
import sys


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_import_service import DB_DEFAULT, import_retailer_csv
from services.supermarket_coverage_service import find_bulk_raw_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 12 bulk imports from imports/bulk/<retailer>/raw.csv.")
    parser.add_argument("--base-dir", default=os.path.join(BACKEND_DIR, "imports", "bulk"))
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-future-retailers", action="store_true")
    args = parser.parse_args()

    files = find_bulk_raw_files(args.base_dir, active_only=not args.include_future_retailers)
    print("Phase 12 bulk folder scan")
    print("Files found: {0}".format(len(files)))
    if not args.include_future_retailers:
        print("Scope: current coverage retailers only")

    total_rows = 0
    total_imported = 0
    total_skipped = 0
    total_errors = 0

    for item in files:
        summary = import_retailer_csv(
            csv_path=item["path"],
            retailer=item["retailer"],
            db_path=args.db,
            dry_run=args.dry_run,
        )
        total_rows += int(summary["rows_total"])
        total_imported += int(summary["rows_imported"])
        total_skipped += int(summary["rows_skipped"])
        total_errors += int(summary["errors_count"])
        print(
            "{0}: rows={1}, imported={2}, skipped={3}, errors={4}, status={5}".format(
                summary["retailer"],
                summary["rows_total"],
                summary["rows_imported"],
                summary["rows_skipped"],
                summary["errors_count"],
                summary["status"],
            )
        )

    print("Totals: rows={0}, imported={1}, skipped={2}, errors={3}".format(
        total_rows,
        total_imported,
        total_skipped,
        total_errors,
    ))
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
