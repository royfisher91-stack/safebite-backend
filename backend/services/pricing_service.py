from typing import Any, Dict, List, Optional

from domains.food.services.food_pricing import (
    build_food_pricing_summary,
    normalise_food_offer,
)
from services.offer_pricing_service import build_offer_pricing_snapshot, safe_float


def get_effective_price(offer: Dict[str, Any]) -> Optional[float]:
    snapshot = build_offer_pricing_snapshot(offer)
    return snapshot.get("single_unit_price")


def is_offer_in_stock(offer: Dict[str, Any]) -> bool:
    in_stock_value = offer.get("in_stock")
    if in_stock_value is True or in_stock_value == 1:
        return True

    if isinstance(in_stock_value, str):
        text = in_stock_value.strip().lower()
        if text in {"1", "true", "yes", "y", "in_stock", "in stock", "available", "limited", "low stock"}:
            return True

    stock_status = str(offer.get("stock_status") or "").strip().lower()
    return stock_status in {"in_stock", "in stock", "available", "limited", "low stock"}


def get_stock_status(offer: Optional[Dict[str, Any]]) -> str:
    if not offer:
        return "unknown"

    stock_status = str(offer.get("stock_status") or "").strip()
    if stock_status:
        return stock_status
    return "in_stock" if is_offer_in_stock(offer) else "out_of_stock"


def normalise_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    return normalise_food_offer(offer)


def get_valid_offers(offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [normalise_offer(offer) for offer in offers if get_effective_price(offer) is not None]


def _sort_key(offer: Dict[str, Any], key: str = "effective_price") -> tuple:
    return (
        offer.get(key) if offer.get(key) is not None else 999999,
        str(offer.get("retailer") or "").lower(),
    )


def _pick_lowest(offers: List[Dict[str, Any]], key: str = "effective_price") -> Optional[Dict[str, Any]]:
    if not offers:
        return None
    return min(offers, key=lambda item: _sort_key(item, key=key))


def _shape_offer_preview(offer: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not offer:
        return None
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


def build_pricing_summary(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    return build_food_pricing_summary(offers)
