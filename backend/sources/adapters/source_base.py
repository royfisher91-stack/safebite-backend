from typing import Any, Dict


class SourceAdapter:
    source_name = "unknown"
    supported_domain = "food"

    def normalize_product_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "barcode": row.get("barcode"),
            "name": row.get("name"),
            "brand": row.get("brand"),
            "category": row.get("category"),
            "subcategory": row.get("subcategory"),
            "source": self.source_name,
            "source_retailer": row.get("source_retailer") or self.source_name,
        }

    def normalize_offer_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "barcode": row.get("barcode"),
            "retailer": row.get("retailer") or self.source_name,
            "price": row.get("price"),
            "promo_price": row.get("promo_price"),
            "stock_status": row.get("stock_status"),
            "in_stock": row.get("in_stock"),
            "product_url": row.get("product_url"),
            "source": self.source_name,
            "source_retailer": row.get("source_retailer") or self.source_name,
        }
