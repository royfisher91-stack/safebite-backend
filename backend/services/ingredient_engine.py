import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ALLERGEN_KEYWORDS = {
    "milk": "Milk",
    "whey": "Milk",
    "lactose": "Milk",
    "casein": "Milk",
    "gluten": "Gluten",
    "wheat": "Gluten",
    "barley": "Gluten",
    "rye": "Gluten",
    "oats": "Oats",
    "egg": "Egg",
    "soya": "Soya",
    "soy": "Soya",
    "nut": "Nuts",
    "almond": "Nuts",
    "hazelnut": "Nuts",
    "peanut": "Peanuts",
    "sesame": "Sesame",
    "fish": "Fish",
}

FALLBACK_CATEGORY_PATTERNS = [
    ("sugar", ["sugar", "syrup", "juice concentrate", "nectar", "honey", "molasses"]),
    ("flavouring", ["flavouring", "flavoring", "flavour", "flavor"]),
    ("preservative", ["preservative"]),
    ("stabiliser", ["stabiliser", "stabilizer", "emulsifier", "thickener"]),
    ("oil/fat", ["oil", "butter", "cream"]),
    ("milk/dairy", ["milk", "whey", "lactose", "casein", "fromage frais", "cheese", "mozzarella"]),
    ("sweetener", ["sucralose", "aspartame", "acesulfame", "sweetener"]),
    ("cereal/grain", ["oat", "corn", "maize", "rice", "wheat", "barley", "grain", "pasta"]),
    ("fruit", ["apple", "banana", "pear", "peach", "mango", "strawberry", "raspberry", "fruit"]),
    ("vegetable", ["carrot", "parsnip", "pea", "broccoli", "vegetable", "tomato", "sweet potato", "lentil", "onion"]),
    ("protein", ["chicken", "beef", "lamb", "fish"]),
    ("vitamin/mineral", ["vitamin", "mineral", "thiamin", "iron", "calcium", "dha", "ara"]),
    ("fibre/prebiotic", ["inulin", "fibre", "fiber", "oligosaccharide", "f.o.s", "g.o.s"]),
    ("spice", ["spice", "curry", "pepper", "chilli", "garlic"]),
    ("herb", ["herb", "parsley", "basil", "thyme", "marjoram", "rosemary"]),
]


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


@lru_cache(maxsize=1)
def load_alias_map() -> Dict[str, str]:
    path = DATA_DIR / "ingredient_aliases.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(key).lower(): str(value).lower() for key, value in raw.get("aliases", {}).items()}


@lru_cache(maxsize=1)
def load_rules() -> List[Dict[str, Any]]:
    path = DATA_DIR / "ingredient_rules.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return list(raw.get("rules", []))


