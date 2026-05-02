import os
import sqlite3
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.bulk_import_service import DB_DEFAULT, ensure_phase12_schema


def main() -> int:
    ensure_phase12_schema(DB_DEFAULT)
    conn = sqlite3.connect(DB_DEFAULT)
    conn.row_factory = sqlite3.Row
    try:
        summary = conn.execute(
            """
            SELECT COUNT(*) AS batch_count,
                   COALESCE(SUM(rows_total), 0) AS rows_total,
                   COALESCE(SUM(rows_imported), 0) AS rows_imported,
                   COALESCE(SUM(rows_skipped), 0) AS rows_skipped,
                   COALESCE(SUM(errors_count), 0) AS errors_count
            FROM product_import_batches
            """
        ).fetchone()
        by_status = conn.execute(
            """
            SELECT status, COUNT(*) AS batch_count,
                   COALESCE(SUM(rows_total), 0) AS rows_total,
                   COALESCE(SUM(rows_imported), 0) AS rows_imported,
                   COALESCE(SUM(rows_skipped), 0) AS rows_skipped,
                   COALESCE(SUM(errors_count), 0) AS errors_count
            FROM product_import_batches
            GROUP BY status
            ORDER BY status
            """
        ).fetchall()
        error_rows = conn.execute(
            """
            SELECT batch_id, row_number, retailer, barcode, reason
            FROM product_import_errors
            ORDER BY id DESC
            LIMIT 10
            """
        ).fetchall()

        print("BULK IMPORT QUALITY REPORT")
        print("=" * 80)
        print("Batch count: {0}".format(summary["batch_count"]))
        print("Rows total: {0}".format(summary["rows_total"]))
        print("Rows imported: {0}".format(summary["rows_imported"]))
        print("Rows skipped: {0}".format(summary["rows_skipped"]))
        print("Errors count: {0}".format(summary["errors_count"]))
        print("")
        print("By status")
        for row in by_status:
            print("- {0}: batches={1}, rows={2}, imported={3}, skipped={4}, errors={5}".format(
                row["status"],
                row["batch_count"],
                row["rows_total"],
                row["rows_imported"],
                row["rows_skipped"],
                row["errors_count"],
            ))
        print("")
        print("Recent errors")
        if not error_rows:
            print("- none")
        for row in error_rows:
            print("- batch {0}, row {1}, {2}, {3}: {4}".format(
                row["batch_id"],
                row["row_number"],
                row["retailer"],
                row["barcode"],
                row["reason"],
            ))
        print("")
        print("Issues")
        if int(summary["errors_count"] or 0) == 0 and int(summary["rows_skipped"] or 0) == 0:
            print("- none")
            return 0
        print("- skipped rows or errors are present")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

