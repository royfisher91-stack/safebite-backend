#!/usr/bin/env python3
import argparse
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
DB_DEFAULT = BACKEND_DIR / "safebite.db"
DOC_DEFAULT = PROJECT_DIR / "docs" / "data" / "product_volume_status.md"

ACTIVE_RETAILERS = ["Tesco", "Asda", "Sainsbury's", "Waitrose", "Ocado", "Iceland", "Morrisons"]
FUTURE_RETAILERS = ["M&S", "Aldi", "Lidl", "Farmfoods", "Home Bargains", "B&M", "Heron"]

UNKNOWN_VALUES = {
    "",
    "unknown",
    "data unavailable",
    "data_unavailable",
    "null",
    "none",
    "[]",
    '["unknown"]',
    "['unknown']",
}


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def fetch_all(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
    return [row_to_dict(row) for row in conn.execute(sql, tuple(params)).fetchall()]


def fetch_one(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> Dict[str, Any]:
    row = conn.execute(sql, tuple(params)).fetchone()
    return row_to_dict(row) if row else {}


def fetch_count(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> int:
    row = conn.execute(sql, tuple(params)).fetchone()
    if not row:
        return 0
    return int(row[0] or 0)


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    return text in UNKNOWN_VALUES


def pct(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round((part / float(whole)) * 100.0, 1)


def build_availability_rows(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    if table_exists(conn, "offers"):
        offer_rows = fetch_all(
            conn,
            """
            SELECT
                barcode,
                retailer,
                COALESCE(NULLIF(stock_status, ''), CASE WHEN in_stock = 1 THEN 'in_stock' ELSE 'out_of_stock' END) AS stock_status,
                COALESCE(NULLIF(product_url, ''), NULLIF(url, '')) AS product_url,
                'offers' AS source_table
            FROM offers
            """,
        )
        rows.extend(offer_rows)

    if table_exists(conn, "retailer_offers"):
        retailer_offer_rows = fetch_all(
            conn,
            """
            SELECT
                barcode,
                retailer,
                COALESCE(stock_status, 'unknown') AS stock_status,
                product_url,
                'retailer_offers' AS source_table
            FROM retailer_offers
            """,
        )
        rows.extend(retailer_offer_rows)

    return rows


def count_by(items: Iterable[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "Unknown").strip() or "Unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts


def distinct_products_by_retailer(availability_rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    seen: Dict[str, set] = {}
    for row in availability_rows:
        retailer = str(row.get("retailer") or "Unknown").strip() or "Unknown"
        barcode = str(row.get("barcode") or "").strip()
        if not barcode:
            continue
        seen.setdefault(retailer, set()).add(barcode)
    return {retailer: len(barcodes) for retailer, barcodes in seen.items()}


def product_retailer_counts(availability_rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    seen: Dict[str, set] = {}
    for row in availability_rows:
        barcode = str(row.get("barcode") or "").strip()
        retailer = str(row.get("retailer") or "").strip()
        if not barcode or not retailer:
            continue
        seen.setdefault(barcode, set()).add(retailer)
    return {barcode: len(retailers) for barcode, retailers in seen.items()}


def bucket_product_coverage(total_products: int, retailer_counts: Dict[str, int]) -> Dict[str, int]:
    one = 0
    two_three = 0
    four_plus = 0
    zero = max(total_products - len(retailer_counts), 0)
    for count in retailer_counts.values():
        if count == 1:
            one += 1
        elif 2 <= count <= 3:
            two_three += 1
        elif count >= 4:
            four_plus += 1
    return {
        "0 retailers": zero,
        "1 retailer": one,
        "2-3 retailers": two_three,
        "4+ retailers": four_plus,
    }


def build_report(db_path: Path = DB_DEFAULT) -> Dict[str, Any]:
    if not db_path.exists():
        return {
            "database_found": False,
            "database_path": str(db_path),
            "summary": {},
            "recommendations": {},
        }

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        total_products = fetch_count(conn, "SELECT COUNT(*) FROM products") if table_exists(conn, "products") else 0
        total_offers = fetch_count(conn, "SELECT COUNT(*) FROM offers") if table_exists(conn, "offers") else 0
        total_retailer_offers = (
            fetch_count(conn, "SELECT COUNT(*) FROM retailer_offers")
            if table_exists(conn, "retailer_offers")
            else 0
        )
        availability_rows = build_availability_rows(conn)
        combined_availability = len(availability_rows)
        retailer_counts = product_retailer_counts(availability_rows)
        coverage_buckets = bucket_product_coverage(total_products, retailer_counts)

        products = fetch_all(
            conn,
            """
            SELECT barcode, name, category, subcategory, ingredients, allergens
            FROM products
            ORDER BY category COLLATE NOCASE, subcategory COLLATE NOCASE, name COLLATE NOCASE
            """,
        ) if table_exists(conn, "products") else []

        category_breakdown = fetch_all(
            conn,
            """
            SELECT
                COALESCE(NULLIF(category, ''), 'Unknown') AS category,
                COALESCE(NULLIF(subcategory, ''), 'Unknown') AS subcategory,
                COUNT(*) AS product_count
            FROM products
            GROUP BY COALESCE(NULLIF(category, ''), 'Unknown'), COALESCE(NULLIF(subcategory, ''), 'Unknown')
            ORDER BY product_count ASC, category COLLATE NOCASE, subcategory COLLATE NOCASE
            """,
        ) if table_exists(conn, "products") else []

        missing_ingredients = sum(1 for product in products if is_missing(product.get("ingredients")))
        missing_allergens = sum(1 for product in products if is_missing(product.get("allergens")))
        unknown_stock = sum(1 for row in availability_rows if is_missing(row.get("stock_status")))
        missing_urls = sum(1 for row in availability_rows if is_missing(row.get("product_url")))

        offers_per_retailer = []
        offer_row_counts = count_by(availability_rows, "retailer")
        distinct_counts = distinct_products_by_retailer(availability_rows)
        all_retailers = sorted(set(ACTIVE_RETAILERS + FUTURE_RETAILERS + list(offer_row_counts.keys())))
        for retailer in all_retailers:
            product_count = int(distinct_counts.get(retailer, 0))
            offers_per_retailer.append(
                {
                    "retailer": retailer,
                    "offer_rows": int(offer_row_counts.get(retailer, 0)),
                    "distinct_products": product_count,
                    "coverage_percent": pct(product_count, total_products),
                    "phase": "active" if retailer in ACTIVE_RETAILERS else "future-compatible",
                }
            )

        retailer_offer_table_rows = fetch_all(
            conn,
            """
            SELECT retailer, COUNT(*) AS offer_count, COUNT(DISTINCT barcode) AS product_count
            FROM retailer_offers
            GROUP BY retailer
            ORDER BY retailer COLLATE NOCASE
            """,
        ) if table_exists(conn, "retailer_offers") else []

        phase12_batch_stats = (
            fetch_one(
                conn,
                """
                SELECT
                    COUNT(*) AS batch_count,
                    COALESCE(SUM(rows_total), 0) AS rows_total,
                    COALESCE(SUM(rows_imported), 0) AS rows_imported,
                    COALESCE(SUM(rows_skipped), 0) AS rows_skipped,
                    COALESCE(SUM(errors_count), 0) AS errors_count
                FROM product_import_batches
                """,
            )
            if table_exists(conn, "product_import_batches")
            else {}
        )
        phase12_batches_by_retailer = (
            fetch_all(
                conn,
                """
                SELECT
                    COALESCE(retailer, 'Unknown') AS retailer,
                    COALESCE(status, 'unknown') AS status,
                    COUNT(*) AS batch_count,
                    COALESCE(SUM(rows_total), 0) AS rows_total,
                    COALESCE(SUM(rows_imported), 0) AS rows_imported,
                    COALESCE(SUM(rows_skipped), 0) AS rows_skipped,
                    COALESCE(SUM(errors_count), 0) AS errors_count
                FROM product_import_batches
                GROUP BY COALESCE(retailer, 'Unknown'), COALESCE(status, 'unknown')
                ORDER BY retailer COLLATE NOCASE, status COLLATE NOCASE
                """,
            )
            if table_exists(conn, "product_import_batches")
            else []
        )
        phase12_error_count = (
            fetch_count(conn, "SELECT COUNT(*) FROM product_import_errors")
            if table_exists(conn, "product_import_errors")
            else 0
        )

        staging_batch_stats = (
            fetch_one(
                conn,
                """
                SELECT
                    COUNT(*) AS batch_count,
                    COALESCE(SUM(row_count), 0) AS rows_total,
                    COALESCE(SUM(accepted_count), 0) AS accepted_count,
                    COALESCE(SUM(rejected_count), 0) AS rejected_count,
                    COALESCE(SUM(warning_count), 0) AS warning_count,
                    COALESCE(SUM(error_count), 0) AS error_count
                FROM bulk_intake_batches
                """,
            )
            if table_exists(conn, "bulk_intake_batches")
            else {}
        )
        staging_batches_by_status = (
            fetch_all(
                conn,
                """
                SELECT
                    COALESCE(status, 'unknown') AS status,
                    COUNT(*) AS batch_count,
                    COALESCE(SUM(row_count), 0) AS rows_total,
                    COALESCE(SUM(accepted_count), 0) AS accepted_count,
                    COALESCE(SUM(rejected_count), 0) AS rejected_count,
                    COALESCE(SUM(warning_count), 0) AS warning_count,
                    COALESCE(SUM(error_count), 0) AS error_count
                FROM bulk_intake_batches
                GROUP BY COALESCE(status, 'unknown')
                ORDER BY status COLLATE NOCASE
                """,
            )
            if table_exists(conn, "bulk_intake_batches")
            else []
        )

        weakest_category = category_breakdown[0] if category_breakdown else {}
        active_retailer_rows = [row for row in offers_per_retailer if row["phase"] == "active"]
        weakest_retailer = min(
            active_retailer_rows,
            key=lambda row: (int(row["distinct_products"]), int(row["offer_rows"]), row["retailer"]),
        ) if active_retailer_rows else {}
        next_batch_priority = build_next_batch_priority(weakest_category, weakest_retailer)

        return {
            "database_found": True,
            "database_path": str(db_path),
            "summary": {
                "total_products": total_products,
                "total_offers": total_offers,
                "total_retailer_offers": total_retailer_offers,
                "combined_availability_footprint": combined_availability,
                "missing_ingredients": missing_ingredients,
                "missing_allergens": missing_allergens,
                "unknown_stock": unknown_stock,
                "missing_urls": missing_urls,
            },
            "category_breakdown": category_breakdown,
            "offers_per_retailer": offers_per_retailer,
            "retailer_offer_table_rows": retailer_offer_table_rows,
            "coverage_buckets": coverage_buckets,
            "phase12_batch_stats": phase12_batch_stats,
            "phase12_batches_by_retailer": phase12_batches_by_retailer,
            "phase12_error_count": phase12_error_count,
            "staging_batch_stats": staging_batch_stats,
            "staging_batches_by_status": staging_batches_by_status,
            "recommendations": {
                "weakest_category": weakest_category,
                "weakest_retailer": weakest_retailer,
                "next_batch_priority": next_batch_priority,
            },
        }
    finally:
        conn.close()


def build_next_batch_priority(weakest_category: Dict[str, Any], weakest_retailer: Dict[str, Any]) -> str:
    category = weakest_category.get("category") or "lowest-stocked category"
    subcategory = weakest_category.get("subcategory") or "lowest-stocked subcategory"
    retailer = weakest_retailer.get("retailer") or "lowest-coverage active retailer"
    return (
        "Prioritise a verified {0} / {1} batch for {2}. Keep using approved CSV/feed/API/manual sources only, "
        "and promote only after validation has zero errors, blocked rows, malformed rows, and duplicates."
    ).format(category, subcategory, retailer)


def format_table(rows: List[Dict[str, Any]], columns: List[Tuple[str, str]]) -> List[str]:
    if not rows:
        return ["- none"]
    header = "| " + " | ".join(label for label, _key in columns) + " |"
    divider = "| " + " | ".join("---" for _label, _key in columns) + " |"
    lines = [header, divider]
    for row in rows:
        values = []
        for _label, key in columns:
            value = row.get(key)
            values.append(str(value if value is not None else ""))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# SafeBite Product Volume Status",
        "",
        "This tracker is read-only. It measures product volume, retailer coverage, and import-batch health without changing app logic, safety scoring, billing, frontend, mobile, or backend routes.",
        "",
        "Run from the backend folder:",
        "",
        "```bash",
        "./.venv/bin/python scripts/product_volume_tracker.py",
        "./.venv/bin/python scripts/product_volume_tracker.py --write-markdown ../docs/data/product_volume_status.md",
        "```",
        "",
    ]

    if not report.get("database_found"):
        lines.extend([
            "## Current Snapshot",
            "",
            "Database not found: `{0}`".format(report.get("database_path") or ""),
            "",
        ])
        return "\n".join(lines).rstrip() + "\n"

    summary = report["summary"]
    lines.extend([
        "## Current Snapshot",
        "",
        "- Database: `{0}`".format(report["database_path"]),
        "- Total products: {0}".format(summary["total_products"]),
        "- Total legacy offers: {0}".format(summary["total_offers"]),
        "- Total retailer_offers: {0}".format(summary["total_retailer_offers"]),
        "- Combined availability footprint: {0}".format(summary["combined_availability_footprint"]),
        "- Missing ingredients: {0}".format(summary["missing_ingredients"]),
        "- Missing allergens: {0}".format(summary["missing_allergens"]),
        "- Unknown stock rows: {0}".format(summary["unknown_stock"]),
        "- Missing URL rows: {0}".format(summary["missing_urls"]),
        "",
        "## Products Per Category",
        "",
    ])
    lines.extend(format_table(
        report["category_breakdown"],
        [("Category", "category"), ("Subcategory", "subcategory"), ("Products", "product_count")],
    ))
    lines.extend(["", "## Retailer Coverage", ""])
    lines.extend(format_table(
        report["offers_per_retailer"],
        [
            ("Retailer", "retailer"),
            ("Phase", "phase"),
            ("Offer rows", "offer_rows"),
            ("Distinct products", "distinct_products"),
            ("Product coverage %", "coverage_percent"),
        ],
    ))
    lines.extend(["", "## Retailer Offers Table", ""])
    lines.extend(format_table(
        report["retailer_offer_table_rows"],
        [("Retailer", "retailer"), ("Retailer offer rows", "offer_count"), ("Products", "product_count")],
    ))
    lines.extend(["", "## Product Retailer Spread", ""])
    for label, value in report["coverage_buckets"].items():
        lines.append("- {0}: {1}".format(label, value))

    phase12 = report["phase12_batch_stats"] or {}
    staging = report["staging_batch_stats"] or {}
    lines.extend([
        "",
        "## Batch Import Stats",
        "",
        "Phase 12 retailer importer:",
        "",
        "- Batch count: {0}".format(phase12.get("batch_count", 0)),
        "- Rows total: {0}".format(phase12.get("rows_total", 0)),
        "- Rows imported: {0}".format(phase12.get("rows_imported", 0)),
        "- Rows skipped: {0}".format(phase12.get("rows_skipped", 0)),
        "- Errors count: {0}".format(phase12.get("errors_count", 0)),
        "- Logged product_import_errors rows: {0}".format(report["phase12_error_count"]),
        "",
    ])
    lines.extend(format_table(
        report["phase12_batches_by_retailer"],
        [
            ("Retailer", "retailer"),
            ("Status", "status"),
            ("Batches", "batch_count"),
            ("Rows", "rows_total"),
            ("Imported", "rows_imported"),
            ("Skipped", "rows_skipped"),
            ("Errors", "errors_count"),
        ],
    ))
    lines.extend([
        "",
        "Controlled staging intake:",
        "",
        "- Batch count: {0}".format(staging.get("batch_count", 0)),
        "- Rows total: {0}".format(staging.get("rows_total", 0)),
        "- Accepted rows: {0}".format(staging.get("accepted_count", 0)),
        "- Rejected rows: {0}".format(staging.get("rejected_count", 0)),
        "- Warnings: {0}".format(staging.get("warning_count", 0)),
        "- Errors: {0}".format(staging.get("error_count", 0)),
        "",
    ])
    lines.extend(format_table(
        report["staging_batches_by_status"],
        [
            ("Status", "status"),
            ("Batches", "batch_count"),
            ("Rows", "rows_total"),
            ("Accepted", "accepted_count"),
            ("Rejected", "rejected_count"),
            ("Warnings", "warning_count"),
            ("Errors", "error_count"),
        ],
    ))

    recommendations = report["recommendations"]
    weakest_category = recommendations["weakest_category"] or {}
    weakest_retailer = recommendations["weakest_retailer"] or {}
    lines.extend([
        "",
        "## Recommendations",
        "",
        "- Weakest category: {0} / {1} ({2} product(s))".format(
            weakest_category.get("category", "n/a"),
            weakest_category.get("subcategory", "n/a"),
            weakest_category.get("product_count", 0),
        ),
        "- Weakest active retailer: {0} ({1} distinct product(s), {2} offer row(s))".format(
            weakest_retailer.get("retailer", "n/a"),
            weakest_retailer.get("distinct_products", 0),
            weakest_retailer.get("offer_rows", 0),
        ),
        "- Next batch priority: {0}".format(recommendations["next_batch_priority"]),
        "",
        "Future-compatible retailers are tracked for readiness, but they are not treated as current phase blockers.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def print_report(report: Dict[str, Any]) -> None:
    print(render_markdown(report))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track SafeBite product volume and retailer coverage.")
    parser.add_argument("--db", default=str(DB_DEFAULT), help="Path to safebite SQLite database.")
    parser.add_argument(
        "--write-markdown",
        nargs="?",
        const=str(DOC_DEFAULT),
        default=None,
        help="Write the rendered status report to the given path, or the default docs/data path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(Path(args.db))
    markdown = render_markdown(report)
    print(markdown)
    if args.write_markdown:
        output_path = Path(args.write_markdown)
        if not output_path.is_absolute():
            output_path = BACKEND_DIR / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print("Wrote product volume status: {0}".format(output_path))
    return 0 if report.get("database_found") else 1


if __name__ == "__main__":
    raise SystemExit(main())
