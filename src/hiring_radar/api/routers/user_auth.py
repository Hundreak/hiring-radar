from __future__ import annotations

import html
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from hiring_radar.api.dependencies import (
    get_current_user_session,
    get_env_path,
    get_repository,
    get_user_auth_settings,
)
from hiring_radar.api.schemas.user_auth import (
    UserAuthMeResponse,
    UserConfirmPasswordResetRequest,
    UserConfirmPasswordResetResponse,
    UserConsumeMagicLinkRequest,
    UserPasswordLoginRequest,
    UserPasswordLoginResponse,
    UserPasswordResetRequest,
    UserPasswordResetRequestResponse,
    UserRequestMagicLinkRequest,
    UserRequestMagicLinkResponse,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.email_config import EmailConfigError, load_smtp_settings
from hiring_radar.models import Subscriber
from hiring_radar.services.email import EmailDeliveryError, EmailMessagePayload, send_email_via_smtp
from hiring_radar.services.user_auth import (
    PasswordValidationError,
    UserAuthSettings,
    UserSession,
    build_magic_link_expiration,
    build_magic_link_url,
    build_password_reset_expiration,
    build_password_reset_url,
    create_session_cookie_value,
    generate_magic_link_token,
    generate_password_reset_token,
    hash_magic_link_token,
    hash_password,
    hash_password_reset_token,
    normalize_email,
    parse_utc_datetime,
    password_hash_needs_upgrade,
    session_cookie_kwargs,
    utc_now,
    utc_now_iso,
    verify_password,
)

router = APIRouter(prefix="/api/user/auth", tags=["user-auth"])

GENERIC_MAGIC_LINK_RESPONSE = (
    "If that address is eligible, we have sent a secure sign-in link."
)
GENERIC_PASSWORD_RESET_RESPONSE = (
    "If that address is eligible, we have sent password reset instructions."
)
INVALID_LOGIN_DETAIL = "Invalid email or password."
PASSWORD_RESET_COMPLETED_MESSAGE = (
    "Password updated successfully. You can now sign in with your new password."
)

RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
UserAuthSettingsDep = Annotated[UserAuthSettings, Depends(get_user_auth_settings)]
UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]


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


def _resolve_frontend_base_url() -> str:
    app_base_url = os.getenv("HIRING_RADAR_APP_BASE_URL", "http://localhost:3000").strip()
    if not app_base_url:
        app_base_url = "http://localhost:3000"
    return app_base_url.rstrip("/")


def _resolve_frontend_login_base_url() -> str:
    login_path = os.getenv("HIRING_RADAR_FRONTEND_LOGIN_PATH", "/tr/login").strip() or "/tr/login"
    if not login_path.startswith("/"):
        login_path = f"/{login_path}"
    return f"{_resolve_frontend_base_url()}{login_path}"


def _resolve_frontend_reset_password_base_url() -> str:
    reset_path = os.getenv("HIRING_RADAR_FRONTEND_RESET_PASSWORD_PATH", "/tr/reset-password").strip() or "/tr/reset-password"
    if not reset_path.startswith("/"):
        reset_path = f"/{reset_path}"
    return f"{_resolve_frontend_base_url()}{reset_path}"


def _build_html_shell(*, title: str, intro: str, cta_href: str, cta_label: str, footer_lines: list[str], body_block: str) -> str:
    safe_title = html.escape(title)
    safe_intro = html.escape(intro)
    safe_href = html.escape(cta_href)
    safe_label = html.escape(cta_label)
    footer_html = "".join(
        f'<div style="margin-top:6px;color:#94a3b8;font-size:13px;line-height:1.7;">{html.escape(line)}</div>'
        for line in footer_lines
    )

    return f"""
    <html>
      <body style="margin:0;padding:0;background:#0b1220;font-family:Arial,sans-serif;color:#e5e7eb;">
        <div style="max-width:640px;margin:0 auto;padding:32px 20px;">
          <div style="background:#111827;border:1px solid #1f2937;border-radius:24px;overflow:hidden;">
            <div style="padding:28px 32px;border-bottom:1px solid #1f2937;">
              <div style="font-size:13px;letter-spacing:0.18em;text-transform:uppercase;color:#93c5fd;">CoreSift</div>
              <h1 style="margin:14px 0 0;font-size:28px;line-height:1.2;color:#ffffff;">{safe_title}</h1>
              <p style="margin:12px 0 0;font-size:15px;line-height:1.7;color:#cbd5e1;">{safe_intro}</p>
            </div>

            <div style="padding:32px;">
              {body_block}

              <div style="margin-top:28px;">
                <a href="{safe_href}" style="display:inline-block;background:#3b52f0;color:#ffffff;text-decoration:none;padding:14px 22px;border-radius:14px;font-size:15px;font-weight:600;">
                  {safe_label}
                </a>
              </div>

              <div style="margin-top:24px;">
                {footer_html}
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """


