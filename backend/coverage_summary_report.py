import sqlite3
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "safebite.db"
TARGET_RETAILERS = ["Tesco", "Asda", "Sainsbury's", "Waitrose", "Ocado", "Iceland", "Morrisons"]
MIN_PRODUCTS_PER_SUBCATEGORY = 2
MIN_OFFERS_PER_PRODUCT = 1


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _fetch_all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute(sql, params)
    return [_row_to_dict(row) for row in cur.fetchall()]


def _fetch_count(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    if not row:
        return 0
    return int(row[0] or 0)


def _split_csv(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_coverage_summary_report() -> Dict[str, Any]:
    if not DB_PATH.exists():
        return {
            "database_found": False,
            "database_path": str(DB_PATH),
            "summary": {},
            "category_breakdown": [],
            "retailer_breakdown": [],
            "product_offer_coverage": [],
            "thin_subcategories": [],
            "products_without_offers": [],
            "products_missing_target_retailers": [],
            "issues": [],
        }

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    category_breakdown = _fetch_all(
        conn,
        """
        SELECT
            category,
            subcategory,
            COUNT(*) AS product_count
        FROM products
        GROUP BY category, subcategory
        ORDER BY category COLLATE NOCASE ASC, subcategory COLLATE NOCASE ASC
        """,
    )

    retailer_breakdown = _fetch_all(
        conn,
        """
        SELECT
            retailer,
            COUNT(*) AS offer_count,
            COUNT(DISTINCT barcode) AS product_count,
            ROUND(AVG(price), 2) AS average_price,
            MIN(price) AS lowest_price,
            MAX(price) AS highest_price
        FROM offers
        GROUP BY retailer
        ORDER BY retailer COLLATE NOCASE ASC
        """,
    )

    product_offer_coverage = _fetch_all(
        conn,
        """
        SELECT
            p.barcode,
            p.name,
            p.category,
            p.subcategory,
            COUNT(o.id) AS offer_count,
            GROUP_CONCAT(DISTINCT o.retailer) AS retailers,
            MIN(
                CASE
                    WHEN o.promo_price IS NOT NULL AND o.promo_price > 0 THEN o.promo_price
                    ELSE o.price
                END
            ) AS best_price
        FROM products p
        LEFT JOIN offers o
            ON o.barcode = p.barcode
        GROUP BY p.barcode, p.name, p.category, p.subcategory
        ORDER BY
            offer_count ASC,
            p.category COLLATE NOCASE ASC,
            p.subcategory COLLATE NOCASE ASC,
            p.name COLLATE NOCASE ASC
        """,
    )

    thin_subcategories = [
        row
        for row in category_breakdown
        if int(row.get("product_count") or 0) < MIN_PRODUCTS_PER_SUBCATEGORY
    ]

    products_without_offers = [
        row
        for row in product_offer_coverage
        if int(row.get("offer_count") or 0) < MIN_OFFERS_PER_PRODUCT
    ]

    products_missing_target_retailers = []
    for row in product_offer_coverage:
        retailers = set(_split_csv(row.get("retailers") or ""))
        missing = [retailer for retailer in TARGET_RETAILERS if retailer not in retailers]
        if missing:
            item = dict(row)
            item["missing_retailers"] = missing
            products_missing_target_retailers.append(item)

    issues = []

    for row in thin_subcategories:
        issues.append(
            {
                "type": "thin_subcategory",
                "message": "{category} / {subcategory} has only {count} product(s)".format(
                    category=row.get("category") or "",
                    subcategory=row.get("subcategory") or "",
                    count=row.get("product_count") or 0,
                ),
            }
        )

    for row in products_without_offers:
        issues.append(
            {
                "type": "missing_offers",
                "message": "{barcode} | {name} has no offers".format(
                    barcode=row.get("barcode") or "",
                    name=row.get("name") or "",
                ),
            }
        )

    summary = {
        "products_total": _fetch_count(conn, "SELECT COUNT(*) FROM products"),
        "offers_total": _fetch_count(conn, "SELECT COUNT(*) FROM offers"),
        "categories_total": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM (
                SELECT category
                FROM products
                GROUP BY category
            )
            """,
        ),
        "subcategories_total": len(category_breakdown),
        "retailers_total": len(retailer_breakdown),
        "target_retailers": ", ".join(TARGET_RETAILERS),
        "thin_subcategory_count": len(thin_subcategories),
        "products_without_offers": len(products_without_offers),
        "products_missing_target_retailers": len(products_missing_target_retailers),
        "issue_count": len(issues),
    }

    conn.close()

    return {
        "database_found": True,
        "database_path": str(DB_PATH),
        "summary": summary,
        "category_breakdown": category_breakdown,
        "retailer_breakdown": retailer_breakdown,
        "product_offer_coverage": product_offer_coverage,
        "thin_subcategories": thin_subcategories,
        "products_without_offers": products_without_offers,
        "products_missing_target_retailers": products_missing_target_retailers,
        "issues": issues,
    }


def print_coverage_summary_report() -> None:
    report = build_coverage_summary_report()

    print("\nCOVERAGE SUMMARY REPORT")
    print("=" * 80)

    if not report["database_found"]:
        print(f"Database not found: {report['database_path']}")
        return

    print(f"Database: {report['database_path']}")
    print("\nSummary")
    for key, value in report["summary"].items():
        print(f"- {key}: {value}")

    print("\nCategory / Subcategory Coverage")
    for row in report["category_breakdown"]:
        print(
            "- {category} / {subcategory}: {count} product(s)".format(
                category=row.get("category") or "",
                subcategory=row.get("subcategory") or "",
                count=row.get("product_count") or 0,
            )
        )

    print("\nRetailer Offer Coverage")
    for row in report["retailer_breakdown"]:
        print(
            "- {retailer}: {offers} offer(s), {products} product(s), avg={avg}, min={low}, max={high}".format(
                retailer=row.get("retailer") or "",
                offers=row.get("offer_count") or 0,
                products=row.get("product_count") or 0,
                avg=row.get("average_price"),
                low=row.get("lowest_price"),
                high=row.get("highest_price"),
            )
        )

    print("\nProduct Offer Coverage")
    for row in report["product_offer_coverage"]:
        print(
            "- {barcode} | {name}: {count} offer(s), retailers={retailers}, best_price={price}".format(
                barcode=row.get("barcode") or "",
                name=row.get("name") or "",
                count=row.get("offer_count") or 0,
                retailers=row.get("retailers") or "",
                price=row.get("best_price"),
            )
        )

    print("\nThin Subcategories")
    if not report["thin_subcategories"]:
        print("- none")
    else:
        for row in report["thin_subcategories"]:
            print(
                "- {category} / {subcategory}: {count} product(s)".format(
                    category=row.get("category") or "",
                    subcategory=row.get("subcategory") or "",
                    count=row.get("product_count") or 0,
                )
            )

    print("\nProducts Missing Target Retailers")
    if not report["products_missing_target_retailers"]:
        print("- none")
    else:
        for row in report["products_missing_target_retailers"]:
            print(
                "- {barcode} | {name}: missing {missing}".format(
                    barcode=row.get("barcode") or "",
                    name=row.get("name") or "",
                    missing=", ".join(row.get("missing_retailers") or []),
                )
            )

    print("\nIssues")
    if not report["issues"]:
        print("- none")
    else:
        for issue in report["issues"]:
            print(f"- {issue.get('message') or ''}")


def main() -> None:
    print_coverage_summary_report()


if __name__ == "__main__":
    main()
