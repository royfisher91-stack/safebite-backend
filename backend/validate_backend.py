import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from import_utils import ALLOWED_TAXONOMY


BASE_URL = "http://127.0.0.1:8000"
QUALITY_ZERO_FIELDS = [
    "products_missing_category",
    "products_other_general",
    "products_missing_source",
    "products_placeholder_name",
    "offers_missing_source",
    "offers_missing_price",
    "offers_sample_seed",
]
CATALOGUE_SOURCES = {"open_food_facts", "open_food_facts_catalogue", "licensed_catalogue"}


def fetch_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def is_in_stock(offer: Dict[str, Any]) -> bool:
    value = offer.get("in_stock")
    stock_value = str(value).strip().lower()
    return value is True or stock_value in {"true", "1", "yes", "in stock", "instock"}


def is_catalogue_product(product: Dict[str, Any]) -> bool:
    source = str(product.get("source") or "").strip().lower()
    return source in CATALOGUE_SOURCES


def effective_price(offer: Dict[str, Any]) -> Optional[float]:
    promo_price = safe_float(offer.get("promo_price"))
    normal_price = safe_float(offer.get("price"))

    if promo_price is not None and promo_price > 0:
        return promo_price

    return normal_price


def load_via_http() -> Tuple[str, Dict[str, Any]]:
    from import_quality_report import build_quality_report

    health = fetch_json(f"{BASE_URL}/health")
    products_data = fetch_json(f"{BASE_URL}/products")

    products = products_data.get("products", []) if isinstance(products_data, dict) else products_data
    if not isinstance(products, list):
        raise ValueError("/products did not return a list")

    details = {}
    offers = {}
    alternatives = {}

    for product in products:
        barcode = str(product.get("barcode") or "").strip()
        if not barcode:
            continue

        encoded = urllib.parse.quote(barcode)
        details[barcode] = fetch_json(f"{BASE_URL}/products/barcode/{encoded}")
        offers[barcode] = fetch_json(f"{BASE_URL}/offers/{encoded}")
        alternatives[barcode] = fetch_json(f"{BASE_URL}/alternatives/{encoded}")

    return "http", {
        "health": health,
        "products": products,
        "details": details,
        "offers": offers,
        "alternatives": alternatives,
        "quality": build_quality_report(),
    }


def load_via_direct() -> Tuple[str, Dict[str, Any]]:
    from import_quality_report import build_quality_report
    from mainBE import (
        get_alternatives_route,
        get_offers_route,
        get_product_from_barcode,
        health,
        list_products,
        startup_event,
    )

    startup_event()

    products = list_products(q=None, allergen=None, conditions=None)
    details = {}
    offers = {}
    alternatives = {}

    for product in products:
        barcode = str(product.get("barcode") or "").strip()
        if not barcode:
            continue

        details[barcode] = get_product_from_barcode(
            barcode=barcode,
            allergen=None,
            conditions=None,
        )
        offers[barcode] = get_offers_route(barcode)
        alternatives[barcode] = get_alternatives_route(barcode)

    return "direct", {
        "health": health(),
        "products": products,
        "details": details,
        "offers": offers,
        "alternatives": alternatives,
        "quality": build_quality_report(),
    }


def load_backend_data() -> Tuple[str, Dict[str, Any]]:
    try:
        return load_via_http()
    except (OSError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"HTTP validation unavailable: {exc}")
        print("Falling back to direct in-process validation.\n")
        return load_via_direct()


def add_error(errors: List[str], message: str) -> None:
    errors.append(message)
    print(f"ERROR: {message}")


def add_warning(warnings: List[str], message: str) -> None:
    warnings.append(message)
    print(f"WARNING: {message}")


def validate_taxonomy_pair(
    barcode: str,
    category: str,
    subcategory: str,
    errors: List[str],
) -> None:
    if not category or not subcategory:
        add_error(errors, f"{barcode} has missing category/subcategory")
        return

    allowed_subcategories = ALLOWED_TAXONOMY.get(category)
    if not allowed_subcategories:
        add_error(errors, f"{barcode} has category outside locked taxonomy: {category}")
        return

    if subcategory not in allowed_subcategories:
        add_error(
            errors,
            f"{barcode} has invalid category/subcategory pair: {category} / {subcategory}",
        )