def _build_magic_link_email_payload(
    *,
    subscriber: Subscriber,
    login_url: str,
    expires_at: str,
) -> EmailMessagePayload:
    recipient_name = subscriber.full_name or "CoreSift kullanıcısı"
    body_text = "\n".join(
        [
            "CoreSift",
            "",
            f"Merhaba {recipient_name},",
            "",
            "Hesabına güvenli giriş yapmak için aşağıdaki bağlantıyı kullan:",
            login_url,
            "",
            f"Bu bağlantı {expires_at} tarihine kadar geçerlidir.",
            "Talebi sen başlatmadıysan bu e-postayı güvenle yok sayabilirsin.",
        ]
    )
    body_block = f"""
      <p style="margin:0 0 18px;font-size:15px;line-height:1.8;color:#cbd5e1;">
        Merhaba <strong style="color:#ffffff;">{html.escape(recipient_name)}</strong>, hesabına güvenli şekilde giriş yapabilmen için bağlantın hazır.
      </p>
      <div style="padding:18px 20px;border-radius:18px;background:#0f172a;border:1px solid #1e293b;">
        <div style="font-size:13px;color:#94a3b8;">Bağlantı geçerlilik süresi</div>
        <div style="margin-top:8px;font-size:15px;color:#ffffff;">{html.escape(expires_at)}</div>
      </div>
    """
    body_html = _build_html_shell(
        title="Güvenli giriş bağlantın hazır",
        intro="CoreSift hesabına tek tıkla güvenli şekilde erişebilmen için bu e-postayı gönderiyoruz.",
        cta_href=login_url,
        cta_label="Hesabıma giriş yap",
        footer_lines=[
            f"Bu bağlantı {expires_at} tarihine kadar geçerlidir.",
            "Bu talebi sen başlatmadıysan bu e-postayı güvenle yok sayabilirsin.",
        ],
        body_block=body_block,
    )
    return EmailMessagePayload(
        to=subscriber.email,
        subject="CoreSift giriş bağlantın",
        body_text=body_text,
        body_html=body_html,
    )


def _build_password_reset_email_payload(
    *,
    subscriber: Subscriber,
    reset_url: str,
    expires_at: str,
) -> EmailMessagePayload:
    recipient_name = subscriber.full_name or "CoreSift kullanıcısı"
    body_text = "\n".join(
        [
            "CoreSift",
            "",
            f"Merhaba {recipient_name},",
            "",
            "Şifreni güvenli şekilde sıfırlamak için aşağıdaki bağlantıyı kullan:",
            reset_url,
            "",
            f"Bu bağlantı {expires_at} tarihine kadar geçerlidir.",
            "Talebi sen başlatmadıysan bu e-postayı güvenle yok sayabilirsin.",
        ]
    )
    body_block = f"""
      <p style="margin:0 0 18px;font-size:15px;line-height:1.8;color:#cbd5e1;">
        Merhaba <strong style="color:#ffffff;">{html.escape(recipient_name)}</strong>, şifreni güvenli şekilde yenileyebilmen için bağlantın hazır.
      </p>
      <div style="padding:18px 20px;border-radius:18px;background:#0f172a;border:1px solid #1e293b;">
        <div style="font-size:13px;color:#94a3b8;">Bağlantı geçerlilik süresi</div>
        <div style="margin-top:8px;font-size:15px;color:#ffffff;">{html.escape(expires_at)}</div>
      </div>
    """
    body_html = _build_html_shell(
        title="Şifre sıfırlama bağlantın hazır",
        intro="CoreSift hesabında yeni bir şifre belirleyebilmen için bu e-postayı gönderiyoruz.",
        cta_href=reset_url,
        cta_label="Şifremi yenile",
        footer_lines=[
            f"Bu bağlantı {expires_at} tarihine kadar geçerlidir.",
            "Bu talebi sen başlatmadıysan hesabın için şu an bir işlem yapmana gerek yoktur.",
        ],
        body_block=body_block,
    )
    return EmailMessagePayload(
        to=subscriber.email,
        subject="CoreSift şifre sıfırlama bağlantın",
        body_text=body_text,
        body_html=body_html,
    )


