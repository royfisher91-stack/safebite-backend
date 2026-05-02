from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from database import db


PASSWORD_HASH_ITERATIONS = 260000
TOKEN_TTL_DAYS = 30


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialise_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalise_email(email: str) -> str:
    return str(email or "").strip().lower()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_HASH_ITERATIONS,
    ).hex()
    return "pbkdf2_sha256${}${}${}".format(PASSWORD_HASH_ITERATIONS, salt, digest)


def _verify_password(password: str, stored_hash: str) -> bool:
    parts = str(stored_hash or "").split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False

    try:
        iterations = int(parts[1])
        salt = parts[2]
        expected = parts[3]
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            iterations,
        ).hex()
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(digest, expected)


def _row_to_user(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None

    payload = dict(row)
    return {
        "id": payload.get("id"),
        "email": payload.get("email") or "",
        "is_active": bool(payload.get("is_active")),
        "subscription_status": payload.get("subscription_status") or "inactive",
        "subscription_plan": payload.get("subscription_plan") or "free",
        "free_scans_used": int(payload.get("free_scans_used") or 0),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ? LIMIT 1", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_user(row)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    cleaned_email = _normalise_email(email)
    if not cleaned_email:
        return None

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? LIMIT 1", (cleaned_email,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_user(row)


def register_user(email: str, password: str) -> Dict[str, Any]:
    cleaned_email = _normalise_email(email)
    if "@" not in cleaned_email or "." not in cleaned_email.split("@")[-1]:
        raise ValueError("A valid email address is required")
    if len(password or "") < 8:
        raise ValueError("Password must be at least 8 characters")
    if get_user_by_email(cleaned_email):
        raise ValueError("An account with this email already exists")

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (
            email,
            password_hash,
            is_active,
            subscription_status,
            subscription_plan,
            free_scans_used
        )
        VALUES (?, ?, 1, 'inactive', 'free', 0)
        """,
        (cleaned_email, _hash_password(password)),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("Account could not be created")
    return user


def _get_user_with_password(email: str) -> Optional[Dict[str, Any]]:
    cleaned_email = _normalise_email(email)
    if not cleaned_email:
        return None

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? LIMIT 1", (cleaned_email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row is not None else None


def create_access_token(user_id: int) -> Dict[str, Any]:
    token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + timedelta(days=TOKEN_TTL_DAYS)

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO auth_tokens (user_id, token_hash, expires_at)
        VALUES (?, ?, ?)
        """,
        (user_id, _hash_token(token), _serialise_datetime(expires_at)),
    )
    conn.commit()
    conn.close()

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": _serialise_datetime(expires_at),
    }


def login_user(email: str, password: str) -> Dict[str, Any]:
    stored = _get_user_with_password(email)
    if not stored or not _verify_password(password, stored.get("password_hash") or ""):
        raise ValueError("Invalid email or password")
    if not bool(stored.get("is_active")):
        raise ValueError("Account is inactive")

    user = _row_to_user(stored)
    if not user:
        raise ValueError("Invalid email or password")

    token = create_access_token(int(user["id"]))
    return {
        **token,
        "user": user,
    }


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    value = str(authorization or "").strip()
    if not value:
        return None

    pieces = value.split()
    if len(pieces) == 2 and pieces[0].lower() == "bearer":
        return pieces[1].strip()

    return None


def get_user_from_authorization(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    token = _extract_bearer_token(authorization)
    if not token:
        return None

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT users.*
        FROM auth_tokens
        JOIN users ON users.id = auth_tokens.user_id
        WHERE auth_tokens.token_hash = ?
          AND auth_tokens.revoked_at IS NULL
          AND auth_tokens.expires_at > ?
          AND users.is_active = 1
        LIMIT 1
        """,
        (_hash_token(token), _serialise_datetime(_utc_now())),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_user(row)


def logout_token(authorization: Optional[str]) -> bool:
    token = _extract_bearer_token(authorization)
    if not token:
        return False

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE auth_tokens
        SET revoked_at = ?
        WHERE token_hash = ? AND revoked_at IS NULL
        """,
        (_serialise_datetime(_utc_now()), _hash_token(token)),
    )
    revoked = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return revoked
