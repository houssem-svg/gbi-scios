from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt truncates passwords at 72 bytes. We pre-hash with SHA-256 (still salted
# by bcrypt afterwards) so that long passwords are supported without silent truncation.
# This is the same scheme Django uses for bcrypt + long passwords.
_BCRYPT_MAX_BYTES = 72


def _prepare_password(password: str) -> bytes:
    """Return a bytes representation suitable for bcrypt.

    bcrypt accepts at most 72 bytes; for longer inputs we hash with SHA-256 first
    (base64-encoded to stay within ASCII) and then bcrypt that. The bcrypt salt is
    still generated per-password, so the result is properly salted.
    """
    raw = password.encode("utf-8")
    if len(raw) <= _BCRYPT_MAX_BYTES:
        return raw
    digest = hashlib.sha256(raw).hexdigest().encode("ascii")
    return digest


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash of the password (salt generated automatically)."""
    prepared = _prepare_password(password)
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(prepared, salt).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Supports modern bcrypt hashes (``$2b$``/``$2a$``/``$2y$``) with constant-time
    comparison. Also falls back to legacy unsalted SHA-256 hexdigests so existing
    accounts created before the bcrypt migration can still log in (they are then
    transparently re-hashed by auth_service.authenticate_user).
    """
    if not hashed_password:
        return False
    if hashed_password.startswith("$2"):
        try:
            prepared = _prepare_password(plain_password)
            return bcrypt.checkpw(prepared, hashed_password.encode("ascii"))
        except (ValueError, TypeError):
            return False
    # Legacy unsalted SHA-256 fallback — compare in constant time.
    legacy_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_hash, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """True if the stored hash is a legacy SHA-256 (needs upgrade to bcrypt)."""
    return not hashed_password.startswith("$2")


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid authentication token") from exc


def generate_secret_token(length: int = 64) -> str:
    """Generate a URL-safe secret token (use for JWT keys, API tokens, etc.)."""
    return secrets.token_urlsafe(length)
