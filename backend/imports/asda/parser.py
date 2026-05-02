import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def clean_price(value: Any) -> Optional[float]:
    text = clean_text(value).replace("£", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def clean_bool(value: Any) -> bool:
    text = clean_text(value).lower()
    return text in {"true", "1", "yes", "y", "in stock", "instock"}


def parse_asda_csv(csv_path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = Path(csv_path) if csv_path else Path(__file__).resolve().parent / "raw.csv"
    rows: List[Dict[str, Any]] = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            barcode = clean_text(row.get("barcode"))
            name = clean_text(row.get("name"))
            if not barcode or not name:
                continue

            rows.append(
                {
                    "source": "asda_import",
                    "retailer": "Asda",
                    "barcode": barcode,
                    "name": name,
                    "brand": clean_text(row.get("brand")),
                    "category": clean_text(row.get("category")) or "unknown",
                    "price": clean_price(row.get("price")),
                    "promo_price": clean_price(row.get("promo_price")),
                    "in_stock": clean_bool(row.get("in_stock")),
                    "product_url": clean_text(row.get("product_url")),
                    "image_url": clean_text(row.get("image_url")),
                }
            )

    return rows