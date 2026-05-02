import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import database as database_module
from database import DatabaseManager
from services.analysis_service import analyse_product
from services.condition_engine import apply_conditions


def expect(condition: bool, message: str, failures: list[str]) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        failures.append(message)


def with_checks(product, allergies=None, conditions=None):
    base_analysis = analyse_product(product)
    updated = apply_conditions(
        analysis=base_analysis,
        allergies=allergies or [],
        conditions=conditions or [],
        product=product,
    )
    return base_analysis, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SafeBite Phase 4 condition engine outputs")
    parser.add_argument("--db", default="safebite.db", help="Path to SQLite DB")
    args = parser.parse_args()

    database_module.db = DatabaseManager(args.db)
    failures: list[str] = []

    dairy_product = {
        "barcode": "test-dairy",
        "name": "Milk Cereal",
        "category": "Baby & Toddler",
        "subcategory": "Porridge",
        "ingredients": ["Skimmed Milk Powder", "Rice Flour"],
        "allergens": ["Milk"],
    }
    dairy_base, dairy_checked = with_checks(dairy_product, allergies=["dairy"])
    expect(dairy_checked["condition_results"]["dairy"]["result"] == "Avoid", "Dairy trigger should return Avoid", failures)
    expect(dairy_checked.get("safety_score") == dairy_base.get("safety_score"), "Condition engine must not overwrite core safety score", failures)

    alias_base, alias_checked = with_checks(dairy_product, allergies=["milk"])
    expect("dairy" in alias_checked.get("condition_results", {}), "Milk alias should normalize to dairy", failures)
    expect(alias_checked.get("safety_result") == alias_base.get("safety_result"), "Alias check should also preserve core safety result", failures)

    coeliac_product = {
        "barcode": "test-coeliac",
        "name": "Wheat Biscuit",
        "category": "Baby Snacks",
        "subcategory": "Oat Snacks",
        "ingredients": ["Wheat Flour", "Apple Puree"],
        "allergens": ["Gluten"],
    }
    _, coeliac_checked = with_checks(coeliac_product, conditions=["coeliac"])
    expect(coeliac_checked["condition_results"]["coeliac"]["result"] == "Avoid", "Coeliac engine should reject gluten ingredients", failures)

    ibs_product = {
        "barcode": "test-ibs",
        "name": "Prebiotic Puree",
        "category": "Baby & Toddler",
        "subcategory": "Fruit Puree",
        "ingredients": ["Apple Puree", "Inulin"],
        "allergens": [],
    }
    _, ibs_checked = with_checks(ibs_product, conditions=["ibs"])
    expect(ibs_checked["condition_results"]["ibs"]["result"] == "Caution", "IBS engine should flag inulin as a caution trigger", failures)

    stoma_product = {
        "barcode": "test-stoma",
        "name": "Seeded Oat Bar",
        "category": "Baby Snacks",
        "subcategory": "Oat Snacks",
        "ingredients": ["Wholegrain Oats", "Pumpkin Seeds"],
        "allergens": [],
    }
    _, stoma_checked = with_checks(stoma_product, conditions=["stoma"])
    expect(stoma_checked["condition_results"]["stoma"]["result"] == "Caution", "Stoma engine should flag seeds or high-fibre grains", failures)

    baby_product = {
        "barcode": "test-baby-sensitive",
        "name": "Sweet Snack",
        "category": "Baby Snacks",
        "subcategory": "Oat Snacks",
        "ingredients": ["Glucose Syrup", "Apple Juice Concentrate", "Natural Flavouring"],
        "allergens": [],
    }
    _, baby_checked = with_checks(baby_product, conditions=["baby-specific sensitivity"])
    expect(
        baby_checked["condition_results"]["baby-specific sensitivity"]["result"] in {"Caution", "Avoid"},
        "Baby sensitivity should react to sugar and additive patterns",
        failures,
    )

    unknown_product = {
        "barcode": "test-unknown-condition",
        "name": "Unknown Mix",
        "category": "Baby & Toddler",
        "subcategory": "Fruit Puree",
        "ingredients": [],
        "allergens": [],
    }
    _, unknown_checked = with_checks(unknown_product, allergies=["dairy"], conditions=["ibs"])
    expect(unknown_checked["condition_results"]["dairy"]["result"] == "Unknown", "Missing ingredients should return Unknown for allergy checks", failures)
    expect(unknown_checked["condition_results"]["ibs"]["result"] == "Unknown", "Missing ingredients should return Unknown for condition checks", failures)

    mixed_product = {
        "barcode": "test-multi",
        "name": "Mixed Trigger Product",
        "category": "Baby & Toddler",
        "subcategory": "Porridge",
        "ingredients": ["Skimmed Milk Powder", "Wheat Flour", "Inulin"],
        "allergens": ["Milk", "Gluten"],
    }
    _, mixed_checked = with_checks(mixed_product, allergies=["dairy"], conditions=["coeliac", "ibs"])
    expect(set(mixed_checked["condition_results"].keys()) == {"dairy", "coeliac", "ibs"}, "Multiple condition requests should return all requested results", failures)

    if failures:
        print("\nCondition engine validation: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nCondition engine validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
