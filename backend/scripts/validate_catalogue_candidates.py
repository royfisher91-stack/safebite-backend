#!/usr/bin/env python3
"""Validate staged SafeBite catalogue candidates."""

import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.gtin_service import normalise_barcode, validate_gtin  # noqa: E402


CANDIDATES_PATH = ROOT / "imports" / "staged" / "open_food_facts_catalogue_candidates.csv"
REPORT_PATH = PROJECT_ROOT / "docs" / "data" / "catalogue_volume_gate_report.md"
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

VALID_CONFIDENCE = {"community", "verified", "manual_verified"}
CATALOGUE_SOURCES = {"open_food_facts", "open_food_facts_catalogue", "licensed_catalogue"}
MIN_SAFETY_READY_FOR_PROMOTION = 25


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_lower(value: Any) -> str:
    return _clean(value).lower()


def _read_candidates() -> List[Dict[str, str]]:
    if not CANDIDATES_PATH.exists():
        return []
    with CANDIDATES_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _downloaded_candidate_count() -> int:
    source_path = ROOT / "imports" / "external" / "open_food_facts_sample.jsonl"
    if not source_path.exists():
        return 0
    with source_path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_count(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...] = ()) -> int:
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    if not row:
        return 0
    return int(row[0] or 0)


def _live_barcodes(conn: sqlite3.Connection) -> Set[str]:
    cur = conn.cursor()
    cur.execute("SELECT barcode FROM products")
    return {normalise_barcode(row[0]) for row in cur.fetchall() if normalise_barcode(row[0])}


def _live_counts(conn: sqlite3.Connection) -> Dict[str, int]:
    products_total = _fetch_count(conn, "SELECT COUNT(*) FROM products")
    products_with_offers = _fetch_count(
        conn,
        """
        SELECT COUNT(*)
        FROM products p
        WHERE EXISTS (
            SELECT 1
            FROM offers o
            WHERE o.barcode = p.barcode
        )
        """,
    )
    offers_total = _fetch_count(conn, "SELECT COUNT(*) FROM offers")
    return {
        "products_total": products_total,
        "products_with_offers": products_with_offers,
        "products_without_offers": max(products_total - products_with_offers, 0),
        "offers_total": offers_total,
    }


