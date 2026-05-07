from __future__ import annotations

import html
import os
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel, EmailStr, Field

from hiring_radar.api.dependencies import get_env_path, get_repository, get_user_auth_settings
from hiring_radar.api.schemas.public_auth import (
    PublicSignupConfirmRequest,
    PublicSignupResponse,
    PublicSignupVerificationRequest,
    PublicSignupVerificationResponse,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.email_config import EmailConfigError, load_smtp_settings
from hiring_radar.services.email import EmailDeliveryError, EmailMessagePayload, send_email_via_smtp
from hiring_radar.services.user_auth import (
    PasswordValidationError,
    UserAuthSettings,
    build_signup_verification_expiration,
    create_session_cookie_value,
    generate_signup_verification_code,
    hash_password,
    hash_signup_verification_code,
    normalize_email,
    parse_utc_datetime,
    session_cookie_kwargs,
    utc_now,
    utc_now_iso,
    verify_signup_verification_code,
)

router = APIRouter(prefix="/api/public/auth", tags=["public-auth"])

SIGNUP_VERIFICATION_SENT_MESSAGE = (
    "Verification code sent. Please check your email inbox."
)
SIGNUP_COMPLETED_MESSAGE = (
    "Your account has been created successfully. You are now signed in."
)

RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
UserAuthSettingsDep = Annotated[UserAuthSettings, Depends(get_user_auth_settings)]


class LegacySignupChallengeResponse(BaseModel):
    challenge_text: str
    challenge_token: str


class LegacySignupRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=200)
    challenge_token: str = Field(min_length=1)
    challenge_answer: str = Field(min_length=1, max_length=32)


def _legacy_signup_serializer() -> URLSafeSerializer:
    secret_key = os.getenv("HIRING_RADAR_AUTH_SECRET") or os.getenv("HIRING_RADAR_SECRET_KEY") or "dev-user-auth-secret"
    return URLSafeSerializer(secret_key=secret_key, salt="hiring-radar:legacy-signup-challenge:v1")


def _build_legacy_challenge_text() -> str:
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(5))


def issue_magic_link_for_email(**_: object) -> None:
    """Backward-compatible hook for the legacy public signup flow.

    Older tests and local scripts monkeypatch this symbol directly. The current
    product flow uses email verification before account creation, so the legacy
    endpoint keeps this as a no-op hook rather than sending mail by default.
    """
    return None


@router.get("/signup-challenge", response_model=LegacySignupChallengeResponse)
def create_legacy_signup_challenge() -> LegacySignupChallengeResponse:
    challenge_text = _build_legacy_challenge_text()
    challenge_token = _legacy_signup_serializer().dumps({"answer": challenge_text})
    return LegacySignupChallengeResponse(
        challenge_text=challenge_text,
        challenge_token=challenge_token,
    )


@router.post("/signup")
def legacy_public_signup(
    payload: LegacySignupRequest,
    repository: RepositoryDep,
    env_path: Annotated[str, Depends(get_env_path)],
) -> dict[str, bool]:
    try:
        token_payload = _legacy_signup_serializer().loads(payload.challenge_token)
    except BadSignature as exc:
        raise HTTPException(status_code=400, detail="Invalid signup challenge.") from exc

    expected_answer = str(token_payload.get("answer", "")).strip().casefold() if isinstance(token_payload, dict) else ""
    supplied_answer = payload.challenge_answer.strip().casefold()
    if not expected_answer or supplied_answer != expected_answer:
        raise HTTPException(status_code=400, detail="Invalid signup challenge answer.")

    normalized_email = normalize_email(str(payload.email))
    full_name = (payload.full_name or "").strip() or None
    repository.upsert_subscriber(
        email=normalized_email,
        full_name=full_name,
        updated_at=utc_now_iso(),
    )
    issue_magic_link_for_email(
        email=normalized_email,
        full_name=full_name,
        repository=repository,
        env_path=env_path,
    )
    return {"ok": True}


def _resolve_frontend_base_url() -> str:
    app_base_url = os.getenv("HIRING_RADAR_APP_BASE_URL", "http://localhost:3000").strip()
    if not app_base_url:
        app_base_url = "http://localhost:3000"
    return app_base_url.rstrip("/")


