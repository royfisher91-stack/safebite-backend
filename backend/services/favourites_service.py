from typing import Any, Dict, List, Optional

from database import db
from services.image_rights_service import normalise_image_metadata, public_image_url


def _row_to_favourite(row: Any) -> Optional[Dict[str, Any]]:
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
        "brand": payload.get("brand") or "",
        "category": payload.get("category") or "",
        "subcategory": payload.get("subcategory") or "",
        "image_url": display_image_url,
        "image_source_type": image_metadata["image_source_type"],
        "image_rights_status": image_metadata["image_rights_status"],
        "image_credit": image_metadata["image_credit"],
        "image_last_verified_at": image_metadata["image_last_verified_at"],
        "created_at": payload.get("created_at"),
    }


_FAVOURITES_SELECT = """
    SELECT
        favourites.*,
        products.brand AS brand,
        products.category AS category,
        products.subcategory AS subcategory,
        products.image_url AS image_url,
        products.image_source_type AS image_source_type,
        products.image_rights_status AS image_rights_status,
        products.image_credit AS image_credit,
        products.image_last_verified_at AS image_last_verified_at
    FROM favourites
    LEFT JOIN products ON products.barcode = favourites.barcode
"""


def list_favourites(
    barcode: Optional[str] = None,
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    owner_clause = "favourites.user_id IS NULL" if user_id is None else "favourites.user_id = ?"
    params: List[Any] = [] if user_id is None else [user_id]
    if barcode:
        params.append(barcode)
        cursor.execute(
            _FAVOURITES_SELECT
            + """
            WHERE {owner_clause} AND favourites.barcode = ?
            ORDER BY favourites.created_at DESC, favourites.id DESC
            """.format(owner_clause=owner_clause),
            tuple(params),
        )
    else:
        cursor.execute(
            _FAVOURITES_SELECT
            + """
            WHERE {owner_clause}
            ORDER BY favourites.created_at DESC, favourites.id DESC
            """.format(owner_clause=owner_clause),
            tuple(params),
        )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_favourite(row) for row in rows if row is not None]


def add_favourite(
    barcode: str,
    product_name: str,
    profile_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    conn = db.get_connection()
    cursor = conn.cursor()
    owner_clause = "favourites.user_id IS NULL" if user_id is None else "favourites.user_id = ?"
    existing_params: List[Any] = [] if user_id is None else [user_id]
    existing_params.append(barcode)
    cursor.execute(
        _FAVOURITES_SELECT
        + """
        WHERE {owner_clause} AND favourites.barcode = ?
        LIMIT 1
        """.format(owner_clause=owner_clause),
        tuple(existing_params),
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return _row_to_favourite(existing) or {}

    cursor.execute(
        """
        INSERT INTO favourites (user_id, barcode, product_name, profile_id)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, barcode.strip(), product_name.strip(), profile_id),
    )
    favourite_id = cursor.lastrowid
    conn.commit()
    cursor.execute(
        _FAVOURITES_SELECT
        + """
        WHERE favourites.id = ?
        """,
        (favourite_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_favourite(row) or {}


def delete_favourite(favourite_id: int, user_id: Optional[int] = None) -> bool:
    conn = db.get_connection()
    cursor = conn.cursor()
    if user_id is None:
        cursor.execute("DELETE FROM favourites WHERE id = ? AND user_id IS NULL", (favourite_id,))
    else:
        cursor.execute("DELETE FROM favourites WHERE id = ? AND user_id = ?", (favourite_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
