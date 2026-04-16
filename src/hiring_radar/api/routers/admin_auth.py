from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from hiring_radar.api.dependencies import get_admin_auth_settings, get_current_admin_session
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
    response: Response,
    auth_settings: Annotated[AdminAuthSettings, Depends(get_admin_auth_settings)],
) -> AdminAuthMeResponse:
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
        samesite="lax",
        secure=False,
        path="/",
    )
    return AdminAuthMeResponse(email=auth_settings.email)


@router.post("/logout")
def admin_logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(
        key=ADMIN_SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return {"ok": True}


@router.get("/me", response_model=AdminAuthMeResponse)
def admin_me(
    admin_session: Annotated[AdminSession, Depends(get_current_admin_session)],
) -> AdminAuthMeResponse:
    return AdminAuthMeResponse(email=admin_session.email)
