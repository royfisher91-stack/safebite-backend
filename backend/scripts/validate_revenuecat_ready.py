from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import List


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


EXPECTED_PRODUCT_IDS = ["safebite_core_monthly", "safehome_addon"]
EXPECTED_ENV_NAMES = [
    "REVENUECAT_PROJECT_ID",
    "REVENUECAT_API_KEY",
    "REVENUECAT_WEBHOOK_SECRET",
    "REVENUECAT_ENV",
    "APPLE_PRODUCT_ID",
    "GOOGLE_PRODUCT_ID",
    "SAFEHOME_ADDON_PRODUCT_ID",
]
EXPECTED_ROUTES = [
    "/billing/products",
    "/billing/verify",
    "/subscription/entitlement",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_contains(text: str, needles: List[str], label: str, errors: List[str]) -> None:
    for needle in needles:
        if needle not in text:
            errors.append("{0} missing {1}".format(label, needle))


def validate_no_fake_paid_access(errors: List[str]) -> None:
    import database

    with tempfile.TemporaryDirectory() as tmpdir:
        database.db = database.DatabaseManager(str(Path(tmpdir) / "revenuecat_ready.db"))

        from services.auth_service import register_user
        from services.entitlement_service import get_entitlement
        from services.subscription_service import activate_monthly_subscription, verify_and_apply_billing_subscription

        user = register_user("revenuecat-ready@example.com", "StrongPassword123!")

        activation = activate_monthly_subscription(int(user["id"]))
        entitlement = get_entitlement(int(user["id"]))
        if activation.get("status") == "active" or entitlement.get("access_active"):
            errors.append("/subscription/activate grants paid access without provider verification")

        verification = verify_and_apply_billing_subscription(
            int(user["id"]),
            provider="apple_iap",
            product_id="safebite_core_monthly",
        )
        entitlement = get_entitlement(int(user["id"]))
        if verification.get("verified") or entitlement.get("access_active"):
            errors.append("/billing/verify grants paid access without purchase token or transaction id")


def main() -> int:
    errors: List[str] = []
    warnings: List[str] = []

    billing_path = BACKEND_DIR / "services" / "billing_service.py"
    main_path = BACKEND_DIR / "mainBE.py"
    doc_path = PROJECT_DIR / "docs" / "launch" / "revenuecat_setup.md"

    if not billing_path.exists():
        errors.append("services/billing_service.py missing")
        billing_text = ""
    else:
        billing_text = read_text(billing_path)

    if not main_path.exists():
        errors.append("mainBE.py missing")
        main_text = ""
    else:
        main_text = read_text(main_path)

    if not doc_path.exists():
        errors.append("docs/launch/revenuecat_setup.md missing")
        doc_text = ""
    else:
        doc_text = read_text(doc_path)

    check_contains(billing_text, EXPECTED_PRODUCT_IDS, "billing_service.py", errors)
    check_contains(main_text, EXPECTED_ROUTES, "mainBE.py", errors)
    check_contains(doc_text, EXPECTED_ENV_NAMES, "revenuecat_setup.md", errors)
    check_contains(doc_text, EXPECTED_PRODUCT_IDS, "revenuecat_setup.md", errors)

    if "SAFEBITE_DEV_VERIFIED" in billing_text and "billing_dev_mode_enabled" not in billing_text:
        warnings.append("development verification token found without explicit development flag check")

    if re.search(r"sk_(live|test)_|rc_[A-Za-z0-9]{20,}", billing_text + doc_text):
        errors.append("possible real secret key found in billing service or RevenueCat docs")

    try:
        from services.billing_service import list_billing_products

        products = list_billing_products()
        product_ids = [item.get("product_id") for item in products.get("products", [])]
        for product_id in EXPECTED_PRODUCT_IDS:
            if product_id not in product_ids:
                errors.append("billing products response missing {0}".format(product_id))
        revenuecat = products.get("revenuecat") or {}
        placeholders = revenuecat.get("placeholder_env_names") or []
        for env_name in EXPECTED_ENV_NAMES:
            if env_name not in placeholders:
                errors.append("billing products response missing RevenueCat placeholder {0}".format(env_name))
        json.dumps(products)
    except Exception as exc:
        errors.append("billing products response failed: {0}".format(exc))

    try:
        validate_no_fake_paid_access(errors)
    except Exception as exc:
        errors.append("paid-access safeguard check failed: {0}".format(exc))

    print("RevenueCat readiness validation")
    print("- billing_service.py: {0}".format("present" if billing_path.exists() else "missing"))
    print("- revenuecat_setup.md: {0}".format("present" if doc_path.exists() else "missing"))
    print("- expected_product_ids: {0}".format(", ".join(EXPECTED_PRODUCT_IDS)))
    print("- expected_env_placeholders: {0}".format(", ".join(EXPECTED_ENV_NAMES)))
    print("- warnings: {0}".format(len(warnings)))
    print("- errors: {0}".format(len(errors)))

    if warnings:
        print("\nWarnings")
        for warning in warnings:
            print("- {0}".format(warning))

    if errors:
        print("\nErrors")
        for error in errors:
            print("- {0}".format(error))
        return 1

    print("RevenueCat readiness validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
