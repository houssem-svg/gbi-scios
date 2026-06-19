"""In-memory rate limiter for authentication endpoints.

A simple sliding-window rate limiter keyed by (identifier, action).
Suitable for single-process deployments. For multi-process / multi-node
deployments, replace the backend with Redis.

Limits:
  - login:    10 attempts per 60 seconds per (email + client IP).
  - register: 5  attempts per 300 seconds per client IP.

When the limit is exceeded, raises HTTP 429 with a Retry-After header.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, status

_DEFAULT_LOGIN_LIMIT = 10
_DEFAULT_LOGIN_WINDOW = 60  # seconds
_DEFAULT_REGISTER_LIMIT = 5
_DEFAULT_REGISTER_WINDOW = 300  # seconds


@dataclass
class _Bucket:
    timestamps: list[float] = field(default_factory=list)


class _RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, _Bucket] = defaultdict(_Bucket)
        self._lock = threading.Lock()

    def _prune(self, bucket: _Bucket, window: float, now: float) -> None:
        cutoff = now - window
        bucket.timestamps = [t for t in bucket.timestamps if t > cutoff]

    def hit(self, key: str, limit: int, window: float) -> tuple[bool, float]:
        """Record a hit. Returns (allowed, retry_after_seconds)."""
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets[key]
            self._prune(bucket, window, now)
            if len(bucket.timestamps) >= limit:
                # Earliest timestamp in the window → when it expires.
                oldest = bucket.timestamps[0]
                retry_after = max(0.1, oldest + window - now)
                return False, retry_after
            bucket.timestamps.append(now)
            return True, 0.0


_limiter = _RateLimiter()


def _client_ip(request: Request) -> str:
    # Honour X-Forwarded-For from a trusted proxy; fall back to the direct client.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_login_rate_limit(request: Request, email: str) -> None:
    """Raise HTTP 429 if the (email, ip) bucket is exhausted for login."""
    ip = _client_ip(request)
    key = f"login:{email.lower()}:{ip}"
    allowed, retry_after = _limiter.hit(
        key, _DEFAULT_LOGIN_LIMIT, _DEFAULT_LOGIN_WINDOW
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )


def check_register_rate_limit(request: Request) -> None:
    """Raise HTTP 429 if the client IP bucket is exhausted for registration."""
    ip = _client_ip(request)
    key = f"register:{ip}"
    allowed, retry_after = _limiter.hit(
        key, _DEFAULT_REGISTER_LIMIT, _DEFAULT_REGISTER_WINDOW
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
