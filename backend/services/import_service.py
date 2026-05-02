import csv
from pathlib import Path
from typing import Any, Dict, List

from database import get_product_by_barcode, upsert_offer, upsert_product
from import_utils import build_offer_payload, build_product_payload, normalise_product_row
from services.csv_mappers import get_column_map


def product_exists_by_barcode(barcode: str) -> bool:
    if not barcode:
        return False
    return get_product_by_barcode(barcode) is not None


def create_placeholder_product_from_offer(mapped: Dict[str, Any], retailer: str) -> None:
    barcode = str(mapped.get("barcode", "") or "").strip()
    if not barcode:
        return

    product_payload = build_product_payload(mapped, retailer=retailer)
    if not product_payload.get("name"):
        product_payload["name"] = f"Unknown Product {barcode}"

    product_payload["safety_score"] = None
    product_payload["safety_result"] = "Unknown"
    product_payload["ingredient_reasoning"] = (
        "Imported from retailer offer data only. Insufficient verified product information is available for a reliable decision."
    )
    product_payload["allergen_warnings"] = ""

    upsert_product(product_payload)


def map_csv_row(row: Dict[str, Any], retailer: str) -> Dict[str, Any]:
    column_map = get_column_map(retailer)
    if not column_map:
        raise ValueError("No CSV column map found for retailer: {0}".format(retailer))

    shaped_row = dict(row)

    for target_key, source_key in column_map.items():
        if source_key and source_key in row:
            shaped_row[target_key] = row.get(source_key)

    mapped = normalise_product_row(shaped_row, retailer=retailer)
    if not mapped:
        raise ValueError("CSV row is empty or missing product identifiers")

    return mapped


def import_offers_from_csv(csv_path: Path, retailer: str) -> Dict[str, Any]:
    stats = {
        "retailer": retailer,
        "file": str(csv_path),
        "rows_read": 0,
        "rows_imported": 0,
        "rows_skipped": 0,
        "missing_products": 0,
        "missing_products_created": 0,
        "invalid_rows": 0,
        "errors": [],
    }

    if not csv_path.exists():
        raise FileNotFoundError("CSV file not found: {0}".format(csv_path))

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for index, row in enumerate(reader, start=1):
            stats["rows_read"] += 1

            try:
                mapped = map_csv_row(row, retailer)
            except Exception as exc:
                stats["invalid_rows"] += 1
                stats["rows_skipped"] += 1
                stats["errors"].append(f"Row {index}: {str(exc)}")
                continue

            barcode = str(mapped.get("barcode", "") or "").strip()
            price = mapped.get("price")
            product_url = mapped.get("product_url")

            if not barcode or (price is None and not product_url):
                stats["invalid_rows"] += 1
                stats["rows_skipped"] += 1
                continue

            if not product_exists_by_barcode(barcode):
                create_placeholder_product_from_offer(mapped, retailer=retailer)
                stats["missing_products"] += 1
                stats["missing_products_created"] += 1

            try:
                upsert_offer(build_offer_payload(mapped, retailer=retailer))
                stats["rows_imported"] += 1
            except Exception as exc:
                stats["rows_skipped"] += 1
                stats["errors"].append(f"Row {index}: {str(exc)}")

    return stats


def import_multiple_csvs(file_map: Dict[str, Path]) -> List[Dict[str, Any]]:
    results = []

    for retailer, path in file_map.items():
        result = import_offers_from_csv(path, retailer)
        results.append(result)

    return results
