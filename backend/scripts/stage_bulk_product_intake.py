import argparse
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_product_intake_service import stage_bulk_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage a controlled SafeBite bulk product/feed CSV.")
    parser.add_argument("--db", default=os.path.join(BACKEND_DIR, "safebite.db"))
    parser.add_argument("--csv", required=True, help="Path to the supplier/feed/manual CSV")
    parser.add_argument("--source-type", required=True, help="manual_csv, licensed_feed, approved_api, affiliate_feed, supplier_feed, local_business")
    parser.add_argument("--retailer", required=True, help="Target retailer name")
    parser.add_argument("--source-name", default="", help="Readable source/feed name")
    parser.add_argument("--notes", default="")
    parser.add_argument("--max-rows", type=int, default=5000)
    args = parser.parse_args()

    summary = stage_bulk_csv(
        db_path=args.db,
        csv_path=args.csv,
        source_type=args.source_type,
        retailer=args.retailer,
        source_name=args.source_name,
        notes=args.notes,
        max_rows=args.max_rows,
    )

    print("Bulk intake staged")
    print("Batch id: {0}".format(summary["id"]))
    print("Source: {0} ({1})".format(summary["source_name"], summary["source_type"]))
    print("Retailer: {0}".format(summary["retailer"]))
    print("Rows: {0}".format(summary["row_count"]))
    print("Accepted: {0}".format(summary["accepted_count"]))
    print("Rejected: {0}".format(summary["rejected_count"]))
    print("Warnings: {0}".format(summary["warning_count"]))
    print("Errors: {0}".format(summary["error_count"]))
    print("Product ready: {0}".format(summary["product_ready_count"]))
    print("Offer ready: {0}".format(summary["offer_ready_count"]))
    return 1 if summary["rejected_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

