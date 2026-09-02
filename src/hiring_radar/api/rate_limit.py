"""Small in-memory rate limiter for abuse-prone API endpoints.

This is intentionally dependency-free for the first production hardening step.
It is safe for a single API process and gives us a narrow interface that can be
replaced by Redis or another shared store when the deployment becomes multi-node.
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from threading import RLock

from fastapi import HTTPException, Request, status

from hiring_radar.security_runtime import bool_env

GENERIC_RATE_LIMIT_DETAIL = "Too many attempts. Please try again later."
TRUST_PROXY_HEADERS_ENV = "HIRING_RADAR_RATE_LIMIT_TRUST_PROXY_HEADERS"
RATE_LIMIT_ENABLED_ENV = "HIRING_RADAR_RATE_LIMIT_ENABLED"


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """A single fixed-window limiter rule."""

    name: str
    limit: int
    window_seconds: int


@dataclass(slots=True)
class _Bucket:
    count: int
    reset_at: float


class InMemoryRateLimiter:
    """Thread-safe fixed-window limiter.

    The implementation keeps no raw email/user identifiers. Identity values are
    normalized and SHA-256 hashed before they become bucket keys.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._buckets: dict[str, _Bucket] = {}

    def check(self, *, key: str, rule: RateLimitRule, now: float | None = None) -> int:
        if rule.limit <= 0 or rule.window_seconds <= 0:
            return 0

        current_time = time.monotonic() if now is None else now
        with self._lock:
            self._prune_locked(current_time)
            bucket = self._buckets.get(key)
            if bucket is None or bucket.reset_at <= current_time:
                self._buckets[key] = _Bucket(
                    count=1,
                    reset_at=current_time + rule.window_seconds,
                )
                return 0

            if bucket.count >= rule.limit:
                return max(1, int(bucket.reset_at - current_time))

            bucket.count += 1
            return 0

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()

    def _prune_locked(self, current_time: float) -> None:
        expired_keys = [key for key, bucket in self._buckets.items() if bucket.reset_at <= current_time]
        for key in expired_keys:
            self._buckets.pop(key, None)


_rate_limiter = InMemoryRateLimiter()


def reset_rate_limiter_for_tests() -> None:
    """Clear limiter state for isolated tests."""

    _rate_limiter.reset()


def rate_limit_enabled() -> bool:
    return bool_env(RATE_LIMIT_ENABLED_ENV, default=True)


def _env_int(name: str, *, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}.")
    return value


def _rule_from_env(
    *,
    action: str,
    scope: str,
    default_limit: int,
    default_window_seconds: int,
) -> RateLimitRule:
    env_prefix = f"HIRING_RADAR_RATE_LIMIT_{action.upper()}_{scope.upper()}"
    return RateLimitRule(
        name=f"{action}:{scope}",
        limit=_env_int(f"{env_prefix}_LIMIT", default=default_limit),
        window_seconds=_env_int(
            f"{env_prefix}_WINDOW_SECONDS",
            default=default_window_seconds,
            minimum=1,
        ),
    )


def normalize_rate_limit_identity(value: object | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().casefold()
    if not normalized:
        return None
    return normalized


def _identity_digest(identity: str) -> str:
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def client_ip_for_rate_limit(request: Request) -> str:
    """Return the client IP used for abuse protection.

    Proxy headers are ignored by default because they are spoofable unless the
    app is deployed behind a trusted reverse proxy. Set
    HIRING_RADAR_RATE_LIMIT_TRUST_PROXY_HEADERS=true at the edge when trusted.
    """

    if bool_env(TRUST_PROXY_HEADERS_ENV, default=False):
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            candidate = forwarded_for.split(",")[0].strip()
            if candidate:
                return candidate
        real_ip = request.headers.get("x-real-ip", "").strip()
        if real_ip:
            return real_ip

    return request.client.host if request.client else "unknown"


def _raise_rate_limit(retry_after_seconds: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=GENERIC_RATE_LIMIT_DETAIL,
        headers={"Retry-After": str(max(1, retry_after_seconds))},
    )


def enforce_rate_limit(
    request: Request,
    *,
    action: str,
    identity: object | None = None,
    ip_limit: int,
    ip_window_seconds: int,
    identity_limit: int | None = None,
    identity_window_seconds: int | None = None,
) -> None:
    """Apply IP and optional identity fixed-window limits.

    Environment override format:
    - HIRING_RADAR_RATE_LIMIT_<ACTION>_IP_LIMIT
    - HIRING_RADAR_RATE_LIMIT_<ACTION>_IP_WINDOW_SECONDS
    - HIRING_RADAR_RATE_LIMIT_<ACTION>_IDENTITY_LIMIT
    - HIRING_RADAR_RATE_LIMIT_<ACTION>_IDENTITY_WINDOW_SECONDS
    """

    if not rate_limit_enabled():
        return

    ip_rule = _rule_from_env(
        action=action,
        scope="ip",
        default_limit=ip_limit,
        default_window_seconds=ip_window_seconds,
    )
    client_ip = client_ip_for_rate_limit(request)
    retry_after = _rate_limiter.check(
        key=f"{ip_rule.name}:{client_ip}",
        rule=ip_rule,
    )
    if retry_after:
        _raise_rate_limit(retry_after)

    normalized_identity = normalize_rate_limit_identity(identity)
    if normalized_identity is None or identity_limit is None:
        return

    identity_rule = _rule_from_env(
        action=action,
        scope="identity",
        default_limit=identity_limit,
        default_window_seconds=identity_window_seconds or ip_window_seconds,
    )
    retry_after = _rate_limiter.check(
        key=f"{identity_rule.name}:{_identity_digest(normalized_identity)}",
        rule=identity_rule,
    )
    if retry_after:
        _raise_rate_limit(retry_after)
