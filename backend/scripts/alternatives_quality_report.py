import argparse
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.phase1_alternatives_service import build_alternatives


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def main() -> int:
    parser = argparse.ArgumentParser(description="SafeBite Phase 1 alternatives quality report")
    parser.add_argument("--db", required=True, help="Path to safebite.db")
    args = parser.parse_args()

    conn = connect(args.db)
    try:
        rows = conn.execute(
            """
            SELECT barcode, name, category, subcategory
            FROM products
            ORDER BY subcategory COLLATE NOCASE, name COLLATE NOCASE
            """
        ).fetchall()

        issue_count = 0
        print("PHASE 1 ALTERNATIVES QUALITY REPORT\n")

        for row in rows:
            alt = build_alternatives(conn, row["barcode"])
            issues = []
            if alt.get("error"):
                issues.append("product missing")
            else:
                same_count = conn.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM products
                    WHERE barcode != ? AND category = ? AND subcategory = ?
                    """,
                    (row["barcode"], row["category"], row["subcategory"]),
                ).fetchone()["count"]
                if int(same_count or 0) > 0 and not alt.get("same_category_option"):
                    issues.append("same-subcategory products exist but no priced same_category_option")

                for key in ("safer_option", "cheaper_option", "same_category_option"):
                    option = alt.get(key)
                    if option and option.get("subcategory") != row["subcategory"]:
                        issues.append("{0} cross-subcategory mismatch".format(key))

            if issues:
                issue_count += 1
                print("- {0} | {1} | {2}".format(row["barcode"], row["name"], "; ".join(issues)))

        if issue_count == 0:
            print("No alternatives quality issues found.")

        print("\nAlternatives issue count: {0}".format(issue_count))
        return 0 if issue_count == 0 else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
