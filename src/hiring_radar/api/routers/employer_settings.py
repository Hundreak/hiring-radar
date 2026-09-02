"""Employer workspace settings endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from hiring_radar.api.employer_dependencies import (
    get_current_employer_session,
    get_employer_repository,
)
from hiring_radar.api.schemas.employer_settings import (
    EmployerCommunicationPreferences,
    EmployerCommunicationPreferencesResponse,
    EmployerCommunicationPreferencesUpdate,
    EmployerCommunicationTeamSummary,
)
from hiring_radar.db.employer_repository import EmployerRepository, EmployerTeamMember
from hiring_radar.services.employer_auth import EmployerSession

router = APIRouter(prefix="/api/employer/settings", tags=["employer-settings"])

_MANAGE_WORKSPACE_SETTINGS_ROLES = {"owner", "admin"}


def _require_workspace_settings_manager(session: EmployerSession) -> None:
    if session.role_key not in _MANAGE_WORKSPACE_SETTINGS_ROLES:
        raise HTTPException(status_code=403, detail="workspace_settings_forbidden")


def _team_summary(members: list[EmployerTeamMember]) -> EmployerCommunicationTeamSummary:
    roles: dict[str, int] = {}
    active_members = 0
    invited_members = 0
    for member in members:
        roles[member.role_key] = roles.get(member.role_key, 0) + 1
        if member.status == "active":
            active_members += 1
        if member.status == "invited":
            invited_members += 1
    return EmployerCommunicationTeamSummary(
        active_members=active_members,
        invited_members=invited_members,
        roles=roles,
    )


def _response(
    *,
    repository: EmployerRepository,
    session: EmployerSession,
    preferences: dict[str, Any],
) -> EmployerCommunicationPreferencesResponse:
    company = repository.get_company_by_id(session.company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="company_not_found")
    members = repository.list_team_members(session.company_id)
    return EmployerCommunicationPreferencesResponse(
        company_id=session.company_id,
        preferences=EmployerCommunicationPreferences(**preferences),
        team_summary=_team_summary(members),
        updated_at=company.updated_at,
    )


@router.get("/communication-preferences", response_model=EmployerCommunicationPreferencesResponse)
def get_communication_preferences(
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> EmployerCommunicationPreferencesResponse:
    preferences = repository.get_company_communication_preferences(session.company_id)
    if preferences is None:
        raise HTTPException(status_code=404, detail="company_not_found")
    return _response(repository=repository, session=session, preferences=preferences)


@router.patch("/communication-preferences", response_model=EmployerCommunicationPreferencesResponse)
def update_communication_preferences(
    payload: EmployerCommunicationPreferencesUpdate,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> EmployerCommunicationPreferencesResponse:
    _require_workspace_settings_manager(session)
    before = repository.get_company_communication_preferences(session.company_id)
    if before is None:
        raise HTTPException(status_code=404, detail="company_not_found")

    updates = payload.model_dump(exclude_unset=True)
    if "security_alerts_enabled" in updates:
        updates["security_alerts_enabled"] = True

    preferences = repository.update_company_communication_preferences(
        company_id=session.company_id,
        updates=updates,
    )
    if preferences is None:
        raise HTTPException(status_code=404, detail="company_not_found")

    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="employer.settings.communication_preferences.updated",
        resource_type="company_settings",
        resource_id=str(session.company_id),
        before=before,
        after=preferences,
        metadata={"section": "communication_preferences"},
    )
    return _response(repository=repository, session=session, preferences=preferences)
