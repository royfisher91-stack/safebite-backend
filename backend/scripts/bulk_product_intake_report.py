import argparse
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_product_intake_service import list_batch_summaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Report staged SafeBite bulk intake batches.")
    parser.add_argument("--db", default=os.path.join(BACKEND_DIR, "safebite.db"))
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    batches = list_batch_summaries(args.db, limit=args.limit)

    print("BULK PRODUCT INTAKE REPORT")
    print("=" * 80)
    if not batches:
        print("No bulk intake batches found.")
        return 0

    for batch in batches:
        print("#{0} | {1} | {2} | {3}".format(
            batch["id"],
            batch["retailer"],
            batch["source_type"],
            batch["status"],
        ))
        print("- rows: {0}, accepted: {1}, rejected: {2}".format(
            batch["row_count"],
            batch["accepted_count"],
            batch["rejected_count"],
        ))
        print("- product_ready: {0}, offer_ready: {1}".format(
            batch["product_ready_count"],
            batch["offer_ready_count"],
        ))
        print("- warnings: {0}, errors: {1}".format(
            batch["warning_count"],
            batch["error_count"],
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