def _issue_magic_link(
    *,
    repository: HiringRadarRepository,
    subscriber: Subscriber,
    settings: UserAuthSettings,
    redirect_path: str | None = None,
) -> tuple[str, str] | None:
    if subscriber.id is None or not subscriber.is_active:
        return None

    raw_token = generate_magic_link_token()
    token_hash = hash_magic_link_token(raw_token)
    expires_at = build_magic_link_expiration(settings=settings)
    created_at = utc_now_iso()

    repository.create_subscriber_magic_link(
        subscriber_id=subscriber.id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=created_at,
    )

    login_base_url = _resolve_frontend_login_base_url()
    login_url = build_magic_link_url(
        base_url=login_base_url,
        token=raw_token,
        email=subscriber.email,
        redirect_path=redirect_path,
    )
    return login_url, expires_at


def _load_magic_link_subscriber(
    *,
    repository: HiringRadarRepository,
    raw_token: str,
) -> Subscriber:
    token_hash = hash_magic_link_token(raw_token)
    link = repository.get_subscriber_magic_link_by_hash(token_hash)

    if link is None or link.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired sign-in link.",
        )

    if link.consumed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This sign-in link has already been used.",
        )

    if parse_utc_datetime(link.expires_at) <= utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This sign-in link has expired.",
        )

    subscriber = repository.get_subscriber_by_id(link.subscriber_id)
    if subscriber is None or subscriber.id is None or not subscriber.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is unavailable.",
        )

    consumed = repository.consume_subscriber_magic_link(
        link.id,
        consumed_at=utc_now_iso(),
    )
    if not consumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This sign-in link is no longer valid.",
        )

    return subscriber


@router.post("/request-magic-link", response_model=UserRequestMagicLinkResponse)
def request_magic_link(
    payload: UserRequestMagicLinkRequest,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
    env_path: Annotated[str, Depends(get_env_path)],
) -> UserRequestMagicLinkResponse:
    subscriber = repository.get_subscriber_by_email(normalize_email(payload.email))

    if subscriber is not None and subscriber.is_active:
        issued = _issue_magic_link(
            repository=repository,
            subscriber=subscriber,
            settings=auth_settings,
            redirect_path=payload.redirect_path,
        )

        if issued is not None:
            login_url, expires_at = issued
            try:
                smtp_settings = load_smtp_settings(env_path)
                send_email_via_smtp(
                    settings=smtp_settings,
                    payload=_build_magic_link_email_payload(
                        subscriber=subscriber,
                        login_url=login_url,
                        expires_at=expires_at,
                    ),
                )
            except (EmailConfigError, EmailDeliveryError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Sign-in email could not be sent: {exc}",
                ) from exc

    return UserRequestMagicLinkResponse(message=GENERIC_MAGIC_LINK_RESPONSE)


@router.post("/consume-magic-link", response_model=UserAuthMeResponse)
def consume_magic_link(
    payload: UserConsumeMagicLinkRequest,
    request: Request,
    response: Response,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
) -> UserAuthMeResponse:
    import hashlib as _hashlib
    subscriber = _load_magic_link_subscriber(
        repository=repository,
        raw_token=payload.token,
    )

    session_token = create_session_cookie_value(
        subscriber_id=subscriber.id or 0,
        email=subscriber.email,
        settings=auth_settings,
    )
    response.set_cookie(
        key=auth_settings.session_cookie_name,
        value=session_token,
        **session_cookie_kwargs(settings=auth_settings),
    )

    now = utc_now_iso()
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    token_hash = _hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    repository.create_session(
        subscriber_id=subscriber.id or 0,
        session_token_hash=token_hash,
        device_label=_parse_device_label(ua),
        ip_address=ip,
        user_agent=ua,
        now=now,
    )
    repository.add_login_history(
        subscriber_id=subscriber.id or 0,
        event_type="login_magic_link",
        ip_address=ip,
        user_agent=ua,
        now=now,
    )

    return UserAuthMeResponse(
        subscriber_id=subscriber.id or 0,
        email=subscriber.email,
    )


@router.post("/login-password", response_model=UserPasswordLoginResponse)
def login_password(
    payload: UserPasswordLoginRequest,
    request: Request,
    response: Response,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
) -> UserPasswordLoginResponse:
    import hashlib as _hashlib
    subscriber = repository.get_subscriber_by_email(normalize_email(payload.email))
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")

    if (
        subscriber is None
        or subscriber.id is None
        or not subscriber.is_active
        or not verify_password(payload.password, subscriber.password_hash)
    ):
        if subscriber and subscriber.id:
            repository.add_login_history(
                subscriber_id=subscriber.id,
                event_type="login_failed",
                ip_address=ip,
                user_agent=ua,
                now=utc_now_iso(),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_LOGIN_DETAIL,
        )

    if password_hash_needs_upgrade(subscriber.password_hash, settings=auth_settings):
        new_hash = hash_password(payload.password, settings=auth_settings)
        repository.set_subscriber_password(
            subscriber_id=subscriber.id,
            password_hash=new_hash,
            password_updated_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )

    session_token = create_session_cookie_value(
        subscriber_id=subscriber.id,
        email=subscriber.email,
        settings=auth_settings,
    )
    response.set_cookie(
        key=auth_settings.session_cookie_name,
        value=session_token,
        **session_cookie_kwargs(settings=auth_settings),
    )

    now = utc_now_iso()
    token_hash = _hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    repository.create_session(
        subscriber_id=subscriber.id,
        session_token_hash=token_hash,
        device_label=_parse_device_label(ua),
        ip_address=ip,
        user_agent=ua,
        now=now,
    )
    repository.add_login_history(
        subscriber_id=subscriber.id,
        event_type="login_success",
        ip_address=ip,
        user_agent=ua,
        now=now,
    )

    return UserPasswordLoginResponse(
        subscriber_id=subscriber.id,
        email=subscriber.email,
    )


