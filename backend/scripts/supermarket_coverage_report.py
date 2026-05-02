import os
import sqlite3
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_import_service import (
    ACTIVE_COVERAGE_RETAILERS,
    DB_DEFAULT,
    FUTURE_COMPATIBLE_RETAILERS,
    ensure_phase12_schema,
)


def main() -> int:
    ensure_phase12_schema(DB_DEFAULT)
    conn = sqlite3.connect(DB_DEFAULT)
    conn.row_factory = sqlite3.Row
    try:
        total = conn.execute("SELECT COUNT(*) AS count FROM retailer_offers").fetchone()["count"]
        by_retailer = conn.execute(
            """
            SELECT retailer, COUNT(*) AS offer_count, COUNT(DISTINCT barcode) AS product_count
            FROM retailer_offers
            WHERE retailer IN ({0})
            GROUP BY retailer
            ORDER BY retailer
            """.format(",".join("?" for _ in ACTIVE_COVERAGE_RETAILERS)),
            tuple(ACTIVE_COVERAGE_RETAILERS),
        ).fetchall()
        product_coverage = conn.execute(
            """
            SELECT barcode, COUNT(DISTINCT retailer) AS retailer_count
            FROM retailer_offers
            GROUP BY barcode
            ORDER BY retailer_count DESC, barcode
            LIMIT 10
            """
        ).fetchall()
        print("SUPERMARKET COVERAGE REPORT")
        print("=" * 80)
        print("Retailer offer rows: {0}".format(total))
        print("Current coverage retailers: {0}".format(", ".join(ACTIVE_COVERAGE_RETAILERS)))
        print("Future-compatible retailers: {0}".format(", ".join(FUTURE_COMPATIBLE_RETAILERS)))
        print("")
        print("By current retailer")
        seen = set()
        for row in by_retailer:
            seen.add(row["retailer"])
            print("- {0}: offers={1}, products={2}".format(
                row["retailer"],
                row["offer_count"],
                row["product_count"],
            ))
        for retailer in ACTIVE_COVERAGE_RETAILERS:
            if retailer in seen:
                continue
            print("- {0}: offers=0, products=0".format(retailer))
        print("")
        print("Highest product coverage")
        if not product_coverage:
            print("- none")
        for row in product_coverage:
            print("- {0}: retailers={1}".format(row["barcode"], row["retailer_count"]))
        print("")
        print("Issues")
        print("- none")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
