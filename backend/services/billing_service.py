from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple


CORE_PRODUCT_ID = "safebite_core_monthly"
SAFEHOME_ADDON_PRODUCT_ID = "safehome_addon"

REVENUECAT_PROJECT_ID_ENV = "REVENUECAT_PROJECT_ID"
REVENUECAT_API_KEY_ENV = "REVENUECAT_API_KEY"
REVENUECAT_WEBHOOK_SECRET_ENV = "REVENUECAT_WEBHOOK_SECRET"
REVENUECAT_ENV_ENV = "REVENUECAT_ENV"
APPLE_PRODUCT_ID_ENV = "APPLE_PRODUCT_ID"
GOOGLE_PRODUCT_ID_ENV = "GOOGLE_PRODUCT_ID"
SAFEHOME_ADDON_PRODUCT_ID_ENV = "SAFEHOME_ADDON_PRODUCT_ID"

REVENUECAT_ENV_PLACEHOLDERS = [
    REVENUECAT_PROJECT_ID_ENV,
    REVENUECAT_API_KEY_ENV,
    REVENUECAT_WEBHOOK_SECRET_ENV,
    REVENUECAT_ENV_ENV,
    APPLE_PRODUCT_ID_ENV,
    GOOGLE_PRODUCT_ID_ENV,
    SAFEHOME_ADDON_PRODUCT_ID_ENV,
]

BILLING_PROVIDER_APPLE = "apple_iap"
BILLING_PROVIDER_GOOGLE = "google_play_billing"
BILLING_PROVIDER_STRIPE = "stripe_web"

SUPPORTED_BILLING_PROVIDERS = {
    BILLING_PROVIDER_APPLE,
    BILLING_PROVIDER_GOOGLE,
    BILLING_PROVIDER_STRIPE,
}

SUPPORTED_PRODUCTS = {
    CORE_PRODUCT_ID: {
        "product_id": CORE_PRODUCT_ID,
        "name": "SafeBite Core",
        "plan_code": "paid_monthly",
        "price": 5.00,
        "currency": "GBP",
        "billing_period": "month",
        "entitlement": "safebite_core",
    },
    SAFEHOME_ADDON_PRODUCT_ID: {
        "product_id": SAFEHOME_ADDON_PRODUCT_ID,
        "name": "SafeHome Add-on",
        "plan_code": "safehome_addon",
        "price": None,
        "currency": "GBP",
        "billing_period": "month",
        "entitlement": "safehome_addon",
    },
}

BILLING_NOTICE = (
    "Billing is provider-ready. Paid access is granted only after a verified App Store, Google Play, "
    "or future Stripe subscription status, except promo/influencer access."
)


def revenuecat_environment() -> str:
    cleaned = os.environ.get(REVENUECAT_ENV_ENV, "development").strip().lower()
    return cleaned if cleaned in {"development", "production"} else "development"


def revenuecat_public_config() -> Dict[str, Any]:
    return {
        "provider": "revenuecat",
        "environment": revenuecat_environment(),
        "placeholder_env_names": list(REVENUECAT_ENV_PLACEHOLDERS),
        "configured": {
            "project_id": bool(os.environ.get(REVENUECAT_PROJECT_ID_ENV)),
            "api_key": bool(os.environ.get(REVENUECAT_API_KEY_ENV)),
            "webhook_secret": bool(os.environ.get(REVENUECAT_WEBHOOK_SECRET_ENV)),
        },
        "product_ids": {
            "apple": os.environ.get(APPLE_PRODUCT_ID_ENV, CORE_PRODUCT_ID),
            "google": os.environ.get(GOOGLE_PRODUCT_ID_ENV, CORE_PRODUCT_ID),
            "safehome_addon": os.environ.get(SAFEHOME_ADDON_PRODUCT_ID_ENV, SAFEHOME_ADDON_PRODUCT_ID),
        },
        "notice": "RevenueCat placeholders are configuration only. Secrets are never returned by this endpoint.",
    }


def billing_dev_mode_enabled() -> bool:
    return os.environ.get("SAFEBITE_BILLING_DEV_MODE", "").strip().lower() in {"1", "true", "yes"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialise(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalise_provider(provider: Any) -> str:
    cleaned = str(provider or "").strip().lower()
    if cleaned not in SUPPORTED_BILLING_PROVIDERS:
        raise ValueError("Unsupported billing provider")
    return cleaned


def normalise_product(product_id: Any) -> Dict[str, Any]:
    cleaned = str(product_id or "").strip()
    product = SUPPORTED_PRODUCTS.get(cleaned)
    if not product:
        raise ValueError("Unsupported billing product")
    return dict(product)


def list_billing_products() -> Dict[str, Any]:
    return {
        "products": [dict(item) for item in SUPPORTED_PRODUCTS.values()],
        "providers": sorted(SUPPORTED_BILLING_PROVIDERS),
        "revenuecat": revenuecat_public_config(),
        "billing_dev_mode": billing_dev_mode_enabled(),
        "notice": BILLING_NOTICE,
    }


def verify_provider_purchase(
    *,
    provider: str,
    product_id: str,
    purchase_token: Optional[str] = None,
    transaction_id: Optional[str] = None,
    platform: Optional[str] = None,
) -> Tuple[bool, Dict[str, Any]]:
    cleaned_provider = normalise_provider(provider)
    product = normalise_product(product_id)
    token = str(purchase_token or "").strip()
    transaction = str(transaction_id or "").strip()

    if not token and not transaction:
        return False, {
            "status": "pending_verification",
            "reason": "purchase_token_or_transaction_id_required",
            "provider": cleaned_provider,
            "product": product,
            "platform": platform or "",
            "notice": BILLING_NOTICE,
        }

    if billing_dev_mode_enabled() and (token == "SAFEBITE_DEV_VERIFIED" or transaction == "SAFEBITE_DEV_VERIFIED"):
        return True, {
            "status": "active",
            "reason": None,
            "provider": cleaned_provider,
            "product": product,
            "platform": platform or "",
            "expires_at": _serialise(_utc_now() + timedelta(days=30)),
            "development_mode": True,
            "notice": "Development verification only. Do not use for production access.",
        }

    return False, {
        "status": "pending_verification",
        "reason": "live_provider_verification_not_configured",
        "provider": cleaned_provider,
        "product": product,
        "platform": platform or "",
        "notice": BILLING_NOTICE,
    }
