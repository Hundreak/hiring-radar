"""Runtime security helpers shared by API/auth surfaces.

This module deliberately stays dependency-light so auth services can validate
production safety without importing FastAPI or application routers.
"""
from __future__ import annotations

import os
from collections.abc import Iterable

PRODUCTION_ENV_VALUES = frozenset({"production", "prod"})
TRUTHY_VALUES = frozenset({"1", "true", "yes", "on"})
FALSY_VALUES = frozenset({"0", "false", "no", "off"})

UNSAFE_SECRET_VALUES = frozenset(
    {
        "dev-user-auth-secret",
        "dev-employer-session-secret-change-me",
        "change-me",
        "changeme",
        "secret",
        "password",
        "admin",
        "test",
    }
)


class RuntimeSecurityError(RuntimeError):
    """Raised when runtime security configuration is unsafe."""


def runtime_env() -> str:
    """Return the normalized application runtime environment."""

    return (
        os.getenv("HIRING_RADAR_ENV")
        or os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT")
        or "development"
    ).strip().lower()


def is_production() -> bool:
    """Whether the app is running in a production-like environment."""

    return runtime_env() in PRODUCTION_ENV_VALUES


def parse_bool(value: str, *, field_name: str) -> bool:
    """Parse a strict boolean environment-style value."""

    normalized = value.strip().lower()
    if normalized in TRUTHY_VALUES:
        return True
    if normalized in FALSY_VALUES:
        return False
    allowed = ", ".join(sorted(TRUTHY_VALUES | FALSY_VALUES))
    raise RuntimeSecurityError(
        f"{field_name} must be a boolean value; use one of: {allowed}."
    )


def bool_env(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return parse_bool(raw, field_name=name)


def normalize_cookie_samesite(name: str, *, default: str = "lax") -> str:
    raw = (os.getenv(name) or default).strip().lower()
    if raw not in {"lax", "strict", "none"}:
        raise RuntimeSecurityError(
            f"{name} must be one of: lax, strict, none."
        )
    return raw


def require_production_secret(
    name: str,
    value: str | None,
    *,
    min_length: int = 32,
    unsafe_values: Iterable[str] = (),
) -> str:
    """Return a secret, failing fast in production when it is absent or weak.

    Local/dev flows may still use their explicit fallback values. Production is
    intentionally stricter: missing values, known placeholders, and short values
    should stop boot instead of silently signing sessions with weak material.
    """

    resolved = (value or "").strip()
    if not is_production():
        return resolved

    if not resolved:
        raise RuntimeSecurityError(f"{name} must be set in production.")

    unsafe = {candidate.strip() for candidate in UNSAFE_SECRET_VALUES | frozenset(unsafe_values)}
    if resolved in unsafe:
        raise RuntimeSecurityError(f"{name} uses an unsafe development placeholder.")

    if len(resolved) < min_length:
        raise RuntimeSecurityError(
            f"{name} must be at least {min_length} characters long in production."
        )

    return resolved


def default_secure_cookie() -> bool:
    """Default cookie security posture for the current runtime."""

    return is_production()
