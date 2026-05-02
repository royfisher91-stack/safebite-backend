import json
import re
from typing import Dict, Iterable, Optional
from urllib.parse import urlparse

from services.phase1_constants import ALLOWED_TAXONOMY, CATEGORY_ALIASES, SUBCATEGORY_ALIASES
from services.phase2_types import ProductImportRow


_WHITESPACE_RE = re.compile(r"\s+")
_TRAILING_SIZE_RE = re.compile(r"\s+(\d+(?:\.\d+)?)\s?(g|kg|ml|l|pack|pk)\b", re.IGNORECASE)
_BRAND_PREFIX_RE = re.compile(r"^\s*([A-Za-z0-9&'’.\+ \-]+)\s+[-:]\s+", re.IGNORECASE)


CANONICAL_CATEGORY_MAP = {
    "baby food": ("Baby & Toddler", None),
    "baby meals": ("Baby & Toddler", "Baby Meals"),
    "formula": ("Baby & Toddler", "Formula Milk"),
    "formula milk": ("Baby & Toddler", "Formula Milk"),
    "first infant milk": ("Baby & Toddler", "Formula Milk"),
    "follow on milk": ("Baby & Toddler", "Formula Milk"),
    "follow-on milk": ("Baby & Toddler", "Formula Milk"),
    "toddler milk": ("Baby & Toddler", "Toddler Milk"),
    "growing up milk": ("Baby & Toddler", "Toddler Milk"),
    "yoghurt": ("Baby & Toddler", "Toddler Yoghurt"),
    "yogurt": ("Baby & Toddler", "Toddler Yoghurt"),
    "baby yoghurt": ("Baby & Toddler", "Toddler Yoghurt"),
    "baby yogurt": ("Baby & Toddler", "Toddler Yoghurt"),
    "puree": ("Baby & Toddler", "Fruit Puree"),
    "fruit puree": ("Baby & Toddler", "Fruit Puree"),
    "porridge": ("Baby & Toddler", "Porridge"),
    "crisps": ("Baby Snacks", "Baby Crisps & Puffs"),
    "puffs": ("Baby Snacks", "Baby Crisps & Puffs"),
    "oat snacks": ("Baby Snacks", "Oat Snacks"),
    "oat snack": ("Baby Snacks", "Oat Snacks"),
    "baby snacks": ("Baby Snacks", None),
}


def clean_text(value: Optional[object]) -> Optional[str]:
    if value is None:
        return None
    value = str(value).replace("\u00a0", " ").strip()
    if not value:
        return None
    return _WHITESPACE_RE.sub(" ", value)


def normalize_barcode(value: Optional[object]) -> Optional[str]:
    value = clean_text(value)
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) in (8, 12, 13, 14):
        return digits
    return digits or None


def normalize_name(name: Optional[object], brand: Optional[object] = None) -> Optional[str]:
    name = clean_text(name)
    brand = clean_text(brand)
    if not name:
        return None

    name = name.replace("’", "'")
    name = re.sub(r"\s+\|\s+", " - ", name)
    name = re.sub(r"\s{2,}", " ", name).strip()

    if brand:
        lower_name = name.lower()
        lower_brand = brand.lower()
        if lower_name.startswith(lower_brand + " "):
            name = name[len(brand):].strip()
        elif lower_name.startswith(lower_brand + "-"):
            name = name[len(brand) + 1:].strip()

    prefix_match = _BRAND_PREFIX_RE.match(name)
    if prefix_match and brand:
        prefix = clean_text(prefix_match.group(1))
        if prefix and prefix.lower() == brand.lower():
            name = name[prefix_match.end():].strip()

    return name


def build_name_key(name: Optional[object], brand: Optional[object] = None) -> Optional[str]:
    name = normalize_name(name, brand)
    if not name:
        return None
    normalized = name.lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = _TRAILING_SIZE_RE.sub("", normalized).strip()
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized


def _subcategory_default_category(subcategory: str) -> str:
    for category, subcategories in ALLOWED_TAXONOMY.items():
        if subcategory in subcategories:
            return category
    return ""


