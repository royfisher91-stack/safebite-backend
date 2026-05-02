import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.ingredient_engine import analyse_ingredients, ensure_ingredient_list
from services.scoring_service import UNKNOWN_RESULT, build_safety_decision


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


@lru_cache(maxsize=1)
def _load_rules(filename: str) -> List[Dict[str, Any]]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return list(raw.get("rules", []))


def _score_to_level(score: Optional[int]) -> str:
    if score is None:
        return "unknown"
    if score >= 80:
        return "low"
    if score >= 55:
        return "medium"
    return "high"


def _apply_rules(text: str, rules: List[Dict[str, Any]], starting_score: int) -> Dict[str, Any]:
    score = starting_score
    matched_reasons: List[str] = []
    matched_flags: List[str] = []

    lowered = text.lower()
    for rule in rules:
        pattern = str(rule.get("pattern") or "").strip().lower()
        if not pattern or pattern not in lowered:
            continue

        score += int(rule.get("score_delta", 0))
        reason = str(rule.get("reason") or "").strip()
        if reason and reason not in matched_reasons:
            matched_reasons.append(reason)
        for flag in rule.get("flags", []):
            flag_text = str(flag).strip()
            if flag_text and flag_text not in matched_flags:
                matched_flags.append(flag_text)

    score = max(0, min(100, score))
    return {
        "score": score,
        "reasons": matched_reasons,
        "flags": matched_flags,
    }


def _evaluate_processing(product: Dict[str, Any], ingredient_analysis: Dict[str, Any]) -> Dict[str, Any]:
    if not ingredient_analysis.get("items"):
        return {
            "score": None,
            "level": "unknown",
            "reason": "Insufficient verified data to assess processing level.",
            "flags": ["missing_processing_data_flag"],
        }

    text = " ".join(
        [
            _safe_text(product.get("name")),
            _safe_text(product.get("category")),
            _safe_text(product.get("subcategory")),
            _safe_text(product.get("description")),
            " ".join(item.get("normalized", "") for item in ingredient_analysis.get("items", [])),
        ]
    )

    applied = _apply_rules(text, _load_rules("processing_rules.json"), 72)
    score = applied["score"]
    reasons = list(applied["reasons"])
    flags = list(applied["flags"])

    subcategory = _safe_text(product.get("subcategory")).lower()
    item_count = len(ingredient_analysis.get("items", []))

    if subcategory == "fruit puree":
        if item_count <= 3:
            score += 12
            reasons.append("Very short puree ingredient list points to lighter processing.")
        elif item_count <= 5:
            score += 6
            reasons.append("Short puree ingredient list keeps processing impact moderate.")
    elif subcategory == "formula milk":
        score = min(score, 58)
        reasons.append("Formula milk is a specialist manufactured product and remains in caution territory.")
    elif subcategory == "toddler milk":
        score = min(score, 62)
        reasons.append("Toddler milk is still a processed nutrition product rather than a simple whole food.")
    elif subcategory in {"baby crisps & puffs", "oat snacks"}:
        score -= 8
        reasons.append("Snack-format baby food is more processed than simple puree or cereal bases.")
    elif subcategory == "baby meals" and item_count >= 8:
        score -= 6
        reasons.append("Longer baby-meal ingredient list increases processing complexity.")

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("No strong processing clue beyond the verified ingredient list.")

    return {
        "score": score,
        "level": _score_to_level(score),
        "reason": " ".join(reasons),
        "flags": sorted(set(flags)),
    }


def _evaluate_sugar(product: Dict[str, Any], ingredient_analysis: Dict[str, Any]) -> Dict[str, Any]:
    items = ingredient_analysis.get("items", [])
    if not items:
        return {
            "score": None,
            "level": "unknown",
            "reason": "Insufficient verified data to assess sugar impact.",
            "flags": ["missing_sugar_data_flag"],
        }

    text = " ".join(item.get("normalized", "") for item in items)
    applied = _apply_rules(text, _load_rules("sugar_rules.json"), 72)
    score = applied["score"]
    reasons = list(applied["reasons"])
    flags = list(applied["flags"])

    simple_categories = {item.get("category") for item in items}
    subcategory = _safe_text(product.get("subcategory")).lower()
    has_concentrated_sugar = any(
        "concentrate" in item.get("normalized", "") or item.get("category") in {"sugar", "sweetener"}
        for item in items
    )

    if not reasons:
        if simple_categories.issubset({"fruit", "vegetable"}) and len(items) <= 4:
            score += 12
            reasons.append("Simple fruit/vegetable recipe with no explicit added sugar signal.")
        else:
            reasons.append("No strong added-sugar signal detected from the verified ingredient list.")

    if subcategory in {"oat snacks", "baby crisps & puffs"} and has_concentrated_sugar:
        score -= 8
        reasons.append("Snack format plus concentrated sugars makes the sugar profile less favourable.")
    elif subcategory == "fruit puree" and not has_concentrated_sugar and len(items) <= 4:
        score += 6
        reasons.append("Puree-style fruit recipe stays on the simpler end of sweetness impact.")

    score = max(0, min(100, score))
    return {
        "score": score,
        "level": _score_to_level(score),
        "reason": " ".join(reasons),
        "flags": sorted(set(flags)),
    }


