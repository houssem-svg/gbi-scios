from datetime import UTC, datetime, timedelta
from typing import Any
import hashlib

from jose import JWTError, jwt
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    # نحقن الـ sub كالمعتاد
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        # خدعة التوافق: إذا قرأ الباكيند التوكن ويبحث عن حقل id نجهزه له
        if "sub" in payload:
            payload["id"] = payload["sub"] 
        return payload
    except JWTError as exc:
        raise ValueError("Invalid authentication token") from exc