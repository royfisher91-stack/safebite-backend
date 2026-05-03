from typing import Any, Dict, List, Optional

from database import get_all_products, get_offers_by_barcode
from services.alternatives_service import build_alternatives
from services.analysis_service import analyse_product
from services.pricing_service import build_pricing_summary


OPTION_KEYS = [
    "safer_option",
    "cheaper_option",
    "same_category_option",
]


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_lower(value: Any) -> str:
    return _clean(value).lower()


def _is_catalogue_product(product: Dict[str, Any]) -> bool:
    source = _clean_lower(product.get("source"))
    return source in {"open_food_facts", "open_food_facts_catalogue", "licensed_catalogue"}


def _product_label(product: Dict[str, Any]) -> str:
    return "{barcode} | {name} | {category} / {subcategory}".format(
        barcode=product.get("barcode") or "",
        name=product.get("name") or "",
        category=product.get("category") or "",
        subcategory=product.get("subcategory") or "",
    )


def _option_label(option: Optional[Dict[str, Any]]) -> str:
    if not option:
        return "none"

    price = option.get("best_price")
    retailer = option.get("cheapest_retailer") or ""

    return "{barcode} | {name} | {category} / {subcategory} | score={score} | price={price} | {retailer}".format(
        barcode=option.get("barcode") or "",
        name=option.get("name") or "",
        category=option.get("category") or "",
        subcategory=option.get("subcategory") or "",
        score=option.get("safety_score"),
        price=price,
        retailer=retailer,
    )


def _pricing_for_product(product: Dict[str, Any]) -> Dict[str, Any]:
    barcode = _clean(product.get("barcode"))
    if not barcode:
        return build_pricing_summary([])
    return build_pricing_summary(get_offers_by_barcode(barcode))


def _same_category(product: Dict[str, Any], option: Dict[str, Any]) -> bool:
    return _clean_lower(product.get("category")) == _clean_lower(option.get("category"))


def _same_subcategory(product: Dict[str, Any], option: Dict[str, Any]) -> bool:
    return (
        _clean_lower(product.get("category")) == _clean_lower(option.get("category"))
        and _clean_lower(product.get("subcategory")) == _clean_lower(option.get("subcategory"))
    )


def _same_subcategory_count(product: Dict[str, Any], products: List[Dict[str, Any]]) -> int:
    barcode = _clean(product.get("barcode"))
    category = _clean_lower(product.get("category"))
    subcategory = _clean_lower(product.get("subcategory"))

    if not category or not subcategory:
        return 0

    total = 0
    for candidate in products:
        if _clean(candidate.get("barcode")) == barcode:
            continue
        if category != _clean_lower(candidate.get("category")):
            continue
        if subcategory != _clean_lower(candidate.get("subcategory")):
            continue
        total += 1

    return total


def _validate_option(
    product: Dict[str, Any],
    option_key: str,
    option: Optional[Dict[str, Any]],
    same_subcategory_count: int,
    current_price: Optional[float],
) -> List[str]:
    issues = []

    if not option:
        return issues

    product_barcode = _clean(product.get("barcode"))
    option_barcode = _clean(option.get("barcode"))

    if product_barcode and product_barcode == option_barcode:
        issues.append(f"{option_key} points to the current product")

    if same_subcategory_count > 0 and not _same_subcategory(product, option):
        issues.append(f"{option_key} should stay in same subcategory when same-subcategory choices exist")
    elif not _same_category(product, option):
        issues.append(f"{option_key} does not match category")

    if option_key == "safer_option":
        current_analysis = analyse_product(product)
        current_score = safe_int(current_analysis.get("safety_score"), 50)
        option_score = safe_int(option.get("safety_score"), 50)
        if current_analysis.get("safety_result") != "Unknown" and option_score <= current_score:
            issues.append("safer_option is not actually safer by score")

    if option_key == "cheaper_option":
        option_price = safe_float(option.get("best_price"))
        if current_price is None:
            if not _is_catalogue_product(product):
                issues.append("cheaper_option exists but current product has no price")
        elif option_price is None:
            issues.append("cheaper_option has no price")
        elif option_price >= current_price:
            issues.append("cheaper_option is not actually cheaper")

    return issues


def build_alternatives_quality_report() -> Dict[str, Any]:
    products = get_all_products(limit=100000)
    rows = []
    issues = []
    products_with_same_subcategory_option = 0
    products_with_cheaper_option = 0
    products_with_safer_option = 0
    products_without_retailer_offers = 0

    for product in products:
        barcode = _clean(product.get("barcode"))
        pricing = _pricing_for_product(product)
        current_price = safe_float(pricing.get("best_price"))
        if current_price is None:
            products_without_retailer_offers += 1
        alternatives = build_alternatives(product)
        same_subcategory_count = _same_subcategory_count(product, products)
        row_issues = []

        for option_key in OPTION_KEYS:
            option = alternatives.get(option_key)

            if option_key == "same_category_option" and option:
                products_with_same_subcategory_option += 1
            if option_key == "cheaper_option" and option:
                products_with_cheaper_option += 1
            if option_key == "safer_option" and option:
                products_with_safer_option += 1

            row_issues.extend(
                _validate_option(
                    product=product,
                    option_key=option_key,
                    option=option,
                    same_subcategory_count=same_subcategory_count,
                    current_price=current_price,
                )
            )

        if same_subcategory_count > 0 and not alternatives.get("same_category_option"):
            row_issues.append("same-subcategory products exist but same_category_option is empty")

        for issue in row_issues:
            issues.append(
                {
                    "barcode": barcode,
                    "name": product.get("name") or "",
                    "issue": issue,
                }
            )

        rows.append(
            {
                "product": product,
                "best_price": current_price,
                "cheapest_retailer": pricing.get("cheapest_retailer"),
                "same_subcategory_count": same_subcategory_count,
                "alternatives": alternatives,
                "issues": row_issues,
            }
        )

    return {
        "summary": {
            "products_total": len(products),
            "products_with_same_category_option": products_with_same_subcategory_option,
            "products_with_cheaper_option": products_with_cheaper_option,
            "products_with_safer_option": products_with_safer_option,
            "products_without_retailer_offers": products_without_retailer_offers,
            "issue_count": len(issues),
        },
        "rows": rows,
        "issues": issues,
    }


def print_alternatives_quality_report() -> None:
    report = build_alternatives_quality_report()
    summary = report["summary"]

    print("\nALTERNATIVES QUALITY REPORT")
    print("=" * 80)
    for key, value in summary.items():
        print(f"- {key}: {value}")

    print("\nProduct Alternatives")

    for row in report["rows"]:
        product = row["product"]
        alternatives = row["alternatives"]
        best_price = row["best_price"]
        retailer = row["cheapest_retailer"] or ""

        print("\n" + _product_label(product))
        print(f"Current price: {best_price} | {retailer}")
        print(f"Same-subcategory candidates: {row['same_subcategory_count']}")

        for option_key in OPTION_KEYS:
            print(f"{option_key}: {_option_label(alternatives.get(option_key))}")

        if row["issues"]:
            for issue in row["issues"]:
                print(f"ISSUE: {issue}")

    print("\nIssues")
    if not report["issues"]:
        print("- none")
    else:
        for issue in report["issues"]:
            print(
                "- {barcode} | {name}: {issue}".format(
                    barcode=issue.get("barcode") or "",
                    name=issue.get("name") or "",
                    issue=issue.get("issue") or "",
                )
            )


def main() -> None:
    print_alternatives_quality_report()


if __name__ == "__main__":
    main()
