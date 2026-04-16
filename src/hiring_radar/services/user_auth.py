from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from itsdangerous import BadSignature, URLSafeSerializer

from hiring_radar.email_config import load_env_file


class UserAuthError(ValueError):
    """Base error for user auth flows."""


class PasswordValidationError(UserAuthError):
    """Raised when a supplied password does not satisfy policy."""


class SessionDecodeError(UserAuthError):
    """Raised when a signed session payload cannot be decoded safely."""


USER_SESSION_COOKIE_NAME = os.getenv(
    "HIRING_RADAR_SESSION_COOKIE_NAME",
    "hiring_radar_session",
)


@dataclass(slots=True, frozen=True)
class UserAuthSettings:
    secret_key: str
    session_cookie_name: str = USER_SESSION_COOKIE_NAME
    session_ttl_seconds: int = 60 * 60 * 24 * 14
    magic_link_ttl_seconds: int = 60 * 30
    password_reset_ttl_seconds: int = 60 * 30
    signup_verification_ttl_seconds: int = 60 * 10
    password_min_length: int = 10
    password_pbkdf2_iterations: int = 600_000
    session_signing_salt: str = "hiring-radar:user-session:v1"


@dataclass(slots=True, frozen=True)
class UserSession:
    subscriber_id: int
    email: str
    issued_at: str
    expires_at: str


def load_user_auth_settings(env_path: str | os.PathLike[str] = ".env") -> UserAuthSettings:
    load_env_file(Path(env_path))

    secret_key = os.getenv("HIRING_RADAR_AUTH_SECRET") or os.getenv(
        "HIRING_RADAR_SECRET_KEY"
    )
    if not secret_key:
        secret_key = "dev-user-auth-secret"

    return UserAuthSettings(
        secret_key=secret_key,
        session_cookie_name=os.getenv(
            "HIRING_RADAR_SESSION_COOKIE_NAME",
            USER_SESSION_COOKIE_NAME,
        ),
        session_ttl_seconds=int(
            os.getenv("HIRING_RADAR_SESSION_TTL_SECONDS", str(60 * 60 * 24 * 14))
        ),
        magic_link_ttl_seconds=int(
            os.getenv("HIRING_RADAR_MAGIC_LINK_TTL_SECONDS", str(60 * 30))
        ),
        password_reset_ttl_seconds=int(
            os.getenv("HIRING_RADAR_PASSWORD_RESET_TTL_SECONDS", str(60 * 30))
        ),
        signup_verification_ttl_seconds=int(
            os.getenv("HIRING_RADAR_SIGNUP_VERIFICATION_TTL_SECONDS", str(60 * 10))
        ),
        password_min_length=int(
            os.getenv("HIRING_RADAR_PASSWORD_MIN_LENGTH", "10")
        ),
        password_pbkdf2_iterations=int(
            os.getenv("HIRING_RADAR_PASSWORD_PBKDF2_ITERATIONS", "600000")
        ),
        session_signing_salt=os.getenv(
            "HIRING_RADAR_SESSION_SIGNING_SALT",
            "hiring-radar:user-session:v1",
        ),
    )


def normalize_email(email: str) -> str:
    return email.strip().lower()


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return format_utc_datetime(utc_now())


