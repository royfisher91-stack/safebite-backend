#!/usr/bin/env python3
"""
Final weak-row review for SafeBite Phase 1 Data Upgrade.

Run from the project root:
    backend/.venv/bin/python scripts/review_weak_rows.py

Outputs:
    reports/weak_rows_ranked.csv
    reports/weak_rows_ranked.json

The script is read-only for SafeBite data. It reads backend/safebite.db and
writes report files only; it does not modify products, offers, schema, or code.
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "backend" / "safebite.db"
REPORT_DIR = PROJECT_ROOT / "reports"
CSV_REPORT = REPORT_DIR / "weak_rows_ranked.csv"
JSON_REPORT = REPORT_DIR / "weak_rows_ranked.json"

TARGET_SUBCATEGORIES = {
    "Formula Milk",
    "Fruit Puree",
    "Porridge",
    "Baby Meals",
}

WEIGHTS = {
    "placeholder_barcode": 35,
    "sample_name": 35,
    "sample_offer_url": 25,
    "legacy_barcode": 20,
    "missing_brand": 15,
    "no_offers": 15,
    "missing_ingredients": 12,
    "thin_ingredients": 8,
    "thin_reasoning": 8,
    "seed_source": 8,
    "missing_weight_or_pack_size": 6,
    "missing_source": 5,
}

PLACEHOLDER_BARCODE_PATTERNS = [
    re.compile(r"^9000+"),
    re.compile(r"^0000+"),
    re.compile(r"^9999+"),
]

LEGACY_BARCODE_PATTERNS = [
    re.compile(r"^12345"),
]

SAMPLE_NAME_PATTERNS = [
    re.compile(r"\bsample\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bexample\b", re.IGNORECASE),
    re.compile(r"\bdemo\b", re.IGNORECASE),
    re.compile(r"\btest product\b", re.IGNORECASE),
]

PACK_SIZE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:g|gram|grams|kg|ml|l|litre|litres|oz)\b",
    re.IGNORECASE,
)

SAMPLE_URL_PATTERNS = [
    re.compile(r"/example", re.IGNORECASE),
    re.compile(r"example\d*", re.IGNORECASE),
    re.compile(r"placeholder", re.IGNORECASE),
    re.compile(r"sample", re.IGNORECASE),
]


@dataclass
class WeakRow:
    rank: int
    barcode: str
    name: str
    brand: str
    category: str
    subcategory: str
    score: int
    priority: str
    reasons: list[str]
    offer_count: int
    retailers: list[str]
    source: str
    source_retailer: str


def normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_jsonish_list(value: Any) -> list[str]:
    text = normalize(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return [part.strip() for part in re.split(r"[,;]", text) if part.strip()]
    if isinstance(parsed, list):
        return [normalize(item) for item in parsed if normalize(item)]
    if isinstance(parsed, str):
        return [parsed]
    return []


def has_pattern(patterns: list[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def matches_barcode(patterns: list[re.Pattern[str]], barcode: str) -> bool:
    return any(pattern.match(barcode) for pattern in patterns)


def priority_for(score: int) -> str:
    if score >= 60:
        return "replace first"
    if score >= 35:
        return "replace soon"
    if score >= 20:
        return "review"
    if score > 0:
        return "low priority"
    return "clean"


def fetch_offers(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT barcode, retailer, price, product_url, url
        FROM offers
        """
    ).fetchall()

    by_barcode: dict[str, dict[str, Any]] = {}
    for row in rows:
        barcode = normalize(row["barcode"])
        entry = by_barcode.setdefault(
            barcode,
            {
                "count": 0,
                "retailers": set(),
                "urls": [],
                "sample_url_count": 0,
            },
        )
        entry["count"] += 1
        retailer = normalize(row["retailer"])
        if retailer:
            entry["retailers"].add(retailer)
        url = normalize(row["product_url"]) or normalize(row["url"])
        if url:
            entry["urls"].append(url)
            if has_pattern(SAMPLE_URL_PATTERNS, url):
                entry["sample_url_count"] += 1

    for entry in by_barcode.values():
        entry["retailers"] = sorted(entry["retailers"])
    return by_barcode


