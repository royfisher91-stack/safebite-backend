import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "safebite.db"


MANUAL_NAME_FIXES = {
    "5000177025658": "Cow & Gate Creamy Porridge",
    "5000112637922": "Heinz By Nature Apple & Banana Baby Food",
}


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    fixed = 0

    for barcode, correct_name in MANUAL_NAME_FIXES.items():
        cur.execute(
            """
            UPDATE products
            SET name = ?
            WHERE barcode = ?
              AND (name IS NULL OR TRIM(name) = '' OR LOWER(TRIM(name)) = 'unknown product')
            """,
            (correct_name, barcode),
        )
        fixed += cur.rowcount

    conn.commit()
    conn.close()

    print(f"✅ Fixed product names: {fixed}")


if __name__ == "__main__":
    main()