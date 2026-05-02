from typing import Any, Dict, Iterable, List, Optional


STANDARD_KEYS = [
    "barcode",
    "name",
    "brand",
    "category",
    "subcategory",
    "ingredients",
    "allergens",
    "image_url",
    "retailer",
    "price",
    "promo_price",
    "multibuy_text",
    "stock_status",
    "product_url",
    "source",
]


BASE_FIELD_MAP = {
    "barcode": ["barcode", "gtin", "ean", "upc", "product_barcode"],
    "name": ["name", "product_name", "title", "product_title", "description", "Product Name"],
    "brand": ["brand", "brand_name", "manufacturer", "Brand"],
    "category": ["category", "department", "Category"],
    "subcategory": ["subcategory", "sub_category", "aisle", "Subcategory"],
    "ingredients": ["ingredients", "ingredient_list", "Ingredients"],
    "allergens": ["allergens", "allergen_info", "Allergens"],
    "image_url": ["image_url", "image", "thumbnail", "Image URL"],
    "price": ["price", "current_price", "sale_price", "Price"],
    "promo_price": ["promo_price", "promotional_price", "offer_price", "Promo Price"],
    "multibuy_text": ["multibuy_text", "promo_text", "promotion", "offer_text"],
    "stock_status": ["stock_status", "stock", "availability", "Stock Status"],
    "product_url": ["product_url", "url", "link", "Product URL"],
    "source": ["source", "feed_name", "source_name"],
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def first_non_empty(row: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = row.get(key)
        if clean_text(value):
            return clean_text(value)

    lower_lookup = {str(key).strip().lower(): key for key in row.keys()}
    for key in keys:
        source_key = lower_lookup.get(str(key).strip().lower())
        if source_key and clean_text(row.get(source_key)):
            return clean_text(row.get(source_key))
    return ""


def parse_price(value: Any) -> Optional[float]:
    text = clean_text(value)
    if not text:
        return None
    text = text.replace("GBP", "").replace("gbp", "").replace("£", "").replace(",", "").strip()
    try:
        price = float(text)
    except (TypeError, ValueError):
        return None
    if price < 0:
        return None
    return round(price, 2)


def normalise_stock(value: Any) -> str:
    text = clean_text(value).lower().replace("-", "_").replace(" ", "_")
    if text in {"1", "yes", "true", "available", "in_stock", "instock"}:
        return "in_stock"
    if text in {"0", "no", "false", "unavailable", "out_of_stock", "outofstock"}:
        return "out_of_stock"
    if text in {"limited", "few_left", "low_stock"}:
        return "limited"
    return "unknown"


def map_standard_row(
    row: Dict[str, Any],
    retailer: str,
    field_map: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    maps = dict(BASE_FIELD_MAP)
    if field_map:
        for key, aliases in field_map.items():
            maps[key] = aliases + maps.get(key, [])

    mapped: Dict[str, Any] = {}
    for key in STANDARD_KEYS:
        if key == "retailer":
            mapped[key] = retailer
        elif key in {"price", "promo_price"}:
            mapped[key] = parse_price(first_non_empty(row, maps.get(key, [key])))
        elif key == "stock_status":
            mapped[key] = normalise_stock(first_non_empty(row, maps.get(key, [key])))
        else:
            mapped[key] = first_non_empty(row, maps.get(key, [key]))

    if not mapped.get("source"):
        mapped["source"] = "{0}_bulk_import".format(retailer.lower().replace("&", "and").replace(" ", "_"))

    return mapped

