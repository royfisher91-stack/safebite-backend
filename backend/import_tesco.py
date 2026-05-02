import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from database import upsert_offer, upsert_product
from import_utils import (
    build_offer_payload,
    build_product_payload,
    first_non_empty,
    normalise_product_row,
)


BASE_DIR = Path(__file__).resolve().parent
RAW_FILE = BASE_DIR / "imports" / "tesco" / "raw.csv"
RETAILER = "Tesco"


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalise_tesco_offer(product: Dict[str, Any], offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Merge product + offer safely
    row = {
        **(product if isinstance(product, dict) else {}),
        **(offer if isinstance(offer, dict) else {}),
    }

    # Normalise core fields early
    row["name"] = first_non_empty(row, ["name", "title", "product_name"])
    row["retailer"] = first_non_empty(offer, ["retailer"]) or RETAILER

    cleaned = normalise_product_row(row, retailer=row["retailer"])

    if not cleaned:
        return None

    # HARD SAFETY RULES
    barcode = _safe_str(cleaned.get("barcode"))
    if not barcode:
        return None

    cleaned["barcode"] = barcode

    # Ensure product_url is always clean
    if "product_url" in cleaned:
        cleaned["product_url"] = _safe_str(cleaned.get("product_url"))

    # Ensure price is valid float or None
    price = cleaned.get("price")
    try:
        cleaned["price"] = float(price) if price not in (None, "", "N/A") else None
    except Exception:
        cleaned["price"] = None

    # Normalise stock
    stock = cleaned.get("stock_status")
    if stock:
        cleaned["stock_status"] = _safe_str(stock).lower()
    else:
        cleaned["stock_status"] = "unknown"

    return cleaned


def normalise_tesco_item(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(row, dict):
        return []

    product = row.get("product", {})
    if not isinstance(product, dict):
        product = {}

    offers = row.get("offers", [])
    if not isinstance(offers, list):
        single_offer = row.get("offer", {})
        offers = [single_offer] if isinstance(single_offer, dict) else [{}]

    if not offers:
        offers = [{}]

    cleaned_items = []

    for offer in offers:
        if not isinstance(offer, dict):
            offer = {}

        cleaned = _normalise_tesco_offer(product, offer)

        if not cleaned:
            continue

        if not cleaned.get("barcode"):
            continue

        cleaned_items.append(cleaned)

    return cleaned_items


def import_tesco() -> Dict[str, Any]:
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

    try:
        with open(RAW_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception as exc:
        stats["errors"].append(f"Failed to parse Tesco JSON: {str(exc)}")
        return stats

    if not isinstance(data, list):
        stats["errors"].append("Tesco file is not a JSON array")
        return stats

    seen_products: Set[str] = set()
    seen_offers: Set[str] = set()

    for index, row in enumerate(data, start=1):
        try:
            cleaned_items = normalise_tesco_item(row)

            if not cleaned_items:
                stats["rows_skipped"] += 1
                continue

            for cleaned in cleaned_items:
                barcode = cleaned.get("barcode", "")

                # --- PRODUCT UPSERT (ONCE PER BARCODE) ---
                if barcode not in seen_products:
                    upsert_product(
                        build_product_payload(
                            cleaned,
                            retailer=cleaned.get("source_retailer") or RETAILER,
                        )
                    )
                    seen_products.add(barcode)
                    stats["products_upserted"] += 1

                # --- OFFER UPSERT (DEDUP PROTECTION) ---
                offer_key = f"{barcode}-{cleaned.get('product_url', '')}"

                if offer_key in seen_offers:
                    continue

                # Only insert valid offers
                if cleaned.get("price") is not None or cleaned.get("product_url"):
                    upsert_offer(
                        build_offer_payload(
                            cleaned,
                            retailer=cleaned.get("source_retailer") or RETAILER,
                        )
                    )
                    seen_offers.add(offer_key)
                    stats["offers_upserted"] += 1

        except Exception as exc:
            stats["rows_skipped"] += 1
            stats["errors"].append(f"Row {index}: {str(exc)}")

    return stats