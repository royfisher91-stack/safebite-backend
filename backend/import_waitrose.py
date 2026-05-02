import csv
from datetime import datetime, timezone
from pathlib import Path

from database import get_product_by_barcode, insert_product, upsert_offer
from import_reporting import ImportReport
from import_utils import normalise_offer_row
from retailer_config import RETAILER_CONFIG

from typing import Optional, List

from fastapi import FastAPI
from services.condition_engine import apply_conditions

app = FastAPI()


def parse_csv_param(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@app.get("/products/barcode/{barcode}")
def get_product_by_barcode(
    barcode: str,
    allergies: Optional[str] = None,
    conditions: Optional[str] = None
):
    # -----------------------------
    # KEEP your existing DB lookup here
    # Example:
    # product = get_product_by_barcode_from_db(barcode)
    # -----------------------------
    product = get_product_by_barcode_from_db(barcode)

    if not product:
        return {"error": "Product not found"}

    # -----------------------------
    # KEEP your existing analysis logic here
    # Example:
    # analysis = analyse_product(product)
    # -----------------------------
    analysis = analyse_product(product)

    allergy_list = parse_csv_param(allergies)
    condition_list = parse_csv_param(conditions)

    personalised_analysis = apply_conditions(
        analysis=analysis,
        allergies=allergy_list,
        conditions=condition_list
    )

    return {
        **product,
        "analysis": personalised_analysis
    }


def run_import() -> ImportReport:
    config = RETAILER_CONFIG["waitrose"]
    report = ImportReport(retailer=config["retailer_name"])

    csv_path = Path(__file__).parent / "imports" / "waitrose.csv"

    if not csv_path.exists():
        report.errors_found += 1
        print(f"Missing file: {csv_path}")
        return report

    imported_at = datetime.now(timezone.utc).isoformat()
    source_file = csv_path.name
    source_retailer = config["retailer_name"]

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            report.rows_read += 1

            try:
                cleaned = normalise_offer_row(
                    row,
                    barcode_key="barcode",
                    name_key="name",
                    brand_key="brand",
                    price_key="price",
                    stock_key="in_stock",
                    url_key="product_url",
                )

                barcode = cleaned["barcode"]
                name = cleaned["name"]
                price = cleaned["price"]

                if not barcode or not name or price is None:
                    report.rows_skipped += 1
                    continue

                existing = get_product_by_barcode(barcode)
                if not existing:
                    insert_product(
                        barcode=barcode,
                        name=name,
                        brand=cleaned["brand"],
                    )
                    report.products_created += 1

                upsert_offer(
                    barcode=barcode,
                    retailer=config["retailer_name"],
                    price=price,
                    in_stock=cleaned["in_stock"],
                    product_url=cleaned["product_url"],
                    source=config["source_name"],
                    imported_at=imported_at,
                    source_file=source_file,
                    source_retailer=source_retailer,
                )
                report.offers_upserted += 1

            except Exception as exc:
                report.errors_found += 1
                print(f"Waitrose row error: {exc}")

    return report


if __name__ == "__main__":
    result = run_import()
    result.print_summary()