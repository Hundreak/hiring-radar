"""Employer authentication and workspace bootstrap endpoints."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from hiring_radar.api.csrf import attach_csrf_cookie, clear_csrf_cookie
from hiring_radar.api.employer_dependencies import (
    get_current_employer_session,
    get_employer_repository,
)
from hiring_radar.api.rate_limit import enforce_rate_limit
from hiring_radar.api.schemas.employer_auth import (
    EmployerAuthResponse,
    EmployerLoginRequest,
    EmployerRefreshRequest,
    EmployerRegisterRequest,
)
from hiring_radar.db.employer_repository import EmployerRepository, EmployerTeamMember
from hiring_radar.services.employer_auth import (
    EMPLOYER_SESSION_COOKIE_NAME,
    EMPLOYER_SESSION_MAX_AGE_SECONDS,
    EmployerSession,
    create_employer_session_token,
    hash_password,
    load_employer_auth_settings,
    verify_password,
)

router = APIRouter(prefix="/api/employer/auth", tags=["employer-auth"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _company_slug_from_email(email: str) -> str:
    domain = email.split("@", 1)[-1].split(".", 1)[0]
    return domain.strip().lower() or f"company-{uuid4().hex[:8]}"


def _unique_company_slug(repository: EmployerRepository, base: str) -> str:
    normalized = base.strip().lower().replace("_", "-") or f"company-{uuid4().hex[:8]}"
    slug = normalized
    suffix = 2
    while repository.get_company_by_slug(slug) is not None:
        slug = f"{normalized}-{suffix}"
        suffix += 1
    return slug


def _set_employer_session_cookie(response: Response, token: str) -> None:
    settings = load_employer_auth_settings()
    response.set_cookie(
        key=EMPLOYER_SESSION_COOKIE_NAME,
        value=token,
        max_age=EMPLOYER_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/",
    )
    attach_csrf_cookie(response)


def _clear_employer_session_cookie(response: Response) -> None:
    settings = load_employer_auth_settings()
    response.delete_cookie(
        key=EMPLOYER_SESSION_COOKIE_NAME,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/",
    )
    clear_csrf_cookie(response)


def _issue_auth_response(
    *,
    repository: EmployerRepository,
    response: Response,
    user_id: int,
    company_id: int,
    email: str,
    role_key: str,
    member_id: int | None,
) -> tuple[str, dict[str, Any]]:
    company = repository.get_company_by_id(company_id)
    user = repository.get_user_by_id(user_id)
    if company is None or user is None:
        raise HTTPException(status_code=401, detail="Invalid employer account.")

    session = EmployerSession(
        user_id=user_id,
        company_id=company_id,
        email=email,
        role_key=role_key,
        member_id=member_id,
        issued_at=_now_iso(),
    )
    token = create_employer_session_token(session, settings=load_employer_auth_settings())
    _set_employer_session_cookie(response, token)
    payload = EmployerAuthResponse(
        access_token=token,
        refresh_token=token,
        user_id=user.id,
        company_id=company.id,
        member_id=member_id,
        email=user.email,
        full_name=user.full_name,
        company_name=company.name,
        role="employer",
        role_key=role_key,
    ).model_dump()
    return token, payload


def _serialize_member(member: EmployerTeamMember) -> dict[str, Any]:
    return {
        "id": member.id,
        "company_id": member.company_id,
        "user_id": member.user_id,
        "email": member.email or member.invited_email,
        "full_name": member.full_name,
        "role_key": member.role_key,
        "status": member.status,
        "invited_email": member.invited_email,
        "invited_at": member.invited_at,
        "joined_at": member.joined_at,
        "last_active_at": member.last_active_at,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }


@router.post("/register")
def employer_register(
    payload: EmployerRegisterRequest,
    request: Request,
    response: Response,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict[str, Any]:
    enforce_rate_limit(
        request,
        action="employer_register",
        identity=payload.company_email,
        ip_limit=30,
        ip_window_seconds=1800,
        identity_limit=4,
        identity_window_seconds=3600,
    )

    email = str(payload.company_email).strip().lower()
    if repository.get_user_by_email(email) is not None:
        raise HTTPException(status_code=409, detail="employer_user_exists")
    if payload.password != payload.password_confirmation:
        raise HTTPException(status_code=400, detail="password_mismatch")

    slug = _unique_company_slug(repository, _company_slug_from_email(email))
    try:
        company = repository.create_company(
            name=payload.company_name.strip(),
            slug=slug,
            website_url=payload.website_url,
            default_locale=payload.default_locale,
            brand_profile={
                "public_email": email,
                "response_sla": "3 business days",
                "transparency_policy": "human_review_required",
            },
            settings={
                "ai_review_required": True,
                "locale_policy": ["tr", "en"],
            },
        )
        user = repository.create_user(
            email=email,
            full_name=payload.full_name or payload.company_name.strip(),
            password_hash=hash_password(payload.password),
            title="Workspace owner",
        )
        member = repository.add_team_member(
            company_id=company.id,
            user_id=user.id,
            role_key="owner",
            status="active",
        )
        repository.create_audit_event(
            company_id=company.id,
            actor_user_id=user.id,
            event_type="employer.auth.registered",
            resource_type="company",
            resource_id=str(company.id),
            after={"company_name": company.name, "email": email, "role_key": "owner"},
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="employer_account_conflict") from exc

    _, result = _issue_auth_response(
        repository=repository,
        response=response,
        user_id=user.id,
        company_id=company.id,
        email=user.email,
        role_key=member.role_key,
        member_id=member.id,
    )
    return result


@router.post("/login")
def employer_login(
    payload: EmployerLoginRequest,
    request: Request,
    response: Response,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict[str, Any]:
    enforce_rate_limit(
        request,
        action="employer_login",
        identity=payload.email,
        ip_limit=60,
        ip_window_seconds=900,
        identity_limit=10,
        identity_window_seconds=1800,
    )

    email = str(payload.email).strip().lower()
    user = repository.get_user_by_email(email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="user_inactive")

    member = repository.get_primary_team_member_for_user(user.id)
    if member is None or member.user_id is None:
        raise HTTPException(status_code=403, detail="workspace_access_missing")

    repository.update_user_last_login(user.id)
    repository.create_audit_event(
        company_id=member.company_id,
        actor_user_id=user.id,
        event_type="employer.auth.login",
        resource_type="user",
        resource_id=str(user.id),
    )
    _, result = _issue_auth_response(
        repository=repository,
        response=response,
        user_id=user.id,
        company_id=member.company_id,
        email=user.email,
        role_key=member.role_key,
        member_id=member.id,
    )
    return result


@router.get("/me")
def employer_me(
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict[str, Any]:
    company = repository.get_company_by_id(session.company_id)
    user = repository.get_user_by_id(session.user_id)
    member = (
        repository.get_team_member(session.member_id)
        if session.member_id is not None
        else repository.get_active_team_member_for_user(company_id=session.company_id, user_id=session.user_id)
    )
    if company is None or user is None or member is None:
        raise HTTPException(status_code=401, detail="Invalid employer session.")
    return {
        "ok": True,
        "user_id": user.id,
        "company_id": company.id,
        "member_id": member.id,
        "email": user.email,
        "name": user.full_name,
        "company_name": company.name,
        "role": "employer",
        "role_key": member.role_key,
        "email_verified": True,
        "created_at": user.created_at,
        "company": {
            "id": company.id,
            "slug": company.slug,
            "name": company.name,
            "default_locale": company.default_locale,
            "plan_tier": company.plan_tier,
            "status": company.status,
        },
    }


@router.post("/logout")
def employer_logout(response: Response) -> dict[str, bool]:
    _clear_employer_session_cookie(response)
    return {"ok": True}


@router.post("/refresh")
def employer_refresh(
    payload: EmployerRefreshRequest,
    response: Response,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict[str, Any]:
    # The refresh token is currently the same signed session token. The dependency above
    # validates either the HttpOnly cookie or the bearer token before issuing a fresh token.
    _ = payload
    _, result = _issue_auth_response(
        repository=repository,
        response=response,
        user_id=session.user_id,
        company_id=session.company_id,
        email=session.email,
        role_key=session.role_key,
        member_id=session.member_id,
    )
    return result
