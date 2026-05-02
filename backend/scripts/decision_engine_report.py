import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from collections import Counter
from typing import Any, Dict, List

import database as database_module
from database import DatabaseManager
from services.analysis_service import analyse_product
from services.alternatives_service import build_alternatives
from services.pricing_service import build_pricing_summary


def product_label(product: Dict[str, Any]) -> str:
    return "{barcode} | {name} | {category} / {subcategory}".format(
        barcode=product.get("barcode") or "",
        name=product.get("name") or "",
        category=product.get("category") or "",
        subcategory=product.get("subcategory") or "",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SafeBite Phase 3 decision-engine quality")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)
    products = database_module.get_all_products()

    unknown_products: List[Dict[str, Any]] = []
    products_with_unknown_flags: List[Dict[str, Any]] = []
    products_without_ranked_alternatives: List[Dict[str, Any]] = []
    products_with_incomplete_pricing: List[Dict[str, Any]] = []
    unknown_flag_counts: Counter[str] = Counter()

    for product in products:
        analysis = analyse_product(product)
        pricing = build_pricing_summary(database_module.get_offers_by_barcode(product.get("barcode") or ""))
        alternatives = build_alternatives(product)

        if analysis.get("safety_result") == "Unknown":
            unknown_products.append({"product": product, "analysis": analysis})

        if analysis.get("unknown_flags"):
            products_with_unknown_flags.append({"product": product, "analysis": analysis})
            unknown_flag_counts.update(analysis.get("unknown_flags", []))

        if not any(alternatives.get(key) for key in ["safer_option", "cheaper_option", "same_category_option"]):
            products_without_ranked_alternatives.append({"product": product, "alternatives": alternatives})

        if pricing.get("best_price") is None or pricing.get("cheapest_retailer") is None:
            products_with_incomplete_pricing.append({"product": product, "pricing": pricing})

    print("PHASE 3 DECISION ENGINE REPORT")
    print("=" * 80)
    print(f"Products total: {len(products)}")
    print(f"Products with Unknown decision: {len(unknown_products)}")
    print(f"Products with unknown flags: {len(products_with_unknown_flags)}")
    print(f"Products without ranked alternatives: {len(products_without_ranked_alternatives)}")
    print(f"Products with incomplete pricing intelligence: {len(products_with_incomplete_pricing)}")

    print("\nUnknown flags by type")
    if unknown_flag_counts:
        for flag_name, count in unknown_flag_counts.most_common():
            print(f"- {flag_name}: {count}")
    else:
        print("- none")

    print("\nProducts with Unknown decision")
    if not unknown_products:
        print("- none")
    else:
        for item in unknown_products[:10]:
            print(f"- {product_label(item['product'])}")

    print("\nProducts without ranked alternatives")
    if not products_without_ranked_alternatives:
        print("- none")
    else:
        for item in products_without_ranked_alternatives[:10]:
            print(f"- {product_label(item['product'])}")

    print("\nProducts with incomplete pricing intelligence")
    if not products_with_incomplete_pricing:
        print("- none")
    else:
        for item in products_with_incomplete_pricing[:10]:
            print(f"- {product_label(item['product'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
