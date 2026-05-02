import re
from typing import Any, Dict, List, Optional

from database import get_all_products, get_offers_by_barcode
from services.analysis_service import analyse_product
from services.pricing_service import build_pricing_summary


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item).strip().lower() for item in value if str(item).strip())
    return str(value).strip().lower()


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _same_barcode(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return str(a.get("barcode") or "").strip() == str(b.get("barcode") or "").strip()


def _extract_profile(product: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(
        [
            _clean_text(product.get("name")),
            _clean_text(product.get("category")),
            _clean_text(product.get("subcategory")),
        ]
    )

    stage = None
    if any(token in text for token in ["stage 1", "first infant", "from birth"]):
        stage = "1"
    elif any(token in text for token in ["stage 2", "follow on", "6-12 months", "6+ months"]):
        stage = "2"
    elif any(token in text for token in ["stage 3", "1+ years", "toddler milk"]):
        stage = "3"

    use_case_tokens = set()
    for token in ["goat", "comfort", "organic", "porridge", "puree", "meal", "puffs", "bars", "yoghurt", "yogurt"]:
        if token in text:
            use_case_tokens.add(token)

    age_match = re.findall(r"\b(?:from birth|\d+\+? months|1\+ years)\b", text)

    return {
        "stage": stage,
        "use_case_tokens": use_case_tokens,
        "age_tokens": set(age_match),
        "text": text,
    }


def _with_analysis_and_pricing(product: Dict[str, Any]) -> Dict[str, Any]:
    shaped = dict(product)
    barcode = str(shaped.get("barcode") or "").strip()
    offers = get_offers_by_barcode(barcode) if barcode else []
    pricing = build_pricing_summary(offers)
    analysis = analyse_product(shaped)

    shaped["offers"] = offers
    shaped["pricing"] = pricing
    shaped["analysis"] = analysis
    shaped["best_price"] = pricing.get("best_price")
    shaped["lowest_in_stock_price"] = pricing.get("lowest_in_stock_price")
    shaped["cheapest_retailer"] = pricing.get("cheapest_retailer")
    shaped["stock_status"] = pricing.get("stock_status")
    shaped["product_url"] = pricing.get("product_url")
    shaped["safety_score"] = analysis.get("safety_score")
    shaped["safety_result"] = analysis.get("safety_result")
    shaped["ingredient_reasoning"] = analysis.get("ingredient_reasoning")
    shaped["allergen_warnings"] = analysis.get("allergen_warnings")
    shaped["unknown_flags"] = analysis.get("unknown_flags", [])
    return shaped


def _match_strength(product: Dict[str, Any], candidate: Dict[str, Any]) -> int:
    score = 0
    product_category = _clean_text(product.get("category"))
    product_subcategory = _clean_text(product.get("subcategory"))
    candidate_category = _clean_text(candidate.get("category"))
    candidate_subcategory = _clean_text(candidate.get("subcategory"))

    if product_subcategory and candidate_subcategory and product_subcategory == candidate_subcategory:
        score += 140
    elif product_category and candidate_category and product_category == candidate_category:
        score += 60
    else:
        return 0

    product_profile = _extract_profile(product)
    candidate_profile = _extract_profile(candidate)

    if product_profile["stage"] and candidate_profile["stage"]:
        if product_profile["stage"] == candidate_profile["stage"]:
            score += 28
        else:
            score -= 30

    shared_use_case = product_profile["use_case_tokens"].intersection(candidate_profile["use_case_tokens"])
    score += len(shared_use_case) * 12

    if product_profile["age_tokens"] and candidate_profile["age_tokens"]:
        score += len(product_profile["age_tokens"].intersection(candidate_profile["age_tokens"])) * 8

    if _clean_text(product.get("brand")) and _clean_text(product.get("brand")) == _clean_text(candidate.get("brand")):
        score += 6

    return score


def _completeness_score(candidate: Dict[str, Any]) -> int:
    score = 40
    if candidate.get("best_price") is None:
        score -= 12
    if candidate.get("pricing", {}).get("best_in_stock_offer") is None:
        score -= 6
    if candidate.get("safety_result") == "Unknown" or candidate.get("safety_score") is None:
        score -= 12
    score -= min(len(candidate.get("unknown_flags") or []), 4) * 3
    return max(0, score)


def _candidate_price(candidate: Dict[str, Any]) -> Optional[float]:
    pricing = candidate.get("pricing", {}) or {}
    price = _safe_float(pricing.get("lowest_in_stock_price"))
    if price is not None:
        return price
    return _safe_float(pricing.get("best_price"))


def _shape_candidate(candidate: Dict[str, Any], reason: str) -> Dict[str, Any]:
    pricing = candidate.get("pricing", {}) or {}
    return {
        "barcode": candidate.get("barcode"),
        "name": candidate.get("name"),
        "brand": candidate.get("brand"),
        "category": candidate.get("category", ""),
        "subcategory": candidate.get("subcategory", ""),
        "safety_score": candidate.get("safety_score"),
        "safety_result": candidate.get("safety_result"),
        "ingredient_reasoning": candidate.get("ingredient_reasoning"),
        "allergen_warnings": candidate.get("allergen_warnings"),
        "best_price": pricing.get("best_price"),
        "lowest_in_stock_price": pricing.get("lowest_in_stock_price"),
        "cheapest_retailer": pricing.get("cheapest_retailer"),
        "stock_status": pricing.get("stock_status"),
        "product_url": pricing.get("product_url"),
        "reason": reason,
        "confidence": candidate.get("analysis", {}).get("confidence", {}),
    }


def _collect_candidates(product: Dict[str, Any]) -> List[Dict[str, Any]]:
    priced_product = _with_analysis_and_pricing(product)
    current_price = _candidate_price(priced_product)
    current_score = _safe_int(priced_product.get("safety_score"))

    candidates = []
    for raw_candidate in get_all_products():
        if _same_barcode(priced_product, raw_candidate):
            continue

        candidate = _with_analysis_and_pricing(raw_candidate)
        match_strength = _match_strength(priced_product, candidate)
        if match_strength <= 0:
            continue

        candidate_price = _candidate_price(candidate)
        candidate_score = _safe_int(candidate.get("safety_score"))
        completeness = _completeness_score(candidate)

        if candidate_price is None:
            continue
        if candidate_score is None:
            continue

        candidates.append(
            {
                "product": candidate,
                "match_strength": match_strength,
                "candidate_price": candidate_price,
                "candidate_score": candidate_score,
                "current_price": current_price,
                "current_score": current_score,
                "price_saving": (current_price - candidate_price) if current_price is not None else None,
                "score_gain": (candidate_score - current_score) if current_score is not None else None,
                "completeness": completeness,
                "in_stock": pricing_in_stock(candidate),
            }
        )

    return candidates


def pricing_in_stock(candidate: Dict[str, Any]) -> bool:
    pricing = candidate.get("pricing", {}) or {}
    return pricing.get("best_in_stock_offer") is not None


def _is_same_subcategory(product: Dict[str, Any], candidate: Dict[str, Any]) -> bool:
    return (
        _clean_text(product.get("category"))
        and _clean_text(product.get("category")) == _clean_text(candidate.get("category"))
        and _clean_text(product.get("subcategory"))
        and _clean_text(product.get("subcategory")) == _clean_text(candidate.get("subcategory"))
    )


def _find_safer_option(product: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    current_score = _safe_int(product.get("safety_score"))
    if current_score is None:
        return None

    eligible = [
        item for item in candidates if item.get("candidate_score") is not None and item["candidate_score"] > current_score
    ]
    if not eligible:
        return None

    same_subcategory = [item for item in eligible if _is_same_subcategory(product, item["product"])]
    ranked_pool = same_subcategory if same_subcategory else []

    ranked = sorted(
        ranked_pool,
        key=lambda item: (
            -(item.get("score_gain") or 0),
            -item["match_strength"],
            -item["completeness"],
            -(1 if item["in_stock"] else 0),
            item["candidate_price"],
            str(item["product"].get("name") or "").lower(),
        ),
    )

    if not ranked:
        return None

    best = ranked[0]["product"]
    return _shape_candidate(best, "Higher safety score within the same subcategory.")


def _find_cheaper_option(product: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    current_price = _candidate_price(product)
    if current_price is None:
        return None

    eligible = [
        item for item in candidates if item.get("candidate_price") is not None and item["candidate_price"] < current_price
    ]
    if not eligible:
        return None

    same_subcategory = [item for item in eligible if _is_same_subcategory(product, item["product"])]
    ranked_pool = same_subcategory if same_subcategory else []

    ranked = sorted(
        ranked_pool,
        key=lambda item: (
            item["candidate_price"],
            -(1 if item["in_stock"] else 0),
            -item["match_strength"],
            -item["completeness"],
            -(item.get("candidate_score") or 0),
            str(item["product"].get("name") or "").lower(),
        ),
    )

    if not ranked:
        return None

    best = ranked[0]["product"]
    return _shape_candidate(best, "Lower tracked price within the same subcategory.")


def _find_same_category_option(product: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    same_subcategory = [item for item in candidates if _is_same_subcategory(product, item["product"])]
    ranked_pool = same_subcategory if same_subcategory else candidates

    ranked = sorted(
        ranked_pool,
        key=lambda item: (
            -item["match_strength"],
            -(1 if item["in_stock"] else 0),
            -item["completeness"],
            -(item.get("candidate_score") or 0),
            item["candidate_price"],
            str(item["product"].get("name") or "").lower(),
        ),
    )

    if not ranked:
        return None

    best = ranked[0]["product"]
    reason = "Best same-subcategory match after ranking safety, stock and price quality." if same_subcategory else "Best same-category match after ranking safety, stock and price quality."
    return _shape_candidate(best, reason)


def build_alternatives(product: Dict[str, Any]) -> Dict[str, Any]:
    if not product:
        return {
            "safer_option": None,
            "cheaper_option": None,
            "same_category_option": None,
        }

    current = _with_analysis_and_pricing(product)
    candidates = _collect_candidates(current)

    return {
        "safer_option": _find_safer_option(current, candidates),
        "cheaper_option": _find_cheaper_option(current, candidates),
        "same_category_option": _find_same_category_option(current, candidates),
    }
