from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import db, init_db


def _count_rows(table_name: str) -> int:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM {}".format(table_name))
    row = cursor.fetchone()
    conn.close()
    return int((dict(row).get("count") if row is not None else 0) or 0)


def _subscription_breakdown() -> Dict[str, int]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT plan_code, status, COUNT(*) AS count
        FROM subscriptions
        GROUP BY plan_code, status
        ORDER BY plan_code, status
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return {
        "{}:{}".format(row["plan_code"] or "unknown", row["status"] or "unknown"): int(row["count"] or 0)
        for row in rows
    }


def _usage_breakdown() -> Dict[str, int]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT event_type, COUNT(*) AS count
        FROM usage_events
        GROUP BY event_type
        ORDER BY event_type
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return {
        str(row["event_type"] or "unknown"): int(row["count"] or 0)
        for row in rows
    }


def main() -> int:
    init_db()

    report: Dict[str, Any] = {
        "users": _count_rows("users"),
        "auth_tokens": _count_rows("auth_tokens"),
        "subscriptions": _count_rows("subscriptions"),
        "usage_events": _count_rows("usage_events"),
        "subscription_breakdown": _subscription_breakdown(),
        "usage_breakdown": _usage_breakdown(),
        "monthly_plan": {
            "plan_code": "paid_monthly",
            "price": 5.00,
            "currency": "GBP",
            "interval": "month",
        },
        "separation_notice": (
            "Monetisation reports account/access state only; safety, ingredient, condition, and community logic remain separate."
        ),
    }

    for key, value in report.items():
        print("{}: {}".format(key, value))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
