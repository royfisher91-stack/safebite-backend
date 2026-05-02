from typing import Dict, Set

CORE_SUBCATEGORY_TARGETS: Dict[str, Dict[str, int]] = {
    "Formula Milk": {"min": 25, "max": 40},
    "Fruit Puree": {"min": 25, "max": 40},
    "Porridge": {"min": 25, "max": 40},
    "Baby Meals": {"min": 25, "max": 40},
    "Baby Crisps & Puffs": {"min": 25, "max": 40},
    "Oat Snacks": {"min": 25, "max": 40},
}

ALLOWED_TAXONOMY: Dict[str, Set[str]] = {
    "Baby & Toddler": {
        "Baby Meals",
        "Formula Milk",
        "Fruit Puree",
        "Porridge",
        "Toddler Milk",
        "Toddler Yoghurt",
    },
    "Baby Snacks": {
        "Baby Crisps & Puffs",
        "Oat Snacks",
    },
}

CATEGORY_ALIASES = {
    "baby and toddler": "Baby & Toddler",
    "baby/toddler": "Baby & Toddler",
    "baby toddler": "Baby & Toddler",
    "baby snacks": "Baby Snacks",
    "snacks": "Baby Snacks",
}

SUBCATEGORY_ALIASES = {
    "baby meal": "Baby Meals",
    "baby meals": "Baby Meals",
    "meals": "Baby Meals",
    "formula": "Formula Milk",
    "infant formula": "Formula Milk",
    "formula milk": "Formula Milk",
    "fruit puree": "Fruit Puree",
    "fruit purees": "Fruit Puree",
    "puree": "Fruit Puree",
    "purees": "Fruit Puree",
    "porridge": "Porridge",
    "porridges": "Porridge",
    "toddler milk": "Toddler Milk",
    "growing up milk": "Toddler Milk",
    "toddler yoghurt": "Toddler Yoghurt",
    "toddler yogurt": "Toddler Yoghurt",
    "baby crisps": "Baby Crisps & Puffs",
    "baby puffs": "Baby Crisps & Puffs",
    "baby crisps & puffs": "Baby Crisps & Puffs",
    "oat snack": "Oat Snacks",
    "oat snacks": "Oat Snacks",
}

VALID_RETAILERS: Set[str] = {
    "Tesco",
    "Asda",
    "Sainsbury's",
    "Waitrose",
}

PLACEHOLDER_BARCODES: Set[str] = {
    "0000000000000",
    "1111111111111",
    "1234567890",
    "1234567891",
    "1234567890123",
    "900000000001",
    "900000000002",
    "900000000003",
    "900000000004",
    "900000000005",
    "900000000006",
    "900000000007",
    "900000000008",
    "900000000009",
    "900000000010",
    "900000000011",
    "9999999999999",
}

REQUIRED_PRODUCT_FIELDS = [
    "barcode",
    "name",
    "brand",
    "category",
    "subcategory",
    "ingredients",
    "gtin_source_url",
    "title_source_url",
]

REQUIRED_OFFER_FIELDS = [
    "barcode",
    "retailer",
    "price",
    "stock_status",
    "product_url",
]

VALID_STOCK_STATUSES = {"in_stock", "out_of_stock"}