def ensure_ingredient_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    pieces = re.split(r"[,;]", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def normalise_ingredient_name(raw_value: Any) -> str:
    text = str(raw_value or "").strip().lower()
    if not text:
        return ""

    text = text.replace("’", "'")
    text = re.sub(r"<\s*0\.1%", "", text)
    text = re.sub(r"\d+(?:\.\d+)?%", "", text)
    text = text.replace("(", " ").replace(")", " ")
    text = re.sub(r"[^a-z0-9+'\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.-")

    aliases = load_alias_map()
    return aliases.get(text, text)


def _match_rule(normalized: str) -> Optional[Dict[str, Any]]:
    if not normalized:
        return None

    for rule in load_rules():
        pattern = str(rule.get("pattern") or "").strip().lower()
        if not pattern:
            continue

        match_type = str(rule.get("match_type") or "contains").strip().lower()
        if match_type == "exact" and normalized == pattern:
            return rule
        if match_type != "exact" and pattern in normalized:
            return rule

    return None


def _detect_allergens(normalized: str, declared_allergens: List[str]) -> List[str]:
    hits = []

    declared = [str(item).strip() for item in declared_allergens if str(item).strip()]
    for allergen in declared:
        allergen_text = allergen.lower()
        if allergen_text and allergen_text in normalized:
            hits.append(allergen)

    for keyword, label in ALLERGEN_KEYWORDS.items():
        if keyword in normalized and label not in hits:
            hits.append(label)

    return sorted(set(hits))


def _fallback_item(normalized: str) -> Dict[str, Any]:
    category = "other"
    risk_level = "unknown"
    score_delta = 0
    reason = "Ingredient is not yet mapped to a more specific rule."
    flags: List[str] = []

    for detected_category, patterns in FALLBACK_CATEGORY_PATTERNS:
        if any(pattern in normalized for pattern in patterns):
            category = detected_category
            break

    if category in {"fruit", "vegetable"}:
        risk_level = "low"
        score_delta = 5
        reason = "Whole-food fruit or vegetable ingredient."
    elif category == "cereal/grain":
        risk_level = "low"
        score_delta = 3
        reason = "Cereal or grain ingredient with a straightforward food role."
    elif category == "protein":
        risk_level = "low"
        score_delta = 2
        reason = "Protein ingredient with a clear whole-food origin."
    elif category == "milk/dairy":
        risk_level = "medium"
        score_delta = -3
        reason = "Dairy ingredient that is nutritionally common but allergen-relevant."
    elif category in {"sugar", "sweetener"}:
        risk_level = "high"
        score_delta = -14
        reason = "Ingredient contributes directly to sugar or sweetness impact."
        flags.append("added_sugar_flag")
    elif category == "oil/fat":
        risk_level = "low"
        score_delta = -1
        reason = "Added fat or oil ingredient."
    elif category in {"flavouring", "spice", "herb"}:
        risk_level = "unknown"
        score_delta = 0
        reason = "Generic flavouring or seasoning term without a full breakdown."
        flags.append("unknown_ingredient_flag")
    elif category in {"preservative", "stabiliser"}:
        risk_level = "medium"
        score_delta = -8
        reason = "Additive-style ingredient that increases processing intensity."
    elif category == "vitamin/mineral":
        risk_level = "low"
        score_delta = 0
        reason = "Vitamin or mineral fortification ingredient."
    elif category == "fibre/prebiotic":
        risk_level = "low"
        score_delta = 1
        reason = "Fibre or prebiotic ingredient."
    else:
        flags.append("unknown_ingredient_flag")

    return {
        "category": category,
        "risk_level": risk_level,
        "score_delta": score_delta,
        "reason": reason,
        "flags": flags,
    }


def analyse_single_ingredient(raw_value: Any, declared_allergens: Optional[List[str]] = None) -> Dict[str, Any]:
    raw_text = str(raw_value or "").strip()
    normalized = normalise_ingredient_name(raw_text)
    declared_allergens = declared_allergens or []

    if not normalized:
        return {
            "ingredient": raw_text,
            "normalized": "",
            "category": "other",
            "risk_level": "unknown",
            "reason": "Ingredient value is blank or unavailable.",
            "flags": ["unknown_ingredient_flag"],
            "score_delta": 0,
            "matched_allergens": [],
        }

    rule = _match_rule(normalized)
    if rule:
        category = str(rule.get("category") or "other")
        risk_level = str(rule.get("risk_level") or "unknown")
        reason = str(rule.get("reason") or "Ingredient matched a configured rule.")
        flags = [str(flag) for flag in rule.get("flags", []) if str(flag).strip()]
        score_delta = int(rule.get("score_delta", 0))
    else:
        fallback = _fallback_item(normalized)
        category = fallback["category"]
        risk_level = fallback["risk_level"]
        reason = fallback["reason"]
        flags = list(fallback["flags"])
        score_delta = int(fallback["score_delta"])

    matched_allergens = _detect_allergens(normalized, declared_allergens)
    if matched_allergens and "allergen_flag" not in flags:
        flags.append("allergen_flag")
        if risk_level == "low":
            risk_level = "medium"

    return {
        "ingredient": raw_text,
        "normalized": normalized,
        "category": category,
        "risk_level": risk_level,
        "reason": reason,
        "flags": sorted(set(flags)),
        "score_delta": score_delta,
        "matched_allergens": matched_allergens,
    }


def analyse_ingredients(
    ingredients: Any,
    allergens: Optional[List[str]] = None,
) -> Dict[str, Any]:
    ingredient_list = ensure_ingredient_list(ingredients)
    declared_allergens = allergens or []

    if not ingredient_list:
        return {
            "items": [],
            "score": None,
            "known_count": 0,
            "unknown_count": 0,
            "allergen_hits": [],
            "flags": ["missing_ingredients_flag"],
            "summary": "No verified ingredient list is available.",
        }

    items = [analyse_single_ingredient(item, declared_allergens) for item in ingredient_list]
    known_items = [item for item in items if item.get("risk_level") != "unknown"]
    unknown_items = [item for item in items if item.get("risk_level") == "unknown"]

    score_delta = sum(int(item.get("score_delta", 0)) for item in items)
    score = _clamp_score(75 + score_delta)

    flags = set()
    allergen_hits = set()
    for item in items:
        flags.update(item.get("flags", []))
        allergen_hits.update(item.get("matched_allergens", []))

    summary_parts = []
    high_risk = [item for item in items if item.get("risk_level") == "high"]
    medium_risk = [item for item in items if item.get("risk_level") == "medium"]

    if high_risk:
        summary_parts.append(
            "High-risk ingredients include {0}.".format(
                ", ".join(sorted({item["ingredient"] for item in high_risk}))
            )
        )
    elif medium_risk:
        summary_parts.append(
            "Moderate-risk ingredients include {0}.".format(
                ", ".join(sorted({item["ingredient"] for item in medium_risk[:3]}))
            )
        )
    else:
        summary_parts.append("Ingredient list is mostly whole-food or straightforward ingredient-led.")

    if unknown_items:
        summary_parts.append(
            "Unknown-detail ingredients include {0}.".format(
                ", ".join(sorted({item["ingredient"] for item in unknown_items[:3]}))
            )
        )

    return {
        "items": items,
        "score": score,
        "known_count": len(known_items),
        "unknown_count": len(unknown_items),
        "allergen_hits": sorted(allergen_hits),
        "flags": sorted(flags),
        "summary": " ".join(summary_parts),
    }
