import argparse
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.phase1_constants import CORE_SUBCATEGORY_TARGETS

TARGET_RETAILERS = ["Tesco", "Asda", "Sainsbury's", "Waitrose", "Ocado", "Iceland", "Morrisons"]


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def split_csv(value: object) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in str(value).split(",") if item.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description="SafeBite Phase 1 coverage summary")
    parser.add_argument("--db", required=True, help="Path to safebite.db")
    args = parser.parse_args()

    conn = connect(args.db)
    try:
        products_total = conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
        offers_total = conn.execute("SELECT COUNT(*) AS count FROM offers").fetchone()["count"]

        print("PHASE 1 COVERAGE SUMMARY")
        print("Products total: {0}".format(products_total))
        print("Offers total:   {0}".format(offers_total))
        print("")

        sub_rows = conn.execute(
            """
            SELECT category, subcategory, COUNT(*) AS product_count
            FROM products
            GROUP BY category, subcategory
            ORDER BY category COLLATE NOCASE, subcategory COLLATE NOCASE
            """
        ).fetchall()
        counts = {row["subcategory"]: row["product_count"] for row in sub_rows}

        print("Core subcategory depth progress")
        for name, target in CORE_SUBCATEGORY_TARGETS.items():
            count = int(counts.get(name, 0) or 0)
            min_target = target["min"]
            max_target = target["max"]
            if count < min_target:
                status = "BUILDING"
            elif count <= max_target:
                status = "READY"
            else:
                status = "OVER_TARGET_REVIEW"
            print("- {0}: {1} product(s) | target {2}-{3} | {4}".format(
                name, count, min_target, max_target, status
            ))

        print("\nRetailer offer coverage")
        retailer_rows = conn.execute(
            """
            SELECT retailer,
                   COUNT(*) AS offer_count,
                   COUNT(DISTINCT barcode) AS product_count,
                   ROUND(AVG(CASE WHEN promo_price IS NOT NULL AND promo_price > 0 THEN promo_price ELSE price END), 2) AS avg_price,
                   ROUND(MIN(CASE WHEN promo_price IS NOT NULL AND promo_price > 0 THEN promo_price ELSE price END), 2) AS min_price,
                   ROUND(MAX(CASE WHEN promo_price IS NOT NULL AND promo_price > 0 THEN promo_price ELSE price END), 2) AS max_price
            FROM offers
            GROUP BY retailer
            ORDER BY retailer COLLATE NOCASE
            """
        ).fetchall()
        for row in retailer_rows:
            print("- {0}: {1} offer(s), {2} product(s), avg={3}, min={4}, max={5}".format(
                row["retailer"], row["offer_count"], row["product_count"], row["avg_price"], row["min_price"], row["max_price"]
            ))

        product_rows = conn.execute(
            """
            SELECT p.barcode, p.name, p.category, p.subcategory,
                   COUNT(o.id) AS offer_count,
                   GROUP_CONCAT(DISTINCT o.retailer) AS retailers
            FROM products p
            LEFT JOIN offers o ON o.barcode = p.barcode
            GROUP BY p.barcode, p.name, p.category, p.subcategory
            ORDER BY p.subcategory COLLATE NOCASE, p.name COLLATE NOCASE
            """
        ).fetchall()

        issue_count = 0
        missing_retailer_count = 0

        print("\nProducts without offers")
        no_offer_rows = [row for row in product_rows if int(row["offer_count"] or 0) == 0]
        if not no_offer_rows:
            print("- none")
        else:
            issue_count += len(no_offer_rows)
            for row in no_offer_rows:
                print("- {0} | {1}".format(row["barcode"], row["name"]))

        for row in product_rows:
            retailers = split_csv(row["retailers"])
            missing = [retailer for retailer in TARGET_RETAILERS if retailer not in retailers]
            if missing:
                missing_retailer_count += 1

        print("\nProducts missing one or more target retailers: {0}".format(missing_retailer_count))
        print("Coverage issue count: {0}".format(issue_count))
        return 0 if issue_count == 0 else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
