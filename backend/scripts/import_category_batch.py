from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.bulk_import_service import DB_DEFAULT, import_retailer_csv, normalise_retailer
from services.gtin_service import normalise_barcode


CATEGORY_FILES = {
    "baby_formula",
    "baby_meals",
    "baby_porridge",
    "fruit_puree",
    "baby_snacks",
    "toddler_yoghurt",
    "household_cleaning",
    "laundry",
    "dishwasher",
    "surface_cleaners",
}


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalise_missing(value: object) -> str:
    text = clean(value).lower()
    if text in {"", "unknown", "data unavailable", "unavailable", "null", "none", "[]"}:
        return ""
    raw = clean(value)
    try:
        parsed = json.loads(raw)
    except Exception:
        return raw
    if isinstance(parsed, list):
        cleaned = [
            clean(item)
            for item in parsed
            if clean(item).lower() not in {"", "unknown", "data unavailable", "unavailable", "null", "none"}
        ]
        return "; ".join(cleaned)
    return raw


def run_validator(csv_path: Path) -> int:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "validate_real_product_batch.py"),
        "--csv",
        str(csv_path),
    ]
    completed = subprocess.run(command, cwd=str(BACKEND_DIR))
    return int(completed.returncode)


def read_rows(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def existing_product(conn: sqlite3.Connection, barcode: str) -> Dict[str, Any]:
    row = conn.execute(
        """
        SELECT barcode, ingredients, allergens, data_quality_status
        FROM products
        WHERE barcode = ?
        """,
        (barcode,),
    ).fetchone()
    return dict(row) if row else {}


def count_expected_changes(csv_path: Path, retailer: str, db_path: str) -> Tuple[Dict[str, int], List[str]]:
    rows = read_rows(csv_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    summary = {
        "rows_total": 0,
        "new_products": 0,
        "existing_products": 0,
        "new_retailer_offers": 0,
        "existing_retailer_offers": 0,
        "quality_blocks": 0,
    }
    blockers: List[str] = []
    canonical = normalise_retailer(retailer)

    try:
        for index, row in enumerate(rows, start=2):
            if not any(clean(value) for value in row.values()):
                continue
            summary["rows_total"] += 1
            barcode = normalise_barcode(row.get("barcode"))
            product = existing_product(conn, barcode)
            if product:
                summary["existing_products"] += 1
            else:
                summary["new_products"] += 1

            incoming_ingredients = normalise_missing(row.get("ingredients"))
            incoming_allergens = normalise_missing(row.get("allergens"))
            existing_ingredients = normalise_missing(product.get("ingredients"))
            existing_allergens = normalise_missing(product.get("allergens"))

            if product and existing_ingredients and not incoming_ingredients:
                summary["quality_blocks"] += 1
                blockers.append("row {0}: incoming ingredients would downgrade existing product data".format(index))
            if product and existing_allergens and not incoming_allergens:
                summary["quality_blocks"] += 1
                blockers.append("row {0}: incoming allergens would downgrade existing product data".format(index))

            offer = conn.execute(
                """
                SELECT id
                FROM retailer_offers
                WHERE barcode = ? AND retailer = ? AND product_url = ?
                """,
                (barcode, canonical, clean(row.get("product_url"))),
            ).fetchone()
            if offer:
                summary["existing_retailer_offers"] += 1
            else:
                summary["new_retailer_offers"] += 1
    finally:
        conn.close()

    return summary, blockers


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and import a SafeBite retailer/category batch.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--retailer", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    category = clean(args.category)

    if category not in CATEGORY_FILES:
        print("Category batch import: BLOCKED")
        print("- reason: unsupported category file {0}".format(category))
        return 1

    if csv_path.name != "{0}.csv".format(category):
        print("Category batch import: BLOCKED")
        print("- reason: --category must match the CSV filename")
        return 1

    if not csv_path.exists():
        print("Category batch import: BLOCKED")
        print("- reason: CSV not found: {0}".format(csv_path))
        return 1

    print("Step 1: validating batch")
    validator_status = run_validator(csv_path)
    if validator_status != 0:
        print("Category batch import: BLOCKED")
        print("- reason: validator reported errors")
        return validator_status

    try:
        expected, blockers = count_expected_changes(csv_path, args.retailer, args.db)
    except Exception as exc:
        print("Category batch import: BLOCKED")
        print("- reason: expected-change analysis failed: {0}".format(exc))
        return 1

    print("Step 2: expected changes")
    print("- rows_total: {0}".format(expected["rows_total"]))
    print("- new_products: {0}".format(expected["new_products"]))
    print("- existing_products: {0}".format(expected["existing_products"]))
    print("- new_retailer_offers: {0}".format(expected["new_retailer_offers"]))
    print("- existing_retailer_offers: {0}".format(expected["existing_retailer_offers"]))
    print("- quality_blocks: {0}".format(expected["quality_blocks"]))

    if blockers:
        print("Category batch import: BLOCKED")
        print("- reason: incoming data could downgrade existing verified data")
        for blocker in blockers[:20]:
            print("- {0}".format(blocker))
        return 1

    if args.dry_run:
        print("Category batch import dry-run: PASS")
        return 0

    print("Step 3: running Phase 12 importer")
    try:
        summary = import_retailer_csv(
            csv_path=str(csv_path),
            retailer=args.retailer,
            db_path=args.db,
            dry_run=False,
        )
    except Exception as exc:
        print("Category batch import: FAILED")
        print("- reason: {0}".format(exc))
        return 1

    print("Category batch import result")
    print("- batch_id: {0}".format(summary["batch_id"]))
    print("- status: {0}".format(summary["status"]))
    print("- rows_total: {0}".format(summary["rows_total"]))
    print("- rows_imported: {0}".format(summary["rows_imported"]))
    print("- rows_skipped: {0}".format(summary["rows_skipped"]))
    print("- errors_count: {0}".format(summary["errors_count"]))
    if summary["errors"]:
        print("Skipped/error rows")
        for item in summary["errors"][:20]:
            print("- {0}".format(item))
    return 1 if summary["errors_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
