from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse
import re

from services.category_service import normalise_category


RETAILER_NAMES = {
    "asda": "Asda",
    "sainsburys": "Sainsbury's",
    "sainsbury's": "Sainsbury's",
    "tesco": "Tesco",
    "waitrose": "Waitrose",
}

TRUTHY_VALUES = {"1", "available", "in stock", "instock", "true", "yes"}
FALSY_VALUES = {"0", "false", "no", "out of stock", "outofstock", "unavailable"}
LIMITED_VALUES = {"few left", "limited", "low", "low stock"}

# LOCKED PHASE 1 TAXONOMY
# Keep this strict for current SafeBite Phase 1 scope.
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

# Alias handling to prevent drift from real imports.
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


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def safe_lower(value: Any) -> str:
    return safe_str(value).lower()


def safe_get(row: Optional[Dict[str, Any]], key: str, default: str = "") -> str:
    if not isinstance(row, dict):
        return default
    value = row.get(key, default)
    if value is None:
        return default
    return safe_str(value)


def first_non_empty(row: Optional[Dict[str, Any]], keys: Iterable[str]) -> str:
    if not isinstance(row, dict):
        return ""

    for key in keys:
        value = row.get(key)
        if value is not None and safe_str(value) != "":
            return safe_str(value)

    lower_key_lookup = {str(key).strip().lower(): key for key in row.keys()}

    for key in keys:
        source_key = lower_key_lookup.get(str(key).strip().lower())
        if source_key is None:
            continue
        value = row.get(source_key)
        if value is not None and safe_str(value) != "":
            return safe_str(value)

    return ""


def normalise_retailer_name(value: Any) -> str:
    text = safe_str(value)
    if not text:
        return ""

    key = text.lower().replace("_", " ").strip()
    return RETAILER_NAMES.get(key, text[:1].upper() + text[1:])


def build_source_name(retailer: Any, fallback: str = "import") -> str:
    text = safe_lower(retailer)
    if not text:
        return fallback

    source_key = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if not source_key:
        return fallback

    return f"{source_key}_import"


def parse_price(value: Any) -> Optional[float]:
    text = safe_str(value)
    if not text:
        return None

    text = text.replace("£", "").replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None

    try:
        price = float(match.group(1))
    except (TypeError, ValueError):
        return None

    if price < 0:
        return None

    return round(price, 2)


def parse_bool(value: Any, default: bool = False) -> bool:
    text = safe_lower(value)
    if text in TRUTHY_VALUES:
        return True
    if text in FALSY_VALUES:
        return False
    return default


def parse_stock(value: Any, in_stock_value: Any = None) -> str:
    text = safe_lower(value)

    if text in TRUTHY_VALUES:
        return "in_stock"

    if text in FALSY_VALUES:
        return "out_of_stock"

    if text in LIMITED_VALUES:
        return "limited"

    if in_stock_value is not None:
        return "in_stock" if parse_bool(in_stock_value, default=False) else "out_of_stock"

    return "unknown"


def parse_ingredients(value: Any) -> List[str]:
    text = safe_str(value)
    if not text:
        return []

    parts = re.split(r",|;|\n", text)
    return [part.strip() for part in parts if part.strip()]


def parse_allergens(value: Any) -> List[str]:
    text = safe_str(value)
    if not text:
        return []

    parts = re.split(r",|;|\n", text)
    return [part.strip().lower() for part in parts if part.strip()]


def clean_url(value: Any) -> str:
    text = safe_str(value)
    if not text:
        return ""

    parsed = urlparse(text)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return text

    return ""


