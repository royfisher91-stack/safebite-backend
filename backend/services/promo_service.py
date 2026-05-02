from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database import db


ALLOWED_CODE_TYPES = {"subscription", "influencer", "campaign"}
ALLOWED_DISCOUNT_TYPES = {"percent", "fixed", "free_access", "trial_extension"}
SUPPORTED_PLANS = {
    "monthly": 4.99,
    "annual": 49.99,
}
PROMO_PRICING_NOTICE = (
    "Promo codes only affect access pricing. They do not change product safety, ingredient analysis, or condition results."
)


def _normalise_code(value: str) -> str:
    return str(value or "").strip().upper()


def _normalise_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_optional_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    text = _normalise_text(value)
    if not text:
        return None

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _serialise_datetime(value: Any) -> Optional[str]:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return parsed.isoformat().replace("+00:00", "Z")


def _row_to_promo_code(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None

    payload = dict(row)
    return {
        "id": payload.get("id"),
        "code": payload.get("code") or "",
        "code_type": payload.get("code_type") or "",
        "discount_type": payload.get("discount_type") or "",
        "discount_value": _safe_float(payload.get("discount_value")),
        "plan_scope": payload.get("plan_scope") or "all",
        "campaign_label": payload.get("campaign_label") or "",
        "is_active": bool(payload.get("is_active")),
        "usage_limit": _safe_optional_int(payload.get("usage_limit")),
        "usage_count": _safe_optional_int(payload.get("usage_count")) or 0,
        "expires_at": _serialise_datetime(payload.get("expires_at")),
        "notes": payload.get("notes") or "",
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }


def _validate_payload(
    code_type: str,
    discount_type: str,
    discount_value: Optional[float],
    usage_limit: Optional[int],
    plan_scope: Optional[str],
    expires_at: Optional[str],
) -> None:
    if code_type not in ALLOWED_CODE_TYPES:
        raise ValueError("Unsupported code_type")

    if discount_type not in ALLOWED_DISCOUNT_TYPES:
        raise ValueError("Unsupported discount_type")

    if discount_type == "percent":
        if discount_value is None or discount_value <= 0 or discount_value > 100:
            raise ValueError("Percent discounts must be between 0 and 100")
    elif discount_type == "fixed":
        if discount_value is None or discount_value <= 0:
            raise ValueError("Fixed discounts must be greater than 0")
    elif discount_type == "trial_extension":
        if discount_value is None or discount_value <= 0:
            raise ValueError("Trial extension discounts must be greater than 0")

    if usage_limit is not None and usage_limit <= 0:
        raise ValueError("usage_limit must be greater than 0")

    if plan_scope:
        scope = plan_scope.strip().lower()
        if scope not in {"all", *SUPPORTED_PLANS.keys()}:
            raise ValueError("plan_scope must be all, monthly, or annual")

    if expires_at and _parse_datetime(expires_at) is None:
        raise ValueError("expires_at must be ISO-8601 compatible")


def list_promo_codes(active_only: bool = False) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()

    query = [
        "SELECT * FROM promo_codes",
    ]
    params: List[Any] = []

    if active_only:
        query.append("WHERE is_active = 1")

    query.append("ORDER BY created_at DESC, id DESC")
    cursor.execute("\n".join(query), tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_promo_code(row) for row in rows if row is not None]


def get_promo_code_by_code(code: str) -> Optional[Dict[str, Any]]:
    cleaned = _normalise_code(code)
    if not cleaned:
        return None

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM promo_codes
        WHERE code = ?
        LIMIT 1
        """,
        (cleaned,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_promo_code(row)


def create_promo_code(
    code: str,
    code_type: str,
    discount_type: str,
    discount_value: Optional[float] = None,
    is_active: bool = True,
    usage_limit: Optional[int] = None,
    expires_at: Optional[str] = None,
    plan_scope: str = "all",
    campaign_label: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    cleaned_code = _normalise_code(code)
    cleaned_type = _normalise_text(code_type).lower()
    cleaned_discount_type = _normalise_text(discount_type).lower()
    cleaned_discount_value = _safe_float(discount_value)
    cleaned_usage_limit = _safe_optional_int(usage_limit)
    cleaned_plan_scope = _normalise_text(plan_scope).lower() or "all"
    cleaned_expires_at = _serialise_datetime(expires_at)

    _validate_payload(
        code_type=cleaned_type,
        discount_type=cleaned_discount_type,
        discount_value=cleaned_discount_value,
        usage_limit=cleaned_usage_limit,
        plan_scope=cleaned_plan_scope,
        expires_at=cleaned_expires_at,
    )

    if cleaned_discount_type == "free_access":
        cleaned_discount_value = 100.0

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO promo_codes (
            code,
            code_type,
            discount_type,
            discount_value,
            plan_scope,
            campaign_label,
            is_active,
            usage_limit,
            usage_count,
            expires_at,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (
            cleaned_code,
            cleaned_type,
            cleaned_discount_type,
            cleaned_discount_value,
            cleaned_plan_scope,
            _normalise_text(campaign_label),
            1 if is_active else 0,
            cleaned_usage_limit,
            cleaned_expires_at,
            _normalise_text(notes),
        ),
    )
    promo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return get_promo_code_by_code(cleaned_code) or {"id": promo_id, "code": cleaned_code}


def update_promo_code(
    promo_id: int,
    *,
    is_active: Optional[bool] = None,
    usage_limit: Optional[int] = None,
    expires_at: Optional[str] = None,
    plan_scope: Optional[str] = None,
    campaign_label: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promo_codes WHERE id = ? LIMIT 1", (promo_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return None

    current = _row_to_promo_code(existing) or {}
    next_usage_limit = _safe_optional_int(usage_limit) if usage_limit is not None else current.get("usage_limit")
    next_plan_scope = _normalise_text(plan_scope).lower() if plan_scope is not None else current.get("plan_scope")
    next_expires_at = _serialise_datetime(expires_at) if expires_at is not None else current.get("expires_at")

    _validate_payload(
        code_type=str(current.get("code_type") or ""),
        discount_type=str(current.get("discount_type") or ""),
        discount_value=_safe_float(current.get("discount_value")),
        usage_limit=next_usage_limit,
        plan_scope=next_plan_scope,
        expires_at=next_expires_at,
    )

    cursor.execute(
        """
        UPDATE promo_codes
        SET
            is_active = ?,
            usage_limit = ?,
            expires_at = ?,
            plan_scope = ?,
            campaign_label = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            current.get("is_active") if is_active is None else (1 if is_active else 0),
            next_usage_limit,
            next_expires_at,
            next_plan_scope or "all",
            current.get("campaign_label") if campaign_label is None else _normalise_text(campaign_label),
            current.get("notes") if notes is None else _normalise_text(notes),
            promo_id,
        ),
    )
    conn.commit()
    conn.close()

    refreshed = None
    for item in list_promo_codes(active_only=False):
        if int(item.get("id") or 0) == promo_id:
            refreshed = item
            break
    return refreshed


