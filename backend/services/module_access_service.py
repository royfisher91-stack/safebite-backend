from typing import Any, Dict, Optional

from core.registry import get_module_config
from services.entitlement_service import get_entitlement


def check_module_access(module_code: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    config = get_module_config(module_code)
    requirement = config.get("requires_subscription")

    if requirement == "base_subscription":
        return {
            "module_code": module_code,
            "allowed": True,
            "requires_subscription": requirement,
            "reason": None,
        }

    if requirement == "safehome_addon":
        if user_id is None:
            return {
                "module_code": module_code,
                "allowed": False,
                "requires_subscription": requirement,
                "reason": "SafeHome requires a signed-in account with the SafeHome add-on.",
            }

        entitlement = get_entitlement(user_id)
        plan = str(entitlement.get("plan") or "").lower()
        add_ons = set(entitlement.get("add_on_entitlements") or [])
        allowed = plan in {"safehome_addon", "safehome_paid", "safehome_bundle"} or "safehome_addon" in add_ons
        return {
            "module_code": module_code,
            "allowed": allowed,
            "requires_subscription": requirement,
            "reason": None if allowed else "SafeHome add-on is locked for this account.",
            "entitlement": entitlement,
        }

    return {
        "module_code": module_code,
        "allowed": False,
        "requires_subscription": requirement,
        "reason": "Unsupported module access requirement.",
    }
