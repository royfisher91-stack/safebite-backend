from typing import Optional
from urllib.parse import urlparse


VALID_STOCK_VALUES = {
    "in stock": "in_stock",
    "instock": "in_stock",
    "available": "in_stock",
    "yes": "in_stock",
    "true": "in_stock",
    "1": "in_stock",
    "out of stock": "out_of_stock",
    "outofstock": "out_of_stock",
    "unavailable": "out_of_stock",
    "no": "out_of_stock",
    "false": "out_of_stock",
    "0": "out_of_stock",
    "limited": "limited",
    "low stock": "limited",
    "low": "limited",
    "unknown": "unknown",
    "": "unknown",
}


def clean_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_price(value: Optional[str]) -> Optional[float]:
    text = clean_text(value)
    if not text:
        return None

    text = text.replace("£", "").replace(",", "").strip()

    try:
        price = float(text)
    except ValueError:
        return None

    if price < 0:
        return None

    return round(price, 2)


def normalise_stock_status(value: Optional[str]) -> str:
    text = clean_text(value).lower()
    return VALID_STOCK_VALUES.get(text, "unknown")


def is_valid_url(value: Optional[str]) -> bool:
    text = clean_text(value)
    if not text:
        return False

    try:
        parsed = urlparse(text)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def clean_url(value: Optional[str]) -> str:
    text = clean_text(value)
    if is_valid_url(text):
        return text
    return ""