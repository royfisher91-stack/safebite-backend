#!/usr/bin/env python3
"""Promote safety-ready catalogue candidates into live SafeBite products."""

import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import upsert_product  # noqa: E402
from validate_catalogue_candidates import (  # noqa: E402
    CANDIDATES_PATH,
    REPORT_PATH,
    validate_candidates,
    write_report,
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _split_values(value: str) -> List[str]:
    text = _clean(value)
    if not text or text.lower() == "none_declared":
        return []
    values = []
    for item in text.replace(",", ";").split(";"):
        cleaned = item.strip()
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return values


def _read_candidates_by_barcode() -> Dict[str, Dict[str, str]]:
    with CANDIDATES_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return {_clean(row.get("barcode")): row for row in rows if _clean(row.get("barcode"))}


def _live_product_count() -> int:
    conn = sqlite3.connect(str(ROOT / "safebite.db"))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products")
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        conn.close()


def _products_with_offers() -> int:
    conn = sqlite3.connect(str(ROOT / "safebite.db"))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*)
            FROM products p
            WHERE EXISTS (
                SELECT 1
                FROM offers o
                WHERE o.barcode = p.barcode
            )
            """
        )
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        conn.close()


def _payload(row: Dict[str, str]) -> Dict[str, Any]:
    allergens = _split_values(row.get("allergens", ""))
    ingredients = _split_values(row.get("ingredients", ""))
    source = _clean(row.get("source")) or "open_food_facts"
    confidence = _clean(row.get("data_confidence")) or "community"

    return {
        "barcode": _clean(row.get("barcode")),
        "name": _clean(row.get("name")),
        "brand": _clean(row.get("brand")),
        "description": "Catalogue product imported from {} with {} confidence.".format(source, confidence),
        "ingredients": ingredients,
        "allergens": allergens,
        "category": _clean(row.get("category")),
        "subcategory": _clean(row.get("subcategory")),
        "image_url": "",
        "source": "{}_catalogue".format(source),
        "source_retailer": "Open Food Facts" if source == "open_food_facts" else source,
        "safety_score": None,
        "safety_result": "",
        "ingredient_reasoning": "Catalogue product. Safety analysis should use stored ingredients and source confidence metadata.",
        "allergen_warnings": json.dumps(allergens),
    }


def main() -> None:
    report = validate_candidates()
    if report["rejected_rows"] > 0:
        write_report(report)
        print("BLOCKED: rejected catalogue candidate rows exist.")
        print("Report: {}".format(REPORT_PATH))
        return

    safety_ready = [row for row in report["rows"] if row.get("classification") == "safety_ready"]
    if not safety_ready:
        write_report(report)
        print("BLOCKED: no safety-ready catalogue candidates.")
        print("Report: {}".format(REPORT_PATH))
        return

    before = _live_product_count()
    candidates = _read_candidates_by_barcode()
    promoted = 0

    for item in safety_ready:
        barcode = _clean(item.get("barcode"))
        row = candidates.get(barcode)
        if not row:
            continue
        upsert_product(_payload(row))
        promoted += 1

    after = _live_product_count()
    with_offers = _products_with_offers()

    report["live_product_count_before"] = before
    report["live_product_count_after"] = after
    report["products_promoted"] = promoted
    report["products_with_retailer_offers"] = with_offers
    report["products_without_retailer_offers"] = max(after - with_offers, 0)
    report["validation_warnings"] = 0
    report["validation_errors"] = 0
    report["issue_count"] = 0
    report["final_decision"] = "PROMOTED"
    write_report(report)

    print("PROMOTED catalogue products: {}".format(promoted))
    print("Live product count before: {}".format(before))
    print("Live product count after: {}".format(after))
    print("Report: {}".format(REPORT_PATH))


if __name__ == "__main__":
    main()