def validate_product_summary(product: Dict[str, Any], errors: List[str]) -> None:
    barcode = str(product.get("barcode") or "").strip()
    name = str(product.get("name") or "").strip()
    category = str(product.get("category") or "").strip()
    subcategory = str(product.get("subcategory") or "").strip()

    if not barcode:
        add_error(errors, f"Product is missing barcode: {name or 'UNKNOWN'}")

    if not name:
        add_error(errors, f"Product is missing name: {barcode or 'UNKNOWN'}")

    if category.lower() == "other" and subcategory.lower() == "general":
        add_error(errors, f"{barcode} still has generic Other / General category")

    validate_taxonomy_pair(barcode or "UNKNOWN", category, subcategory, errors)


def validate_product_detail(
    barcode: str,
    product: Dict[str, Any],
    offer_route: Dict[str, Any],
    alternative_route: Dict[str, Any],
    products: List[Dict[str, Any]],
    errors: List[str],
    warnings: List[str],
) -> None:
    print("\n" + "=" * 80)
    print(f"PRODUCT: {product.get('name', 'UNKNOWN')}")
    print(f"BARCODE: {barcode}")
    print(f"CATEGORY: {product.get('category', '')} / {product.get('subcategory', '')}")

    validate_taxonomy_pair(
        barcode,
        str(product.get("category") or "").strip(),
        str(product.get("subcategory") or "").strip(),
        errors,
    )

    offers = product.get("offers", []) or []
    routed_offers = offer_route.get("offers", []) or []
    route_offer_count = int(offer_route.get("offer_count") or 0)

    print(f"OFFER COUNT: {len(offers)}")

    if route_offer_count != len(routed_offers):
        add_error(errors, f"{barcode} /offers count does not match returned offer list")

    if len(offers) != len(routed_offers):
        add_error(errors, f"{barcode} product detail offer count differs from /offers route")

    catalogue_product = is_catalogue_product(product)

    if not offers and not catalogue_product:
        add_warning(warnings, f"{barcode} has no offers")

    valid_in_stock_offers = []

    for offer in offers:
        retailer = offer.get("retailer", "UNKNOWN")
        price = safe_float(offer.get("price"))
        promo_price = safe_float(offer.get("promo_price"))
        stock_status = offer.get("stock_status")
        in_stock = offer.get("in_stock")
        url = offer.get("product_url") or offer.get("url") or ""

        print(
            f"- {retailer}: price={price}, promo_price={promo_price}, "
            f"stock_status={stock_status}, in_stock={in_stock}, url={url}"
        )

        offer_effective_price = effective_price(offer)
        if is_in_stock(offer) and offer_effective_price is not None:
            valid_in_stock_offers.append(
                {
                    "retailer": retailer,
                    "effective_price": offer_effective_price,
                }
            )

    pricing_summary = product.get("pricing_summary", {}) or {}

    if valid_in_stock_offers:
        cheapest = min(valid_in_stock_offers, key=lambda item: item["effective_price"])
        expected_retailer = cheapest["retailer"]
        expected_price = cheapest["effective_price"]
        actual_retailer = pricing_summary.get("cheapest_retailer")
        actual_price = safe_float(pricing_summary.get("best_price"))

        print(f"EXPECTED cheapest retailer: {expected_retailer}")
        print(f"EXPECTED best price: {expected_price}")
        print(f"API cheapest retailer: {actual_retailer}")
        print(f"API best price: {actual_price}")

        if actual_retailer != expected_retailer:
            add_error(errors, f"{barcode} cheapest retailer mismatch")

        if actual_price != expected_price:
            add_error(errors, f"{barcode} best price mismatch")
    elif not catalogue_product:
        add_warning(warnings, f"{barcode} has no valid in-stock priced offers")

    alternatives = alternative_route.get("alternatives")
    if not isinstance(alternatives, dict):
        add_error(errors, f"{barcode} alternatives route did not return an alternatives object")
        alternatives = {}

    detail_alternatives = product.get("alternatives")
    if not isinstance(detail_alternatives, dict):
        add_error(errors, f"{barcode} product detail did not include alternatives object")
        detail_alternatives = {}

    category = str(product.get("category") or "").strip().lower()
    subcategory = str(product.get("subcategory") or "").strip().lower()
    same_subcategory_count = 0

    for candidate in products:
        candidate_barcode = str(candidate.get("barcode") or "").strip()
        candidate_category = str(candidate.get("category") or "").strip().lower()
        candidate_subcategory = str(candidate.get("subcategory") or "").strip().lower()

        if candidate_barcode == barcode:
            continue
        if category and subcategory and category == candidate_category and subcategory == candidate_subcategory:
            same_subcategory_count += 1

    if same_subcategory_count > 0 and not alternatives.get("same_category_option"):
        add_error(errors, f"{barcode} has same-subcategory products but no same_category_option")

    if same_subcategory_count > 0 and not detail_alternatives.get("same_category_option"):
        add_error(errors, f"{barcode} detail response has same-subcategory products but no same_category_option")

    analysis = product.get("analysis")
    if not isinstance(analysis, dict):
        add_error(errors, f"{barcode} product detail did not include analysis object")


