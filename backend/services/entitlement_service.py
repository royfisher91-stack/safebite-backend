from __future__ import annotations

from typing import Any, Dict, Optional

from database import db
from services.auth_service import get_user_by_id
from services.subscription_service import (
    get_subscription,
    is_subscription_access_active,
)


FREE_SCAN_LIMIT = 3
SCAN_EVENT_TYPE = "product_lookup"
ENTITLEMENT_NOTICE = (
    "Entitlement checks only gate access. They do not change product safety, ingredient analysis, condition results, or community feedback."
)


def get_free_scan_usage(user_id: int) -> int:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS used
        FROM usage_events
        WHERE user_id = ? AND event_type = ?
        """,
        (user_id, SCAN_EVENT_TYPE),
    )
    row = cursor.fetchone()
    used = int((dict(row).get("used") if row is not None else 0) or 0)
    cursor.execute(
        """
        UPDATE users
        SET free_scans_used = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (used, user_id),
    )
    conn.commit()
    conn.close()
    return used


def get_entitlement(user_id: int) -> Dict[str, Any]:
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")

    subscription = get_subscription(user_id)
    active_access = is_subscription_access_active(subscription)
    plan = (subscription or {}).get("plan_code") or user.get("subscription_plan") or "free"
    status = (subscription or {}).get("status") or user.get("subscription_status") or "inactive"
    add_on_entitlements = (subscription or {}).get("add_on_entitlements") or []

    free_scans_used = get_free_scan_usage(user_id)
    free_scans_remaining = max(FREE_SCAN_LIMIT - free_scans_used, 0)

    if active_access:
        can_scan = True
        free_scans_remaining_value: Optional[int] = None
    else:
        plan = "free"
        can_scan = free_scans_remaining > 0
        free_scans_remaining_value = free_scans_remaining

    return {
        "user_id": user_id,
        "plan": plan,
        "subscription_status": status,
        "access_active": active_access,
        "add_on_entitlements": add_on_entitlements,
        "safehome_addon_active": "safehome_addon" in add_on_entitlements,
        "free_scan_limit": FREE_SCAN_LIMIT,
        "free_scans_used": free_scans_used,
        "free_scans_remaining": free_scans_remaining_value,
        "can_scan": can_scan,
        "scan_count_rule": "Successful barcode/manual product lookups that return a product result count for free users.",
        "access_notice": ENTITLEMENT_NOTICE,
    }


def record_successful_scan(
    user_id: int,
    *,
    barcode: Optional[str] = None,
    source: str = "product_lookup",
) -> Dict[str, Any]:
    entitlement = get_entitlement(user_id)
    if entitlement.get("access_active"):
        return entitlement
    if not entitlement.get("can_scan"):
        return entitlement

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO usage_events (user_id, event_type, barcode, source)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            SCAN_EVENT_TYPE,
            str(barcode or "").strip() or None,
            str(source or "product_lookup").strip() or "product_lookup",
        ),
    )
    conn.commit()
    conn.close()
    return get_entitlement(user_id)
