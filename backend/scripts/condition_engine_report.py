import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import database as database_module
from database import DatabaseManager
from services.analysis_service import analyse_product
from services.condition_engine import apply_conditions


LOCKED_ALLERGIES = ["dairy", "nuts", "gluten", "soy", "egg"]
LOCKED_CONDITIONS = ["ibs", "stoma", "coeliac", "baby-specific sensitivity"]


def product_label(product: dict[str, Any]) -> str:
    return "{barcode} | {name} | {category} / {subcategory}".format(
        barcode=product.get("barcode") or "",
        name=product.get("name") or "",
        category=product.get("category") or "",
        subcategory=product.get("subcategory") or "",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SafeBite Phase 4 condition-engine quality")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)
    products = database_module.get_all_products()

    condition_result_counts: Counter[str] = Counter()
    products_with_unknowns: list[str] = []
    products_with_multiple_flags: list[str] = []
    products_with_missing_explanations: list[str] = []

    for product in products:
        analysis = analyse_product(product)
        health_analysis = apply_conditions(
            analysis=analysis,
            allergies=LOCKED_ALLERGIES,
            conditions=LOCKED_CONDITIONS,
            product=product,
        )
        results = health_analysis.get("condition_results", {}) or {}
        non_safe = []
        has_unknown = False
        missing_explanation = False

        for key, result in results.items():
            label = str(result.get("result") or "Unknown")
            condition_result_counts[f"{key}:{label}"] += 1
            if label != "Safe":
                non_safe.append(key)
            if label == "Unknown":
                has_unknown = True
            if label != "Safe" and not str(result.get("summary") or "").strip():
                missing_explanation = True

        if has_unknown:
            products_with_unknowns.append(product_label(product))
        if len(non_safe) >= 2:
            products_with_multiple_flags.append(product_label(product))
        if missing_explanation:
            products_with_missing_explanations.append(product_label(product))

    print("PHASE 4 CONDITION ENGINE REPORT")
    print("=" * 80)
    print(f"Products total: {len(products)}")
    print(f"Products with any Unknown condition result: {len(products_with_unknowns)}")
    print(f"Products with 2+ non-safe health flags: {len(products_with_multiple_flags)}")
    print(f"Products with missing health explanations: {len(products_with_missing_explanations)}")

    print("\nCondition result counts")
    if condition_result_counts:
        for key, count in condition_result_counts.most_common():
            print(f"- {key}: {count}")
    else:
        print("- none")

    print("\nProducts with Unknown condition result")
    if products_with_unknowns:
        for label in products_with_unknowns[:10]:
            print(f"- {label}")
    else:
        print("- none")

    print("\nProducts with multiple non-safe health flags")
    if products_with_multiple_flags:
        for label in products_with_multiple_flags[:10]:
            print(f"- {label}")
    else:
        print("- none")

    print("\nProducts with missing health explanations")
    if products_with_missing_explanations:
        for label in products_with_missing_explanations[:10]:
            print(f"- {label}")
    else:
        print("- none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
