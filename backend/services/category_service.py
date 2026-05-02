from typing import Dict, Optional, Tuple


# ORDER MATTERS — top rules = highest priority
CATEGORY_RULES = [
    # -----------------------------
    # BABY / TODDLER — HIGHEST PRIORITY
    # -----------------------------
    {
        "match": [
            "toddler milk",
            "growing up milk",
            "growing-up milk",
            "1-2 years milk",
            "1 to 2 years milk",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Toddler Milk",
    },
    {
        "match": [
            "toddler yoghurt",
            "toddler yogurt",
            "baby yoghurt",
            "baby yogurt",
            "little yoghurt",
            "little yogurt",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Toddler Yoghurt",
    },
    {
        "match": [
            "baby formula",
            "infant formula",
            "follow-on milk",
            "first infant milk",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Formula Milk",
    },
    {
        "match": [
            "porridge",
            "baby porridge",
            "baby cereal",
            "infant cereal",
            "weaning cereal",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Porridge",
    },
    {
        "match": [
            "fruit puree",
            "fruit purée",
            "smooth puree",
            "smooth purée",
            "apple & banana",
            "apple and banana",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Fruit Puree",
    },
    {
        "match": [
            "baby meal",
            "baby meals",
            "lentil baby meal",
            "sweet potato baby meal",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Baby Meals",
    },
    {
        "match": [
            "baby food",
            "baby jars",
            "baby pouch",
            "baby pouches",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Baby Food",
    },
    {
        "match": [
            "oat snack",
            "oat snacks",
            "oat bar",
            "oat bites",
        ],
        "category": "Baby Snacks",
        "subcategory": "Oat Snacks",
    },
    {
        "match": [
            "baby snack",
            "baby crisps",
            "baby puffs",
            "baby biscuits",
        ],
        "category": "Baby Snacks",
        "subcategory": "Baby Crisps & Puffs",
    },
    {
        "match": [
            "nappy",
            "nappies",
            "diaper",
            "diapers",
            "baby wipes",
            "wipes",
        ],
        "category": "Baby & Toddler",
        "subcategory": "Nappies & Wipes",
    },

    # -----------------------------
    # FOOD — GENERAL
    # -----------------------------
    {
        "match": [
            "snack",
            "crisps",
            "chocolate",
            "sweets",
            "biscuits",
            "cereal bar",
        ],
        "category": "Food Cupboard",
        "subcategory": "Snacks",
    },
    {
        "match": [
            "pasta",
            "rice",
            "noodles",
            "flour",
            "tinned",
            "canned",
            "soup",
            "beans",
        ],
        "category": "Food Cupboard",
        "subcategory": "Cupboard Food",
    },

    # -----------------------------
    # DRINKS
    # -----------------------------
    {
        "match": [
            "juice",
            "water",
            "cola",
            "drink",
            "drinks",
            "squash",
        ],
        "category": "Drinks",
        "subcategory": "Soft Drinks",
    },

    # -----------------------------
    # DAIRY — LOW PRIORITY (IMPORTANT)
    # -----------------------------
    {
        "match": [
            "cheese",
            "butter",
            "yoghurt",
            "yogurt",
            "cream",
        ],
        "category": "Fridge",
        "subcategory": "Dairy",
    },

    # -----------------------------
    # FROZEN
    # -----------------------------
    {
        "match": [
            "frozen",
            "ice cream",
            "frozen food",
        ],
        "category": "Frozen",
        "subcategory": "Frozen Food",
    },

    # -----------------------------
    # HOUSEHOLD
    # -----------------------------
    {
        "match": [
            "cleaning",
            "bleach",
            "detergent",
            "washing up",
            "laundry",
        ],
        "category": "Household",
        "subcategory": "Cleaning",
    },

    # -----------------------------
    # HEALTH & BEAUTY
    # -----------------------------
    {
        "match": [
            "toiletries",
            "shampoo",
            "conditioner",
            "soap",
            "toothpaste",
        ],
        "category": "Health & Beauty",
        "subcategory": "Toiletries",
    },
]


DEFAULT_CATEGORY = "Other"
DEFAULT_SUBCATEGORY = "General"


def _clean(text: Optional[str]) -> str:
    return (text or "").strip().lower()


def _title_case(text: str) -> str:
    return " ".join(word.capitalize() for word in text.strip().split())


def normalise_category(
    raw_category: Optional[str],
    raw_subcategory: Optional[str],
    product_name: Optional[str] = None,
) -> Tuple[str, str]:

    raw_category_clean = _clean(raw_category)
    raw_subcategory_clean = _clean(raw_subcategory)
    name_clean = _clean(product_name)

    combined = " | ".join(
        part for part in [raw_category_clean, raw_subcategory_clean, name_clean] if part
    )

    # -----------------------------
    # RULE MATCHING (ORDERED)
    # -----------------------------
    for rule in CATEGORY_RULES:
        if any(term in combined for term in rule["match"]):
            return rule["category"], rule["subcategory"]

    # -----------------------------
    # SAFE FALLBACKS
    # -----------------------------
    if raw_category_clean and raw_subcategory_clean:
        return _title_case(raw_category_clean), _title_case(raw_subcategory_clean)

    if raw_category_clean:
        return _title_case(raw_category_clean), DEFAULT_SUBCATEGORY

    if raw_subcategory_clean:
        return DEFAULT_CATEGORY, _title_case(raw_subcategory_clean)

    return DEFAULT_CATEGORY, DEFAULT_SUBCATEGORY


def build_category_payload(
    raw_category: Optional[str],
    raw_subcategory: Optional[str],
    product_name: Optional[str] = None,
) -> Dict[str, str]:

    category, subcategory = normalise_category(
        raw_category=raw_category,
        raw_subcategory=raw_subcategory,
        product_name=product_name,
    )

    return {
        "category": category,
        "subcategory": subcategory,
    }