def _build_allergen_warnings(allergen_hits: List[str]) -> List[str]:
    warnings = []
    for allergen in allergen_hits:
        label = str(allergen).strip()
        if not label:
            continue
        warnings.append(f"Contains {label.lower()}.")
    return warnings


def _build_confidence(unknown_flags: List[str], ingredient_analysis: Dict[str, Any]) -> Dict[str, Any]:
    known = int(ingredient_analysis.get("known_count") or 0)
    unknown = int(ingredient_analysis.get("unknown_count") or 0)
    completeness = max(0, min(100, 100 - (len(unknown_flags) * 12) - (unknown * 8) + (known * 2)))

    if completeness >= 80:
        band = "high"
    elif completeness >= 55:
        band = "medium"
    else:
        band = "low"

    return {
        "decision_confidence": band,
        "completeness_score": completeness,
    }


def _build_reasoning_lines(
    ingredient_analysis: Dict[str, Any],
    processing_analysis: Dict[str, Any],
    sugar_analysis: Dict[str, Any],
    force_unknown: bool,
    unknown_flags: List[str],
) -> List[str]:
    lines = []
    summary = _safe_text(ingredient_analysis.get("summary"))
    if summary:
        lines.append(summary)

    processing_reason = _safe_text(processing_analysis.get("reason"))
    if processing_reason:
        lines.append(f"Processing: {processing_reason}")

    sugar_reason = _safe_text(sugar_analysis.get("reason"))
    if sugar_reason:
        lines.append(f"Sugar: {sugar_reason}")

    if force_unknown or unknown_flags:
        lines.append("Unknown handling: insufficient verified data for at least one core decision input.")

    return lines


def build_decision(product: Dict[str, Any]) -> Dict[str, Any]:
    product = dict(product or {})
    ingredients = ensure_ingredient_list(product.get("ingredients"))
    allergens = _safe_list(product.get("allergens"))

    ingredient_analysis = analyse_ingredients(ingredients, allergens)
    processing_analysis = _evaluate_processing(product, ingredient_analysis)
    sugar_analysis = _evaluate_sugar(product, ingredient_analysis)

    unknown_flags = set(ingredient_analysis.get("flags", []))
    unknown_flags.update(processing_analysis.get("flags", []))
    unknown_flags.update(sugar_analysis.get("flags", []))

    if not _safe_text(product.get("category")):
        unknown_flags.add("missing_category_flag")
    if not _safe_text(product.get("subcategory")):
        unknown_flags.add("missing_subcategory_flag")

    known_count = int(ingredient_analysis.get("known_count") or 0)
    unknown_count = int(ingredient_analysis.get("unknown_count") or 0)
    force_unknown = False
    if not ingredients:
        force_unknown = True
    elif known_count == 0 and unknown_count > 0:
        force_unknown = True
    elif unknown_count > known_count and known_count < 2:
        force_unknown = True
    elif "missing_category_flag" in unknown_flags or "missing_subcategory_flag" in unknown_flags:
        force_unknown = True

    component_scores = {
        "ingredient": ingredient_analysis.get("score"),
        "processing": processing_analysis.get("score"),
        "sugar": sugar_analysis.get("score"),
    }

    decision = build_safety_decision(
        component_scores,
        category=_safe_text(product.get("category")),
        subcategory=_safe_text(product.get("subcategory")),
        name=_safe_text(product.get("name")),
        force_unknown=force_unknown,
        unknown_flags=sorted(unknown_flags),
    )

    reasoning_lines = _build_reasoning_lines(
        ingredient_analysis=ingredient_analysis,
        processing_analysis=processing_analysis,
        sugar_analysis=sugar_analysis,
        force_unknown=force_unknown,
        unknown_flags=sorted(unknown_flags),
    )

    allergen_hits = sorted(set(ingredient_analysis.get("allergen_hits", [])) | set(allergens))
    allergen_warnings = _build_allergen_warnings(allergen_hits)
    confidence = _build_confidence(sorted(unknown_flags), ingredient_analysis)

    if decision.get("safety_result") == UNKNOWN_RESULT:
        reasoning_lines.append("Insufficient verified data to calculate a reliable decision.")

    reasoning_text = " | ".join(line for line in reasoning_lines if line)

    return {
        "score": decision.get("safety_score"),
        "safety_score": decision.get("safety_score"),
        "result": decision.get("safety_result"),
        "safety_result": decision.get("safety_result"),
        "ingredient_reasoning": reasoning_text,
        "reasoning": reasoning_lines,
        "allergen_warnings": allergen_warnings,
        "ingredients": ingredients,
        "allergens": allergen_hits,
        "ingredient_analysis": ingredient_analysis,
        "processing_analysis": processing_analysis,
        "sugar_analysis": sugar_analysis,
        "component_scores": component_scores,
        "unknown_flags": sorted(unknown_flags),
        "confidence": confidence,
        "personal_warnings": [],
    }
