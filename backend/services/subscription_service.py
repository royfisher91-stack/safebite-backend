from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from database import db
from services.auth_service import get_user_by_id
from services.billing_service import (
    BILLING_NOTICE,
    CORE_PRODUCT_ID,
    SAFEHOME_ADDON_PRODUCT_ID,
    list_billing_products,
    normalise_product,
    verify_provider_purchase,
)
from services.promo_service import apply_promo_code


MONTHLY_PLAN_CODE = "paid_monthly"
SAFEHOME_ADDON_PLAN_CODE = "safehome_addon"
MONTHLY_PRICE_GBP = 5.00
SUPPORTED_PLAN_CODES = {"free", MONTHLY_PLAN_CODE, SAFEHOME_ADDON_PLAN_CODE, "safehome_bundle", "influencer_free", "discounted"}
ACTIVE_ACCESS_STATUSES = {"active", "trial", "cancelled"}
SUBSCRIPTION_NOTICE = (
    "Subscription and promo state only controls access. It does not change safety scores, ingredient analysis, condition results, or community feedback."
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialise_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: Any) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _json_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


def _row_to_subscription(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None

    payload = dict(row)
    return {
        "id": payload.get("id"),
        "user_id": payload.get("user_id"),
        "plan_code": payload.get("plan_code") or "free",
        "status": payload.get("status") or "inactive",
        "started_at": payload.get("started_at"),
        "expires_at": payload.get("expires_at"),
        "cancelled_at": payload.get("cancelled_at"),
        "source": payload.get("source") or "internal",
        "promo_code": payload.get("promo_code") or "",
        "is_auto_renew": bool(payload.get("is_auto_renew")),
        "monthly_price": float(payload.get("monthly_price") or MONTHLY_PRICE_GBP),
        "currency": payload.get("currency") or "GBP",
        "provider": payload.get("provider") or "",
        "platform": payload.get("platform") or "",
        "product_id": payload.get("product_id") or "",
        "purchase_token": payload.get("purchase_token") or "",
        "transaction_id": payload.get("transaction_id") or "",
        "add_on_entitlements": _json_list(payload.get("add_on_entitlements")),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }


def get_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM subscriptions
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_subscription(row)


def is_subscription_access_active(subscription: Optional[Dict[str, Any]]) -> bool:
    if not subscription:
        return False

    status = str(subscription.get("status") or "").strip().lower()
    plan_code = str(subscription.get("plan_code") or "").strip().lower()
    if status not in ACTIVE_ACCESS_STATUSES:
        return False
    if plan_code not in {"paid_monthly", "safehome_bundle", "influencer_free", "discounted"}:
        return False

    expires_at = _parse_datetime(subscription.get("expires_at"))
    return expires_at is None or expires_at > _utc_now()


def upsert_subscription(
    user_id: int,
    *,
    plan_code: str,
    status: str,
    expires_at: Optional[datetime] = None,
    source: str = "internal",
    promo_code: Optional[str] = None,
    is_auto_renew: bool = False,
    cancelled_at: Optional[datetime] = None,
    provider: Optional[str] = None,
    platform: Optional[str] = None,
    product_id: Optional[str] = None,
    purchase_token: Optional[str] = None,
    transaction_id: Optional[str] = None,
    add_on_entitlements: Optional[list] = None,
) -> Dict[str, Any]:
    if not get_user_by_id(user_id):
        raise ValueError("User not found")

    cleaned_plan = str(plan_code or "").strip().lower()
    if cleaned_plan not in SUPPORTED_PLAN_CODES:
        raise ValueError("Unsupported subscription plan")

    cleaned_status = str(status or "").strip().lower()
    if cleaned_status not in {"active", "inactive", "cancelled", "expired", "trial"}:
        raise ValueError("Unsupported subscription status")

    expires_at_text = _serialise_datetime(expires_at)
    cancelled_at_text = _serialise_datetime(cancelled_at)
    add_on_text = json.dumps(add_on_entitlements or [], ensure_ascii=False)
    existing = get_subscription(user_id)

    conn = db.get_connection()
    cursor = conn.cursor()
    if existing:
        cursor.execute(
            """
            UPDATE subscriptions
            SET plan_code = ?,
                status = ?,
                expires_at = ?,
                cancelled_at = ?,
                source = ?,
                promo_code = ?,
                is_auto_renew = ?,
                monthly_price = ?,
                currency = 'GBP',
                provider = ?,
                platform = ?,
                product_id = ?,
                purchase_token = ?,
                transaction_id = ?,
                add_on_entitlements = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                cleaned_plan,
                cleaned_status,
                expires_at_text,
                cancelled_at_text,
                str(source or "internal").strip() or "internal",
                str(promo_code or "").strip() or None,
                1 if is_auto_renew else 0,
                MONTHLY_PRICE_GBP,
                str(provider or "").strip() or None,
                str(platform or "").strip() or None,
                str(product_id or "").strip() or None,
                str(purchase_token or "").strip() or None,
                str(transaction_id or "").strip() or None,
                add_on_text,
                existing["id"],
            ),
        )
    else:
        cursor.execute(
            """
            INSERT INTO subscriptions (
                user_id,
                plan_code,
                status,
                expires_at,
                cancelled_at,
                source,
                promo_code,
                is_auto_renew,
                monthly_price,
                currency,
                provider,
                platform,
                product_id,
                purchase_token,
                transaction_id,
                add_on_entitlements
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'GBP', ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                cleaned_plan,
                cleaned_status,
                expires_at_text,
                cancelled_at_text,
                str(source or "internal").strip() or "internal",
                str(promo_code or "").strip() or None,
                1 if is_auto_renew else 0,
                MONTHLY_PRICE_GBP,
                str(provider or "").strip() or None,
                str(platform or "").strip() or None,
                str(product_id or "").strip() or None,
                str(purchase_token or "").strip() or None,
                str(transaction_id or "").strip() or None,
                add_on_text,
            ),
        )

    cursor.execute(
        """
        UPDATE users
        SET subscription_status = ?,
            subscription_plan = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (cleaned_status, cleaned_plan, user_id),
    )
    conn.commit()
    conn.close()

    refreshed = get_subscription(user_id)
    if not refreshed:
        raise ValueError("Subscription could not be saved")
    return refreshed


def get_subscription_status(user_id: int) -> Dict[str, Any]:
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")

    subscription = get_subscription(user_id)
    return {
        "user_id": user_id,
        "plan_code": (subscription or {}).get("plan_code") or user.get("subscription_plan") or "free",
        "status": (subscription or {}).get("status") or user.get("subscription_status") or "inactive",
        "active_access": is_subscription_access_active(subscription),
        "monthly_price": MONTHLY_PRICE_GBP,
        "currency": "GBP",
        "core_product_id": CORE_PRODUCT_ID,
        "safehome_addon_product_id": SAFEHOME_ADDON_PRODUCT_ID,
        "add_on_entitlements": (subscription or {}).get("add_on_entitlements") or [],
        "subscription": subscription,
        "access_notice": SUBSCRIPTION_NOTICE,
        "billing_notice": BILLING_NOTICE,
    }


def activate_monthly_subscription(user_id: int) -> Dict[str, Any]:
    return create_pending_billing_subscription(
        user_id,
        product_id=CORE_PRODUCT_ID,
        source="billing_required",
    )


def create_pending_billing_subscription(
    user_id: int,
    *,
    product_id: str = CORE_PRODUCT_ID,
    source: str = "billing_required",
) -> Dict[str, Any]:
    product = normalise_product(product_id)
    plan_code = product.get("plan_code") or MONTHLY_PLAN_CODE
    return upsert_subscription(
        user_id,
        plan_code=str(plan_code),
        status="inactive",
        source=source,
        product_id=str(product_id),
        add_on_entitlements=[],
        is_auto_renew=False,
    )


def cancel_subscription(user_id: int) -> Dict[str, Any]:
    subscription = get_subscription(user_id)
    if not subscription:
        return upsert_subscription(
            user_id,
            plan_code="free",
            status="inactive",
            source="internal",
        )

    expires_at = _parse_datetime(subscription.get("expires_at"))
    return upsert_subscription(
        user_id,
        plan_code=str(subscription.get("plan_code") or "free"),
        status="cancelled",
        expires_at=expires_at,
        cancelled_at=_utc_now(),
        source=str(subscription.get("source") or "internal"),
        promo_code=str(subscription.get("promo_code") or "") or None,
        provider=str(subscription.get("provider") or "") or None,
        platform=str(subscription.get("platform") or "") or None,
        product_id=str(subscription.get("product_id") or "") or None,
        purchase_token=str(subscription.get("purchase_token") or "") or None,
        transaction_id=str(subscription.get("transaction_id") or "") or None,
        add_on_entitlements=subscription.get("add_on_entitlements") or [],
        is_auto_renew=False,
    )


def verify_and_apply_billing_subscription(
    user_id: int,
    *,
    provider: str,
    product_id: str,
    purchase_token: Optional[str] = None,
    transaction_id: Optional[str] = None,
    platform: Optional[str] = None,
) -> Dict[str, Any]:
    verified, verification = verify_provider_purchase(
        provider=provider,
        product_id=product_id,
        purchase_token=purchase_token,
        transaction_id=transaction_id,
        platform=platform,
    )
    product = verification.get("product") or normalise_product(product_id)
    add_ons = [product_id] if product_id == SAFEHOME_ADDON_PRODUCT_ID and verified else []
    if not verified:
        subscription = upsert_subscription(
            user_id,
            plan_code=str(product.get("plan_code") or MONTHLY_PLAN_CODE),
            status="inactive",
            source="billing_unverified",
            provider=provider,
            platform=platform,
            product_id=product_id,
            purchase_token=purchase_token,
            transaction_id=transaction_id,
            add_on_entitlements=[],
            is_auto_renew=False,
        )
        return {
            "verified": False,
            "subscription": subscription,
            "subscription_status": get_subscription_status(user_id),
            "verification": verification,
            "billing_products": list_billing_products(),
        }

    expires_at = _parse_datetime(verification.get("expires_at")) or (_utc_now() + timedelta(days=30))
    subscription = upsert_subscription(
        user_id,
        plan_code=str(product.get("plan_code") or MONTHLY_PLAN_CODE),
        status="active",
        expires_at=expires_at,
        source="billing_verified",
        provider=provider,
        platform=platform,
        product_id=product_id,
        purchase_token=purchase_token,
        transaction_id=transaction_id,
        add_on_entitlements=add_ons,
        is_auto_renew=True,
    )
    return {
        "verified": True,
        "subscription": subscription,
        "subscription_status": get_subscription_status(user_id),
        "verification": verification,
        "billing_products": list_billing_products(),
    }


def apply_promo_to_subscription(user_id: int, code: str) -> Dict[str, Any]:
    promo_result = apply_promo_code(code, plan="monthly")
    if not promo_result.get("applied"):
        return {
            "applied": False,
            "reason": promo_result.get("reason"),
            "subscription": get_subscription_status(user_id),
            "promo": promo_result,
            "access_notice": SUBSCRIPTION_NOTICE,
        }

    preview = promo_result.get("preview") or {}
    promo_code = (promo_result.get("promo_code") or {}).get("code") or code
    code_type = str((promo_result.get("promo_code") or {}).get("code_type") or "").lower()
    discount_type = str(preview.get("discount_type") or "").lower()
    final_price = preview.get("final_price")

    plan_code = "discounted"
    expires_at = _utc_now() + timedelta(days=30)
    if code_type == "influencer" or discount_type == "free_access" or final_price == 0:
        plan_code = "influencer_free"

    subscription = upsert_subscription(
        user_id,
        plan_code=plan_code,
        status="active",
        expires_at=expires_at,
        source="promo",
        promo_code=str(promo_code),
        is_auto_renew=False,
    )
    return {
        "applied": True,
        "reason": None,
        "subscription": subscription,
        "promo": promo_result,
        "access_notice": SUBSCRIPTION_NOTICE,
    }
