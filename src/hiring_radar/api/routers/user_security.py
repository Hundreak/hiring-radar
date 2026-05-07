from __future__ import annotations

import base64
import hashlib
import hmac
import html
import os
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from hiring_radar.api.dependencies import (
    get_current_user_session,
    get_env_path,
    get_repository,
    get_user_auth_settings,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.email_config import EmailConfigError, load_smtp_settings
from hiring_radar.services.email import EmailDeliveryError, EmailMessagePayload, send_email_via_smtp
from hiring_radar.services.user_auth import (
    PasswordValidationError,
    UserAuthSettings,
    UserSession,
    build_expiration_iso,
    hash_password,
    normalize_email,
    session_cookie_kwargs,
    utc_now,
    utc_now_iso,
    verify_password,
)

router = APIRouter(prefix="/api/user/security", tags=["user-security"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
UserAuthSettingsDep = Annotated[UserAuthSettings, Depends(get_user_auth_settings)]

# ── Request / Response schemas ──────────────────────────────────


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=4096)
    new_password: str = Field(min_length=1, max_length=4096)
    new_password_confirmation: str = Field(min_length=1, max_length=4096)


class SessionResponse(BaseModel):
    id: int
    device_label: str
    ip_address: str
    is_current: bool
    created_at: str | None
    last_active_at: str | None


class LoginHistoryResponse(BaseModel):
    id: int
    event_type: str
    ip_address: str
    detail: str | None
    created_at: str | None


class RequestEmailChangeRequest(BaseModel):
    new_email: EmailStr
    current_password: str = Field(min_length=1, max_length=4096)


class ConfirmEmailChangeRequest(BaseModel):
    verification_code: str = Field(min_length=6, max_length=6)


class SetupTotpResponse(BaseModel):
    secret: str
    otpauth_uri: str


class VerifyTotpRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class DeleteAccountRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)
    current_password: str = Field(min_length=1, max_length=4096)


# ── Helpers ─────────────────────────────────────────────────────


def _hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _generate_email_verification_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


def _hash_email_verification_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def _resolve_frontend_base_url() -> str:
    return (os.getenv("HIRING_RADAR_APP_BASE_URL", "http://localhost:3000").strip().rstrip("/")
            or "http://localhost:3000")


def _build_email_change_email(
    *,
    recipient_email: str,
    recipient_name: str,
    verification_code: str,
) -> EmailMessagePayload:
    safe_name = html.escape(recipient_name)
    safe_code = html.escape(verification_code)

    body_text = (
        f"Merhaba {recipient_name},\n\n"
        f"E-posta adresini değiştirmek için doğrulama kodun: {verification_code}\n\n"
        "Bu kodu 10 dakika içinde gir.\n"
        "Bu talebi sen başlatmadıysan bu e-postayı güvenle yok sayabilirsin."
    )

    body_html = f"""
    <html>
      <body style="margin:0;padding:0;background:#0b1220;font-family:Arial,sans-serif;color:#e5e7eb;">
        <div style="max-width:640px;margin:0 auto;padding:32px 20px;">
          <div style="background:#111827;border:1px solid #1f2937;border-radius:24px;overflow:hidden;">
            <div style="padding:28px 32px;border-bottom:1px solid #1f2937;">
              <div style="font-size:13px;letter-spacing:0.18em;text-transform:uppercase;color:#93c5fd;">CoreSift</div>
              <h1 style="margin:14px 0 0;font-size:28px;line-height:1.2;color:#ffffff;">E-posta değişikliği doğrulama</h1>
              <p style="margin:12px 0 0;font-size:15px;line-height:1.7;color:#cbd5e1;">
                Merhaba <strong style="color:#ffffff;">{safe_name}</strong>, yeni e-posta adresini doğrulamak için aşağıdaki kodu kullan.
              </p>
            </div>
            <div style="padding:32px;">
              <div style="padding:24px;border-radius:18px;background:#0f172a;border:1px solid #1e293b;text-align:center;">
                <div style="font-size:13px;color:#94a3b8;">Doğrulama kodu</div>
                <div style="margin-top:12px;font-size:36px;letter-spacing:0.3em;font-weight:700;color:#3b52f0;">{safe_code}</div>
              </div>
              <div style="margin-top:24px;">
                <div style="margin-top:6px;color:#94a3b8;font-size:13px;line-height:1.7;">Bu kod 10 dakika geçerlidir.</div>
                <div style="margin-top:6px;color:#94a3b8;font-size:13px;line-height:1.7;">Bu talebi sen başlatmadıysan bu e-postayı güvenle yok sayabilirsin.</div>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """

    return EmailMessagePayload(
        to=recipient_email,
        subject="CoreSift — E-posta değişikliği doğrulama kodu",
        body_text=body_text,
        body_html=body_html,
    )


# ── Endpoints ───────────────────────────────────────────────────


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    user_session: UserSessionDep,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
) -> dict:
    if body.new_password != body.new_password_confirmation:
        raise HTTPException(400, "Password confirmation does not match.")

    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(404, "Account not found.")

    if not verify_password(body.current_password, subscriber.password_hash):
        raise HTTPException(401, "Current password is incorrect.")

    try:
        new_hash = hash_password(body.new_password, settings=auth_settings)
    except PasswordValidationError as exc:
        raise HTTPException(422, str(exc)) from exc

    now = utc_now_iso()
    repository.set_subscriber_password(
        subscriber_id=user_session.subscriber_id,
        password_hash=new_hash,
        password_updated_at=now,
        updated_at=now,
    )
    repository.add_login_history(
        subscriber_id=user_session.subscriber_id,
        event_type="password_changed",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        now=now,
    )
    return {"ok": True}


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> list[SessionResponse]:
    sessions = repository.list_active_sessions(user_session.subscriber_id)
    return [
        SessionResponse(
            id=s.id or 0,
            device_label=s.device_label,
            ip_address=s.ip_address,
            is_current=s.is_current,
            created_at=s.created_at,
            last_active_at=s.last_active_at,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204, response_class=Response)
def end_session(
    session_id: int,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> Response:
    ok = repository.expire_session(
        session_id, subscriber_id=user_session.subscriber_id, now=utc_now_iso()
    )
    if not ok:
        raise HTTPException(404, "Session not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessions/end-all-others")
def end_all_other_sessions(
    request: Request,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> dict:
    token_hash = _hash_session_token(
        request.cookies.get("hiring_radar_session", "")
    )
    current = repository.get_session_by_token_hash(token_hash)
    count = repository.expire_all_other_sessions(
        subscriber_id=user_session.subscriber_id,
        keep_session_id=current.id if current else None,
        now=utc_now_iso(),
    )
    return {"ended": count}


@router.get("/login-history", response_model=list[LoginHistoryResponse])
def login_history(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> list[LoginHistoryResponse]:
    entries = repository.list_login_history(user_session.subscriber_id, limit=20)
    return [
        LoginHistoryResponse(
            id=e.id or 0,
            event_type=e.event_type,
            ip_address=e.ip_address,
            detail=e.detail,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.post("/request-email-change")
def request_email_change(
    body: RequestEmailChangeRequest,
    request: Request,
    user_session: UserSessionDep,
    repository: RepositoryDep,
    env_path: Annotated[str, Depends(get_env_path)],
) -> dict:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(404, "Account not found.")

    if not verify_password(body.current_password, subscriber.password_hash):
        raise HTTPException(401, "Current password is incorrect.")

    new_email = normalize_email(body.new_email)
    if new_email == normalize_email(subscriber.email):
        raise HTTPException(422, "New email is the same as current.")

    existing = repository.get_subscriber_by_email(new_email)
    if existing is not None:
        raise HTTPException(409, "Email is already in use.")

    code = _generate_email_verification_code()
    code_hash = _hash_email_verification_code(code)
    now = utc_now_iso()
    expires_at = build_expiration_iso(ttl_seconds=600)

    repository.create_email_change_request(
        subscriber_id=user_session.subscriber_id,
        new_email=new_email,
        verification_code_hash=code_hash,
        expires_at=expires_at,
        now=now,
    )

    try:
        smtp_settings = load_smtp_settings(env_path)
        send_email_via_smtp(
            settings=smtp_settings,
            payload=_build_email_change_email(
                recipient_email=new_email,
                recipient_name=subscriber.full_name or "CoreSift kullanıcısı",
                verification_code=code,
            ),
        )
    except (EmailConfigError, EmailDeliveryError) as exc:
        raise HTTPException(500, f"Verification email could not be sent: {exc}") from exc

    return {"ok": True, "message": "Verification code sent to new email."}


@router.post("/confirm-email-change")
def confirm_email_change(
    body: ConfirmEmailChangeRequest,
    request: Request,
    user_session: UserSessionDep,
    repository: RepositoryDep,
    response: Response,
    auth_settings: UserAuthSettingsDep,
) -> dict:
    req = repository.get_latest_email_change_request(user_session.subscriber_id)
    if req is None or req.id is None:
        raise HTTPException(404, "No pending email change request.")

    from hiring_radar.services.user_auth import parse_utc_datetime
    if parse_utc_datetime(req.expires_at) <= utc_now():
        raise HTTPException(400, "Verification code has expired.")

    code_hash = _hash_email_verification_code(body.verification_code)
    if not hmac.compare_digest(code_hash, req.verification_code_hash):
        raise HTTPException(400, "Invalid verification code.")

    now = utc_now_iso()
    repository.consume_email_change_request(req.id, consumed_at=now)
    repository.update_subscriber_email(
        user_session.subscriber_id, new_email=req.new_email, updated_at=now
    )

    repository.add_login_history(
        subscriber_id=user_session.subscriber_id,
        event_type="email_changed",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        detail=f"Changed to {req.new_email}",
        now=now,
    )

    from hiring_radar.services.user_auth import create_session_cookie_value
    new_token = create_session_cookie_value(
        subscriber_id=user_session.subscriber_id,
        email=req.new_email,
        settings=auth_settings,
    )
    response.set_cookie(
        key=auth_settings.session_cookie_name,
        value=new_token,
        **session_cookie_kwargs(settings=auth_settings),
    )

    return {"ok": True, "new_email": req.new_email}


@router.post("/totp/setup", response_model=SetupTotpResponse)
def setup_totp(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SetupTotpResponse:
    secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    email = subscriber.email if subscriber else user_session.email

    repository.upsert_totp_secret(
        subscriber_id=user_session.subscriber_id,
        secret_encrypted=secret,
        now=utc_now_iso(),
    )

    otpauth_uri = f"otpauth://totp/CoreSift:{email}?secret={secret}&issuer=CoreSift&digits=6&period=30"
    return SetupTotpResponse(secret=secret, otpauth_uri=otpauth_uri)


@router.post("/totp/verify")
def verify_totp(
    body: VerifyTotpRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> dict:
    totp = repository.get_totp_secret(user_session.subscriber_id)
    if totp is None:
        raise HTTPException(404, "TOTP not set up.")

    if not _verify_totp_code(totp.secret_encrypted, body.code):
        raise HTTPException(400, "Invalid TOTP code.")

    repository.verify_totp_secret(user_session.subscriber_id, verified_at=utc_now_iso())
    return {"ok": True}


@router.delete("/totp", status_code=204, response_class=Response)
def disable_totp(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> Response:
    repository.delete_totp_secret(user_session.subscriber_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/totp/status")
def totp_status(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> dict:
    totp = repository.get_totp_secret(user_session.subscriber_id)
    if totp is None:
        return {"enabled": False, "verified": False}
    return {"enabled": True, "verified": totp.is_verified}


@router.post("/delete-account", status_code=200)
def delete_account(
    body: DeleteAccountRequest,
    request: Request,
    response: Response,
    user_session: UserSessionDep,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
) -> dict:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(404, "Account not found.")

    if not verify_password(body.current_password, subscriber.password_hash):
        raise HTTPException(401, "Password is incorrect.")

    now = utc_now_iso()
    deleted = repository.delete_subscriber_account(
        user_session.subscriber_id,
        email=subscriber.email,
        reason=body.reason,
        deleted_at=now,
    )
    if not deleted:
        raise HTTPException(500, "Account deletion failed.")

    response.delete_cookie(
        key=auth_settings.session_cookie_name,
        path="/",
        samesite=session_cookie_kwargs(settings=auth_settings)["samesite"],
        secure=session_cookie_kwargs(settings=auth_settings)["secure"],
    )

    return {"ok": True, "message": "Account permanently deleted."}


# ── TOTP verification helper ───────────────────────────────────

import time as _time
import struct as _struct


def _verify_totp_code(secret_b32: str, code: str, *, window: int = 1) -> bool:
    try:
        padded = secret_b32 + "=" * (-len(secret_b32) % 8)
        key = base64.b32decode(padded.upper())
    except Exception:
        return False

    now_counter = int(_time.time()) // 30
    for offset in range(-window, window + 1):
        counter = now_counter + offset
        msg = _struct.pack(">Q", counter)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[-1] & 0x0F
        truncated = _struct.unpack(">I", h[o: o + 4])[0] & 0x7FFFFFFF
        expected = str(truncated % 10**6).zfill(6)
        if hmac.compare_digest(code.strip(), expected):
            return True
    return False
