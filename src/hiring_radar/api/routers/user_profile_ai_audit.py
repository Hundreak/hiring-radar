from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from hiring_radar.api.routers.user_profile_modules.shared import (
    RepositoryDep,
    UserSessionDep,
    get_user_profile_aggregate_response,
)
from hiring_radar.api.schemas.user_profile import (
    CreateUserAiAuditLogRequest,
    FinalizeUserAiAuditLogRequest,
    UserAiAuditLogResponse,
    UserAiAuditRevertResponse,
)
from hiring_radar.services.ai_audit import compare_saved_snapshot, dumps_snapshot, loads_snapshot

router = APIRouter()


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _serialize_ai_audit_log(item: Any) -> UserAiAuditLogResponse:
    return UserAiAuditLogResponse(
        id=item.id or 0,
        telemetry_ref=item.telemetry_ref,
        target_field=item.target_field,
        target_entity_id=item.target_entity_id,
        action_type=item.action_type,
        source_panel=item.source_panel,
        before_snapshot=loads_snapshot(item.before_snapshot_json),
        after_snapshot=loads_snapshot(item.after_snapshot_json),
        persistence_status=item.persistence_status,
        evaluation_status=item.evaluation_status,
        evaluation_score=item.evaluation_score,
        manual_edit_distance=item.manual_edit_distance,
        request_ref=item.request_ref,
        metadata=loads_snapshot(item.metadata_json) or {},
        created_at=item.created_at,
        updated_at=item.updated_at,
        reverted_at=item.reverted_at,
    )


@router.post(
    "/ai-audit/events",
    response_model=UserAiAuditLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_ai_audit_event(
    payload: CreateUserAiAuditLogRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiAuditLogResponse:
    now = _utc_now_iso()
    item = repository.create_subscriber_ai_audit_log(
        user_session.subscriber_id,
        telemetry_ref=payload.telemetry_ref,
        target_field=payload.target_field,
        target_entity_id=payload.target_entity_id,
        action_type=payload.action_type,
        source_panel=payload.source_panel,
        before_snapshot_json=dumps_snapshot(payload.before_snapshot),
        after_snapshot_json=dumps_snapshot(payload.after_snapshot),
        persistence_status=payload.persistence_status,
        evaluation_status=payload.evaluation_status or "pending",
        evaluation_score=None,
        manual_edit_distance=None,
        request_ref=None,
        metadata_json=dumps_snapshot(payload.metadata),
        created_at=now,
    )
    return _serialize_ai_audit_log(item)


@router.patch(
    "/ai-audit/events/{audit_log_id}",
    response_model=UserAiAuditLogResponse,
)
def finalize_user_ai_audit_event(
    audit_log_id: int,
    payload: FinalizeUserAiAuditLogRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiAuditLogResponse:
    existing = repository.get_subscriber_ai_audit_log_by_id(
        user_session.subscriber_id,
        audit_log_id,
    )
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI audit event not found.",
        )

    result = compare_saved_snapshot(
        loads_snapshot(existing.after_snapshot_json),
        payload.saved_snapshot,
    )
    item = repository.update_subscriber_ai_audit_log(
        user_session.subscriber_id,
        audit_log_id,
        after_snapshot_json=result.resolved_after_snapshot_json,
        persistence_status=payload.persistence_status,
        evaluation_status=payload.evaluation_status or result.evaluation_status,
        evaluation_score=result.evaluation_score,
        manual_edit_distance=result.manual_edit_distance,
        metadata_json=dumps_snapshot(payload.metadata),
        updated_at=_utc_now_iso(),
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI audit event not found.",
        )
    return _serialize_ai_audit_log(item)


@router.get("/ai-audit/export")
def export_user_ai_audit_events(
    user_session: UserSessionDep,
    repository: RepositoryDep,
    format: str = "json",
) -> list[dict[str, Any]]:
    if format.lower() != "json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON export is supported.",
        )
    return [
        _serialize_ai_audit_log(item).model_dump(mode="json")
        for item in repository.list_subscriber_ai_audit_logs(
            user_session.subscriber_id,
            limit=500,
        )
    ]


@router.post(
    "/ai-audit/events/{audit_log_id}/revert",
    response_model=UserAiAuditRevertResponse,
)
def revert_user_ai_audit_event(
    audit_log_id: int,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiAuditRevertResponse:
    existing = repository.get_subscriber_ai_audit_log_by_id(
        user_session.subscriber_id,
        audit_log_id,
    )
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI audit event not found.",
        )

    before_value = loads_snapshot(existing.before_snapshot_json)
    profile = repository.get_subscriber_profile(user_session.subscriber_id)
    now = _utc_now_iso()
    target_field = existing.target_field
    if target_field in {"headline", "summary", "phone"}:
        repository.upsert_subscriber_profile(
            user_session.subscriber_id,
            phone=before_value if target_field == "phone" else profile.phone,
            headline=before_value if target_field == "headline" else profile.headline,
            summary=before_value if target_field == "summary" else profile.summary,
            target_roles=profile.target_roles,
            skills=profile.skills,
            preferred_locations=profile.preferred_locations,
            remote_preference=profile.remote_preference,
            cv_filename=profile.cv_filename,
            cv_uploaded_at=profile.cv_uploaded_at,
            updated_at=now,
        )
    elif target_field == "full_name":
        repository.update_subscriber_fields_by_id(
            user_session.subscriber_id,
            fields={"full_name": before_value},
            updated_at=now,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This audit target cannot be reverted automatically.",
        )

    item = repository.update_subscriber_ai_audit_log(
        user_session.subscriber_id,
        audit_log_id,
        persistence_status="reverted",
        evaluation_status="reverted",
        evaluation_score=0.25,
        reverted_at=now,
        updated_at=now,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI audit event not found.",
        )

    aggregate = get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    ).model_dump(mode="json")
    return UserAiAuditRevertResponse(
        audit_log=_serialize_ai_audit_log(item),
        aggregate=aggregate,
    )
