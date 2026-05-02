from database import get_product_by_barcode, insert_product, upsert_offer
from pathlib import Path

from services.import_service import import_multiple_csvs


BASE_DIR = Path(__file__).resolve().parent
IMPORTS_DIR = BASE_DIR / "imports"


def main() -> None:
    files = {
        "tesco": IMPORTS_DIR / "tesco_offers.csv",
        "asda": IMPORTS_DIR / "asda_offers.csv",
    }

    results = import_multiple_csvs(files)

    for result in results:
        print("-" * 50)
        print("Retailer:", result["retailer"])
        print("File:", result["file"])
        print("Rows read:", result["rows_read"])
        print("Rows imported:", result["rows_imported"])
        print("Rows skipped:", result["rows_skipped"])
        print("Missing products:", result["missing_products"])
        print("Invalid rows:", result["invalid_rows"])


if __name__ == "__main__":
    main()