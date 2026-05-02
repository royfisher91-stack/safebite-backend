import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.phase1_batch_service import import_batch
from services.phase2_data_quality import refresh_existing_quality_records
from services.phase2_reporting import build_phase2_summary, render_phase2_text_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a small verified SafeBite Phase 1 batch.")
    parser.add_argument("--db", required=True, help="Path to safebite.db")
    parser.add_argument("--products", required=True, help="Path to products batch CSV")
    parser.add_argument("--offers", required=True, help="Path to offers batch CSV")
    args = parser.parse_args()

    errors, warnings, stats = import_batch(args.db, args.products, args.offers)

    if errors or warnings:
        print("Batch import blocked")
        if errors:
            print("\nErrors:")
            for item in errors:
                print("- {0}".format(item))
        if warnings:
            print("\nWarnings:")
            for item in warnings:
                print("- {0}".format(item))
        print("\nLocked rule triggered: import stopped because Phase 1 requires 0 errors and 0 warnings.")
        return 1

    print("Batch import complete")
    print("Products loaded: {0}".format(stats["products_loaded"]))
    print("Offers upserted:  {0}".format(stats["offers_upserted"]))
    print("")
    print("Phase 2 data quality")
    refresh_existing_quality_records(args.db)
    print(render_phase2_text_report(build_phase2_summary(args.db)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
