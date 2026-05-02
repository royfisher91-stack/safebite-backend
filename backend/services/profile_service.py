import json
from typing import Any, Dict, List, Optional, Tuple

from database import db


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


def _dumps_list(values: List[str]) -> str:
    return json.dumps(_unique(values), ensure_ascii=False)


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


def _row_to_profile(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    payload = dict(row)
    return {
        "id": payload.get("id"),
        "user_id": payload.get("user_id"),
        "name": payload.get("name") or "",
        "allergies": _loads_list(payload.get("allergies_json")),
        "conditions": _loads_list(payload.get("conditions_json")),
        "notes": payload.get("notes") or "",
        "is_default": bool(payload.get("is_default")),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }


def list_profiles(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    if user_id is None:
        cursor.execute(
            """
            SELECT *
            FROM profiles
            WHERE user_id IS NULL
            ORDER BY is_default DESC, updated_at DESC, id DESC
            """
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM profiles
            WHERE user_id = ?
            ORDER BY is_default DESC, updated_at DESC, id DESC
            """,
            (user_id,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_profile(row) for row in rows if row is not None]


def get_profile(profile_id: Optional[int], user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    if profile_id is None:
        return None
    conn = db.get_connection()
    cursor = conn.cursor()
    if user_id is None:
        cursor.execute(
            """
            SELECT *
            FROM profiles
            WHERE id = ? AND user_id IS NULL
            LIMIT 1
            """,
            (profile_id,),
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM profiles
            WHERE id = ? AND user_id = ?
            LIMIT 1
            """,
            (profile_id, user_id),
        )
    row = cursor.fetchone()
    conn.close()
    return _row_to_profile(row)


def create_profile(
    name: str,
    allergies: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    is_default: bool = False,
    notes: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    conn = db.get_connection()
    cursor = conn.cursor()

    if is_default:
        if user_id is None:
            cursor.execute("UPDATE profiles SET is_default = 0 WHERE user_id IS NULL")
        else:
            cursor.execute("UPDATE profiles SET is_default = 0 WHERE user_id = ?", (user_id,))

    cursor.execute(
        """
        INSERT INTO profiles (user_id, name, allergies_json, conditions_json, notes, is_default)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name.strip(),
            _dumps_list(allergies or []),
            _dumps_list(conditions or []),
            (notes or "").strip(),
            1 if is_default else 0,
        ),
    )
    profile_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_profile(profile_id, user_id=user_id) or {}


def update_profile(
    profile_id: int,
    name: str,
    allergies: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    is_default: bool = False,
    notes: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    existing = get_profile(profile_id, user_id=user_id)
    if not existing:
        return None

    conn = db.get_connection()
    cursor = conn.cursor()

    if is_default:
        if user_id is None:
            cursor.execute("UPDATE profiles SET is_default = 0 WHERE user_id IS NULL")
        else:
            cursor.execute("UPDATE profiles SET is_default = 0 WHERE user_id = ?", (user_id,))

    cursor.execute(
        """
        UPDATE profiles
        SET
            name = ?,
            allergies_json = ?,
            conditions_json = ?,
            notes = ?,
            is_default = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            name.strip(),
            _dumps_list(allergies or []),
            _dumps_list(conditions or []),
            (notes or "").strip(),
            1 if is_default else 0,
            profile_id,
        ),
    )
    conn.commit()
    conn.close()
    return get_profile(profile_id, user_id=user_id)


def delete_profile(profile_id: int, user_id: Optional[int] = None) -> bool:
    conn = db.get_connection()
    cursor = conn.cursor()
    if user_id is None:
        cursor.execute("DELETE FROM profiles WHERE id = ? AND user_id IS NULL", (profile_id,))
    else:
        cursor.execute("DELETE FROM profiles WHERE id = ? AND user_id = ?", (profile_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def resolve_profile_preferences(
    profile_id: Optional[int],
    manual_allergies: Optional[List[str]] = None,
    manual_conditions: Optional[List[str]] = None,
    user_id: Optional[int] = None,
) -> Tuple[List[str], List[str], Optional[Dict[str, Any]]]:
    manual_allergies = _unique(manual_allergies or [])
    manual_conditions = _unique(manual_conditions or [])

    profile = get_profile(profile_id, user_id=user_id)
    if not profile:
        return manual_allergies, manual_conditions, None

    effective_allergies = manual_allergies if manual_allergies else _unique(profile.get("allergies", []))
    effective_conditions = manual_conditions if manual_conditions else _unique(profile.get("conditions", []))
    return effective_allergies, effective_conditions, profile