def is_probably_empty_row(row: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(row, dict):
        return True

    for value in row.values():
        if safe_str(value):
            return False
    return True


def _canonicalise_category_name(value: str) -> str:
    text = safe_str(value)
    if not text:
        return ""
    key = safe_lower(text)
    return CATEGORY_ALIASES.get(key, text)


def _canonicalise_subcategory_name(value: str) -> str:
    text = safe_str(value)
    if not text:
        return ""
    key = safe_lower(text)
    return SUBCATEGORY_ALIASES.get(key, text)


def _subcategory_default_category(subcategory: str) -> str:
    for category, subcategories in ALLOWED_TAXONOMY.items():
        if subcategory in subcategories:
            return category
    return ""


def enforce_phase1_taxonomy(category: str, subcategory: str) -> Tuple[str, str]:
    """
    Enforce the locked SafeBite Phase 1 taxonomy.

    Rules:
    - Canonicalise aliases first.
    - If subcategory is known, force it into the correct parent category.
    - If category exists but subcategory is invalid for that category, blank subcategory.
    - If category is unknown, blank both fields.
    """
    category = _canonicalise_category_name(category)
    subcategory = _canonicalise_subcategory_name(subcategory)

    if subcategory:
        forced_category = _subcategory_default_category(subcategory)
        if forced_category:
            return forced_category, subcategory

    if category in ALLOWED_TAXONOMY:
        if subcategory in ALLOWED_TAXONOMY[category]:
            return category, subcategory
        return category, ""

    return "", ""


def build_product_payload(cleaned: Dict[str, Any], retailer: Any = "") -> Dict[str, Any]:
    retailer_name = normalise_retailer_name(retailer or cleaned.get("source_retailer"))
    source = cleaned.get("source") or build_source_name(retailer_name, fallback="product_import")

    category, subcategory = enforce_phase1_taxonomy(
        safe_str(cleaned.get("category")),
        safe_str(cleaned.get("subcategory")),
    )

    return {
        "barcode": cleaned.get("barcode", ""),
        "name": cleaned.get("name", ""),
        "brand": cleaned.get("brand", ""),
        "description": cleaned.get("description", ""),
        "ingredients": cleaned.get("ingredients", []),
        "allergens": cleaned.get("allergens", []),
        "category": category,
        "subcategory": subcategory,
        "image_url": cleaned.get("image_url", ""),
        "source": source,
        "source_retailer": retailer_name,
    }


def build_offer_payload(cleaned: Dict[str, Any], retailer: Any) -> Dict[str, Any]:
    retailer_name = normalise_retailer_name(retailer or cleaned.get("retailer"))
    stock_status = cleaned.get("stock_status") or "unknown"
    in_stock = stock_status in ("in_stock", "limited")

    return {
        "barcode": cleaned.get("barcode", ""),
        "retailer": retailer_name,
        "price": cleaned.get("price"),
        "promo_price": cleaned.get("promo_price"),
        "original_price": cleaned.get("original_price"),
        "promo_text": cleaned.get("promo_text", ""),
        "promotion_type": cleaned.get("promotion_type", ""),
        "promotion_label": cleaned.get("promotion_label", ""),
        "buy_quantity": cleaned.get("buy_quantity"),
        "pay_quantity": cleaned.get("pay_quantity"),
        "bundle_price": cleaned.get("bundle_price"),
        "valid_from": cleaned.get("valid_from"),
        "valid_to": cleaned.get("valid_to"),
        "stock_status": stock_status,
        "in_stock": in_stock,
        "product_url": cleaned.get("product_url", ""),
        "image_url": cleaned.get("image_url", ""),
        "source": cleaned.get("source") or build_source_name(retailer_name, fallback="offer_import"),
        "source_retailer": retailer_name,
    }


def normalise_product_row(
    row: Optional[Dict[str, Any]],
    retailer: Any = "",
) -> Optional[Dict[str, Any]]:
    if is_probably_empty_row(row):
        return None

    barcode = first_non_empty(row, [
        "barcode",
        "ean",
        "upc",
        "product_barcode",
        "gtin",
    ])

    name = first_non_empty(row, [
        "name",
        "product_name",
        "title",
        "product_title",
        "display_name",
        "item_name",
        "offer_title",
        "description",
        "product",
        "productDescription",
        "Product Name",
        "Title",
        "Description",
    ])

    brand = first_non_empty(row, [
        "brand",
        "brand_name",
        "Brand",
        "Brand Name",
        "manufacturer",
    ])

    description = first_non_empty(row, [
        "description",
        "product_description",
        "long_description",
        "Description",
    ])

    ingredients = first_non_empty(row, [
        "ingredients",
        "ingredient_list",
        "Ingredients",
    ])

    allergens = first_non_empty(row, [
        "allergens",
        "allergen_info",
        "Allergens",
    ])

    raw_category = first_non_empty(row, [
        "category",
        "department",
        "Category",
        "Department",
    ])

    raw_subcategory = first_non_empty(row, [
        "subcategory",
        "sub_category",
        "aisle",
        "Subcategory",
        "Sub Category",
        "Aisle",
    ])

    category_context = " ".join(part for part in [name, brand] if part)
    category, subcategory = normalise_category(raw_category, raw_subcategory, category_context)
    category, subcategory = enforce_phase1_taxonomy(category, subcategory)

    price_raw = first_non_empty(row, [
        "price",
        "current_price",
        "sale_price",
        "Price",
        "Current Price",
    ])

    promo_price_raw = first_non_empty(row, [
        "promo_price",
        "promotional_price",
        "offer_price",
        "Promo Price",
    ])

    original_price_raw = first_non_empty(row, [
        "original_price",
        "was_price",
        "Original Price",
        "Was Price",
    ])

    stock_raw = first_non_empty(row, [
        "stock_status",
        "stock",
        "availability",
        "Stock Status",
        "Stock",
        "Availability",
    ])

    in_stock_raw = first_non_empty(row, [
        "in_stock",
        "available",
        "available_for_delivery",
        "In Stock",
    ])

    product_url = first_non_empty(row, [
        "product_url",
        "url",
        "link",
        "Product URL",
        "URL",
        "Link",
    ])

    image_url = first_non_empty(row, [
        "image_url",
        "image",
        "thumbnail",
        "Image URL",
    ])
    image_source_type = first_non_empty(row, [
        "image_source_type",
        "image_source",
        "image_type",
        "Image Source Type",
    ])
    image_rights_status = first_non_empty(row, [
        "image_rights_status",
        "image_rights",
        "rights_status",
        "Image Rights Status",
    ])
    image_credit = first_non_empty(row, [
        "image_credit",
        "credit",
        "attribution",
        "Image Credit",
    ])
    image_last_verified_at = first_non_empty(row, [
        "image_last_verified_at",
        "image_verified_at",
        "Image Last Verified At",
    ])

    retailer_name = normalise_retailer_name(retailer or first_non_empty(row, ["retailer", "source_retailer"]))
    stock_status = parse_stock(stock_raw, in_stock_raw if in_stock_raw else None)

    if not barcode and not name:
        return None

    return {
        "barcode": barcode,
        "name": name,
        "brand": brand,
        "description": description,
        "ingredients": parse_ingredients(ingredients),
        "allergens": parse_allergens(allergens),
        "category": category,
        "subcategory": subcategory,
        "price": parse_price(price_raw),
        "promo_price": parse_price(promo_price_raw),
        "original_price": parse_price(original_price_raw),
        "promo_text": first_non_empty(row, ["promo_text", "promotion", "offer_text"]),
        "stock_status": stock_status,
        "in_stock": stock_status in ("in_stock", "limited"),
        "product_url": clean_url(product_url),
        "image_url": clean_url(image_url),
        "image_source_type": image_source_type,
        "image_rights_status": image_rights_status,
        "image_credit": image_credit,
        "image_last_verified_at": image_last_verified_at,
        "source": build_source_name(retailer_name, fallback="product_import"),
        "source_retailer": retailer_name,
    }


def normalise_offer_row(
    row: Optional[Dict[str, Any]],
    retailer: Any = "",
    barcode_key: str = "barcode",
    name_key: str = "name",
    brand_key: str = "brand",
    price_key: str = "price",
    stock_key: str = "stock_status",
    url_key: str = "product_url",
) -> Optional[Dict[str, Any]]:
    if is_probably_empty_row(row):
        return None

    shaped = dict(row or {})
    shaped.setdefault("barcode", shaped.get(barcode_key, ""))
    shaped.setdefault("name", shaped.get(name_key, shaped.get("offer_title", "")))
    shaped.setdefault("brand", shaped.get(brand_key, ""))
    shaped.setdefault("price", shaped.get(price_key, ""))
    shaped.setdefault("stock_status", shaped.get(stock_key, ""))
    shaped.setdefault("product_url", shaped.get(url_key, ""))

    return normalise_product_row(shaped, retailer=retailer)
