#!/usr/bin/env python3
"""Stage local Open Food Facts catalogue rows for SafeBite review."""

import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from import_utils import enforce_phase1_taxonomy  # noqa: E402
from services.gtin_service import normalise_barcode, validate_gtin  # noqa: E402


EXTERNAL_DIR = ROOT / "imports" / "external"
CSV_SOURCE = EXTERNAL_DIR / "open_food_facts_sample.csv"
JSONL_SOURCE = EXTERNAL_DIR / "open_food_facts_sample.jsonl"
CANDIDATES_PATH = ROOT / "imports" / "staged" / "open_food_facts_catalogue_candidates.csv"
DB_PATH = ROOT / "safebite.db"

CANDIDATE_COLUMNS = [
    "barcode",
    "name",
    "brand",
    "category",
    "subcategory",
    "ingredients",
    "allergens",
    "source",
    "source_url",
    "data_confidence",
    "needs_manual_review",
    "notes",
]

UK_MARKERS = {
    "uk",
    "gb",
    "united kingdom",
    "united-kingdom",
    "en:united-kingdom",
    "great britain",
}

NONE_DECLARED_MARKERS = {
    "none",
    "none_declared",
    "no allergens",
    "no declared allergens",
    "no known allergens",
    "free from declared allergens",
}


def _clean(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(" ".join(str(item or "").split()) for item in value if " ".join(str(item or "").split()))
    return " ".join(str(value or "").split())


def _clean_lower(value: Any) -> str:
    return _clean(value).lower()


def _first(row: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = _clean(row.get(key))
        if value:
            return value
    return ""


def _live_barcodes() -> Set[str]:
    if not DB_PATH.exists():
        return set()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute("SELECT barcode FROM products")
        return {normalise_barcode(row[0]) for row in cur.fetchall() if normalise_barcode(row[0])}
    finally:
        conn.close()


def _find_source() -> Optional[Path]:
    if CSV_SOURCE.exists():
        return CSV_SOURCE
    if JSONL_SOURCE.exists():
        return JSONL_SOURCE
    return None


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            item = json.loads(text)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _read_source(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return _read_jsonl(path)
    return _read_csv(path)


def _is_uk_relevant(row: Dict[str, Any]) -> bool:
    countries = " ".join(
        [
            _first(row, ["countries", "countries_en", "countries_tags"]),
            _first(row, ["stores", "stores_tags"]),
        ]
    ).lower()
    if not countries:
        return True
    return any(marker in countries for marker in UK_MARKERS)


def _normalise_allergens(value: str) -> str:
    text = _clean(value)
    if not text:
        return ""

    lower = text.lower().replace("-", "_")
    if lower in NONE_DECLARED_MARKERS:
        return "none_declared"

    parts = []
    for item in text.replace(",", ";").split(";"):
        cleaned = item.strip().lower()
        if not cleaned:
            continue
        if ":" in cleaned:
            cleaned = cleaned.split(":", 1)[1]
        cleaned = cleaned.replace("_", " ").strip()
        if cleaned and cleaned not in parts:
            parts.append(cleaned)
    return "; ".join(parts)


def _map_category(row: Dict[str, Any]) -> Tuple[str, str]:
    text = " ".join(
        [
            _first(row, ["product_name", "product_name_en", "name"]),
            _first(row, ["categories", "categories_en", "categories_tags"]),
        ]
    ).lower()

    if "baby" not in text and "toddler" not in text and "infant" not in text:
        return "General Food", "Uncategorised"

    subcategory = ""
    if any(term in text for term in ["formula", "infant milk"]):
        subcategory = "Formula Milk"
    elif any(term in text for term in ["toddler milk", "growing up milk"]):
        subcategory = "Toddler Milk"
    elif any(term in text for term in ["porridge", "cereal"]):
        subcategory = "Porridge"
    elif any(term in text for term in ["puree", "puree", "fruit pouch", "fruit pur"]):
        subcategory = "Fruit Puree"
    elif any(term in text for term in ["puff", "crisps"]):
        subcategory = "Baby Crisps & Puffs"
    elif any(term in text for term in ["oat bar", "snack", "wafer", "biscuit"]):
        subcategory = "Oat Snacks"
    elif any(term in text for term in ["meal", "pasta", "risotto", "bolognese", "casserole", "jar"]):
        subcategory = "Baby Meals"

    if not subcategory:
        return "General Food", "Uncategorised"

    category, mapped_subcategory = enforce_phase1_taxonomy("", subcategory)
    return category, mapped_subcategory


def _source_url(row: Dict[str, Any], barcode: str) -> str:
    url = _first(row, ["url", "source_url", "link"])
    if url:
        return url
    if barcode:
        return "https://world.openfoodfacts.org/product/{}".format(barcode)
    return ""


def _candidate_from_row(row: Dict[str, Any], live_barcodes: Set[str]) -> Optional[Dict[str, str]]:
    if not _is_uk_relevant(row):
        return None

    barcode = normalise_barcode(_first(row, ["code", "barcode", "gtin", "ean", "_id"]))
    if barcode in live_barcodes:
        return None

    name = _first(row, ["product_name", "product_name_en", "name"])
    brand = _first(row, ["brands", "brand", "brands_tags"])
    ingredients = _first(row, ["ingredients_text", "ingredients_text_en", "ingredients"])
    allergens = _normalise_allergens(_first(row, ["allergens", "allergens_en", "allergens_tags"]))
    category, subcategory = _map_category(row)

    notes: List[str] = []
    valid_gtin, gtin_message = validate_gtin(barcode)
    if not valid_gtin:
        notes.append(gtin_message)
    if not name:
        notes.append("product name missing")
    if category == "General Food" and subcategory == "Uncategorised":
        notes.append("no clean SafeBite subcategory mapped")
    elif not category or not subcategory:
        notes.append("category/subcategory missing")
    if not ingredients:
        notes.append("ingredients missing")
    if not allergens:
        notes.append("allergens missing or not explicitly declared")

    needs_manual_review = bool(notes)

    return {
        "barcode": barcode,
        "name": name,
        "brand": brand,
        "category": category,
        "subcategory": subcategory,
        "ingredients": ingredients,
        "allergens": allergens,
        "source": "open_food_facts",
        "source_url": _source_url(row, barcode),
        "data_confidence": "community",
        "needs_manual_review": "true" if needs_manual_review else "false",
        "notes": "; ".join(notes),
    }


def _write_candidates(rows: List[Dict[str, str]]) -> None:
    CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CANDIDATES_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CANDIDATE_COLUMNS})


def main() -> None:
    source = _find_source()
    if not source:
        _write_candidates([])
        print("No local Open Food Facts sample found.")
        print("Expected one of:")
        print("- {}".format(CSV_SOURCE))
        print("- {}".format(JSONL_SOURCE))
        print("Wrote header-only candidate file: {}".format(CANDIDATES_PATH))
        return

    raw_rows = _read_source(source)
    live_barcodes = _live_barcodes()
    candidates = []
    seen = set()

    for raw in raw_rows:
        candidate = _candidate_from_row(raw, live_barcodes)
        if not candidate:
            continue
        barcode = candidate.get("barcode", "")
        if barcode and barcode in seen:
            continue
        seen.add(barcode)
        candidates.append(candidate)

    _write_candidates(candidates)
    print("Source: {}".format(source))
    print("Raw rows read: {}".format(len(raw_rows)))
    print("Catalogue candidates staged: {}".format(len(candidates)))
    print("Candidate file: {}".format(CANDIDATES_PATH))


if __name__ == "__main__":
    main()
