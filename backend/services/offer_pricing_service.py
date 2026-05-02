from typing import Any, Dict, Optional


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_optional_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def get_single_unit_price(offer: Dict[str, Any]) -> Optional[float]:
    promo_price = safe_float(offer.get("promo_price"))
    if promo_price is not None and promo_price >= 0:
        return round(promo_price, 2)

    price = safe_float(offer.get("price"))
    if price is not None and price >= 0:
        return round(price, 2)

    return None


def calculate_multi_buy_effective_price(offer: Dict[str, Any]) -> Optional[float]:
    bundle_price = safe_float(offer.get("bundle_price"))
    buy_quantity = safe_optional_int(offer.get("buy_quantity"))
    pay_quantity = safe_optional_int(offer.get("pay_quantity"))
    single_unit_price = get_single_unit_price(offer)

    if buy_quantity is None or buy_quantity <= 1:
        return None

    if bundle_price is not None and bundle_price > 0:
        return round(bundle_price / float(buy_quantity), 2)

    if (
        pay_quantity is not None
        and pay_quantity > 0
        and pay_quantity < buy_quantity
        and single_unit_price is not None
    ):
        return round((single_unit_price * float(pay_quantity)) / float(buy_quantity), 2)

    return None


def build_offer_pricing_snapshot(offer: Dict[str, Any]) -> Dict[str, Any]:
    standard_unit_price = safe_float(offer.get("price"))
    promo_unit_price = safe_float(offer.get("promo_price"))
    single_unit_price = get_single_unit_price(offer)
    multi_buy_effective_price = calculate_multi_buy_effective_price(offer)

    best_unit_price = single_unit_price
    better_value_when_buying = False
    if (
        multi_buy_effective_price is not None
        and single_unit_price is not None
        and multi_buy_effective_price < single_unit_price
    ):
        best_unit_price = multi_buy_effective_price
        better_value_when_buying = True

    bundle_price = safe_float(offer.get("bundle_price"))
    buy_quantity = safe_optional_int(offer.get("buy_quantity"))
    pay_quantity = safe_optional_int(offer.get("pay_quantity"))
    promotion_label = str(offer.get("promotion_label") or offer.get("promo_text") or "").strip()
    promotion_type = str(offer.get("promotion_type") or "").strip().lower()
    is_multi_buy = multi_buy_effective_price is not None
    is_promo = bool(
        promo_unit_price is not None
        or promotion_label
        or str(offer.get("promo_text") or "").strip()
    )

    discount_amount = None
    if (
        standard_unit_price is not None
        and single_unit_price is not None
        and standard_unit_price > single_unit_price
    ):
        discount_amount = round(standard_unit_price - single_unit_price, 2)

    multi_buy_saving = None
    if (
        single_unit_price is not None
        and multi_buy_effective_price is not None
        and single_unit_price > multi_buy_effective_price
    ):
        multi_buy_saving = round(single_unit_price - multi_buy_effective_price, 2)

    promotion_summary = ""
    if is_multi_buy and better_value_when_buying and buy_quantity:
        if bundle_price is not None:
            promotion_summary = (
                f"{buy_quantity} for £{bundle_price:.2f} works out to £{multi_buy_effective_price:.2f} each."
            )
        elif pay_quantity is not None:
            promotion_summary = (
                f"Buy {buy_quantity}, pay for {pay_quantity} works out to £{multi_buy_effective_price:.2f} each."
            )
    elif promo_unit_price is not None and standard_unit_price is not None and discount_amount is not None:
        promotion_summary = (
            f"Promo price lowers the unit price from £{standard_unit_price:.2f} to £{promo_unit_price:.2f}."
        )

    return {
        "standard_unit_price": round(standard_unit_price, 2) if standard_unit_price is not None else None,
        "promo_unit_price": round(promo_unit_price, 2) if promo_unit_price is not None else None,
        "single_unit_price": single_unit_price,
        "multi_buy_effective_price": multi_buy_effective_price,
        "best_unit_price": best_unit_price,
        "promotion_type": promotion_type,
        "promotion_label": promotion_label,
        "buy_quantity": buy_quantity,
        "pay_quantity": pay_quantity,
        "bundle_price": round(bundle_price, 2) if bundle_price is not None else None,
        "valid_from": offer.get("valid_from"),
        "valid_to": offer.get("valid_to"),
        "is_multi_buy": is_multi_buy,
        "is_promo": is_promo,
        "better_value_when_buying": better_value_when_buying,
        "discount_amount": discount_amount,
        "multi_buy_saving": multi_buy_saving,
        "promotion_summary": promotion_summary,
    }
