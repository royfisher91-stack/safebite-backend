import json
from collections import Counter
from typing import Any, Dict, List, Optional

from database import db


LOCKED_ALLERGY_TAGS = ["dairy", "nuts", "gluten", "soy", "egg"]
LOCKED_CONDITION_TAGS = ["ibs", "stoma", "coeliac", "baby-specific sensitivity"]
ALLOWED_FEEDBACK_TYPES = {"positive", "negative"}
COMMENT_MAX_LENGTH = 280
COMMUNITY_DISCLAIMER = (
    "Reported by users only. This does not change the verified safety analysis."
)
COMMUNITY_LABEL = "Community experiences"


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


def _unique(values: List[str]) -> List[str]:
    seen = set()
    items: List[str] = []
    for value in values:
        trimmed = str(value).strip()
        if not trimmed:
            continue
        key = trimmed.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(trimmed)
    return items


def _normalise_tags(values: Optional[List[str]], allowed_values: List[str]) -> List[str]:
    allowed_map = {value.lower(): value for value in allowed_values}
    normalised: List[str] = []
    for value in values or []:
        key = str(value or "").strip().lower()
        if key and key in allowed_map:
            normalised.append(allowed_map[key])
    return _unique(normalised)


def _normalise_feedback_type(value: str) -> str:
    return str(value or "").strip().lower()


def _row_to_feedback(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    payload = dict(row)
    return {
        "id": payload.get("id"),
        "barcode": payload.get("barcode") or "",
        "product_name": payload.get("product_name") or "",
        "feedback_type": payload.get("feedback_type") or "negative",
        "comment": payload.get("comment") or "",
        "allergy_tags": _loads_list(payload.get("allergy_tags_json")),
        "condition_tags": _loads_list(payload.get("condition_tags_json")),
        "is_visible": bool(payload.get("is_visible")),
        "is_flagged": bool(payload.get("is_flagged")),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }


def _fetch_feedback_rows(
    barcode: str,
    limit: Optional[int] = None,
    include_hidden: bool = False,
    include_flagged: bool = False,
) -> List[Any]:
    conn = db.get_connection()
    cursor = conn.cursor()

    query = [
        "SELECT * FROM community_feedback WHERE barcode = ?",
    ]
    params: List[Any] = [barcode.strip()]

    if not include_hidden:
        query.append("AND is_visible = 1")
    if not include_flagged:
        query.append("AND is_flagged = 0")

    query.append("ORDER BY created_at DESC, id DESC")
    if limit is not None:
        query.append("LIMIT ?")
        params.append(limit)

    cursor.execute("\n".join(query), tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_feedback(feedback_id: int) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM community_feedback
        WHERE id = ?
        LIMIT 1
        """,
        (feedback_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_feedback(row)


def list_feedback(
    barcode: str,
    limit: int = 20,
    include_hidden: bool = False,
    include_flagged: bool = False,
) -> List[Dict[str, Any]]:
    rows = _fetch_feedback_rows(
        barcode=barcode,
        limit=limit,
        include_hidden=include_hidden,
        include_flagged=include_flagged,
    )
    return [_row_to_feedback(row) for row in rows if row is not None]


def create_feedback(
    barcode: str,
    product_name: str,
    feedback_type: str,
    comment: str,
    allergy_tags: Optional[List[str]] = None,
    condition_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    cleaned_type = _normalise_feedback_type(feedback_type)
    cleaned_comment = str(comment or "").strip()
    cleaned_allergies = _normalise_tags(allergy_tags, LOCKED_ALLERGY_TAGS)
    cleaned_conditions = _normalise_tags(condition_tags, LOCKED_CONDITION_TAGS)

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO community_feedback (
            barcode,
            product_name,
            feedback_type,
            comment,
            allergy_tags_json,
            condition_tags_json,
            is_visible,
            is_flagged
        )
        VALUES (?, ?, ?, ?, ?, ?, 1, 0)
        """,
        (
            barcode.strip(),
            product_name.strip(),
            cleaned_type,
            cleaned_comment,
            json.dumps(cleaned_allergies, ensure_ascii=False),
            json.dumps(cleaned_conditions, ensure_ascii=False),
        ),
    )
    feedback_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_feedback(feedback_id) or {}


def flag_feedback(feedback_id: int, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE community_feedback
        SET
            is_flagged = 1,
            flag_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        ((reason or "").strip(), feedback_id),
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    if not updated:
        return None
    return get_feedback(feedback_id)


def delete_feedback(feedback_id: int) -> bool:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM community_feedback WHERE id = ?", (feedback_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def build_feedback_summary(barcode: str) -> Dict[str, Any]:
    rows = _fetch_feedback_rows(
        barcode=barcode,
        limit=None,
        include_hidden=False,
        include_flagged=False,
    )
    items = [_row_to_feedback(row) for row in rows if row is not None]

    feedback_counts: Counter[str] = Counter()
    allergy_tag_counts: Counter[str] = Counter()
    condition_tag_counts: Counter[str] = Counter()

    latest_feedback_at = None
    for item in items:
        feedback_counts[str(item.get("feedback_type") or "").lower()] += 1
        allergy_tag_counts.update(item.get("allergy_tags") or [])
        condition_tag_counts.update(item.get("condition_tags") or [])
        if latest_feedback_at is None:
            latest_feedback_at = item.get("created_at")

    return {
        "barcode": barcode.strip(),
        "opinion_label": COMMUNITY_LABEL,
        "disclaimer": COMMUNITY_DISCLAIMER,
        "visible_count": len(items),
        "positive_count": feedback_counts.get("positive", 0),
        "negative_count": feedback_counts.get("negative", 0),
        "allergy_tag_counts": dict(allergy_tag_counts),
        "condition_tag_counts": dict(condition_tag_counts),
        "latest_feedback_at": latest_feedback_at,
    }
