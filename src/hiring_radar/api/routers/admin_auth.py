from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from hiring_radar.api.csrf import attach_csrf_cookie, clear_csrf_cookie
from hiring_radar.api.dependencies import get_admin_auth_settings, get_current_admin_session
from hiring_radar.api.rate_limit import enforce_rate_limit
from hiring_radar.api.schemas.auth import AdminAuthMeResponse, AdminLoginRequest
from hiring_radar.api.security import (
    ADMIN_SESSION_COOKIE_NAME,
    AdminAuthSettings,
    AdminSession,
    create_admin_session_token,
    verify_admin_credentials,
)

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminAuthMeResponse)
def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    auth_settings: Annotated[AdminAuthSettings, Depends(get_admin_auth_settings)],
) -> AdminAuthMeResponse:
    enforce_rate_limit(
        request,
        action="admin_login",
        identity=payload.email,
        ip_limit=40,
        ip_window_seconds=900,
        identity_limit=8,
        identity_window_seconds=1800,
    )

    if not verify_admin_credentials(
        email=payload.email,
        password=payload.password,
        settings=auth_settings,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
        )

    session_token = create_admin_session_token(
        email=auth_settings.email,
        settings=auth_settings,
    )
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE_NAME,
        value=session_token,
        max_age=auth_settings.session_ttl_seconds,
        httponly=True,
        samesite=auth_settings.cookie_samesite,
        secure=auth_settings.secure_cookie,
        path="/",
    )
    attach_csrf_cookie(response)
    return AdminAuthMeResponse(email=auth_settings.email)


@router.post("/logout")
def admin_logout(
    response: Response,
    auth_settings: Annotated[AdminAuthSettings, Depends(get_admin_auth_settings)],
) -> dict[str, bool]:
    response.delete_cookie(
        key=ADMIN_SESSION_COOKIE_NAME,
        httponly=True,
        samesite=auth_settings.cookie_samesite,
        secure=auth_settings.secure_cookie,
        path="/",
    )
    clear_csrf_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=AdminAuthMeResponse)
def admin_me(
    admin_session: Annotated[AdminSession, Depends(get_current_admin_session)],
) -> AdminAuthMeResponse:
    return AdminAuthMeResponse(email=admin_session.email)
