from typing import Dict, Optional


SAFE_RESULT = "Safe"
CAUTION_RESULT = "Caution"
AVOID_RESULT = "Avoid"
UNKNOWN_RESULT = "Unknown"


DEFAULT_WEIGHTS = {
    "ingredient": 0.60,
    "processing": 0.25,
    "sugar": 0.15,
}

PRODUCT_SCORE_CAPS = {
    "formula milk": 68,
    "toddler milk": 72,
}


def clamp_score(score: float) -> int:
    return max(0, min(100, int(round(score))))


def map_score_to_result(score: Optional[int]) -> str:
    if score is None:
        return UNKNOWN_RESULT
    if score >= 80:
        return SAFE_RESULT
    if score >= 50:
        return CAUTION_RESULT
    return AVOID_RESULT


def calculate_weighted_score(
    component_scores: Dict[str, Optional[int]],
    weights: Optional[Dict[str, float]] = None,
) -> Optional[int]:
    weights = weights or DEFAULT_WEIGHTS
    known = {
        key: value
        for key, value in component_scores.items()
        if value is not None and key in weights
    }

    if not known or "ingredient" not in known:
        return None

    total_weight = sum(weights[key] for key in known)
    if total_weight <= 0:
        return None

    weighted_total = sum(float(known[key]) * weights[key] for key in known)
    return clamp_score(weighted_total / total_weight)


def apply_product_caps(
    score: int,
    category: str = "",
    subcategory: str = "",
    name: str = "",
) -> int:
    lowered_subcategory = str(subcategory or "").strip().lower()
    lowered_name = str(name or "").strip().lower()
    lowered_category = str(category or "").strip().lower()

    capped = score

    if lowered_subcategory in PRODUCT_SCORE_CAPS:
        capped = min(capped, PRODUCT_SCORE_CAPS[lowered_subcategory])
    elif lowered_category in PRODUCT_SCORE_CAPS:
        capped = min(capped, PRODUCT_SCORE_CAPS[lowered_category])

    if "comfort milk" in lowered_name:
        capped = min(capped, 63)
    if "goat first infant milk" in lowered_name:
        capped = min(capped, 66)
    if "follow on milk" in lowered_name and "formula milk" in lowered_subcategory:
        capped = min(capped, 66)

    return clamp_score(capped)


def build_safety_decision(
    component_scores: Dict[str, Optional[int]],
    category: str = "",
    subcategory: str = "",
    name: str = "",
    force_unknown: bool = False,
    unknown_flags: Optional[list[str]] = None,
) -> Dict[str, Optional[object]]:
    flags = list(unknown_flags or [])

    if force_unknown:
        return {
            "safety_score": None,
            "safety_result": UNKNOWN_RESULT,
            "unknown_flags": flags,
        }

    weighted_score = calculate_weighted_score(component_scores)
    if weighted_score is None:
        return {
            "safety_score": None,
            "safety_result": UNKNOWN_RESULT,
            "unknown_flags": flags,
        }

    final_score = apply_product_caps(
        weighted_score,
        category=category,
        subcategory=subcategory,
        name=name,
    )
    return {
        "safety_score": final_score,
        "safety_result": map_score_to_result(final_score),
        "unknown_flags": flags,
    }
