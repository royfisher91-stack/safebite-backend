import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "safebite.db"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE offers
        SET source_retailer = retailer
        WHERE source_retailer IS NULL
           OR TRIM(source_retailer) = ''
           OR LOWER(TRIM(source_retailer)) != LOWER(TRIM(retailer))
        """
    )
    fixed_source_retailer = cur.rowcount

    cur.execute(
        """
        UPDATE offers
        SET source = LOWER(TRIM(retailer)) || '_import'
        WHERE source IS NULL
           OR TRIM(source) = ''
           OR LOWER(TRIM(source)) NOT LIKE LOWER(TRIM(retailer)) || '_%'
        """
    )
    fixed_source = cur.rowcount

    conn.commit()
    conn.close()

    print(f"✅ Fixed source_retailer rows: {fixed_source_retailer}")
    print(f"✅ Fixed source rows: {fixed_source}")


if __name__ == "__main__":
    main()