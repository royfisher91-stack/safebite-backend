import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import database as database_module
import services.community_service as community_service_module
from database import DatabaseManager


def label_for_row(row: dict[str, Any]) -> str:
    return "{barcode} | {product_name} | {feedback_type}".format(
        barcode=row.get("barcode") or "",
        product_name=row.get("product_name") or "",
        feedback_type=row.get("feedback_type") or "",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SafeBite Phase 6 community layer quality")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)
    community_service_module.db = database_module.db

    conn = database_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM community_feedback
        ORDER BY created_at DESC, id DESC
        """
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    visible_rows = [row for row in rows if bool(row.get("is_visible")) and not bool(row.get("is_flagged"))]
    flagged_rows = [row for row in rows if bool(row.get("is_flagged"))]
    hidden_rows = [row for row in rows if not bool(row.get("is_visible"))]
    invalid_rows = [
        row
        for row in rows
        if str(row.get("feedback_type") or "").strip().lower() not in {"positive", "negative"}
        or len(str(row.get("comment") or "").strip()) < 4
    ]

    feedback_type_counts: Counter[str] = Counter()
    allergy_tag_counts: Counter[str] = Counter()
    condition_tag_counts: Counter[str] = Counter()
    barcode_counts: Counter[str] = Counter()
    negative_rows: list[str] = []

    for row in visible_rows:
        feedback_type = str(row.get("feedback_type") or "").strip().lower()
        feedback_type_counts[feedback_type] += 1
        barcode_counts[str(row.get("barcode") or "")] += 1

        allergy_tags = database_module._safe_json_loads(row.get("allergy_tags_json"), [])
        condition_tags = database_module._safe_json_loads(row.get("condition_tags_json"), [])
        allergy_tag_counts.update([str(tag).strip() for tag in allergy_tags if str(tag).strip()])
        condition_tag_counts.update([str(tag).strip() for tag in condition_tags if str(tag).strip()])

        if feedback_type == "negative":
            negative_rows.append(label_for_row(row))

    print("PHASE 6 COMMUNITY LAYER REPORT")
    print("=" * 80)
    print(f"Community feedback total: {len(rows)}")
    print(f"Visible public feedback: {len(visible_rows)}")
    print(f"Flagged feedback: {len(flagged_rows)}")
    print(f"Hidden feedback: {len(hidden_rows)}")
    print(f"Invalid feedback rows: {len(invalid_rows)}")

    print("\nFeedback type counts")
    if feedback_type_counts:
        for key, count in feedback_type_counts.most_common():
            print(f"- {key}: {count}")
    else:
        print("- none")

    print("\nAllergy tag counts")
    if allergy_tag_counts:
        for key, count in allergy_tag_counts.most_common():
            print(f"- {key}: {count}")
    else:
        print("- none")

    print("\nCondition tag counts")
    if condition_tag_counts:
        for key, count in condition_tag_counts.most_common():
            print(f"- {key}: {count}")
    else:
        print("- none")

    print("\nProducts with the most visible community feedback")
    if barcode_counts:
        for barcode, count in barcode_counts.most_common(10):
            print(f"- {barcode}: {count}")
    else:
        print("- none")

    print("\nRecent visible negative reactions")
    if negative_rows:
        for row_label in negative_rows[:10]:
            print(f"- {row_label}")
    else:
        print("- none")

    print("\nInvalid feedback rows")
    if invalid_rows:
        for row in invalid_rows[:10]:
            print(f"- {label_for_row(row)}")
    else:
        print("- none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
