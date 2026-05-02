import argparse
import json
import os
import sqlite3
import sys
from typing import Any, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.gtin_service import validate_gtin
from services.phase1_constants import ALLOWED_TAXONOMY, PLACEHOLDER_BARCODES


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def is_placeholder_barcode(barcode: str) -> bool:
    if barcode in PLACEHOLDER_BARCODES:
        return True
    if barcode.startswith("9000000000"):
        return True
    return False


def parse_json_list(value: Any) -> bool:
    if value in (None, ""):
        return True
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except Exception:
        return False
    return isinstance(parsed, list)


def main() -> int:
    parser = argparse.ArgumentParser(description="SafeBite Phase 1 backend validation")
    parser.add_argument("--db", required=True, help="Path to safebite.db")
    args = parser.parse_args()

    conn = connect(args.db)
    errors = []
    warnings = []
    invalid_gtins = []
    placeholder_barcodes = []

    try:
        products = conn.execute(
            """
            SELECT barcode, name, category, subcategory, ingredients, allergens
            FROM products
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()

        barcode_counts = conn.execute(
            """
            SELECT barcode, COUNT(*) AS count
            FROM products
            GROUP BY barcode
            HAVING COUNT(*) > 1
            """
        ).fetchall()
        for row in barcode_counts:
            errors.append("duplicate product barcode in DB: {0}".format(row["barcode"]))

        for row in products:
            barcode = str(row["barcode"] or "").strip()
            name = str(row["name"] or "").strip()
            category = str(row["category"] or "").strip()
            subcategory = str(row["subcategory"] or "").strip()

            if not barcode:
                errors.append("product missing barcode: {0}".format(name or "UNKNOWN"))
            elif is_placeholder_barcode(barcode):
                placeholder_barcodes.append("{0} | {1}".format(barcode, name))
            else:
                ok, detail = validate_gtin(barcode)
                if not ok:
                    invalid_gtins.append("{0} | {1} ({2})".format(barcode, name, detail))

            if not name:
                errors.append("product missing name: {0}".format(barcode or "UNKNOWN"))

            if not category:
                errors.append("blank category: {0} | {1}".format(barcode, name))
            elif category not in ALLOWED_TAXONOMY:
                errors.append("category outside locked taxonomy: {0} | {1} | {2}".format(barcode, name, category))

            if not subcategory:
                errors.append("blank subcategory: {0} | {1}".format(barcode, name))
            elif category in ALLOWED_TAXONOMY and subcategory not in ALLOWED_TAXONOMY[category]:
                errors.append("subcategory outside locked taxonomy: {0} | {1} | {2} / {3}".format(
                    barcode, name, category, subcategory
                ))

            if not str(row["ingredients"] or "").strip():
                errors.append("missing ingredients: {0} | {1}".format(barcode, name))

            if not parse_json_list(row["allergens"]):
                errors.append("allergens JSON invalid: {0} | {1}".format(barcode, name))

        offers = conn.execute(
            """
            SELECT id, barcode, retailer, price, promo_price, stock_status, in_stock, product_url
            FROM offers
            ORDER BY id
            """
        ).fetchall()

        for row in offers:
            offer_id = row["id"]
            barcode = str(row["barcode"] or "").strip()
            price = safe_float(row["price"])
            promo_price = safe_float(row["promo_price"])
            product_url = str(row["product_url"] or "").strip()

            exists = conn.execute(
                "SELECT 1 FROM products WHERE barcode = ? LIMIT 1",
                (barcode,),
            ).fetchone()
            if not exists:
                errors.append("orphan offer: barcode not found in products ({0})".format(barcode))

            if price is None or price <= 0:
                errors.append("invalid offer price: offer_id {0}".format(offer_id))

            if promo_price is not None and promo_price <= 0:
                errors.append("invalid promo_price: offer_id {0}".format(offer_id))

            if promo_price is not None and price is not None and promo_price > price:
                errors.append("promo_price greater than price: offer_id {0}".format(offer_id))

            if not product_url.startswith(("http://", "https://")):
                errors.append("invalid product_url: offer_id {0}".format(offer_id))

        print("PHASE 1 VALIDATION REPORT")
        print("Products: {0}".format(len(products)))
        print("Offers: {0}".format(len(offers)))
        print("Validation warnings: {0}".format(len(warnings)))
        print("Validation errors: {0}".format(len(errors)))
        print("GTIN audit invalid_existing_count: {0}".format(len(invalid_gtins)))
        print("Placeholder audit existing_count: {0}".format(len(placeholder_barcodes)))
        if placeholder_barcodes:
            print("Placeholder audit note: existing legacy sample rows are reported for replacement, not blocked here.")
            for item in placeholder_barcodes[:10]:
                print("- {0}".format(item))
            if len(placeholder_barcodes) > 10:
                print("- ... {0} more".format(len(placeholder_barcodes) - 10))
        if invalid_gtins:
            print("GTIN audit note: existing rows are reported for phased cleanup, not blocked here.")
            for item in invalid_gtins[:10]:
                print("- {0}".format(item))
            if len(invalid_gtins) > 10:
                print("- ... {0} more".format(len(invalid_gtins) - 10))
        print("")

        if warnings:
            print("Warnings")
            for item in warnings:
                print("- {0}".format(item))
            print("")

        if errors:
            print("Errors")
            for item in errors:
                print("- {0}".format(item))
            print("")
            print("Validation status: FAIL")
            return 1

        print("Validation status: PASS")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
