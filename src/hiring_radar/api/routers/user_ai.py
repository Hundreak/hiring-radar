from __future__ import annotations

import inspect
import time
from typing import Annotated, Callable, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.schemas.profile_contract import UserProfileAggregateResponse
from hiring_radar.api.schemas.user_ai import (
    UserAiCopilotChatRequest,
    UserAiCopilotChatResponse,
    UserAiHealthResponse,
    UserAiHeadlineSummaryRequest,
    UserAiHeadlineSummaryResponse,
    UserAiRoleFocusRequest,
    UserAiRoleFocusResponse,
    UserAiSkillEvidenceRequest,
    UserAiSkillEvidenceResponse,
    UserAiSkillGroupingRequest,
    UserAiSkillGroupingResponse,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.ai.contracts import AiAuditRecord
from hiring_radar.services.ai.exceptions import LocalAiGenerationError
from hiring_radar.services.ai.runtime import build_local_ai_runtime_service
from hiring_radar.services.ai.tasks.copilot_chat_task import CopilotChatTask
from hiring_radar.services.ai.tasks.headline_summary_task import HeadlineSummarySuggestionTask
from hiring_radar.services.ai.tasks.role_focus_task import RoleFocusSuggestionTask
from hiring_radar.services.ai.tasks.skill_evidence_task import SkillEvidenceSuggestionTask
from hiring_radar.services.ai.tasks.skill_grouping_task import SkillGroupingSuggestionTask
from hiring_radar.services.ai.telemetry import (
    build_response_preview,
    generate_telemetry_ref,
    persist_ai_audit_record,
    utc_now_iso,
)
from hiring_radar.services.profile_aggregate import build_user_profile_aggregate_response
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user/ai", tags=["user-ai"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)
TaskResultT = TypeVar("TaskResultT", bound=BaseModel)


def _get_user_profile_aggregate_response(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    legacy_profile = repository.get_subscriber_profile(subscriber.id)
    experience_entries = repository.list_subscriber_experience_entries(subscriber.id)
    education_entries = repository.list_subscriber_education_entries(subscriber.id)
    language_entries = repository.list_subscriber_language_entries(subscriber.id)

    return build_user_profile_aggregate_response(
        user_id=str(subscriber.id),
        email=subscriber.email,
        full_name=subscriber.full_name,
        legacy_profile=legacy_profile,
        experience_entries=experience_entries,
        education_entries=education_entries,
        language_entries=language_entries,
    )


def _runtime_meta(runtime) -> tuple[str, str | None, bool, int]:
    config = getattr(runtime, "config", None)
    runtime_name = getattr(config, "runtime", "unknown") if config is not None else "unknown"
    model_name = getattr(config, "default_model", None) if config is not None else None
    audit_enabled = bool(getattr(config, "audit_enabled", False)) if config is not None else False
    preview_chars = int(getattr(config, "audit_preview_chars", 240)) if config is not None else 240
    return runtime_name, model_name, audit_enabled, preview_chars


def _persist_task_audit(
    *,
    runtime,
    telemetry_ref: str,
    task_name: str,
    endpoint_name: str,
    locale: str,
    subscriber_id: int,
    started_at: str,
    completed_at: str,
    duration_ms: int,
    success: bool,
    response_valid: bool,
    warning_count: int = 0,
    prompt_name: str | None = None,
    prompt_version: str | None = None,
    schema_name: str | None = None,
    schema_version: str | None = None,
    response_preview: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    config = getattr(runtime, "config", None)
    if config is None:
        return
    runtime_name, model_name, _, _ = _runtime_meta(runtime)
    record = AiAuditRecord(
        telemetry_ref=telemetry_ref,
        task_name=task_name,
        endpoint_name=endpoint_name,
        runtime=runtime_name,
        model=model_name,
        locale=locale,
        subscriber_id=subscriber_id,
        success=success,
        response_valid=response_valid,
        warning_count=warning_count,
        duration_ms=duration_ms,
        started_at=started_at,
        completed_at=completed_at,
        error_type=error_type,
        error_message=error_message,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        schema_name=schema_name,
        schema_version=schema_version,
        response_preview=response_preview,
    )
    try:
        persist_ai_audit_record(config, record)
    except Exception:
        return


def _execute_task_with_audit(
    *,
    runtime,
    response_model: type[ResponseModelT],
    task_name: str,
    endpoint_name: str,
    locale: str,
    subscriber_id: int,
    prompt_name: str,
    prompt_version: str,
    schema_name: str,
    schema_version: str,
    executor: Callable[[], TaskResultT],
) -> ResponseModelT:
    telemetry_ref = generate_telemetry_ref()
    started_at = utc_now_iso()
    started = time.perf_counter()
    _, _, _, preview_chars = _runtime_meta(runtime)

    try:
        result = executor()
    except LocalAiGenerationError as exc:
        completed_at = utc_now_iso()
        duration_ms = int((time.perf_counter() - started) * 1000)
        _persist_task_audit(
            runtime=runtime,
            telemetry_ref=telemetry_ref,
            task_name=task_name,
            endpoint_name=endpoint_name,
            locale=locale,
            subscriber_id=subscriber_id,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            success=False,
            response_valid=False,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            schema_name=schema_name,
            schema_version=schema_version,
            error_type=exc.__class__.__name__,
            error_message=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    completed_at = utc_now_iso()
    duration_ms = int((time.perf_counter() - started) * 1000)
    warnings = getattr(result, "warnings", [])
    _persist_task_audit(
        runtime=runtime,
        telemetry_ref=telemetry_ref,
        task_name=task_name,
        endpoint_name=endpoint_name,
        locale=locale,
        subscriber_id=subscriber_id,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        success=True,
        response_valid=True,
        warning_count=len(warnings) if isinstance(warnings, list) else 0,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        schema_name=schema_name,
        schema_version=schema_version,
        response_preview=build_response_preview(result, max_chars=preview_chars),
    )
    payload = result.model_dump()
    payload["telemetry_ref"] = telemetry_ref
    return response_model(**payload)


@router.get("/health", response_model=UserAiHealthResponse)
def get_local_ai_runtime_health() -> UserAiHealthResponse:
    service = build_local_ai_runtime_service()
    result = service.health()
    return UserAiHealthResponse(**result.model_dump())


@router.post("/profile/headline-summary", response_model=UserAiHeadlineSummaryResponse)
def suggest_profile_headline_summary(
    payload: UserAiHeadlineSummaryRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiHeadlineSummaryResponse:
    aggregate = _get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )
    runtime = build_local_ai_runtime_service()
    task = HeadlineSummarySuggestionTask(runtime)
    return _execute_task_with_audit(
        runtime=runtime,
        response_model=UserAiHeadlineSummaryResponse,
        task_name="headline_summary",
        endpoint_name="/api/user/ai/profile/headline-summary",
        locale=payload.locale,
        subscriber_id=user_session.subscriber_id,
        prompt_name="headline_summary",
        prompt_version="1",
        schema_name="HeadlineSummarySuggestionResponse",
        schema_version="1",
        executor=lambda: task.run(
            profile=aggregate.profile,
            locale=payload.locale,
            headline_option_count=payload.headline_option_count,
            summary_option_count=payload.summary_option_count,
        ),
    )


@router.post("/profile/role-focus", response_model=UserAiRoleFocusResponse)
def suggest_profile_role_focus(
    payload: UserAiRoleFocusRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiRoleFocusResponse:
    aggregate = _get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )
    runtime = build_local_ai_runtime_service()
    task = RoleFocusSuggestionTask(runtime)
    return _execute_task_with_audit(
        runtime=runtime,
        response_model=UserAiRoleFocusResponse,
        task_name="role_focus",
        endpoint_name="/api/user/ai/profile/role-focus",
        locale=payload.locale,
        subscriber_id=user_session.subscriber_id,
        prompt_name="role_focus",
        prompt_version="1",
        schema_name="RoleFocusSuggestionResponse",
        schema_version="1",
        executor=lambda: task.run(
            profile=aggregate.profile,
            locale=payload.locale,
            suggestion_count=payload.suggestion_count,
        ),
    )


@router.post("/profile/skill-grouping", response_model=UserAiSkillGroupingResponse)
def suggest_profile_skill_grouping(
    payload: UserAiSkillGroupingRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiSkillGroupingResponse:
    aggregate = _get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )
    runtime = build_local_ai_runtime_service()
    task = SkillGroupingSuggestionTask(runtime)
    return _execute_task_with_audit(
        runtime=runtime,
        response_model=UserAiSkillGroupingResponse,
        task_name="skill_grouping",
        endpoint_name="/api/user/ai/profile/skill-grouping",
        locale=payload.locale,
        subscriber_id=user_session.subscriber_id,
        prompt_name="skill_grouping",
        prompt_version="1",
        schema_name="SkillGroupingSuggestionResponse",
        schema_version="1",
        executor=lambda: task.run(
            profile=aggregate.profile,
            locale=payload.locale,
            group_limit=payload.group_limit,
            skill_limit_per_group=payload.skill_limit_per_group,
        ),
    )


@router.post("/profile/skill-evidence", response_model=UserAiSkillEvidenceResponse)
def suggest_profile_skill_evidence(
    payload: UserAiSkillEvidenceRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiSkillEvidenceResponse:
    aggregate = _get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )
    runtime = build_local_ai_runtime_service()
    task = SkillEvidenceSuggestionTask(runtime)
    return _execute_task_with_audit(
        runtime=runtime,
        response_model=UserAiSkillEvidenceResponse,
        task_name="skill_evidence",
        endpoint_name="/api/user/ai/profile/skill-evidence",
        locale=payload.locale,
        subscriber_id=user_session.subscriber_id,
        prompt_name="skill_evidence",
        prompt_version="1",
        schema_name="SkillEvidenceSuggestionResponse",
        schema_version="1",
        executor=lambda: task.run(
            profile=aggregate.profile,
            locale=payload.locale,
            skill_name=payload.skill_name,
            category=payload.category,
            existing_evidence_note=payload.existing_evidence_note,
        ),
    )


@router.post("/copilot/chat", response_model=UserAiCopilotChatResponse)
def chat_with_copilot(
    payload: UserAiCopilotChatRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserAiCopilotChatResponse:
    aggregate = _get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )
    runtime = build_local_ai_runtime_service()
    task = CopilotChatTask(runtime)
    telemetry_ref = generate_telemetry_ref()
    started_at = utc_now_iso()
    started = time.perf_counter()

    conversation_id_value: int | None = None
    if payload.conversation_id is not None and payload.conversation_id.strip().isdigit():
        conversation_id_value = int(payload.conversation_id.strip())

    conversation = None
    if conversation_id_value is not None:
        conversation = repository.get_subscriber_ai_copilot_conversation(
            user_session.subscriber_id,
            conversation_id_value,
        )

    if conversation is None:
        title = payload.message.strip().splitlines()[0][:72] or "New chat"
        conversation = repository.create_subscriber_ai_copilot_conversation(
            user_session.subscriber_id,
            title=title,
            locale=payload.locale,
            created_at=started_at,
            updated_at=started_at,
        )
        conversation_id_value = conversation.id
    else:
        conversation_id_value = conversation.id

    if conversation_id_value is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Copilot conversation could not be prepared.")

    repository.create_subscriber_ai_copilot_message(
        user_session.subscriber_id,
        conversation_id=conversation_id_value,
        role="user",
        content=payload.message.strip(),
        metadata_json={"locale": payload.locale},
        created_at=started_at,
    )

    recent_messages = [
        (item.role, item.content)
        for item in repository.list_subscriber_ai_copilot_messages(
            user_session.subscriber_id,
            conversation_id=conversation_id_value,
            limit=12,
        )
    ]

    try:
        task_run_kwargs = {
            "repository": repository,
            "subscriber_id": user_session.subscriber_id,
            "profile": aggregate.profile,
            "locale": payload.locale,
            "user_message": payload.message,
            "latest_user_message": payload.message,
            "recent_messages": recent_messages,
            "conversation_history": recent_messages,
            "learned_memory": repository.list_subscriber_ai_learned_memories(user_session.subscriber_id, limit=6),
            "conversation_id": conversation_id_value,
            "observed_at": started_at,
        }
        parameters = inspect.signature(task.run).parameters
        result = task.run(**{key: value for key, value in task_run_kwargs.items() if key in parameters})
    except LocalAiGenerationError as exc:
        completed_at = utc_now_iso()
        duration_ms = int((time.perf_counter() - started) * 1000)
        _persist_task_audit(
            runtime=runtime,
            telemetry_ref=telemetry_ref,
            task_name="copilot_chat",
            endpoint_name="/api/user/ai/copilot/chat",
            locale=payload.locale,
            subscriber_id=user_session.subscriber_id,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            success=False,
            response_valid=False,
            prompt_name="copilot_chat",
            prompt_version="1",
            schema_name="CopilotChatResponse",
            schema_version="1",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    assistant_created_at = utc_now_iso()
    assistant_message = repository.create_subscriber_ai_copilot_message(
        user_session.subscriber_id,
        conversation_id=conversation_id_value,
        role="assistant",
        content=result.answer,
        metadata_json={
            "source_labels": [item.label for item in result.sources],
            "follow_up_suggestions": result.follow_up_suggestions,
        },
        created_at=assistant_created_at,
    )
    repository.update_subscriber_ai_copilot_conversation(
        user_session.subscriber_id,
        conversation_id_value,
        title=(payload.message.strip().splitlines()[0][:72] or conversation.title),
        updated_at=assistant_created_at,
        last_message_at=assistant_created_at,
    )

    completed_at = utc_now_iso()
    duration_ms = int((time.perf_counter() - started) * 1000)
    _persist_task_audit(
        runtime=runtime,
        telemetry_ref=telemetry_ref,
        task_name="copilot_chat",
        endpoint_name="/api/user/ai/copilot/chat",
        locale=payload.locale,
        subscriber_id=user_session.subscriber_id,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        success=True,
        response_valid=True,
        warning_count=len(result.warnings),
        prompt_name="copilot_chat",
        prompt_version="1",
        schema_name="CopilotChatResponse",
        schema_version="1",
        response_preview=build_response_preview(result, max_chars=240),
    )
    payload_dict = result.model_dump()
    payload_dict["telemetry_ref"] = telemetry_ref
    payload_dict["conversation_id"] = str(conversation_id_value)
    payload_dict["message_id"] = str(assistant_message.id) if assistant_message.id is not None else None
    return UserAiCopilotChatResponse(**payload_dict)
