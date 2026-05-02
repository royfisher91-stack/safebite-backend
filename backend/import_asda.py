import csv
from pathlib import Path
from typing import Any, Dict, Set

from database import upsert_offer, upsert_product
from import_utils import build_offer_payload, build_product_payload, normalise_product_row


BASE_DIR = Path(__file__).resolve().parent
RAW_FILE = BASE_DIR / "imports" / "asda" / "raw.csv"
RETAILER = "Asda"


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_price(value: Any):
    try:
        if value in (None, "", "N/A"):
            return None
        return float(value)
    except Exception:
        return None


def import_asda() -> Dict[str, Any]:
    stats = {
        "retailer": RETAILER,
        "file_used": str(RAW_FILE.name),
        "products_upserted": 0,
        "offers_upserted": 0,
        "rows_skipped": 0,
        "errors": [],
    }

    if not RAW_FILE.exists():
        stats["errors"].append("raw.csv not found")
        return stats

    seen_products: Set[str] = set()
    seen_offers: Set[str] = set()

    with open(RAW_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for index, row in enumerate(reader, start=1):
            try:
                if not isinstance(row, dict):
                    stats["rows_skipped"] += 1
                    continue

                cleaned = normalise_product_row(row, retailer=RETAILER)

                if not cleaned:
                    stats["rows_skipped"] += 1
                    continue

                # --- HARD VALIDATION ---
                barcode = _safe_str(cleaned.get("barcode"))
                if not barcode:
                    stats["rows_skipped"] += 1
                    continue

                cleaned["barcode"] = barcode

                # --- CLEAN CORE FIELDS ---
                if "product_url" in cleaned:
                    cleaned["product_url"] = _safe_str(cleaned.get("product_url"))

                cleaned["price"] = _safe_price(cleaned.get("price"))

                # Stock normalisation
                stock = cleaned.get("stock_status")
                if stock:
                    cleaned["stock_status"] = _safe_str(stock).lower()
                else:
                    cleaned["stock_status"] = "unknown"

                # --- PRODUCT UPSERT (ONCE PER BARCODE) ---
                if barcode not in seen_products:
                    upsert_product(build_product_payload(cleaned, retailer=RETAILER))
                    seen_products.add(barcode)
                    stats["products_upserted"] += 1

                # --- OFFER UPSERT (DEDUP SAFE) ---
                offer_key = f"{barcode}-{cleaned.get('product_url', '')}"

                if offer_key in seen_offers:
                    continue

                if cleaned.get("price") is not None or cleaned.get("product_url"):
                    upsert_offer(build_offer_payload(cleaned, retailer=RETAILER))
                    seen_offers.add(offer_key)
                    stats["offers_upserted"] += 1

            except Exception as exc:
                stats["rows_skipped"] += 1
                stats["errors"].append(f"Row {index}: {str(exc)}")

    return stats