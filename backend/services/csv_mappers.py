from typing import Dict, Optional


BASE_OFFER_MAP = {
    "barcode": "barcode",
    "name": "name",
    "offer_title": "offer_title",
    "brand": "brand",
    "category": "category",
    "subcategory": "subcategory",
    "price": "price",
    "promo_price": "promo_price",
    "original_price": "original_price",
    "promotion_type": "promotion_type",
    "promotion_label": "promotion_label",
    "buy_quantity": "buy_quantity",
    "pay_quantity": "pay_quantity",
    "bundle_price": "bundle_price",
    "valid_from": "valid_from",
    "valid_to": "valid_to",
    "stock_status": "stock_status",
    "in_stock": "in_stock",
    "product_url": "product_url",
    "image_url": "image_url",
    "unit_price": "unit_price",
    "unit_name": "unit_name",
    "size_text": "size_text",
    "source_product_id": "source_product_id",
}

RETAILER_COLUMN_MAPS = {
    "tesco": dict(BASE_OFFER_MAP),
    "asda": dict(BASE_OFFER_MAP),
    "sainsburys": dict(BASE_OFFER_MAP),
    "sainsbury's": dict(BASE_OFFER_MAP),
    "waitrose": dict(BASE_OFFER_MAP),
}


def get_column_map(retailer: str) -> Optional[Dict[str, str]]:
    return RETAILER_COLUMN_MAPS.get(retailer.lower())
