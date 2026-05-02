import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import database as database_module
import services.promo_service as promo_service_module
from database import DatabaseManager, get_all_products
from services.analysis_service import analyse_product
from services.pricing_service import build_pricing_summary
from services.promo_service import (
    create_promo_code,
    delete_promo_code,
    get_promo_code_by_code,
    list_promo_codes,
    apply_promo_code,
    validate_promo_code,
)


def expect(condition: bool, message: str, failures: list[str]) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SafeBite Phase 7 promo and pricing logic")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)
    promo_service_module.db = database_module.db

    failures: list[str] = []
    created_ids: list[int] = []

    try:
        percent_code = create_promo_code(
            code="PHASE7PERCENT20",
            code_type="subscription",
            discount_type="percent",
            discount_value=20,
            usage_limit=5,
            plan_scope="monthly",
            campaign_label="Phase 7 percent test",
        )
        created_ids.append(int(percent_code["id"]))

        fixed_code = create_promo_code(
            code="PHASE7FIXED10",
            code_type="campaign",
            discount_type="fixed",
            discount_value=10,
            usage_limit=2,
            plan_scope="annual",
            campaign_label="Phase 7 fixed test",
        )
        created_ids.append(int(fixed_code["id"]))

        free_code = create_promo_code(
            code="PHASE7INFLUENCER",
            code_type="influencer",
            discount_type="free_access",
            discount_value=100,
            usage_limit=1,
            plan_scope="all",
            campaign_label="Influencer full access",
        )
        created_ids.append(int(free_code["id"]))

        inactive_code = create_promo_code(
            code="PHASE7INACTIVE",
            code_type="campaign",
            discount_type="percent",
            discount_value=15,
            is_active=False,
        )
        created_ids.append(int(inactive_code["id"]))

        expired_code = create_promo_code(
            code="PHASE7EXPIRED",
            code_type="campaign",
            discount_type="fixed",
            discount_value=3,
            expires_at="2020-01-01T00:00:00Z",
        )
        created_ids.append(int(expired_code["id"]))

        active_codes = list_promo_codes(active_only=True)
        active_code_values = {item.get("code") for item in active_codes}
        expect("PHASE7PERCENT20" in active_code_values, "Active promo code should appear in list", failures)
        expect("PHASE7INACTIVE" not in active_code_values, "Inactive promo code should be filtered from active list", failures)

        validation = validate_promo_code("PHASE7PERCENT20", plan="monthly")
        preview = validation.get("preview") or {}
        expect(validation.get("valid") is True, "Active promo code should validate", failures)
        expect(preview.get("final_price") == 3.99, "Percent discount preview should reduce monthly plan price", failures)

        fixed_validation = validate_promo_code("PHASE7FIXED10", plan="annual")
        fixed_preview = fixed_validation.get("preview") or {}
        expect(fixed_preview.get("final_price") == 39.99, "Fixed discount preview should reduce annual plan price", failures)

        free_application = apply_promo_code("PHASE7INFLUENCER", plan="annual")
        free_preview = free_application.get("preview") or {}
        expect(free_application.get("applied") is True, "Influencer code should apply successfully", failures)
        expect(free_preview.get("final_price") == 0.0, "Free-access code should reduce plan price to zero", failures)
        expect(bool(free_preview.get("access_granted")), "Free-access code should mark access as granted", failures)

        exhausted_validation = validate_promo_code("PHASE7INFLUENCER", plan="monthly")
        expect(exhausted_validation.get("valid") is False, "Usage-limited code should stop validating once exhausted", failures)

        inactive_validation = validate_promo_code("PHASE7INACTIVE", plan="monthly")
        expect(inactive_validation.get("valid") is False, "Inactive promo code should fail validation", failures)

        expired_validation = validate_promo_code("PHASE7EXPIRED", plan="monthly")
        expect(expired_validation.get("valid") is False, "Expired promo code should fail validation", failures)

        offers = [
            {
                "barcode": "demo-1",
                "retailer": "Tesco",
                "price": 1.80,
                "stock_status": "in_stock",
                "in_stock": True,
                "promotion_type": "multi_buy",
                "promotion_label": "2 for £3.00",
                "buy_quantity": 2,
                "bundle_price": 3.00,
                "product_url": "https://example.com/tesco",
            },
            {
                "barcode": "demo-1",
                "retailer": "Sainsbury's",
                "price": 1.70,
                "stock_status": "in_stock",
                "in_stock": True,
                "product_url": "https://example.com/sainsburys",
            },
            {
                "barcode": "demo-1",
                "retailer": "Asda",
                "price": 1.60,
                "stock_status": "out_of_stock",
                "in_stock": False,
                "product_url": "https://example.com/asda",
            },
        ]
        pricing = build_pricing_summary(offers)
        expect(pricing.get("cheapest_retailer") == "Sainsbury's", "Single-unit best price should still prefer the cheapest in-stock retailer", failures)
        expect(pricing.get("best_price") == 1.70, "Best price should remain the best single-unit price", failures)
        expect(pricing.get("best_value_price") == 1.50, "Best value price should reflect the multi-buy effective price", failures)
        expect(pricing.get("best_value_retailer") == "Tesco", "Best value retailer should come from the multi-buy offer when it beats single-unit pricing", failures)
        expect(pricing.get("multi_buy_offer_count") == 1, "Pricing summary should count multi-buy offers", failures)

        products = get_all_products()
        if not products:
            expect(False, "At least one product should exist for promo safeguard validation", failures)
        else:
            product = products[0]
            before = analyse_product(product)
            apply_promo_code("PHASE7PERCENT20", plan="monthly")
            after = analyse_product(product)
            expect(before.get("safety_score") == after.get("safety_score"), "Promo codes must not change the core safety score", failures)
            expect(before.get("safety_result") == after.get("safety_result"), "Promo codes must not change the core safety result", failures)
    finally:
        for promo_id in created_ids:
            delete_promo_code(promo_id)

    if failures:
        print("\nPromo and pricing validation: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPromo and pricing validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
