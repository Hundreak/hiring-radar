from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.email_config import load_env_file
from hiring_radar.models import Subscriber
from hiring_radar.services.email import EmailMessagePayload

USER_SESSION_COOKIE_NAME = "hiring_radar_user_session"
DEFAULT_USER_SESSION_TTL_SECONDS = 60 * 60 * 24 * 3
DEFAULT_MAGIC_LINK_TTL_SECONDS = 60 * 15


class UserAuthError(ValueError):
    """Raised when user auth configuration or tokens are invalid."""


@dataclass(slots=True, frozen=True)
class UserAuthSettings:
    app_base_url: str
    session_secret: str
    session_ttl_seconds: int = DEFAULT_USER_SESSION_TTL_SECONDS
    magic_link_ttl_seconds: int = DEFAULT_MAGIC_LINK_TTL_SECONDS


@dataclass(slots=True, frozen=True)
class UserSession:
    subscriber_id: int
    email: str
    issued_at: str
    expires_at: str


@dataclass(slots=True, frozen=True)
class MagicLinkIssueResult:
    subscriber: Subscriber
    raw_token: str
    login_url: str
    expires_at: str


def _coerce_positive_int(*, field_name: str, value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise UserAuthError(f"{field_name} must be an integer, got {value!r}") from exc

    if parsed < 1:
        raise UserAuthError(f"{field_name} must be >= 1")

    return parsed


def _utc_now(now: datetime | None = None) -> datetime:
    return now or datetime.now(UTC)


def _to_iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hash_magic_link_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def load_user_auth_settings(env_path: str | Path = ".env") -> UserAuthSettings:
    load_env_file(env_path)

    app_base_url = os.environ.get("HIRING_RADAR_APP_BASE_URL")
    session_secret = os.environ.get("HIRING_RADAR_USER_SESSION_SECRET")

    missing = [
        name
        for name, value in (
            ("HIRING_RADAR_APP_BASE_URL", app_base_url),
            ("HIRING_RADAR_USER_SESSION_SECRET", session_secret),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise UserAuthError(f"Missing required user auth settings: {joined}")

    session_ttl_seconds = _coerce_positive_int(
        field_name="HIRING_RADAR_USER_SESSION_TTL_SECONDS",
        value=os.environ.get("HIRING_RADAR_USER_SESSION_TTL_SECONDS"),
        default=DEFAULT_USER_SESSION_TTL_SECONDS,
    )
    magic_link_ttl_seconds = _coerce_positive_int(
        field_name="HIRING_RADAR_MAGIC_LINK_TTL_SECONDS",
        value=os.environ.get("HIRING_RADAR_MAGIC_LINK_TTL_SECONDS"),
        default=DEFAULT_MAGIC_LINK_TTL_SECONDS,
    )

    return UserAuthSettings(
        app_base_url=app_base_url.rstrip("/"),
        session_secret=session_secret,
        session_ttl_seconds=session_ttl_seconds,
        magic_link_ttl_seconds=magic_link_ttl_seconds,
    )


def issue_magic_link_for_email(
    *,
    repository: HiringRadarRepository,
    email: str,
    settings: UserAuthSettings,
    now: datetime | None = None,
) -> MagicLinkIssueResult | None:
    subscriber = repository.get_subscriber_by_email(email)
    if subscriber is None or subscriber.id is None or not subscriber.is_active:
        return None

    issued_at_dt = _utc_now(now)
    expires_at_dt = issued_at_dt + timedelta(seconds=settings.magic_link_ttl_seconds)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_magic_link_token(raw_token)

    repository.create_subscriber_magic_link(
        subscriber_id=subscriber.id,
        token_hash=token_hash,
        expires_at=_to_iso(expires_at_dt),
        created_at=_to_iso(issued_at_dt),
    )

    login_url = f"{settings.app_base_url}/app/login?token={raw_token}"

    return MagicLinkIssueResult(
        subscriber=subscriber,
        raw_token=raw_token,
        login_url=login_url,
        expires_at=_to_iso(expires_at_dt),
    )


def consume_magic_link_token(
    *,
    repository: HiringRadarRepository,
    raw_token: str,
    now: datetime | None = None,
) -> Subscriber:
    token_hash = hash_magic_link_token(raw_token)
    link = repository.get_subscriber_magic_link_by_hash(token_hash)

    if link is None or link.id is None:
        raise UserAuthError("Invalid or expired sign-in link.")

    if link.consumed_at is not None:
        raise UserAuthError("This sign-in link has already been used.")

    current_time = _utc_now(now)
    expires_at_dt = datetime.fromisoformat(link.expires_at.replace("Z", "+00:00"))
    if expires_at_dt < current_time:
        raise UserAuthError("This sign-in link has expired.")

    subscriber = repository.get_subscriber_by_id(link.subscriber_id)
    if subscriber is None or subscriber.id is None or not subscriber.is_active:
        raise UserAuthError("This account is unavailable.")

    consumed = repository.consume_subscriber_magic_link(
        link.id,
        consumed_at=_to_iso(current_time),
    )
    if not consumed:
        raise UserAuthError("This sign-in link is no longer valid.")

    return subscriber


def _encode_payload(payload: dict[str, str | int]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_payload(payload_b64: str) -> dict[str, str | int]:
    padding = "=" * (-len(payload_b64) % 4)

    try:
        raw = base64.urlsafe_b64decode(f"{payload_b64}{padding}".encode())
        payload = json.loads(raw.decode())
    except (ValueError, json.JSONDecodeError) as exc:
        raise UserAuthError("Invalid user session payload.") from exc

    if not isinstance(payload, dict):
        raise UserAuthError("Invalid user session payload.")

    return payload


def _sign_payload(*, payload_b64: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()


def create_user_session_token(
    *,
    subscriber_id: int,
    email: str,
    settings: UserAuthSettings,
    now: datetime | None = None,
) -> str:
    issued_at_dt = _utc_now(now)
    expires_at_dt = issued_at_dt + timedelta(seconds=settings.session_ttl_seconds)

    payload = {
        "sub_id": subscriber_id,
        "email": email,
        "iat": _to_iso(issued_at_dt),
        "exp": _to_iso(expires_at_dt),
    }
    payload_b64 = _encode_payload(payload)
    signature = _sign_payload(
        payload_b64=payload_b64,
        secret=settings.session_secret,
    )
    return f"{payload_b64}.{signature}"


def decode_user_session_token(
    *,
    token: str,
    settings: UserAuthSettings,
    now: datetime | None = None,
) -> UserSession:
    if "." not in token:
        raise UserAuthError("Invalid user session token.")

    payload_b64, provided_signature = token.split(".", 1)
    expected_signature = _sign_payload(
        payload_b64=payload_b64,
        secret=settings.session_secret,
    )
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise UserAuthError("Invalid user session signature.")

    payload = _decode_payload(payload_b64)

    subscriber_id = payload.get("sub_id")
    email = payload.get("email")
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")

    if not isinstance(subscriber_id, int) or not isinstance(email, str):
        raise UserAuthError("Invalid user session payload.")
    if not isinstance(issued_at, str) or not isinstance(expires_at, str):
        raise UserAuthError("Invalid user session payload.")

    expires_at_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    current_time = _utc_now(now)
    if expires_at_dt < current_time:
        raise UserAuthError("User session has expired.")

    return UserSession(
        subscriber_id=subscriber_id,
        email=email,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def build_magic_link_email_payload(
    *,
    recipient_email: str,
    login_url: str,
    expires_at: str,
) -> EmailMessagePayload:
    subject = "Your Hiring Radar sign-in link"
    body_text = "\n".join(
        [
            "Hiring Radar",
            "",
            "Use the secure link below to sign in to your preferences panel.",
            login_url,
            "",
            f"This link expires at {expires_at}.",
            "If you did not request this email, you can ignore it.",
        ]
    )

    return EmailMessagePayload(
        to=recipient_email,
        subject=subject,
        body_text=body_text,
    )