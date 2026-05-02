import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import sys

import database as database_module
from database import DatabaseManager
from services.analysis_service import analyse_product
from services.alternatives_service import build_alternatives
from services.pricing_service import build_pricing_summary


def expect(condition: bool, message: str, failures: list[str]) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SafeBite Phase 3 decision engine outputs")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)

    failures: list[str] = []

    simple_puree = analyse_product(
        {
            "barcode": "test-safe-puree",
            "name": "Simple Apple Puree",
            "category": "Baby & Toddler",
            "subcategory": "Fruit Puree",
            "ingredients": ["Apple"],
            "allergens": [],
        }
    )
    expect(simple_puree.get("safety_result") == "Safe", "Simple fruit puree should score as Safe", failures)
    expect(simple_puree.get("safety_score") is not None, "Simple fruit puree should have a score", failures)

    unknown_product = analyse_product(
        {
            "barcode": "test-unknown",
            "name": "Mystery Product",
            "category": "Baby & Toddler",
            "subcategory": "Fruit Puree",
            "ingredients": [],
            "allergens": [],
        }
    )
    expect(unknown_product.get("safety_result") == "Unknown", "Missing ingredients should return Unknown", failures)
    expect(unknown_product.get("safety_score") is None, "Unknown decision should not fabricate a score", failures)
    expect(
        "missing_ingredients_flag" in unknown_product.get("unknown_flags", []),
        "Unknown decision should carry missing ingredient flag",
        failures,
    )

    pricing = build_pricing_summary(
        [
            {
                "retailer": "Tesco",
                "price": 1.50,
                "promo_price": None,
                "in_stock": False,
                "stock_status": "out_of_stock",
                "product_url": "https://example.com/a",
            },
            {
                "retailer": "Asda",
                "price": 1.80,
                "promo_price": 1.20,
                "in_stock": True,
                "stock_status": "in_stock",
                "product_url": "https://example.com/b",
            },
            {
                "retailer": "Sainsbury's",
                "price": 1.30,
                "promo_price": None,
                "in_stock": True,
                "stock_status": "in_stock",
                "product_url": "https://example.com/c",
            },
        ]
    )
    expect(pricing.get("lowest_price") == 1.2, "Promo price should win lowest overall price", failures)
    expect(pricing.get("lowest_in_stock_price") == 1.2, "Promo price should win lowest in-stock price", failures)
    expect(pricing.get("cheapest_retailer") == "Asda", "Cheapest retailer should prefer actionable in-stock offer", failures)

    products = database_module.get_all_products()
    expect(bool(products), "Database should contain products for live validation", failures)

    target = None
    for product in products:
        alts = build_alternatives(product)
        if alts.get("same_category_option"):
            target = (product, alts)
            break

    expect(target is not None, "At least one live product should produce ranked alternatives", failures)
    if target is not None:
        product, alternatives = target
        expect(
            alternatives.get("same_category_option", {}).get("barcode") != product.get("barcode"),
            "Same-category alternative must not point back to the current product",
            failures,
        )

    if failures:
        print("\nDecision engine validation: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nDecision engine validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
