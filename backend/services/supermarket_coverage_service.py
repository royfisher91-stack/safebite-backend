import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.bulk_import_service import (
    ACTIVE_COVERAGE_RETAILERS,
    ADAPTER_MODULES,
    DB_DEFAULT,
    FUTURE_COMPATIBLE_RETAILERS,
    ensure_phase12_schema,
)


ACTIVE_COVERAGE_SET = set(ACTIVE_COVERAGE_RETAILERS)
FUTURE_COMPATIBLE_SET = set(FUTURE_COMPATIBLE_RETAILERS)


def _connect(db_path: str = DB_DEFAULT) -> sqlite3.Connection:
    ensure_phase12_schema(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _row_to_offer(row: sqlite3.Row) -> Dict[str, Any]:
    price = _safe_float(row["price"])
    promo_price = _safe_float(row["promo_price"])
    effective_price = promo_price if promo_price is not None else price
    return {
        "barcode": row["barcode"],
        "retailer": row["retailer"],
        "price": price,
        "promo_price": promo_price,
        "effective_price": effective_price,
        "multibuy_text": row["multibuy_text"] or "",
        "stock_status": row["stock_status"] or "unknown",
        "product_url": row["product_url"] or "",
        "source": row["source"] or "",
        "last_checked_at": row["last_checked_at"],
    }


def list_retailers(db_path: str = DB_DEFAULT) -> List[Dict[str, Any]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT retailer,
                   COUNT(*) AS offer_count,
                   COUNT(DISTINCT barcode) AS product_count,
                   MAX(last_checked_at) AS last_checked_at
            FROM retailer_offers
            GROUP BY retailer
            ORDER BY retailer
            """
        ).fetchall()
        seen = {row["retailer"] for row in rows}
        response = [
            {
                "retailer": row["retailer"],
                "offer_count": int(row["offer_count"] or 0),
                "product_count": int(row["product_count"] or 0),
                "last_checked_at": row["last_checked_at"],
                "has_adapter": row["retailer"] in ADAPTER_MODULES,
                "active_target": row["retailer"] in ACTIVE_COVERAGE_SET,
                "phase": "current" if row["retailer"] in ACTIVE_COVERAGE_SET else "future",
            }
            for row in rows
        ]
        for retailer in sorted(set(ADAPTER_MODULES.keys()) - seen):
            response.append(
                {
                    "retailer": retailer,
                    "offer_count": 0,
                    "product_count": 0,
                    "last_checked_at": None,
                    "has_adapter": True,
                    "active_target": retailer in ACTIVE_COVERAGE_SET,
                    "phase": "current" if retailer in ACTIVE_COVERAGE_SET else "future",
                }
            )
        return sorted(response, key=lambda item: (0 if item["active_target"] else 1, item["retailer"]))
    finally:
        conn.close()


def get_retailer_coverage(barcode: str, db_path: str = DB_DEFAULT) -> Dict[str, Any]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM retailer_offers
            WHERE barcode = ?
            ORDER BY retailer, last_checked_at DESC
            """,
            (barcode,),
        ).fetchall()
        offers = [_row_to_offer(row) for row in rows]
        stocked = [offer for offer in offers if offer["stock_status"] in {"in_stock", "limited"}]
        covered = sorted({offer["retailer"] for offer in offers})
        active_covered = sorted(ACTIVE_COVERAGE_SET & set(covered))
        future_covered = sorted(FUTURE_COMPATIBLE_SET & set(covered))
        missing = [retailer for retailer in ACTIVE_COVERAGE_RETAILERS if retailer not in set(covered)]
        return {
            "barcode": barcode,
            "retailer_count": len(covered),
            "stocked_retailer_count": len({offer["retailer"] for offer in stocked}),
            "retailers": covered,
            "active_retailers": active_covered,
            "future_compatible_retailers": future_covered,
            "missing_retailers": missing,
            "offers": offers,
        }
    finally:
        conn.close()


def get_stockists(barcode: str, db_path: str = DB_DEFAULT) -> Dict[str, Any]:
    coverage = get_retailer_coverage(barcode, db_path=db_path)
    stockists = [
        offer
        for offer in coverage["offers"]
        if offer["stock_status"] in {"in_stock", "limited"}
    ]
    return {
        "barcode": barcode,
        "stockist_count": len(stockists),
        "stockists": stockists,
    }


def get_best_stocked_offer(barcode: str, db_path: str = DB_DEFAULT) -> Dict[str, Any]:
    stockists = get_stockists(barcode, db_path=db_path)["stockists"]
    candidates = [offer for offer in stockists if offer["effective_price"] is not None]
    candidates.sort(key=lambda item: (item["effective_price"], item["retailer"]))
    return {
        "barcode": barcode,
        "best_offer": candidates[0] if candidates else None,
    }


def list_import_batches(limit: int = 50, db_path: str = DB_DEFAULT) -> List[Dict[str, Any]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM product_import_batches
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def list_import_batch_errors(
    batch_id: int,
    limit: int = 100,
    db_path: str = DB_DEFAULT,
) -> List[Dict[str, Any]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT batch_id, row_number, retailer, barcode, reason, raw_row_preview, created_at
            FROM product_import_errors
            WHERE batch_id = ?
            ORDER BY row_number, id
            LIMIT ?
            """,
            (batch_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def find_bulk_raw_files(base_dir: str, active_only: bool = True) -> List[Dict[str, str]]:
    base = Path(base_dir)
    files: List[Dict[str, str]] = []
    if not base.exists():
        return files
    for path in sorted(base.glob("*/raw.csv")):
        if active_only and path.parent.name not in _active_folder_names():
            continue
        files.append({"retailer": path.parent.name, "path": str(path)})
    return files


def _active_folder_names() -> set:
    return {retailer.lower().replace("&", "and").replace("'", "").replace(" ", "_") for retailer in ACTIVE_COVERAGE_RETAILERS}