def score_product(row: sqlite3.Row, offer_info: dict[str, Any]) -> tuple[int, list[str]]:
    barcode = normalize(row["barcode"])
    name = normalize(row["name"])
    brand = normalize(row["brand"])
    ingredients = load_jsonish_list(row["ingredients"])
    reasoning = normalize(row["ingredient_reasoning"])
    source = normalize(row["source"])
    source_retailer = normalize(row["source_retailer"])

    score = 0
    reasons: list[str] = []

    if matches_barcode(PLACEHOLDER_BARCODE_PATTERNS, barcode):
        score += WEIGHTS["placeholder_barcode"]
        reasons.append("placeholder barcode pattern")

    if matches_barcode(LEGACY_BARCODE_PATTERNS, barcode):
        score += WEIGHTS["legacy_barcode"]
        reasons.append("legacy barcode pattern")

    if has_pattern(SAMPLE_NAME_PATTERNS, name):
        score += WEIGHTS["sample_name"]
        reasons.append("sample/example wording in name")

    if not brand:
        score += WEIGHTS["missing_brand"]
        reasons.append("missing brand")

    if not ingredients:
        score += WEIGHTS["missing_ingredients"]
        reasons.append("missing ingredients")
    elif len(ingredients) <= 2:
        score += WEIGHTS["thin_ingredients"]
        reasons.append("thin ingredient list")

    if not reasoning or len(reasoning) < 50:
        score += WEIGHTS["thin_reasoning"]
        reasons.append("thin ingredient reasoning")

    if source.lower() in {"products_json_seed", "seed", "sample_seed"} or source_retailer.lower() == "safebite":
        score += WEIGHTS["seed_source"]
        reasons.append("seed/sample source")

    if not source:
        score += WEIGHTS["missing_source"]
        reasons.append("missing source")

    if not PACK_SIZE_PATTERN.search(name):
        score += WEIGHTS["missing_weight_or_pack_size"]
        reasons.append("missing visible weight/pack size in name")

    if offer_info["count"] == 0:
        score += WEIGHTS["no_offers"]
        reasons.append("no retailer offers")

    if offer_info["sample_url_count"]:
        score += WEIGHTS["sample_offer_url"]
        reasons.append("sample/example retailer URL")

    return score, reasons


def build_report(conn: sqlite3.Connection) -> list[WeakRow]:
    offers_by_barcode = fetch_offers(conn)
    rows = conn.execute(
        """
        SELECT barcode, name, brand, category, subcategory, ingredients,
               ingredient_reasoning, source, source_retailer
        FROM products
        WHERE subcategory IN (?, ?, ?, ?)
        ORDER BY subcategory, name, barcode
        """,
        tuple(sorted(TARGET_SUBCATEGORIES)),
    ).fetchall()

    scored: list[WeakRow] = []
    for row in rows:
        barcode = normalize(row["barcode"])
        offer_info = offers_by_barcode.get(
            barcode,
            {
                "count": 0,
                "retailers": [],
                "urls": [],
                "sample_url_count": 0,
            },
        )
        score, reasons = score_product(row, offer_info)
        scored.append(
            WeakRow(
                rank=0,
                barcode=barcode,
                name=normalize(row["name"]),
                brand=normalize(row["brand"]),
                category=normalize(row["category"]),
                subcategory=normalize(row["subcategory"]),
                score=score,
                priority=priority_for(score),
                reasons=reasons,
                offer_count=int(offer_info["count"]),
                retailers=list(offer_info["retailers"]),
                source=normalize(row["source"]),
                source_retailer=normalize(row["source_retailer"]),
            )
        )

    scored.sort(key=lambda item: (-item.score, item.subcategory, item.name, item.barcode))
    for index, item in enumerate(scored, start=1):
        item.rank = index
    return scored


def write_reports(rows: list[WeakRow]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "rank",
                "barcode",
                "name",
                "brand",
                "category",
                "subcategory",
                "score",
                "priority",
                "reasons",
                "offer_count",
                "retailers",
                "source",
                "source_retailer",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.rank,
                    row.barcode,
                    row.name,
                    row.brand,
                    row.category,
                    row.subcategory,
                    row.score,
                    row.priority,
                    "; ".join(row.reasons),
                    row.offer_count,
                    ", ".join(row.retailers),
                    row.source,
                    row.source_retailer,
                ]
            )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": str(DB_PATH),
        "target_subcategories": sorted(TARGET_SUBCATEGORIES),
        "rows": [asdict(row) for row in rows],
    }
    JSON_REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_summary(rows: list[WeakRow]) -> None:
    print("\n=== SafeBite weak-row review ===\n")
    print(f"Database: {DB_PATH}")
    print(f"Rows reviewed: {len(rows)}")
    print(f"Report CSV: {CSV_REPORT}")
    print(f"Report JSON: {JSON_REPORT}\n")

    actionable = [row for row in rows if row.score >= 20]
    if not actionable:
        print("No high-priority weak rows found in the four active subcategories.")
        print("Showing the highest-scoring low-priority rows for human review:\n")
        display_rows = rows[:10]
    else:
        print("Ranked weak rows to review or replace:\n")
        display_rows = actionable[:20]

    for row in display_rows:
        reason_text = ", ".join(row.reasons) if row.reasons else "no weakness detected"
        retailer_text = ", ".join(row.retailers) if row.retailers else "none"
        print(f"{row.rank}. {row.barcode} | {row.name} | {row.subcategory} | score={row.score} | {row.priority}")
        print(f"   Why weak: {reason_text}")
        print(f"   Offers: {row.offer_count} ({retailer_text})")

    replace_first = [row for row in rows if row.priority == "replace first"]
    replace_soon = [row for row in rows if row.priority == "replace soon"]
    review = [row for row in rows if row.priority == "review"]

    print("\nReplacement priority summary:")
    print(f"- Replace first: {len(replace_first)}")
    print(f"- Replace soon: {len(replace_soon)}")
    print(f"- Review: {len(review)}")
    print("- Modified data files: None")
    print("- Validation required: No, because this script does not modify SafeBite data")


def main() -> int:
    if not DB_PATH.exists():
        print(f"ERROR: Database not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = build_report(conn)
    finally:
        conn.close()

    write_reports(rows)
    print_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
