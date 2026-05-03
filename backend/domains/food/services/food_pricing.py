from typing import Any, Dict, List

from core.pricing_engine import run_pricing_pipeline
from services.image_rights_service import normalise_image_metadata, public_image_url
from services.offer_pricing_service import build_offer_pricing_snapshot, safe_float


MODULE_CODE = "safebite_food"


def _is_offer_in_stock(offer: Dict[str, Any]) -> bool:
    in_stock_value = offer.get("in_stock")
    if in_stock_value is True or in_stock_value == 1:
        return True

    if isinstance(in_stock_value, str):
        text = in_stock_value.strip().lower()
        if text in {"1", "true", "yes", "y", "in_stock", "in stock", "available", "limited", "low stock"}:
            return True

    stock_status = str(offer.get("stock_status") or "").strip().lower()
    return stock_status in {"in_stock", "in stock", "available", "limited", "low stock"}


def _get_stock_status(offer: Dict[str, Any]) -> str:
    stock_status = str(offer.get("stock_status") or "").strip()
    if stock_status:
        return stock_status
    return "in_stock" if _is_offer_in_stock(offer) else "out_of_stock"


def normalise_food_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(offer)
    snapshot = build_offer_pricing_snapshot(offer)
    image_metadata = normalise_image_metadata(cleaned)
    cleaned.update(snapshot)
    cleaned["effective_price"] = snapshot.get("single_unit_price")
    cleaned["is_valid_price"] = cleaned["effective_price"] is not None
    cleaned["is_available"] = _is_offer_in_stock(offer)
    cleaned["stock_status"] = _get_stock_status(offer)
    cleaned["image_url"] = public_image_url(
        cleaned.get("image_url"),
        image_metadata["image_source_type"],
        image_metadata["image_rights_status"],
    )
    cleaned.update(image_metadata)
    return cleaned


def _shape_offer_preview(offer: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "retailer": offer.get("retailer"),
        "price": safe_float(offer.get("price")),
        "promo_price": safe_float(offer.get("promo_price")),
        "effective_price": offer.get("effective_price"),
        "standard_unit_price": offer.get("standard_unit_price"),
        "promo_unit_price": offer.get("promo_unit_price"),
        "multi_buy_effective_price": offer.get("multi_buy_effective_price"),
        "best_unit_price": offer.get("best_unit_price"),
        "promotion_type": offer.get("promotion_type"),
        "promotion_label": offer.get("promotion_label"),
        "buy_quantity": offer.get("buy_quantity"),
        "pay_quantity": offer.get("pay_quantity"),
        "bundle_price": offer.get("bundle_price"),
        "better_value_when_buying": bool(offer.get("better_value_when_buying")),
        "promotion_summary": offer.get("promotion_summary"),
        "stock_status": offer.get("stock_status"),
        "in_stock": bool(offer.get("is_available")),
        "product_url": offer.get("product_url"),
    }


def _pick_lowest(offers: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    return min(
        offers,
        key=lambda item: (
            item.get(key) if item.get(key) is not None else 999999,
            str(item.get("retailer") or "").lower(),
        ),
    )


def _build_food_pricing_summary(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid_offers = [
        normalise_food_offer(offer)
        for offer in offers
        if build_offer_pricing_snapshot(offer).get("single_unit_price") is not None
    ]
    in_stock_offers = [offer for offer in valid_offers if offer.get("is_available")]

    lowest_offer = _pick_lowest(valid_offers, "effective_price") if valid_offers else None
    lowest_in_stock_offer = _pick_lowest(in_stock_offers, "effective_price") if in_stock_offers else None
    best_available_offer = lowest_in_stock_offer or lowest_offer

    value_candidates = [offer for offer in valid_offers if offer.get("best_unit_price") is not None]
    in_stock_value_candidates = [offer for offer in value_candidates if offer.get("is_available")]
    best_value_offer = (
        _pick_lowest(in_stock_value_candidates or value_candidates, "best_unit_price")
        if value_candidates
        else None
    )

    unknown_flags = []
    if not valid_offers:
        unknown_flags.append("missing_valid_offer_flag")
    if valid_offers and not in_stock_offers:
        unknown_flags.append("no_in_stock_offer_flag")
    if any(offer.get("stock_status") == "unknown" for offer in valid_offers):
        unknown_flags.append("unknown_stock_status_flag")

    best_price = best_available_offer.get("effective_price") if best_available_offer else None
    lowest_price = lowest_offer.get("effective_price") if lowest_offer else None
    lowest_in_stock_price = lowest_in_stock_offer.get("effective_price") if lowest_in_stock_offer else None
    best_value_price = best_value_offer.get("best_unit_price") if best_value_offer else None

    standard_prices = [
        offer.get("standard_unit_price")
        for offer in valid_offers
        if offer.get("standard_unit_price") is not None
    ]
    promo_prices = [
        offer.get("promo_unit_price")
        for offer in valid_offers
        if offer.get("promo_unit_price") is not None
    ]

    if best_available_offer:
        pricing_text = "Best in-stock single price is {0} at £{1:.2f}.".format(
            best_available_offer.get("retailer") or "Unknown retailer",
            float(best_price or 0),
        )
    elif lowest_offer:
        pricing_text = "Only tracked single-unit price is £{0:.2f} at {1}, but stock confidence is limited.".format(
            float(lowest_price or 0),
            lowest_offer.get("retailer") or "Unknown retailer",
        )
    else:
        pricing_text = "No reliable pricing data is available yet."

    return {
        "best_price": best_price,
        "lowest_price": lowest_price,
        "lowest_in_stock_price": lowest_in_stock_price,
        "best_value_price": best_value_price,
        "lowest_standard_price": min(standard_prices) if standard_prices else None,
        "lowest_promo_price": min(promo_prices) if promo_prices else None,
        "cheapest_retailer": best_available_offer.get("retailer") if best_available_offer else None,
        "cheapest_overall_retailer": lowest_offer.get("retailer") if lowest_offer else None,
        "cheapest_in_stock_retailer": lowest_in_stock_offer.get("retailer") if lowest_in_stock_offer else None,
        "best_value_retailer": best_value_offer.get("retailer") if best_value_offer else None,
        "stock_status": _get_stock_status(best_available_offer or {}),
        "product_url": best_available_offer.get("product_url") if best_available_offer else None,
        "offer_count": len(offers),
        "valid_offer_count": len(valid_offers),
        "in_stock_offer_count": len(in_stock_offers),
        "out_of_stock_offer_count": max(len(valid_offers) - len(in_stock_offers), 0),
        "promo_offer_count": sum(1 for offer in valid_offers if offer.get("is_promo")),
        "multi_buy_offer_count": sum(1 for offer in valid_offers if offer.get("is_multi_buy")),
        "best_offer": _shape_offer_preview(best_available_offer) if best_available_offer else None,
        "best_in_stock_offer": _shape_offer_preview(lowest_in_stock_offer) if lowest_in_stock_offer else None,
        "best_value_offer": _shape_offer_preview(best_value_offer) if best_value_offer else None,
        "pricing_summary": pricing_text,
        "unknown_flags": sorted(set(unknown_flags)),
    }


def build_food_pricing_summary(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    return run_pricing_pipeline(MODULE_CODE, offers or [], _build_food_pricing_summary)