def _build_signup_verification_email_payload(
    *,
    recipient_email: str,
    recipient_name: str,
    verification_code: str,
    signup_url: str,
    expires_at: str,
) -> EmailMessagePayload:
    safe_name = html.escape(recipient_name or "CoreSift kullanıcısı")
    safe_code = html.escape(verification_code)
    safe_signup_url = html.escape(signup_url)
    safe_expires_at = html.escape(expires_at)

    body_text = "\n".join(
        [
            "CoreSift",
            "",
            f"Merhaba {recipient_name},",
            "",
            "Kayıt işlemini tamamlamak için aşağıdaki doğrulama kodunu kullan:",
            verification_code,
            "",
            f"Bu kod {expires_at} tarihine kadar geçerlidir.",
            f"Kayıt ekranı: {signup_url}",
        ]
    )

    body_html = f"""
    <html>
      <body style="margin:0;padding:0;background:#0b1220;font-family:Arial,sans-serif;color:#e5e7eb;">
        <div style="max-width:640px;margin:0 auto;padding:32px 20px;">
          <div style="background:#111827;border:1px solid #1f2937;border-radius:24px;overflow:hidden;">
            <div style="padding:28px 32px;border-bottom:1px solid #1f2937;">
              <div style="font-size:13px;letter-spacing:0.18em;text-transform:uppercase;color:#93c5fd;">CoreSift</div>
              <h1 style="margin:14px 0 0;font-size:28px;line-height:1.2;color:#ffffff;">Kayıt doğrulama kodun hazır</h1>
              <p style="margin:12px 0 0;font-size:15px;line-height:1.7;color:#cbd5e1;">
                Merhaba {safe_name}, hesabını güvenli şekilde oluşturabilmen için doğrulama kodunu aşağıda paylaşıyoruz.
              </p>
            </div>

            <div style="padding:32px;">
              <div style="padding:18px 20px;border-radius:18px;background:#0f172a;border:1px solid #1e293b;text-align:center;">
                <div style="font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:#94a3b8;">Doğrulama kodu</div>
                <div style="margin-top:10px;font-size:36px;font-weight:700;letter-spacing:0.18em;color:#ffffff;">{safe_code}</div>
              </div>

              <p style="margin:22px 0 0;font-size:14px;line-height:1.8;color:#cbd5e1;">
                Bu kod <strong style="color:#ffffff;">{safe_expires_at}</strong> tarihine kadar geçerlidir.
              </p>

              <div style="margin-top:28px;">
                <a href="{safe_signup_url}" style="display:inline-block;background:#3b52f0;color:#ffffff;text-decoration:none;padding:14px 22px;border-radius:14px;font-size:15px;font-weight:600;">
                  Kayıt ekranına dön
                </a>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """

    return EmailMessagePayload(
        to=recipient_email,
        subject="CoreSift doğrulama kodun",
        body_text=body_text,
        body_html=body_html,
    )


@router.post(
    "/request-signup-verification",
    response_model=PublicSignupVerificationResponse,
)
@router.post(
    "/signup/request-verification",
    response_model=PublicSignupVerificationResponse,
)
def request_signup_verification(
    payload: PublicSignupVerificationRequest,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
    env_path: Annotated[str, Depends(get_env_path)],
) -> PublicSignupVerificationResponse:
    full_name = payload.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="Full name is required.")

    normalized_email = normalize_email(payload.email)
    existing = repository.get_subscriber_by_email(normalized_email)
    if existing is not None and existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email address. Please sign in instead.",
        )

    try:
        password_hash = hash_password(payload.password, settings=auth_settings)
    except PasswordValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    verification_code = generate_signup_verification_code()
    verification_code_hash = hash_signup_verification_code(verification_code)
    created_at = utc_now_iso()
    expires_at = build_signup_verification_expiration(settings=auth_settings)

    repository.create_or_replace_subscriber_signup_verification(
        email=normalized_email,
        full_name=full_name,
        password_hash=password_hash,
        verification_code_hash=verification_code_hash,
        expires_at=expires_at,
        created_at=created_at,
        updated_at=created_at,
    )

    signup_url = f"{_resolve_frontend_base_url()}/tr/signup"

    try:
        smtp_settings = load_smtp_settings(env_path)
        send_email_via_smtp(
            settings=smtp_settings,
            payload=_build_signup_verification_email_payload(
                recipient_email=normalized_email,
                recipient_name=full_name,
                verification_code=verification_code,
                signup_url=signup_url,
                expires_at=expires_at,
            ),
        )
    except (EmailConfigError, EmailDeliveryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification email could not be sent: {exc}",
        ) from exc

    return PublicSignupVerificationResponse(message=SIGNUP_VERIFICATION_SENT_MESSAGE)


@router.post(
    "/confirm-signup-verification",
    response_model=PublicSignupResponse,
)
@router.post(
    "/signup/confirm-verification",
    response_model=PublicSignupResponse,
)


@router.post(
    "/signup/verify",
    response_model=PublicSignupResponse,
)


def confirm_signup_verification(
    payload: PublicSignupConfirmRequest,
    response: Response,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
) -> PublicSignupResponse:
    normalized_email = normalize_email(payload.email)
    verification = repository.get_subscriber_signup_verification_by_email(normalized_email)
    if verification is None or verification.id is None:
        raise HTTPException(status_code=400, detail="Verification request was not found.")

    if verification.consumed_at is not None:
        raise HTTPException(status_code=400, detail="This verification code has already been used.")

    if parse_utc_datetime(verification.expires_at) <= utc_now():
        raise HTTPException(status_code=400, detail="Verification code has expired.")

    if not verify_signup_verification_code(
        payload.verification_code,
        verification.verification_code_hash,
    ):
        raise HTTPException(status_code=400, detail="Verification code is invalid.")

    existing = repository.get_subscriber_by_email(normalized_email)
    if existing is not None and existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email address. Please sign in instead.",
        )

    password_updated_at = utc_now_iso()
    subscriber, _created = repository.upsert_subscriber(
        email=normalized_email,
        full_name=verification.full_name,
        updated_at=password_updated_at,
        password_hash=verification.password_hash,
        password_updated_at=password_updated_at,
    )

    repository.consume_subscriber_signup_verification(
        verification.id,
        consumed_at=password_updated_at,
    )

    if subscriber.id is None:
        raise HTTPException(status_code=500, detail="Subscriber could not be loaded.")

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

    return PublicSignupResponse(
        subscriber_id=subscriber.id,
        email=subscriber.email,
        full_name=subscriber.full_name,
        message=SIGNUP_COMPLETED_MESSAGE,
    )