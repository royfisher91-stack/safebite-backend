import sqlite3
from typing import Dict

from services.phase2_data_quality import ensure_phase2_tables


def _fetch_count(cursor: sqlite3.Cursor, query: str) -> int:
    cursor.execute(query)
    row = cursor.fetchone()
    return int(row[0] or 0)


def build_phase2_summary(db_path: str) -> Dict[str, object]:
    ensure_phase2_tables(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        summary = {}
        summary["products_total"] = _fetch_count(cursor, "SELECT COUNT(*) FROM products")
        summary["offers_total"] = _fetch_count(cursor, "SELECT COUNT(*) FROM offers")
        summary["quality_flag_total"] = _fetch_count(cursor, "SELECT COUNT(*) FROM product_quality_flags")
        summary["validation_issue_total"] = _fetch_count(cursor, "SELECT COUNT(*) FROM import_validation_issues")
        summary["validation_error_total"] = _fetch_count(cursor, "SELECT COUNT(*) FROM import_validation_issues WHERE severity = 'error'")
        summary["validation_warning_total"] = _fetch_count(cursor, "SELECT COUNT(*) FROM import_validation_issues WHERE severity = 'warning'")

        cursor.execute("""
            SELECT flag_name, COUNT(*) AS c
            FROM product_quality_flags
            GROUP BY flag_name
            ORDER BY c DESC, flag_name ASC
        """)
        summary["quality_flags_by_type"] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT severity, COUNT(*) AS c
            FROM import_validation_issues
            GROUP BY severity
            ORDER BY c DESC, severity ASC
        """)
        summary["validation_issues_by_severity"] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT code, COUNT(*) AS c
            FROM import_validation_issues
            GROUP BY code
            ORDER BY c DESC, code ASC
        """)
        summary["validation_issues_by_code"] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT p.category, p.subcategory, COUNT(*) AS product_count
            FROM products p
            GROUP BY p.category, p.subcategory
            ORDER BY p.category COLLATE NOCASE, p.subcategory COLLATE NOCASE
        """)
        summary["coverage_by_subcategory"] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT p.barcode, p.name, p.brand, p.category, p.subcategory,
                   COUNT(q.id) AS flag_count,
                   GROUP_CONCAT(DISTINCT q.flag_name) AS flags
            FROM products p
            LEFT JOIN product_quality_flags q ON p.barcode = q.barcode
            GROUP BY p.barcode, p.name, p.brand, p.category, p.subcategory
            HAVING flag_count >= 2
            ORDER BY flag_count DESC, p.name COLLATE NOCASE ASC
        """)
        summary["weak_products"] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT p.barcode, p.name, p.brand, p.category, p.subcategory
            FROM products p
            LEFT JOIN offers o ON p.barcode = o.barcode
            GROUP BY p.barcode, p.name, p.brand, p.category, p.subcategory
            HAVING COUNT(o.id) = 0
            ORDER BY p.name COLLATE NOCASE ASC
        """)
        summary["products_without_offers"] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT barcode, product_name, code, severity, message, field_name, retailer
            FROM import_validation_issues
            ORDER BY CASE severity WHEN 'error' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
                     code COLLATE NOCASE,
                     product_name COLLATE NOCASE
            LIMIT 25
        """)
        summary["top_validation_issues"] = [dict(row) for row in cursor.fetchall()]
        return summary
    finally:
        conn.close()


def render_phase2_text_report(summary: Dict[str, object]) -> str:
    lines = []
    lines.append("PHASE 2 DATA QUALITY REPORT")
    lines.append("=" * 35)
    lines.append("Products total: {0}".format(summary.get("products_total", 0)))
    lines.append("Offers total: {0}".format(summary.get("offers_total", 0)))
    lines.append("Quality flags total: {0}".format(summary.get("quality_flag_total", 0)))
    lines.append("Validation issues total: {0}".format(summary.get("validation_issue_total", 0)))
    lines.append("Validation errors: {0}".format(summary.get("validation_error_total", 0)))
    lines.append("Validation warnings: {0}".format(summary.get("validation_warning_total", 0)))
    lines.append("")

    lines.append("Validation issues by severity")
    for item in summary.get("validation_issues_by_severity", []):
        lines.append("- {0}: {1}".format(item["severity"], item["c"]))
    if not summary.get("validation_issues_by_severity"):
        lines.append("- none")
    lines.append("")

    lines.append("Validation issues by code")
    for item in summary.get("validation_issues_by_code", []):
        lines.append("- {0}: {1}".format(item["code"], item["c"]))
    if not summary.get("validation_issues_by_code"):
        lines.append("- none")
    lines.append("")

    lines.append("Quality flags by type")
    for item in summary.get("quality_flags_by_type", []):
        lines.append("- {0}: {1}".format(item["flag_name"], item["c"]))
    if not summary.get("quality_flags_by_type"):
        lines.append("- none")
    lines.append("")

    lines.append("Weak products (2+ flags)")
    weak_products = summary.get("weak_products", [])
    if weak_products:
        for item in weak_products:
            label = "{name} [{barcode}]".format(name=item["name"], barcode=item["barcode"])
            lines.append("- {0} — flags={1} ({2})".format(label, item["flag_count"], item.get("flags") or ""))
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Products without offers")
    products_without_offers = summary.get("products_without_offers", [])
    if products_without_offers:
        for item in products_without_offers:
            label = "{name} [{barcode}]".format(name=item["name"], barcode=item["barcode"])
            lines.append("- {0}".format(label))
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Top validation issues")
    top_issues = summary.get("top_validation_issues", [])
    if top_issues:
        for item in top_issues:
            target = item["product_name"] or item["barcode"] or "unknown"
            retailer = " | {0}".format(item["retailer"]) if item.get("retailer") else ""
            lines.append("- {severity} | {code} | {target}{retailer}: {message}".format(
                severity=item["severity"],
                code=item["code"],
                target=target,
                retailer=retailer,
                message=item["message"],
            ))
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
