from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from hiring_radar.security_runtime import (
    RuntimeSecurityError,
    bool_env,
    default_secure_cookie,
    normalize_cookie_samesite,
    require_production_secret,
)

EMPLOYER_SESSION_COOKIE_NAME = "hiring_radar_employer_session"
EMPLOYER_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
DEV_EMPLOYER_SESSION_SECRET = "dev-employer-session-secret-change-me"
_SESSION_SALT = "hiring-radar-employer-session-v1"
_PASSWORD_ALGORITHM = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 210_000


class EmployerAuthError(ValueError):
    """Raised when an employer auth token or credential cannot be validated."""


@dataclass(frozen=True)
class EmployerAuthSettings:
    session_secret: str
    session_max_age_seconds: int = EMPLOYER_SESSION_MAX_AGE_SECONDS
    secure_cookies: bool = False
    cookie_samesite: str = "lax"


@dataclass(frozen=True)
class EmployerSession:
    user_id: int
    company_id: int
    email: str
    role_key: str
    member_id: int | None = None
    issued_at: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "company_id": self.company_id,
            "email": self.email,
            "role_key": self.role_key,
            "member_id": self.member_id,
            "issued_at": self.issued_at,
        }


def load_employer_auth_settings() -> EmployerAuthSettings:
    secret = (
        os.getenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET")
        or os.getenv("HIRING_RADAR_USER_SESSION_SECRET")
        or os.getenv("HIRING_RADAR_ADMIN_SESSION_SECRET")
        or DEV_EMPLOYER_SESSION_SECRET
    )
    try:
        require_production_secret(
            "HIRING_RADAR_EMPLOYER_SESSION_SECRET",
            secret,
            unsafe_values={DEV_EMPLOYER_SESSION_SECRET},
        )
        secure_cookies = bool_env(
            "HIRING_RADAR_EMPLOYER_SESSION_COOKIE_SECURE",
            default=default_secure_cookie(),
        )
        cookie_samesite = normalize_cookie_samesite(
            "HIRING_RADAR_EMPLOYER_SESSION_COOKIE_SAMESITE",
            default="lax",
        )
    except RuntimeSecurityError as exc:
        raise EmployerAuthError(str(exc)) from exc

    return EmployerAuthSettings(
        session_secret=secret,
        secure_cookies=secure_cookies,
        cookie_samesite=cookie_samesite,
    )


def _serializer(settings: EmployerAuthSettings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt=_SESSION_SALT)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def hash_password(password: str) -> str:
    if not password:
        raise EmployerAuthError("Password cannot be empty.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PASSWORD_ITERATIONS,
    )
    return "$".join(
        [
            _PASSWORD_ALGORITHM,
            str(_PASSWORD_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, encoded_hash: str | None) -> bool:
    if not password or not encoded_hash:
        return False
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = encoded_hash.split("$", 3)
        if algorithm != _PASSWORD_ALGORITHM:
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_raw.encode("ascii"))
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def create_employer_session_token(
    session: EmployerSession,
    *,
    settings: EmployerAuthSettings | None = None,
) -> str:
    auth_settings = settings or load_employer_auth_settings()
    payload = session.to_payload() | {"issued_at": session.issued_at or _now_iso()}
    return _serializer(auth_settings).dumps(payload)


def decode_employer_session_token(
    token: str,
    *,
    settings: EmployerAuthSettings | None = None,
) -> EmployerSession:
    auth_settings = settings or load_employer_auth_settings()
    try:
        payload = _serializer(auth_settings).loads(
            token,
            max_age=auth_settings.session_max_age_seconds,
        )
    except SignatureExpired as exc:
        raise EmployerAuthError("Employer session expired.") from exc
    except BadSignature as exc:
        raise EmployerAuthError("Invalid employer session.") from exc

    try:
        return EmployerSession(
            user_id=int(payload["user_id"]),
            company_id=int(payload["company_id"]),
            email=str(payload["email"]),
            role_key=str(payload.get("role_key") or "viewer"),
            member_id=int(payload["member_id"]) if payload.get("member_id") is not None else None,
            issued_at=str(payload.get("issued_at") or ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EmployerAuthError("Invalid employer session payload.") from exc