def parse_utc_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def format_utc_datetime(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_expiration_iso(*, ttl_seconds: int, now: datetime | None = None) -> str:
    issued_at = now or utc_now()
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    return format_utc_datetime(expires_at)


def build_user_session(
    *,
    subscriber_id: int,
    email: str,
    settings: UserAuthSettings | None = None,
    now: datetime | None = None,
) -> UserSession:
    resolved_settings = settings or load_user_auth_settings()
    issued_at_dt = now or utc_now()
    expires_at_dt = issued_at_dt + timedelta(
        seconds=resolved_settings.session_ttl_seconds
    )
    return UserSession(
        subscriber_id=subscriber_id,
        email=normalize_email(email),
        issued_at=format_utc_datetime(issued_at_dt),
        expires_at=format_utc_datetime(expires_at_dt),
    )


def _build_session_serializer(settings: UserAuthSettings) -> URLSafeSerializer:
    return URLSafeSerializer(
        secret_key=settings.secret_key,
        salt=settings.session_signing_salt,
    )


def sign_user_session(
    session: UserSession,
    *,
    settings: UserAuthSettings | None = None,
) -> str:
    resolved_settings = settings or load_user_auth_settings()
    serializer = _build_session_serializer(resolved_settings)
    return serializer.dumps(asdict(session))


def decode_user_session(
    value: str,
    *,
    settings: UserAuthSettings | None = None,
) -> UserSession:
    resolved_settings = settings or load_user_auth_settings()
    serializer = _build_session_serializer(resolved_settings)

    try:
        payload = serializer.loads(value)
    except BadSignature as exc:
        raise SessionDecodeError("Invalid session signature.") from exc

    if not isinstance(payload, dict):
        raise SessionDecodeError("Invalid session payload shape.")

    try:
        session = UserSession(
            subscriber_id=int(payload["subscriber_id"]),
            email=normalize_email(str(payload["email"])),
            issued_at=str(payload["issued_at"]),
            expires_at=str(payload["expires_at"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SessionDecodeError("Invalid session payload fields.") from exc

    if parse_utc_datetime(session.expires_at) <= utc_now():
        raise SessionDecodeError("Session has expired.")

    return session


decode_user_session_token = decode_user_session


def create_session_cookie_value(
    *,
    subscriber_id: int,
    email: str,
    settings: UserAuthSettings | None = None,
) -> str:
    resolved_settings = settings or load_user_auth_settings()
    session = build_user_session(
        subscriber_id=subscriber_id,
        email=email,
        settings=resolved_settings,
    )
    return sign_user_session(session, settings=resolved_settings)


def generate_magic_link_token() -> str:
    return secrets.token_urlsafe(32)


def hash_magic_link_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_signup_verification_code() -> str:
    alphabet = "0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def hash_signup_verification_code(code: str) -> str:
    normalized = code.strip().upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def verify_signup_verification_code(code: str, expected_hash: str) -> bool:
    actual_hash = hash_signup_verification_code(code)
    return hmac.compare_digest(actual_hash, expected_hash)


def _b64encode_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _b64decode_bytes(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def validate_password_strength(
    password: str,
    *,
    settings: UserAuthSettings | None = None,
) -> None:
    resolved_settings = settings or load_user_auth_settings()

    if len(password) < resolved_settings.password_min_length:
        raise PasswordValidationError(
            "Password must be at least "
            f"{resolved_settings.password_min_length} characters long."
        )
    if password.isspace():
        raise PasswordValidationError("Password cannot contain only whitespace.")
    if not any(char.islower() for char in password):
        raise PasswordValidationError(
            "Password must include at least one lowercase letter."
        )
    if not any(char.isupper() for char in password):
        raise PasswordValidationError(
            "Password must include at least one uppercase letter."
        )
    if not any(char.isdigit() for char in password):
        raise PasswordValidationError("Password must include at least one digit.")
    if not any(not char.isalnum() for char in password):
        raise PasswordValidationError(
            "Password must include at least one special character."
        )


def hash_password(
    password: str,
    *,
    settings: UserAuthSettings | None = None,
) -> str:
    resolved_settings = settings or load_user_auth_settings()
    validate_password_strength(password, settings=resolved_settings)

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        resolved_settings.password_pbkdf2_iterations,
    )
    return (
        "pbkdf2_sha256"
        f"${resolved_settings.password_pbkdf2_iterations}"
        f"${_b64encode_bytes(salt)}"
        f"${_b64encode_bytes(digest)}"
    )


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    try:
        algorithm, iterations_raw, salt_b64, digest_b64 = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_raw)
        salt = _b64decode_bytes(salt_b64)
        expected_digest = _b64decode_bytes(digest_b64)
    except (TypeError, ValueError):
        return False

    derived_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(derived_digest, expected_digest)


def password_hash_needs_upgrade(
    password_hash: str | None,
    *,
    settings: UserAuthSettings | None = None,
) -> bool:
    if not password_hash:
        return True

    resolved_settings = settings or load_user_auth_settings()

    try:
        algorithm, iterations_raw, _, _ = password_hash.split("$", 3)
    except ValueError:
        return True

    if algorithm != "pbkdf2_sha256":
        return True

    try:
        iterations = int(iterations_raw)
    except ValueError:
        return True

    return iterations < resolved_settings.password_pbkdf2_iterations


def build_magic_link_expiration(
    *,
    settings: UserAuthSettings | None = None,
    now: datetime | None = None,
) -> str:
    resolved_settings = settings or load_user_auth_settings()
    return build_expiration_iso(
        ttl_seconds=resolved_settings.magic_link_ttl_seconds,
        now=now,
    )


def build_password_reset_expiration(
    *,
    settings: UserAuthSettings | None = None,
    now: datetime | None = None,
) -> str:
    resolved_settings = settings or load_user_auth_settings()
    return build_expiration_iso(
        ttl_seconds=resolved_settings.password_reset_ttl_seconds,
        now=now,
    )


def build_signup_verification_expiration(
    *,
    settings: UserAuthSettings | None = None,
    now: datetime | None = None,
) -> str:
    resolved_settings = settings or load_user_auth_settings()
    return build_expiration_iso(
        ttl_seconds=resolved_settings.signup_verification_ttl_seconds,
        now=now,
    )


def build_magic_link_url(
    *,
    base_url: str,
    token: str,
    email: str,
    redirect_path: str | None = None,
) -> str:
    separator = "&" if "?" in base_url else "?"
    url = f"{base_url}{separator}token={token}&email={normalize_email(email)}"
    if redirect_path and redirect_path.startswith("/"):
        url += f"&redirect={redirect_path}"
    return url


def build_password_reset_url(
    *,
    base_url: str,
    token: str,
    email: str,
) -> str:
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}token={token}&email={normalize_email(email)}"


def session_cookie_kwargs(
    *,
    settings: UserAuthSettings | None = None,
) -> dict[str, Any]:
    resolved_settings = settings or load_user_auth_settings()
    secure_cookie = os.getenv("HIRING_RADAR_SESSION_COOKIE_SECURE", "0") == "1"
    same_site = os.getenv("HIRING_RADAR_SESSION_COOKIE_SAMESITE", "lax")

    return {
        "httponly": True,
        "secure": secure_cookie,
        "samesite": same_site,
        "max_age": resolved_settings.session_ttl_seconds,
        "path": "/",
    }