@router.post(
    "/request-password-reset",
    response_model=UserPasswordResetRequestResponse,
)
def request_password_reset(
    payload: UserPasswordResetRequest,
    repository: RepositoryDep,
    env_path: Annotated[str, Depends(get_env_path)],
    auth_settings: UserAuthSettingsDep,
) -> UserPasswordResetRequestResponse:
    subscriber = repository.get_subscriber_by_email(normalize_email(payload.email))

    if subscriber is not None and subscriber.is_active and subscriber.id is not None:
        raw_token = generate_password_reset_token()
        token_hash = hash_password_reset_token(raw_token)
        expires_at = build_password_reset_expiration(settings=auth_settings)
        created_at = utc_now_iso()

        repository.create_subscriber_password_reset_token(
            subscriber_id=subscriber.id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=created_at,
        )

        reset_url = build_password_reset_url(
            base_url=_resolve_frontend_reset_password_base_url(),
            token=raw_token,
            email=subscriber.email,
        )

        try:
            smtp_settings = load_smtp_settings(env_path)
            send_email_via_smtp(
                settings=smtp_settings,
                payload=_build_password_reset_email_payload(
                    subscriber=subscriber,
                    reset_url=reset_url,
                    expires_at=expires_at,
                ),
            )
        except (EmailConfigError, EmailDeliveryError) as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password reset email could not be sent: {exc}",
            ) from exc

    return UserPasswordResetRequestResponse(message=GENERIC_PASSWORD_RESET_RESPONSE)


@router.post(
    "/confirm-password-reset",
    response_model=UserConfirmPasswordResetResponse,
)
def confirm_password_reset(
    payload: UserConfirmPasswordResetRequest,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
) -> UserConfirmPasswordResetResponse:
    link = repository.get_subscriber_password_reset_token_by_hash(
        hash_password_reset_token(payload.token)
    )
    if link is None or link.id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    if link.consumed_at is not None:
        raise HTTPException(status_code=400, detail="This reset link has already been used.")

    if parse_utc_datetime(link.expires_at) <= utc_now():
        raise HTTPException(status_code=400, detail="This reset link has expired.")

    subscriber = repository.get_subscriber_by_id(link.subscriber_id)
    if subscriber is None or subscriber.id is None or not subscriber.is_active:
        raise HTTPException(status_code=400, detail="This account is unavailable.")

    try:
        password_hash = hash_password(payload.password, settings=auth_settings)
    except PasswordValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated_at = utc_now_iso()
    updated_subscriber = repository.set_subscriber_password(
        subscriber_id=subscriber.id,
        password_hash=password_hash,
        password_updated_at=updated_at,
        updated_at=updated_at,
    )
    if updated_subscriber is None:
        raise HTTPException(status_code=500, detail="Password could not be updated.")

    consumed = repository.consume_subscriber_password_reset_token(
        link.id,
        consumed_at=updated_at,
    )
    if not consumed:
        raise HTTPException(status_code=400, detail="This reset link is no longer valid.")

    return UserConfirmPasswordResetResponse(message=PASSWORD_RESET_COMPLETED_MESSAGE)


@router.post("/logout")
def user_logout(
    response: Response,
    auth_settings: UserAuthSettingsDep,
) -> dict[str, bool]:
    response.delete_cookie(
        key=auth_settings.session_cookie_name,
        path="/",
        samesite=session_cookie_kwargs(settings=auth_settings)["samesite"],
        secure=session_cookie_kwargs(settings=auth_settings)["secure"],
    )
    return {"ok": True}


@router.get("/me", response_model=UserAuthMeResponse)
def user_auth_me(
    user_session: UserSessionDep,
) -> UserAuthMeResponse:
    return UserAuthMeResponse(
        subscriber_id=user_session.subscriber_id,
        email=user_session.email,
    )