def normalize_category(category: Optional[object], subcategory: Optional[object], name: Optional[object] = None) -> Dict[str, Optional[str]]:
    category_text = clean_text(category) or ""
    subcategory_text = clean_text(subcategory) or ""
    name_text = clean_text(name) or ""

    category_text = CATEGORY_ALIASES.get(category_text.lower(), category_text)
    subcategory_text = SUBCATEGORY_ALIASES.get(subcategory_text.lower(), subcategory_text)

    if subcategory_text:
        forced_category = _subcategory_default_category(subcategory_text)
        if forced_category:
            return {"category": forced_category, "subcategory": subcategory_text}

    for probe in (subcategory_text, category_text, name_text):
        probe_key = probe.lower()
        for alias, mapped in CANONICAL_CATEGORY_MAP.items():
            if alias in probe_key:
                canonical_category, canonical_subcategory = mapped
                return {
                    "category": canonical_category,
                    "subcategory": canonical_subcategory or subcategory_text or None,
                }

    if category_text in ALLOWED_TAXONOMY:
        if subcategory_text in ALLOWED_TAXONOMY[category_text]:
            return {"category": category_text, "subcategory": subcategory_text}
        return {"category": category_text, "subcategory": None}

    return {"category": category_text or None, "subcategory": subcategory_text or None}


def normalize_url(url: Optional[object]) -> Optional[str]:
    url = clean_text(url)
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return url


def normalize_price(value: Optional[object]) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (float, int)):
        result = float(value)
        return round(result, 2) if result >= 0 else None

    text = clean_text(value)
    if not text:
        return None
    text = text.replace("£", "").replace("GBP", "").replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    try:
        result = float(match.group(1))
    except ValueError:
        return None
    if result < 0:
        return None
    return round(result, 2)


def normalize_stock_status(value: Optional[object]) -> Optional[str]:
    value = clean_text(value)
    if not value:
        return None
    lowered = value.lower().replace("-", "_")
    if lowered in ("in stock", "in_stock", "instock", "available", "available now", "yes", "true", "1"):
        return "in_stock"
    if lowered in ("out of stock", "out_of_stock", "outofstock", "unavailable", "sold out", "no", "false", "0"):
        return "out_of_stock"
    if lowered in ("low stock", "limited", "few left"):
        return "limited"
    return lowered.replace(" ", "_")


def safe_json_dict(value: Optional[object]) -> Optional[dict]:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = clean_text(value)
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except (TypeError, ValueError):
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def normalize_row(raw: Dict[str, object], retailer: Optional[str] = None, source: Optional[str] = None) -> ProductImportRow:
    brand = clean_text(raw.get("brand")) or clean_text(raw.get("manufacturer"))
    barcode = normalize_barcode(raw.get("barcode") or raw.get("gtin") or raw.get("ean") or raw.get("upc"))
    name = normalize_name(raw.get("name") or raw.get("product_name") or raw.get("title"), brand=brand)
    category_data = normalize_category(raw.get("category"), raw.get("subcategory"), name=name)

    return ProductImportRow(
        barcode=barcode or "",
        name=name or "",
        brand=brand,
        category=category_data["category"],
        subcategory=category_data["subcategory"],
        ingredients=clean_text(raw.get("ingredients")),
        allergens=clean_text(raw.get("allergens")),
        nutrition_json=safe_json_dict(raw.get("nutrition_json") or raw.get("nutrition")),
        processing_notes=clean_text(raw.get("processing_notes") or raw.get("processing")),
        price=normalize_price(raw.get("price")),
        promo_price=normalize_price(raw.get("promo_price") or raw.get("offer_price")),
        retailer=clean_text(raw.get("retailer")) or clean_text(retailer),
        stock_status=normalize_stock_status(raw.get("stock_status") or raw.get("availability")),
        product_url=normalize_url(raw.get("product_url") or raw.get("url")),
        image_url=normalize_url(raw.get("image_url")),
        source=clean_text(raw.get("source")) or clean_text(source),
        source_retailer=clean_text(raw.get("source_retailer")) or clean_text(retailer),
        extra={k: v for k, v in raw.items() if k not in {
            "barcode", "gtin", "ean", "upc", "name", "product_name", "title", "brand", "manufacturer",
            "category", "subcategory", "ingredients", "allergens", "nutrition_json", "nutrition", "processing_notes",
            "processing", "price", "promo_price", "offer_price", "retailer", "stock_status", "availability",
            "product_url", "url", "image_url", "source", "source_retailer",
        }},
    )


def normalize_rows(rows: Iterable[Dict[str, object]], retailer: Optional[str] = None, source: Optional[str] = None):
    for raw in rows:
        yield normalize_row(raw, retailer=retailer, source=source)
