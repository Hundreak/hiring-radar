"""CSRF protection for cookie-authenticated browser requests.

The API uses HttpOnly session cookies for user, admin and employer sessions.
That is good for XSS resistance, but mutating requests also need an explicit
same-origin signal so a third-party site cannot submit a form/fetch against a
logged-in browser. This module implements a dependency-free double-submit cookie
layer:

- the server issues a non-HttpOnly CSRF cookie alongside session cookies;
- the frontend echoes that value in ``X-CSRF-Token`` for unsafe methods;
- unsafe API requests that carry a session cookie must provide a matching token.

Endpoints that create a session (login/signup/OAuth callback) are intentionally
exempt so users can authenticate before a token exists.
"""
from __future__ import annotations

import hmac
import os
import secrets
from collections.abc import Iterable
from dataclasses import dataclass

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from hiring_radar.api.security import ADMIN_SESSION_COOKIE_NAME
from hiring_radar.security_runtime import (
    bool_env,
    default_secure_cookie,
    normalize_cookie_samesite,
)
from hiring_radar.services.employer_auth import EMPLOYER_SESSION_COOKIE_NAME
from hiring_radar.services.user_auth import USER_SESSION_COOKIE_NAME

CSRF_COOKIE_NAME = os.getenv("HIRING_RADAR_CSRF_COOKIE_NAME", "hiring_radar_csrf")
CSRF_HEADER_NAME = os.getenv("HIRING_RADAR_CSRF_HEADER_NAME", "X-CSRF-Token")
CSRF_TOKEN_BYTES = 32
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
GENERIC_CSRF_DETAIL = "Invalid or missing CSRF token."

# Login/bootstrap endpoints cannot require a token because the browser does not
# have one before a session is created. They still get brute-force protection via
# Patch 03 rate limits.
DEFAULT_EXEMPT_PATHS = frozenset(
    {
        "/api/admin/auth/login",
        "/api/user/auth/login-password",
        "/api/user/auth/request-magic-link",
        "/api/user/auth/consume-magic-link",
        "/api/user/auth/request-password-reset",
        "/api/user/auth/confirm-password-reset",
        "/api/public/auth/signup/request-verification",
        "/api/public/auth/signup/verify",
        "/api/employer/auth/register",
        "/api/employer/auth/login",
    }
)
DEFAULT_EXEMPT_PREFIXES = (
    "/api/auth/google/",
    "/api/oauth/",
)


@dataclass(frozen=True, slots=True)
class CsrfSettings:
    enabled: bool = True
    cookie_name: str = CSRF_COOKIE_NAME
    header_name: str = CSRF_HEADER_NAME
    secure_cookie: bool = False
    cookie_samesite: str = "lax"
    cookie_max_age_seconds: int = 60 * 60 * 24 * 14


def _env_int(name: str, *, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}.")
    return value


def load_csrf_settings() -> CsrfSettings:
    """Resolve CSRF runtime settings from environment variables."""

    secure_cookie = bool_env(
        "HIRING_RADAR_CSRF_COOKIE_SECURE",
        default=default_secure_cookie(),
    )
    cookie_samesite = normalize_cookie_samesite(
        "HIRING_RADAR_CSRF_COOKIE_SAMESITE",
        default="lax",
    )
    return CsrfSettings(
        enabled=bool_env("HIRING_RADAR_CSRF_ENABLED", default=True),
        cookie_name=os.getenv("HIRING_RADAR_CSRF_COOKIE_NAME", CSRF_COOKIE_NAME),
        header_name=os.getenv("HIRING_RADAR_CSRF_HEADER_NAME", CSRF_HEADER_NAME),
        secure_cookie=secure_cookie,
        cookie_samesite=cookie_samesite,
        cookie_max_age_seconds=_env_int(
            "HIRING_RADAR_CSRF_COOKIE_MAX_AGE_SECONDS",
            default=60 * 60 * 24 * 14,
        ),
    )


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(CSRF_TOKEN_BYTES)


def attach_csrf_cookie(
    response: Response,
    *,
    settings: CsrfSettings | None = None,
    token: str | None = None,
) -> str:
    """Set and return a browser-readable CSRF cookie."""

    resolved = settings or load_csrf_settings()
    value = token or generate_csrf_token()
    response.set_cookie(
        key=resolved.cookie_name,
        value=value,
        max_age=resolved.cookie_max_age_seconds,
        httponly=False,
        secure=resolved.secure_cookie,
        samesite=resolved.cookie_samesite,
        path="/",
    )
    return value


def clear_csrf_cookie(response: Response, *, settings: CsrfSettings | None = None) -> None:
    resolved = settings or load_csrf_settings()
    response.delete_cookie(
        key=resolved.cookie_name,
        path="/",
        secure=resolved.secure_cookie,
        samesite=resolved.cookie_samesite,
    )


def _has_session_cookie(request: Request, session_cookie_names: Iterable[str]) -> bool:
    return any(bool(request.cookies.get(name)) for name in session_cookie_names)


def _is_exempt_path(path: str) -> bool:
    if path in DEFAULT_EXEMPT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in DEFAULT_EXEMPT_PREFIXES)


def validate_csrf_request(
    request: Request,
    *,
    settings: CsrfSettings | None = None,
    session_cookie_names: Iterable[str] | None = None,
) -> bool:
    """Return whether a request satisfies the CSRF double-submit check."""

    resolved = settings or load_csrf_settings()
    if not resolved.enabled:
        return True

    if request.method.upper() in SAFE_METHODS:
        return True

    if not request.url.path.startswith("/api/"):
        return True

    if _is_exempt_path(request.url.path):
        return True

    cookie_names = tuple(
        session_cookie_names
        or (
            os.getenv("HIRING_RADAR_SESSION_COOKIE_NAME", USER_SESSION_COOKIE_NAME),
            ADMIN_SESSION_COOKIE_NAME,
            EMPLOYER_SESSION_COOKIE_NAME,
        )
    )
    if not _has_session_cookie(request, cookie_names):
        return True

    cookie_token = request.cookies.get(resolved.cookie_name)
    header_token = request.headers.get(resolved.header_name)
    if not cookie_token or not header_token:
        return False

    return hmac.compare_digest(cookie_token, header_token)


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware enforcing CSRF for session-cookie requests."""

    def __init__(self, app: ASGIApp, *, settings: CsrfSettings | None = None) -> None:
        super().__init__(app)
        self.settings = settings or load_csrf_settings()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not validate_csrf_request(request, settings=self.settings):
            return JSONResponse(
                {"detail": GENERIC_CSRF_DETAIL},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        response = await call_next(request)

        # Backfill a token for already-authenticated browsers after safe API
        # requests. Login/signup endpoints still attach an explicit token when
        # they create a session.
        if (
            self.settings.enabled
            and request.method.upper() in SAFE_METHODS
            and request.url.path.startswith("/api/")
            and not request.cookies.get(self.settings.cookie_name)
            and _has_session_cookie(
                request,
                (
                    os.getenv("HIRING_RADAR_SESSION_COOKIE_NAME", USER_SESSION_COOKIE_NAME),
                    ADMIN_SESSION_COOKIE_NAME,
                    EMPLOYER_SESSION_COOKIE_NAME,
                ),
            )
        ):
            attach_csrf_cookie(response, settings=self.settings)

        return response
