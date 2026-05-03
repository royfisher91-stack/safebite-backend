import json
from typing import Any, Dict, List, Optional

from database import db
from services.image_rights_service import normalise_image_metadata, public_image_url


def _loads_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except Exception:
            parsed = []
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return []


def _loads_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except Exception:
            parsed = {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _row_to_history(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    payload = dict(row)
    image_metadata = normalise_image_metadata(payload)
    display_image_url = public_image_url(
        payload.get("image_url"),
        image_metadata["image_source_type"],
        image_metadata["image_rights_status"],
    )
    return {
        "id": payload.get("id"),
        "user_id": payload.get("user_id"),
        "barcode": payload.get("barcode"),
        "product_name": payload.get("product_name") or "",
        "profile_id": payload.get("profile_id"),
        "profile_name": payload.get("profile_name") or "",
        "brand": payload.get("brand") or "",
        "category": payload.get("category") or "",
        "subcategory": payload.get("subcategory") or "",
        "image_url": display_image_url,
        "image_source_type": image_metadata["image_source_type"],
        "image_rights_status": image_metadata["image_rights_status"],
        "image_credit": image_metadata["image_credit"],
        "image_last_verified_at": image_metadata["image_last_verified_at"],
        "allergies": _loads_list(payload.get("allergies_json")),
        "conditions": _loads_list(payload.get("conditions_json")),
        "safety_result": payload.get("safety_result") or "Unknown",
        "safety_score": payload.get("safety_score"),
        "condition_results": _loads_dict(payload.get("condition_results_json")),
        "scanned_at": payload.get("scanned_at"),
    }


_HISTORY_SELECT = """
    SELECT
        scan_history.*,
        products.brand AS brand,
        products.category AS category,
        products.subcategory AS subcategory,
        products.image_url AS image_url,
        products.image_source_type AS image_source_type,
        products.image_rights_status AS image_rights_status,
        products.image_credit AS image_credit,
        products.image_last_verified_at AS image_last_verified_at
    FROM scan_history
    LEFT JOIN products ON products.barcode = scan_history.barcode
"""


def list_history(limit: int = 50, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    if user_id is None:
        cursor.execute(
            _HISTORY_SELECT
            + """
            WHERE scan_history.user_id IS NULL
            ORDER BY scan_history.scanned_at DESC, scan_history.id DESC
            LIMIT ?
            """,
            (limit,),
        )
    else:
        cursor.execute(
            _HISTORY_SELECT
            + """
            WHERE scan_history.user_id = ?
            ORDER BY scan_history.scanned_at DESC, scan_history.id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_history(row) for row in rows if row is not None]


def add_history_entry(
    barcode: str,
    product_name: str,
    profile_id: Optional[int] = None,
    profile_name: Optional[str] = None,
    allergies: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    safety_result: Optional[str] = None,
    safety_score: Optional[int] = None,
    condition_results: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO scan_history (
            user_id,
            barcode,
            product_name,
            profile_id,
            profile_name,
            allergies_json,
            conditions_json,
            safety_result,
            safety_score,
            condition_results_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            barcode.strip(),
            product_name.strip(),
            profile_id,
            (profile_name or "").strip(),
            json.dumps(allergies or [], ensure_ascii=False),
            json.dumps(conditions or [], ensure_ascii=False),
            safety_result or "Unknown",
            safety_score,
            json.dumps(condition_results or {}, ensure_ascii=False),
        ),
    )
    history_id = cursor.lastrowid
    conn.commit()
    cursor.execute(
        _HISTORY_SELECT
        + """
        WHERE scan_history.id = ?
        """,
        (history_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_history(row) or {}


def delete_history_entry(history_id: int, user_id: Optional[int] = None) -> bool:
    conn = db.get_connection()
    cursor = conn.cursor()
    if user_id is None:
        cursor.execute("DELETE FROM scan_history WHERE id = ? AND user_id IS NULL", (history_id,))
    else:
        cursor.execute("DELETE FROM scan_history WHERE id = ? AND user_id = ?", (history_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
