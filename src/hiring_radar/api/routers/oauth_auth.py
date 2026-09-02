"""Google OAuth 2.0 / OpenID Connect router."""
from __future__ import annotations

import os
from datetime import UTC
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from hiring_radar.api.csrf import attach_csrf_cookie
from hiring_radar.api.dependencies import (
    get_repository,
    get_user_auth_settings,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.google_auth import (
    OAUTH_STATE_TTL_SECONDS,
    GoogleOAuthError,
    GoogleOAuthSettings,
    build_google_authorize_url,
    exchange_code_for_id_token,
    generate_nonce,
    generate_state_token,
    hash_state_token,
    load_google_oauth_settings,
    verify_id_token,
)
from hiring_radar.services.user_auth import (
    UserAuthSettings,
    create_session_cookie_value,
    normalize_email,
    session_cookie_kwargs,
    utc_now_iso,
)

router = APIRouter(prefix="/api/user/auth/google", tags=["google-oauth"])

RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
UserAuthSettingsDep = Annotated[UserAuthSettings, Depends(get_user_auth_settings)]

_SAFE_LOCALES = frozenset({"tr", "en", "de"})
_DEFAULT_POST_AUTH_PATH = "/tr/settings/profile"


def _resolve_frontend_base_url() -> str:
    app_base_url = os.getenv("HIRING_RADAR_APP_BASE_URL", "http://localhost:3000").strip()
    return (app_base_url or "http://localhost:3000").rstrip("/")


def _sanitize_redirect_path(value: str | None) -> str:
    if not value or not value.startswith("/"):
        return _DEFAULT_POST_AUTH_PATH
    if value.startswith("//"):
        return _DEFAULT_POST_AUTH_PATH
    return value


def _build_error_redirect(redirect_path: str, error: str) -> str:
    locale = "tr"
    parts = redirect_path.strip("/").split("/")
    if parts and parts[0] in _SAFE_LOCALES:
        locale = parts[0]
    base = _resolve_frontend_base_url()
    params = urlencode({"error": "google_auth_failed", "detail": error[:120]})
    return f"{base}/{locale}/login?{params}"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _parse_device_label(user_agent: str) -> str:
    ua = user_agent.lower()
    browser = "Browser"
    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "edg" in ua:
        browser = "Edge"
    os_label = ""
    if "windows" in ua:
        os_label = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_label = "macOS"
    elif "linux" in ua:
        os_label = "Linux"
    elif "iphone" in ua:
        os_label = "iPhone"
    elif "android" in ua:
        os_label = "Android"
    return f"{browser} · {os_label}" if os_label else browser


def _issue_session(
    *,
    subscriber_id: int,
    email: str,
    request: Request,
    response: Response,
    repository: HiringRadarRepository,
    auth_settings: UserAuthSettings,
) -> None:
    import hashlib as _hashlib

    session_token = create_session_cookie_value(
        subscriber_id=subscriber_id,
        email=email,
        settings=auth_settings,
    )
    response.set_cookie(
        key=auth_settings.session_cookie_name,
        value=session_token,
        **session_cookie_kwargs(settings=auth_settings),
    )
    attach_csrf_cookie(response)
    now = utc_now_iso()
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    token_hash = _hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    repository.create_session(
        subscriber_id=subscriber_id,
        session_token_hash=token_hash,
        device_label=_parse_device_label(ua),
        ip_address=ip,
        user_agent=ua,
        now=now,
    )
    repository.add_login_history(
        subscriber_id=subscriber_id,
        event_type="login_google_oauth",
        ip_address=ip,
        user_agent=ua,
        now=now,
    )


@router.get("/initiate")
def google_initiate(
    request: Request,
    repository: RepositoryDep,
    redirect_path: str | None = None,
) -> RedirectResponse:
    try:
        settings: GoogleOAuthSettings = load_google_oauth_settings()
    except GoogleOAuthError:
        locale = "tr"
        base = _resolve_frontend_base_url()
        return RedirectResponse(
            url=f"{base}/{locale}/login?error=google_not_configured",
            status_code=302,
        )

    safe_redirect = _sanitize_redirect_path(redirect_path)
    raw_state = generate_state_token()
    nonce = generate_nonce()
    state_hash = hash_state_token(raw_state)

    from datetime import datetime, timedelta
    expires_at = (
        datetime.now(UTC) + timedelta(seconds=OAUTH_STATE_TTL_SECONDS)
    ).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    repository.create_oauth_state(
        state_token_hash=state_hash,
        redirect_path=safe_redirect,
        nonce=nonce,
        expires_at=expires_at,
        created_at=utc_now_iso(),
    )

    authorize_url = build_google_authorize_url(
        client_id=settings.client_id,
        redirect_uri=settings.redirect_uri,
        state=raw_state,
        nonce=nonce,
    )
    return RedirectResponse(url=authorize_url, status_code=302)


@router.get("/callback")
def google_callback(
    request: Request,
    response: Response,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    base = _resolve_frontend_base_url()

    # User cancelled or Google returned an error
    if error or not code or not state:
        return RedirectResponse(
            url=f"{base}/tr/login?error=google_auth_cancelled",
            status_code=302,
        )

    # Validate state (CSRF protection) — single-use, atomically deleted
    state_hash = hash_state_token(state)
    state_record = repository.get_and_delete_oauth_state(state_hash)

    if state_record is None:
        return RedirectResponse(
            url=f"{base}/tr/login?error=google_auth_failed&detail=invalid_state",
            status_code=302,
        )

    # Check state expiry
    from datetime import datetime
    try:
        expires_dt = datetime.fromisoformat(
            state_record.expires_at.replace("Z", "+00:00")
        )
        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=UTC)
    except ValueError:
        return RedirectResponse(
            url=f"{base}/tr/login?error=google_auth_failed&detail=state_expired",
            status_code=302,
        )

    if datetime.now(UTC) > expires_dt:
        return RedirectResponse(
            url=f"{base}/tr/login?error=google_auth_failed&detail=state_expired",
            status_code=302,
        )

    redirect_path = _sanitize_redirect_path(state_record.redirect_path)

    # Exchange code for tokens
    try:
        google_settings: GoogleOAuthSettings = load_google_oauth_settings()
    except GoogleOAuthError:
        return RedirectResponse(
            url=_build_error_redirect(redirect_path, "configuration_error"),
            status_code=302,
        )

    try:
        id_token = exchange_code_for_id_token(code=code, settings=google_settings)
        user_info = verify_id_token(
            id_token=id_token,
            client_id=google_settings.client_id,
            expected_nonce=state_record.nonce,
        )
    except GoogleOAuthError:
        return RedirectResponse(
            url=_build_error_redirect(redirect_path, "token_verification_failed"),
            status_code=302,
        )

    if not user_info.email_verified:
        return RedirectResponse(
            url=_build_error_redirect(redirect_path, "email_not_verified"),
            status_code=302,
        )

    now = utc_now_iso()
    email = normalize_email(user_info.email)

    # Resolve account — 3 cases:
    # 1. Existing Google link → load subscriber
    # 2. No Google link, email matches existing subscriber → link accounts
    # 3. Brand new user → create subscriber + link

    existing_link = repository.get_oauth_provider(
        provider="google", provider_user_id=user_info.sub
    )

    if existing_link is not None:
        subscriber = repository.get_subscriber_by_id(existing_link.subscriber_id)
        if subscriber is None or not subscriber.is_active:
            return RedirectResponse(
                url=_build_error_redirect(redirect_path, "account_unavailable"),
                status_code=302,
            )
    else:
        # Try to find by email — creates new subscriber if none exists
        subscriber, _created = repository.upsert_subscriber(
            email=email,
            full_name=user_info.name,
            updated_at=now,
        )
        # Link this Google identity — ignore if already linked (race condition guard)
        import sqlite3 as _sqlite3
        try:
            repository.create_oauth_provider_link(
                subscriber_id=subscriber.id or 0,
                provider="google",
                provider_user_id=user_info.sub,
                email_at_provider=user_info.email,
                now=now,
            )
        except _sqlite3.IntegrityError:
            # Already linked — proceed normally (concurrent request or retry)
            pass

    # Issue session cookie and redirect
    redirect_response = RedirectResponse(
        url=f"{base}{redirect_path}",
        status_code=302,
    )
    _issue_session(
        subscriber_id=subscriber.id or 0,
        email=subscriber.email,
        request=request,
        response=redirect_response,
        repository=repository,
        auth_settings=auth_settings,
    )
    return redirect_response
