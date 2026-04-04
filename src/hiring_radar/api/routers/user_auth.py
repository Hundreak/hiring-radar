from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from hiring_radar.api.dependencies import (
    get_current_user_session,
    get_env_path,
    get_repository,
    get_user_auth_settings,
)
from hiring_radar.api.schemas.user_auth import (
    UserAuthMeResponse,
    UserConsumeMagicLinkRequest,
    UserRequestMagicLinkRequest,
    UserRequestMagicLinkResponse,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.email_config import EmailConfigError, load_smtp_settings
from hiring_radar.services.email import EmailDeliveryError, send_email_via_smtp
from hiring_radar.services.user_auth import (
    USER_SESSION_COOKIE_NAME,
    UserAuthError,
    UserAuthSettings,
    UserSession,
    build_magic_link_email_payload,
    consume_magic_link_token,
    create_user_session_token,
    issue_magic_link_for_email,
)

router = APIRouter(prefix="/api/user/auth", tags=["user-auth"])

GENERIC_MAGIC_LINK_RESPONSE = (
    "If that email is eligible, a sign-in link has been sent."
)

UserAuthSettingsDep = Annotated[UserAuthSettings, Depends(get_user_auth_settings)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]


@router.post("/request-magic-link", response_model=UserRequestMagicLinkResponse)
def request_magic_link(
    payload: UserRequestMagicLinkRequest,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
    env_path: Annotated[str, Depends(get_env_path)],
) -> UserRequestMagicLinkResponse:
    result = issue_magic_link_for_email(
        repository=repository,
        email=payload.email,
        settings=auth_settings,
    )

    if result is not None:
        try:
            smtp_settings = load_smtp_settings(env_path)
            email_payload = build_magic_link_email_payload(
                recipient_email=result.subscriber.email,
                login_url=result.login_url,
                expires_at=result.expires_at,
            )
            send_email_via_smtp(
                settings=smtp_settings,
                payload=email_payload,
            )
        except (EmailConfigError, EmailDeliveryError):
            # Intentionally return the same generic response to avoid account enumeration.
            pass

    return UserRequestMagicLinkResponse(message=GENERIC_MAGIC_LINK_RESPONSE)


@router.post("/consume-magic-link", response_model=UserAuthMeResponse)
def consume_magic_link(
    payload: UserConsumeMagicLinkRequest,
    response: Response,
    repository: RepositoryDep,
    auth_settings: UserAuthSettingsDep,
) -> UserAuthMeResponse:
    try:
        subscriber = consume_magic_link_token(
            repository=repository,
            raw_token=payload.token,
        )
    except UserAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is unavailable.",
        )

    session_token = create_user_session_token(
        subscriber_id=subscriber.id,
        email=subscriber.email,
        settings=auth_settings,
    )
    response.set_cookie(
        key=USER_SESSION_COOKIE_NAME,
        value=session_token,
        max_age=auth_settings.session_ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

    return UserAuthMeResponse(
        subscriber_id=subscriber.id,
        email=subscriber.email,
    )


@router.post("/logout")
def user_logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(
        key=USER_SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
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