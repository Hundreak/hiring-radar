from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hiring_radar.email_config import load_env_file

ADMIN_SESSION_COOKIE_NAME = "hiring_radar_admin_session"
DEFAULT_ADMIN_SESSION_TTL_SECONDS = 60 * 60 * 12


class AdminAuthError(ValueError):
    """Raised when admin authentication settings or session data are invalid."""


@dataclass(slots=True, frozen=True)
class AdminAuthSettings:
    email: str
    password: str
    session_secret: str
    session_ttl_seconds: int = DEFAULT_ADMIN_SESSION_TTL_SECONDS


@dataclass(slots=True, frozen=True)
class AdminSession:
    email: str
    issued_at: str
    expires_at: str


def _coerce_positive_int(*, field_name: str, value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise AdminAuthError(f"{field_name} must be an integer, got {value!r}") from exc

    if parsed < 1:
        raise AdminAuthError(f"{field_name} must be >= 1")

    return parsed


def _encode_payload(payload: dict[str, str]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _decode_payload(payload_b64: str) -> dict[str, str]:
    padding = "=" * (-len(payload_b64) % 4)

    try:
        raw = base64.urlsafe_b64decode(f"{payload_b64}{padding}".encode())
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AdminAuthError("Invalid admin session payload.") from exc

    if not isinstance(payload, dict):
        raise AdminAuthError("Invalid admin session payload.")

    return payload


def _sign_payload(*, payload_b64: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def load_admin_auth_settings(env_path: str | Path = ".env") -> AdminAuthSettings:
    load_env_file(env_path)

    email = os.environ.get("HIRING_RADAR_ADMIN_EMAIL")
    password = os.environ.get("HIRING_RADAR_ADMIN_PASSWORD")
    session_secret = os.environ.get("HIRING_RADAR_ADMIN_SESSION_SECRET")

    missing = [
        name
        for name, value in (
            ("HIRING_RADAR_ADMIN_EMAIL", email),
            ("HIRING_RADAR_ADMIN_PASSWORD", password),
            ("HIRING_RADAR_ADMIN_SESSION_SECRET", session_secret),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise AdminAuthError(f"Missing required admin auth settings: {joined}")

    session_ttl_seconds = _coerce_positive_int(
        field_name="HIRING_RADAR_ADMIN_SESSION_TTL_SECONDS",
        value=os.environ.get("HIRING_RADAR_ADMIN_SESSION_TTL_SECONDS"),
        default=DEFAULT_ADMIN_SESSION_TTL_SECONDS,
    )

    return AdminAuthSettings(
        email=email,
        password=password,
        session_secret=session_secret,
        session_ttl_seconds=session_ttl_seconds,
    )


def verify_admin_credentials(
    *,
    email: str,
    password: str,
    settings: AdminAuthSettings,
) -> bool:
    return hmac.compare_digest(email, settings.email) and hmac.compare_digest(
        password,
        settings.password,
    )


def create_admin_session_token(
    *,
    email: str,
    settings: AdminAuthSettings,
    now: datetime | None = None,
) -> str:
    issued_at_dt = now or datetime.now(UTC)
    expires_at_dt = issued_at_dt + timedelta(seconds=settings.session_ttl_seconds)

    payload = {
        "sub": email,
        "iat": issued_at_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "exp": expires_at_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    payload_b64 = _encode_payload(payload)
    signature = _sign_payload(
        payload_b64=payload_b64,
        secret=settings.session_secret,
    )
    return f"{payload_b64}.{signature}"


def decode_admin_session_token(
    *,
    token: str,
    settings: AdminAuthSettings,
    now: datetime | None = None,
) -> AdminSession:
    if "." not in token:
        raise AdminAuthError("Invalid admin session token.")

    payload_b64, provided_signature = token.split(".", 1)
    expected_signature = _sign_payload(
        payload_b64=payload_b64,
        secret=settings.session_secret,
    )
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise AdminAuthError("Invalid admin session signature.")

    payload = _decode_payload(payload_b64)

    subject = payload.get("sub")
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if not isinstance(subject, str) or not isinstance(issued_at, str) or not isinstance(
        expires_at, str
    ):
        raise AdminAuthError("Invalid admin session payload.")

    expires_at_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    current_time = now or datetime.now(UTC)
    if expires_at_dt < current_time:
        raise AdminAuthError("Admin session has expired.")

    return AdminSession(
        email=subject,
        issued_at=issued_at,
        expires_at=expires_at,
    )