def delete_promo_code(promo_id: int) -> bool:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM promo_codes WHERE id = ?", (promo_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def _check_promo_state(promo: Optional[Dict[str, Any]], plan: Optional[str] = None) -> Dict[str, Any]:
    cleaned_plan = _normalise_text(plan).lower() or None

    if not promo:
        return {"valid": False, "reason": "Promo code not found"}

    if not promo.get("is_active"):
        return {"valid": False, "reason": "Promo code is inactive", "promo_code": promo}

    expires_at = _parse_datetime(promo.get("expires_at"))
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        return {"valid": False, "reason": "Promo code has expired", "promo_code": promo}

    usage_limit = promo.get("usage_limit")
    usage_count = int(promo.get("usage_count") or 0)
    if usage_limit is not None and usage_count >= int(usage_limit):
        return {"valid": False, "reason": "Promo code has reached its usage limit", "promo_code": promo}

    plan_scope = str(promo.get("plan_scope") or "all").strip().lower()
    if cleaned_plan and plan_scope not in {"all", cleaned_plan}:
        return {"valid": False, "reason": "Promo code does not apply to this plan", "promo_code": promo}

    return {"valid": True, "reason": None, "promo_code": promo}


def build_promo_preview(promo: Dict[str, Any], plan: str) -> Dict[str, Any]:
    cleaned_plan = _normalise_text(plan).lower()
    base_price = SUPPORTED_PLANS.get(cleaned_plan)
    if base_price is None:
        raise ValueError("Unsupported plan")

    discount_type = str(promo.get("discount_type") or "").strip().lower()
    discount_value = _safe_float(promo.get("discount_value")) or 0.0

    final_price = round(base_price, 2)
    trial_extension_days = None

    if discount_type == "percent":
        final_price = round(max(base_price - (base_price * (discount_value / 100.0)), 0.0), 2)
    elif discount_type == "fixed":
        final_price = round(max(base_price - discount_value, 0.0), 2)
    elif discount_type == "free_access":
        final_price = 0.0
    elif discount_type == "trial_extension":
        trial_extension_days = int(discount_value)

    discount_amount = round(max(base_price - final_price, 0.0), 2)
    savings_percent = round((discount_amount / base_price) * 100.0, 2) if base_price else 0.0

    return {
        "code": promo.get("code"),
        "code_type": promo.get("code_type"),
        "discount_type": discount_type,
        "discount_value": discount_value,
        "plan": cleaned_plan,
        "plan_scope": promo.get("plan_scope") or "all",
        "campaign_label": promo.get("campaign_label") or "",
        "base_price": round(base_price, 2),
        "final_price": final_price,
        "discount_amount": discount_amount,
        "savings_percent": savings_percent,
        "trial_extension_days": trial_extension_days,
        "access_granted": final_price <= 0,
        "expires_at": promo.get("expires_at"),
        "usage_limit": promo.get("usage_limit"),
        "usage_count": promo.get("usage_count"),
        "notes": promo.get("notes") or "",
        "pricing_separation_notice": PROMO_PRICING_NOTICE,
    }


def validate_promo_code(code: str, plan: Optional[str] = None) -> Dict[str, Any]:
    promo = get_promo_code_by_code(code)
    state = _check_promo_state(promo, plan=plan)
    result = {
        "valid": bool(state.get("valid")),
        "reason": state.get("reason"),
        "promo_code": state.get("promo_code"),
        "preview": None,
        "pricing_separation_notice": PROMO_PRICING_NOTICE,
    }

    if result["valid"] and plan:
        result["preview"] = build_promo_preview(state["promo_code"], plan)

    return result


def apply_promo_code(code: str, plan: str) -> Dict[str, Any]:
    validation = validate_promo_code(code, plan=plan)
    if not validation.get("valid"):
        return {
            "applied": False,
            "reason": validation.get("reason"),
            "preview": validation.get("preview"),
            "pricing_separation_notice": PROMO_PRICING_NOTICE,
        }

    promo = validation.get("promo_code") or {}

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE promo_codes
        SET usage_count = COALESCE(usage_count, 0) + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE code = ?
        """,
        (_normalise_code(code),),
    )
    conn.commit()
    conn.close()

    refreshed = get_promo_code_by_code(code) or promo
    preview = build_promo_preview(refreshed, plan)
    return {
        "applied": True,
        "reason": None,
        "promo_code": refreshed,
        "preview": preview,
        "pricing_separation_notice": PROMO_PRICING_NOTICE,
    }
