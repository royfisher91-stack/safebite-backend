from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database


def _set_temp_database(db_path: Path) -> None:
    database.db = database.DatabaseManager(str(db_path))


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def main() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "phase9_validation.db"
        _set_temp_database(db_path)

        from services.auth_service import login_user, register_user
        from services.entitlement_service import get_entitlement, record_successful_scan
        from services.subscription_service import activate_monthly_subscription, cancel_subscription

        conn = database.db.get_connection()
        required_tables = ["users", "auth_tokens", "subscriptions", "usage_events"]
        missing = [table for table in required_tables if not _table_exists(conn, table)]
        conn.close()
        if missing:
            raise AssertionError("Missing monetisation tables: {}".format(", ".join(missing)))

        user = register_user("phase9@example.com", "StrongPassword123!")
        assert user["email"] == "phase9@example.com"

        try:
            register_user("phase9@example.com", "StrongPassword123!")
        except ValueError:
            duplicate_blocked = True
        else:
            duplicate_blocked = False
        assert duplicate_blocked, "Duplicate registration must be blocked"

        session = login_user("phase9@example.com", "StrongPassword123!")
        assert session["access_token"]
        assert session["user"]["id"] == user["id"]

        entitlement = get_entitlement(user["id"])
        assert entitlement["plan"] == "free"
        assert entitlement["can_scan"] is True
        assert entitlement["free_scan_limit"] == 3

        for index in range(3):
            entitlement = record_successful_scan(
                user["id"],
                barcode="TEST{}".format(index),
                source="validation",
            )
        assert entitlement["free_scans_used"] == 3
        assert entitlement["can_scan"] is False

        subscription = activate_monthly_subscription(user["id"])
        assert subscription["plan_code"] == "paid_monthly"
        assert subscription["status"] == "active"
        assert get_entitlement(user["id"])["can_scan"] is True

        cancelled = cancel_subscription(user["id"])
        assert cancelled["status"] == "cancelled"

    print("Phase 9 monetisation validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
