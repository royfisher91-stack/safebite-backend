import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any

# Make the backend root importable when running:
# python imports/importer.py
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_connection, upsert_offer  # noqa: E402

BASE_DIR = CURRENT_FILE.parent


def insert_product(product: Dict[str, Any]) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO products (
            product_id,
            barcode,
            name,
            brand,
            category,
            ingredients,
            allergens,
            safety_score,
            safety_result
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product.get("product_id"),
            product["barcode"],
            product["name"],
            product.get("brand"),
            product.get("category"),
            json.dumps(product.get("ingredients", [])),
            json.dumps(product.get("allergens", [])),
            product.get("safety_score", 50),
            product.get("safety_result", "Caution"),
        ),
    )

    conn.commit()
    conn.close()


def import_from_json(file_path: str) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        product = item["product"]
        offers = item.get("offers", [])

        insert_product(product)

        for offer in offers:
            upsert_offer(
                {
                    "barcode": product["barcode"],
                    "retailer": offer["retailer"],
                    "price": float(offer["price"]),
                    "promo_price": (
                        float(offer["promo_price"])
                        if offer.get("promo_price") not in (None, "")
                        else None
                    ),
                    "original_price": (
                        float(offer["original_price"])
                        if offer.get("original_price") not in (None, "")
                        else None
                    ),
                    "promo_text": offer.get("promo_text"),
                    "promotion_type": offer.get("promotion_type"),
                    "promotion_label": offer.get("promotion_label"),
                    "buy_quantity": offer.get("buy_quantity"),
                    "pay_quantity": offer.get("pay_quantity"),
                    "bundle_price": offer.get("bundle_price"),
                    "valid_from": offer.get("valid_from"),
                    "valid_to": offer.get("valid_to"),
                    "product_url": offer.get("product_url"),
                    "in_stock": offer.get("in_stock", True),
                    "stock_status": offer.get("stock_status"),
                    "is_promo": offer.get("is_promo", False),
                    "source": "import",
                    "source_type": "json_import",
                }
            )

    print("✅ JSON import complete")


def import_from_csv(file_path: str, retailer: str) -> None:
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            product = {
                "barcode": row["barcode"],
                "name": row["name"],
                "brand": row.get("brand"),
                "category": row.get("category"),
            }

            insert_product(product)

            upsert_offer(
                {
                    "barcode": row["barcode"],
                    "retailer": retailer,
                    "price": float(row["price"]),
                    "promo_price": (
                        float(row["promo_price"])
                        if row.get("promo_price") not in (None, "")
                        else None
                    ),
                    "original_price": (
                        float(row["original_price"])
                        if row.get("original_price") not in (None, "")
                        else None
                    ),
                    "promo_text": row.get("promo_text"),
                    "promotion_type": row.get("promotion_type"),
                    "promotion_label": row.get("promotion_label"),
                    "buy_quantity": row.get("buy_quantity"),
                    "pay_quantity": row.get("pay_quantity"),
                    "bundle_price": row.get("bundle_price"),
                    "valid_from": row.get("valid_from"),
                    "valid_to": row.get("valid_to"),
                    "product_url": row.get("url"),
                    "in_stock": row.get("in_stock", "1") == "1",
                    "stock_status": row.get("stock_status"),
                    "source": "import",
                    "source_type": "csv_import",
                }
            )

    print(f"✅ CSV import complete for {retailer}")


if __name__ == "__main__":
    print("Importer ready.")
    print("Run from Python shell or add a test call below.")