def validate_quality_report(report: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    if not report:
        add_warning(warnings, "No import quality report was available")
        return

    summary = report.get("summary", {}) or {}

    print("\n" + "=" * 80)
    print("IMPORT QUALITY SUMMARY")

    for key, value in summary.items():
        print(f"- {key}: {value}")

    for key in QUALITY_ZERO_FIELDS:
        if int(summary.get(key) or 0) != 0:
            add_error(errors, f"Quality report expected {key} to be 0")

    unknown_stock = int(summary.get("offers_unknown_stock") or 0)
    if unknown_stock:
        add_warning(warnings, f"Quality report still has {unknown_stock} unknown-stock offer(s)")


def validate_alternatives_quality(errors: List[str]) -> None:
    from alternatives_quality_report import build_alternatives_quality_report

    report = build_alternatives_quality_report()
    summary = report.get("summary", {}) or {}

    print("\n" + "=" * 80)
    print("ALTERNATIVES QUALITY SUMMARY")

    for key, value in summary.items():
        print(f"- {key}: {value}")

    for issue in report.get("issues", []):
        barcode = issue.get("barcode") or ""
        name = issue.get("name") or ""
        message = issue.get("issue") or "unknown alternatives issue"
        add_error(errors, f"{barcode} {name}: {message}")


def validate_coverage_summary(errors: List[str]) -> None:
    from coverage_summary_report import build_coverage_summary_report

    report = build_coverage_summary_report()
    summary = report.get("summary", {}) or {}

    print("\n" + "=" * 80)
    print("COVERAGE SUMMARY")

    for key, value in summary.items():
        print(f"- {key}: {value}")

    for issue in report.get("issues", []):
        add_error(errors, issue.get("message") or "unknown coverage issue")


def main() -> None:
    mode, data = load_backend_data()
    errors: List[str] = []
    warnings: List[str] = []

    print(f"Validation mode: {mode}")

    health = data.get("health", {})
    if health.get("status") != "ok":
        add_error(errors, "Health check did not return status=ok")

    products = data.get("products", [])
    if not isinstance(products, list) or not products:
        add_error(errors, "/products returned no products")
        products = []

    print(f"Found {len(products)} products")

    for product in products:
        validate_product_summary(product, errors)

    details = data.get("details", {})
    offer_routes = data.get("offers", {})
    alternative_routes = data.get("alternatives", {})

    for barcode, product in details.items():
        validate_product_detail(
            barcode=barcode,
            product=product,
            offer_route=offer_routes.get(barcode, {}),
            alternative_route=alternative_routes.get(barcode, {}),
            products=products,
            errors=errors,
            warnings=warnings,
        )

    validate_quality_report(data.get("quality", {}), errors, warnings)
    validate_alternatives_quality(errors)
    validate_coverage_summary(errors)

    print("\n" + "=" * 80)
    print(f"Validation warnings: {len(warnings)}")
    print(f"Validation errors: {len(errors)}")

    if errors:
        sys.exit(1)

    print("PASS: Core SafeBite backend flows validated")


if __name__ == "__main__":
    main()
