import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "safebite.db"


def main() -> None:
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("\n📦 CATEGORY BREAKDOWN\n")

    cur.execute(
        """
        SELECT
            category,
            subcategory,
            COUNT(*) AS total
        FROM products
        GROUP BY category, subcategory
        ORDER BY category COLLATE NOCASE ASC, subcategory COLLATE NOCASE ASC
        """
    )
    rows = cur.fetchall()

    if not rows:
        print("No products found in products table")
    else:
        for row in rows:
            category = str(row["category"] or "").strip() or "(blank)"
            subcategory = str(row["subcategory"] or "").strip() or "(blank)"
            total = int(row["total"] or 0)
            print(f"{category} / {subcategory}: {total}")

    print("\n⚠️ MISSING CATEGORY OR SUBCATEGORY COUNT\n")

    cur.execute(
        """
        SELECT COUNT(*) AS total
        FROM products
        WHERE category IS NULL
           OR TRIM(category) = ''
           OR subcategory IS NULL
           OR TRIM(subcategory) = ''
        """
    )
    missing_row = cur.fetchone()
    missing_total = int(missing_row["total"] or 0) if missing_row else 0
    print(missing_total)

    print("\n🔎 SAMPLE PRODUCTS\n")

    cur.execute(
        """
        SELECT barcode, name, category, subcategory
        FROM products
        ORDER BY name COLLATE NOCASE ASC
        LIMIT 20
        """
    )
    sample_rows = cur.fetchall()

    if not sample_rows:
        print("No sample products available")
    else:
        for row in sample_rows:
            barcode = str(row["barcode"] or "").strip()
            name = str(row["name"] or "").strip()
            category = str(row["category"] or "").strip() or "(blank)"
            subcategory = str(row["subcategory"] or "").strip() or "(blank)"
            print(f"{barcode} | {name} | {category} | {subcategory}")

    conn.close()


if __name__ == "__main__":
    main()