import sqlite3
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "safebite.db"


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


def build_quality_report(limit: int = 25) -> Dict[str, Any]:
    if not DB_PATH.exists():
        return {
            "database_found": False,
            "database_path": str(DB_PATH),
            "summary": {},
            "weak_products": [],
            "weak_offers": [],
        }

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    summary = {
        "products_total": _fetch_count(conn, "SELECT COUNT(*) FROM products"),
        "offers_total": _fetch_count(conn, "SELECT COUNT(*) FROM offers"),
        "products_missing_category": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM products
            WHERE category IS NULL
               OR TRIM(category) = ''
               OR subcategory IS NULL
               OR TRIM(subcategory) = ''
            """,
        ),
        "products_other_general": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM products
            WHERE LOWER(TRIM(category)) = 'other'
              AND LOWER(TRIM(subcategory)) = 'general'
            """,
        ),
        "products_missing_source": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM products
            WHERE source IS NULL
               OR TRIM(source) = ''
               OR source_retailer IS NULL
               OR TRIM(source_retailer) = ''
            """,
        ),
        "products_placeholder_name": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM products
            WHERE LOWER(name) LIKE 'unknown product%'
               OR LOWER(name) = 'unknown product'
            """,
        ),
        "offers_missing_source": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM offers
            WHERE source IS NULL
               OR TRIM(source) = ''
               OR source_retailer IS NULL
               OR TRIM(source_retailer) = ''
            """,
        ),
        "offers_missing_price": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM offers
            WHERE price IS NULL
               OR price <= 0
            """,
        ),
        "offers_unknown_stock": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM offers
            WHERE stock_status IS NULL
               OR TRIM(stock_status) = ''
               OR LOWER(TRIM(stock_status)) = 'unknown'
            """,
        ),
        "offers_sample_seed": _fetch_count(
            conn,
            """
            SELECT COUNT(*)
            FROM offers
            WHERE LOWER(TRIM(source)) = 'sample_seed'
            """,
        ),
    }

    weak_products = _fetch_all(
        conn,
        """
        SELECT
            barcode,
            name,
            brand,
            category,
            subcategory,
            source,
            source_retailer,
            CASE
                WHEN category IS NULL OR TRIM(category) = '' THEN 'missing category'
                WHEN subcategory IS NULL OR TRIM(subcategory) = '' THEN 'missing subcategory'
                WHEN LOWER(TRIM(category)) = 'other'
                 AND LOWER(TRIM(subcategory)) = 'general' THEN 'generic category'
                WHEN source IS NULL OR TRIM(source) = '' THEN 'missing source'
                WHEN source_retailer IS NULL OR TRIM(source_retailer) = '' THEN 'missing source retailer'
                WHEN LOWER(name) LIKE 'unknown product%' THEN 'placeholder name'
                ELSE 'review'
            END AS issue
        FROM products
        WHERE category IS NULL
           OR TRIM(category) = ''
           OR subcategory IS NULL
           OR TRIM(subcategory) = ''
           OR (LOWER(TRIM(category)) = 'other' AND LOWER(TRIM(subcategory)) = 'general')
           OR source IS NULL
           OR TRIM(source) = ''
           OR source_retailer IS NULL
           OR TRIM(source_retailer) = ''
           OR LOWER(name) LIKE 'unknown product%'
        ORDER BY
            CASE
                WHEN LOWER(TRIM(category)) = 'other'
                 AND LOWER(TRIM(subcategory)) = 'general' THEN 0
                WHEN category IS NULL OR TRIM(category) = '' THEN 1
                WHEN subcategory IS NULL OR TRIM(subcategory) = '' THEN 2
                WHEN source IS NULL OR TRIM(source) = '' THEN 3
                WHEN source_retailer IS NULL OR TRIM(source_retailer) = '' THEN 4
                ELSE 5
            END,
            name COLLATE NOCASE ASC
        LIMIT ?
        """,
        (limit,),
    )

    weak_offers = _fetch_all(
        conn,
        """
        SELECT
            barcode,
            retailer,
            price,
            promo_price,
            stock_status,
            in_stock,
            product_url,
            source,
            source_retailer,
            CASE
                WHEN source IS NULL OR TRIM(source) = '' THEN 'missing source'
                WHEN source_retailer IS NULL OR TRIM(source_retailer) = '' THEN 'missing source retailer'
                WHEN price IS NULL OR price <= 0 THEN 'missing price'
                WHEN stock_status IS NULL OR TRIM(stock_status) = '' THEN 'missing stock'
                WHEN LOWER(TRIM(stock_status)) = 'unknown' THEN 'unknown stock'
                WHEN LOWER(TRIM(source)) = 'sample_seed' THEN 'sample seed offer'
                ELSE 'review'
            END AS issue
        FROM offers
        WHERE source IS NULL
           OR TRIM(source) = ''
           OR source_retailer IS NULL
           OR TRIM(source_retailer) = ''
           OR price IS NULL
           OR price <= 0
           OR stock_status IS NULL
           OR TRIM(stock_status) = ''
           OR LOWER(TRIM(stock_status)) = 'unknown'
           OR LOWER(TRIM(source)) = 'sample_seed'
        ORDER BY
            CASE
                WHEN LOWER(TRIM(source)) = 'sample_seed' THEN 0
                WHEN source IS NULL OR TRIM(source) = '' THEN 1
                WHEN source_retailer IS NULL OR TRIM(source_retailer) = '' THEN 2
                WHEN price IS NULL OR price <= 0 THEN 3
                WHEN stock_status IS NULL OR TRIM(stock_status) = '' THEN 4
                WHEN LOWER(TRIM(stock_status)) = 'unknown' THEN 5
                ELSE 6
            END,
            barcode ASC,
            retailer COLLATE NOCASE ASC
        LIMIT ?
        """,
        (limit,),
    )

    conn.close()

    return {
        "database_found": True,
        "database_path": str(DB_PATH),
        "summary": summary,
        "weak_products": weak_products,
        "weak_offers": weak_offers,
    }


def print_quality_report(limit: int = 25) -> None:
    report = build_quality_report(limit=limit)

    print("\nIMPORT QUALITY REPORT")
    print("=" * 80)

    if not report["database_found"]:
        print(f"Database not found: {report['database_path']}")
        return

    print(f"Database: {report['database_path']}")
    print("\nSummary")

    for key, value in report["summary"].items():
        print(f"- {key}: {value}")

    print("\nWeak Products")
    if not report["weak_products"]:
        print("- none")
    else:
        for product in report["weak_products"]:
            print(
                "- {issue}: {barcode} | {name} | {category} / {subcategory} | {source} | {source_retailer}".format(
                    issue=product.get("issue") or "review",
                    barcode=product.get("barcode") or "",
                    name=product.get("name") or "",
                    category=product.get("category") or "",
                    subcategory=product.get("subcategory") or "",
                    source=product.get("source") or "",
                    source_retailer=product.get("source_retailer") or "",
                )
            )

    print("\nWeak Offers")
    if not report["weak_offers"]:
        print("- none")
    else:
        for offer in report["weak_offers"]:
            print(
                "- {issue}: {barcode} | {retailer} | price={price} | stock={stock_status} | source={source} | url={product_url}".format(
                    issue=offer.get("issue") or "review",
                    barcode=offer.get("barcode") or "",
                    retailer=offer.get("retailer") or "",
                    price=offer.get("price"),
                    stock_status=offer.get("stock_status") or "",
                    source=offer.get("source") or "",
                    product_url=offer.get("product_url") or "",
                )
            )


def main() -> None:
    print_quality_report()


if __name__ == "__main__":
    main()
