from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta

from fastapi import Header, HTTPException, status

from app.database import get_db


PASSWORD_ITERATIONS = 210_000
SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "30"))


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str):
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email address.")
    if len(email) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is too long.")


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return salt.hex(), hashed.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    _, calculated = hash_password(password, salt_hex)
    return hmac.compare_digest(calculated, hash_hex)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _session_expiry() -> str:
    return (datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)).strftime("%Y-%m-%d %H:%M:%S")


def create_user(email: str, password: str, full_name: str = "") -> dict:
    email = normalize_email(email)
    validate_email(email)
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")

    salt_hex, hash_hex = hash_password(password)
    with get_db() as conn:
        existing = conn.execute("SELECT email FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
        conn.execute(
            """
            INSERT INTO users (email, full_name, password_salt, password_hash, auth_provider)
            VALUES (?, ?, ?, ?, 'password')
            """,
            (email, full_name.strip(), salt_hex, hash_hex),
        )
    return get_user_by_email(email)


def get_user_by_email(email: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT email, full_name, auth_provider, google_sub, google_sheet_url, google_sheet_tab, created_at FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()
    return dict(row) if row else None


def authenticate_user(email: str, password: str) -> dict:
    email = normalize_email(email)
    validate_email(email)
    with get_db() as conn:
        row = conn.execute(
            "SELECT email, full_name, auth_provider, password_salt, password_hash, google_sub, google_sheet_url, google_sheet_tab, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if not row or not verify_password(password, row["password_salt"], row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    return dict(row)


def create_session(email: str) -> str:
    token = secrets.token_urlsafe(48)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO sessions (token_hash, email, expires_at)
            VALUES (?, ?, ?)
            """,
            (_token_hash(token), normalize_email(email), _session_expiry()),
        )
    return token


def revoke_session(token: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token_hash = ?",
            (_token_hash(token),),
        )


def build_auth_response(user: dict) -> dict:
    token = create_session(user["email"])
    return {
        "token": token,
        "user": {
            "email": user["email"],
            "full_name": user.get("full_name") or user["email"],
            "google_sheet_url": user.get("google_sheet_url", ""),
            "google_sheet_tab": user.get("google_sheet_tab", ""),
        },
    }


def _extract_token(authorization: str | None, x_session_token: str | None) -> str | None:
    if x_session_token:
        return x_session_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def extract_session_token(
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    return _extract_token(authorization, x_session_token)


def get_user_from_token(token: str) -> dict | None:
    token_hash = _token_hash(token)
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT u.email, u.full_name, u.auth_provider, u.google_sub, u.google_sheet_url, u.google_sheet_tab, s.expires_at, s.revoked_at
            FROM sessions s
            JOIN users u ON u.email = s.email
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

    if not row or row["revoked_at"] is not None:
        return None

    expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
    if expires_at < datetime.utcnow():
        return None

    return {
        "email": row["email"],
        "full_name": row["full_name"] or row["email"],
        "auth_provider": row["auth_provider"] or "password",
        "google_sub": row["google_sub"] or "",
        "google_sheet_url": row["google_sheet_url"] or "",
        "google_sheet_tab": row["google_sheet_tab"] or "",
        "session_token": token,
    }


def get_current_user(
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    token = _extract_token(authorization, x_session_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in again.")

    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in again.")
    return user
