import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.phase2_data_quality import refresh_existing_quality_records
from services.phase2_reporting import build_phase2_summary, render_phase2_text_report


def main() -> int:
    parser = argparse.ArgumentParser(description="SafeBite Phase 2 data quality report")
    parser.add_argument("--db", default="safebite.db", help="Path to safebite.db")
    parser.add_argument("--no-refresh", action="store_true", help="Only read existing Phase 2 quality tables")
    parser.add_argument("--fail-on-errors", action="store_true", help="Exit non-zero if Phase 2 validation errors exist")
    args = parser.parse_args()

    if not args.no_refresh:
        stats = refresh_existing_quality_records(args.db)
        print("Phase 2 audit refreshed: {0} product(s), {1} offer(s)".format(
            stats["products_audited"],
            stats["offers_audited"],
        ))
        print("")

    summary = build_phase2_summary(args.db)
    print(render_phase2_text_report(summary))

    if args.fail_on_errors and int(summary.get("validation_error_total", 0) or 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
