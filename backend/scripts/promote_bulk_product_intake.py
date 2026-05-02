import argparse
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_product_intake_service import promote_batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run or apply promotion of a staged SafeBite bulk intake batch.")
    parser.add_argument("--db", default=os.path.join(BACKEND_DIR, "safebite.db"))
    parser.add_argument("--batch-id", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Preview promotion without writing products/offers")
    parser.add_argument("--apply", action="store_true", help="Write ready rows to products/offers")
    parser.add_argument("--update-existing-products", action="store_true", help="Allow verified product fields to update existing products")
    args = parser.parse_args()

    stats = promote_batch(
        db_path=args.db,
        batch_id=args.batch_id,
        apply=args.apply,
        update_existing_products=args.update_existing_products,
    )

    print("Bulk intake promotion {0}".format("apply" if args.apply else "dry run"))
    print("Batch id: {0}".format(stats["batch_id"]))
    print("Products created: {0}".format(stats["products_created"]))
    print("Products skipped: {0}".format(stats["products_skipped"]))
    print("Offers upserted: {0}".format(stats["offers_upserted"]))
    print("Offers skipped: {0}".format(stats["offers_skipped"]))
    print("Blocked rows: {0}".format(stats["blocked_rows"]))
    for message in stats["messages"]:
        print("- {0}".format(message))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
