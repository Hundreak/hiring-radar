"""Employer team and role management endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from hiring_radar.api.employer_dependencies import (
    get_current_employer_session,
    get_employer_repository,
)
from hiring_radar.api.schemas.employer_auth import (
    EmployerTeamInvitationRequest,
    EmployerTeamMemberUpdateRequest,
)
from hiring_radar.db.employer_repository import EmployerRepository, EmployerTeamMember
from hiring_radar.services.employer_auth import EmployerSession

router = APIRouter(prefix="/api/employer/team", tags=["employer-team"])

_MANAGE_TEAM_ROLES = {"owner", "admin"}


def _require_team_manager(session: EmployerSession) -> None:
    if session.role_key not in _MANAGE_TEAM_ROLES:
        raise HTTPException(status_code=403, detail="team_management_forbidden")


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


@router.get("")
def list_team(
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict[str, Any]:
    company = repository.get_company_by_id(session.company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="company_not_found")
    return {
        "ok": True,
        "company": {
            "id": company.id,
            "slug": company.slug,
            "name": company.name,
            "plan_tier": company.plan_tier,
            "status": company.status,
        },
        "members": [_serialize_member(member) for member in repository.list_team_members(company.id)],
        "roles": repository.list_roles(company.id),
    }


@router.post("/invitations")
def invite_team_member(
    payload: EmployerTeamInvitationRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict[str, Any]:
    _require_team_manager(session)
    if not any(role["role_key"] == payload.role_key for role in repository.list_roles(session.company_id)):
        raise HTTPException(status_code=400, detail="invalid_role")
    member = repository.add_team_member(
        company_id=session.company_id,
        invited_email=str(payload.email).strip().lower(),
        role_key=payload.role_key,
        status="invited",
        invited_by_user_id=session.user_id,
    )
    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="employer.team.invited",
        resource_type="team_member",
        resource_id=str(member.id),
        after={"email": member.invited_email, "role_key": member.role_key},
    )
    return {"ok": True, "member": _serialize_member(member)}


@router.patch("/members/{member_id}")
def update_team_member(
    member_id: int,
    payload: EmployerTeamMemberUpdateRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict[str, Any]:
    _require_team_manager(session)
    existing = repository.get_team_member(member_id)
    if existing is None or existing.company_id != session.company_id:
        raise HTTPException(status_code=404, detail="team_member_not_found")
    if existing.role_key == "owner" and payload.role_key and payload.role_key != "owner":
        raise HTTPException(status_code=400, detail="owner_role_cannot_be_downgraded")
    if payload.role_key and not any(role["role_key"] == payload.role_key for role in repository.list_roles(session.company_id)):
        raise HTTPException(status_code=400, detail="invalid_role")
    member = repository.update_team_member(member_id, role_key=payload.role_key, status=payload.status)
    if member is None:  # pragma: no cover
        raise HTTPException(status_code=404, detail="team_member_not_found")
    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="employer.team.updated",
        resource_type="team_member",
        resource_id=str(member.id),
        before={"role_key": existing.role_key, "status": existing.status},
        after={"role_key": member.role_key, "status": member.status},
    )
    return {"ok": True, "member": _serialize_member(member)}