def _json_list(value: Any) -> List[Any]:
    text = _clean(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return []
    if isinstance(parsed, list):
        return parsed
    return []


def _is_catalogue_source(source: str) -> bool:
    return _clean_lower(source) in CATALOGUE_SOURCES


def _is_missing(value: Any) -> bool:
    text = _clean_lower(value)
    return not text or text in {"unknown", "data unavailable", "n/a", "none"}


def _starts_https(value: Any) -> bool:
    return _clean_lower(value).startswith("https://")


def _classify_row(
    row: Dict[str, str],
    row_number: int,
    live_barcodes: Set[str],
    staged_seen: Set[str],
    staged_duplicates: Set[str],
) -> Dict[str, Any]:
    barcode = normalise_barcode(row.get("barcode"))
    source = _clean_lower(row.get("source"))
    confidence = _clean_lower(row.get("data_confidence"))
    ingredients = _clean(row.get("ingredients"))
    allergens = _clean(row.get("allergens"))

    errors: List[str] = []
    review: List[str] = []

    valid_gtin, gtin_message = validate_gtin(barcode)
    if not valid_gtin:
        errors.append(gtin_message)

    if barcode in staged_seen or barcode in staged_duplicates:
        errors.append("duplicate barcode in candidate file")
    if barcode in live_barcodes:
        errors.append("barcode already exists in live products")

    if _is_missing(row.get("name")):
        errors.append("product name missing")
    if _is_missing(row.get("category")):
        errors.append("category missing")
    if _is_missing(row.get("subcategory")):
        errors.append("subcategory missing")
    if _is_missing(source):
        errors.append("source missing")
    elif not _is_catalogue_source(source):
        errors.append("unsupported catalogue source")
    if confidence and confidence not in VALID_CONFIDENCE:
        errors.append("unsupported data_confidence")

    if _is_missing(row.get("source_url")) or not _starts_https(row.get("source_url")):
        review.append("source_url missing or not https")
    if _is_missing(ingredients):
        review.append("ingredients missing")
    if _is_missing(allergens):
        review.append("allergens missing")

    manual_review_flag = _clean_lower(row.get("needs_manual_review")) in {"1", "true", "yes"}
    if manual_review_flag:
        review.append("needs_manual_review is true")

    if errors:
        classification = "rejected"
    elif review:
        classification = "needs_review"
    else:
        classification = "safety_ready"

    return {
        "row_number": row_number,
        "barcode": barcode,
        "name": _clean(row.get("name")),
        "classification": classification,
        "errors": errors,
        "review": review,
    }


def validate_candidates() -> Dict[str, Any]:
    rows = _read_candidates()
    conn = _connect()
    try:
        live_counts = _live_counts(conn)
        live_barcodes = _live_barcodes(conn)
        staged_counts: Dict[str, int] = {}
        for row in rows:
            barcode = normalise_barcode(row.get("barcode"))
            if barcode:
                staged_counts[barcode] = staged_counts.get(barcode, 0) + 1
        staged_duplicates = {barcode for barcode, count in staged_counts.items() if count > 1}

        seen: Set[str] = set()
        classified = []
        for index, row in enumerate(rows, start=2):
            result = _classify_row(row, index, live_barcodes, seen, staged_duplicates)
            barcode = result.get("barcode", "")
            if barcode:
                seen.add(str(barcode))
            classified.append(result)

        safety_ready = [row for row in classified if row["classification"] == "safety_ready"]
        needs_review = [row for row in classified if row["classification"] == "needs_review"]
        rejected = [row for row in classified if row["classification"] == "rejected"]

        report = {
            "live_product_count_before": live_counts["products_total"],
            "live_product_count_after": live_counts["products_total"],
            "candidates_downloaded": _downloaded_candidate_count(),
            "catalogue_candidates_staged": len(rows),
            "safety_ready_rows": len(safety_ready),
            "needs_review_rows": len(needs_review),
            "rejected_rows": len(rejected),
            "products_promoted": 0,
            "retailer_offers_before": live_counts["offers_total"],
            "retailer_offers_after": live_counts["offers_total"],
            "retailer_offers_unchanged": "yes",
            "products_with_retailer_offers": live_counts["products_with_offers"],
            "products_without_retailer_offers": live_counts["products_without_offers"],
            "validation_warnings": 0,
            "validation_errors": len(rejected),
            "issue_count": len(rejected),
            "final_decision": "BLOCKED",
            "promotion_gate": (
                "READY"
                if len(safety_ready) >= MIN_SAFETY_READY_FOR_PROMOTION and not rejected
                else "BLOCKED"
            ),
            "rows": classified,
        }
        return report
    finally:
        conn.close()


def write_report(report: Dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Catalogue Volume Gate Report",
        "",
        "## Summary",
        "",
        "- Live product count before: {}".format(report["live_product_count_before"]),
        "- Candidates downloaded: {}".format(report.get("candidates_downloaded", 0)),
        "- Catalogue candidates staged: {}".format(report["catalogue_candidates_staged"]),
        "- Safety-ready rows: {}".format(report["safety_ready_rows"]),
        "- Needs-review rows: {}".format(report["needs_review_rows"]),
        "- Rejected rows: {}".format(report["rejected_rows"]),
        "- Products promoted: {}".format(report["products_promoted"]),
        "- Live product count after: {}".format(report["live_product_count_after"]),
        "- Retailer offers before: {}".format(report.get("retailer_offers_before", 0)),
        "- Retailer offers after: {}".format(report.get("retailer_offers_after", 0)),
        "- Retailer offers unchanged: {}".format(report.get("retailer_offers_unchanged", "yes")),
        "- Products with retailer offers: {}".format(report["products_with_retailer_offers"]),
        "- Products without retailer offers: {}".format(report["products_without_retailer_offers"]),
        "- Validation warnings: {}".format(report["validation_warnings"]),
        "- Validation errors: {}".format(report["validation_errors"]),
        "- Issue count: {}".format(report["issue_count"]),
        "- Promotion gate: {}".format(report.get("promotion_gate", "BLOCKED")),
        "- Final decision: {}".format(report["final_decision"]),
        "",
        "## Row Details",
        "",
    ]

    if not report["rows"]:
        lines.append("- none")
    else:
        for row in report["rows"]:
            reasons = row.get("errors") or row.get("review") or []
            lines.append(
                "- Row {row_number}: {barcode} | {name} | {classification} | {reasons}".format(
                    row_number=row.get("row_number"),
                    barcode=row.get("barcode") or "",
                    name=row.get("name") or "",
                    classification=row.get("classification") or "",
                    reasons="; ".join(reasons) if reasons else "ready",
                )
            )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    report = validate_candidates()
    write_report(report)
    print("CATALOGUE CANDIDATE VALIDATION")
    print("=" * 80)
    print("Catalogue candidates staged: {}".format(report["catalogue_candidates_staged"]))
    print("Candidates downloaded: {}".format(report.get("candidates_downloaded", 0)))
    print("Safety-ready rows: {}".format(report["safety_ready_rows"]))
    print("Needs-review rows: {}".format(report["needs_review_rows"]))
    print("Rejected rows: {}".format(report["rejected_rows"]))
    print("Promotion gate: {}".format(report.get("promotion_gate", "BLOCKED")))
    print("Final decision: {}".format(report["final_decision"]))
    print("Report: {}".format(REPORT_PATH))


if __name__ == "__main__":
    main()
