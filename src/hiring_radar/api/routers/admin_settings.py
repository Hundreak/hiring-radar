from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from hiring_radar.api.dependencies import (
    get_app_settings,
    get_current_admin_session,
    get_repository,
    get_settings_path,
)
from hiring_radar.api.schemas.settings import (
    AdminFilterPreviewFieldMatchResponse,
    AdminFilterPreviewSampleResponse,
    AdminSettingsFilterPreviewRequest,
    AdminSettingsFilterPreviewResponse,
    AdminSettingsKeywordFilterResponse,
    AdminSettingsResponse,
    AdminSettingsUpdateRequest,
)
from hiring_radar.api.security import AdminSession
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering import JobFilterDecision, filter_jobs_by_keyword_settings
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.services.settings_store import write_app_settings
from hiring_radar.settings import AppSettings, NotificationsSettings

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])

AdminSessionDep = Annotated[AdminSession, Depends(get_current_admin_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
AppSettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
SettingsPathDep = Annotated[str, Depends(get_settings_path)]


def _build_keyword_filter_settings(
    payload,
) -> KeywordFilterSettings:
    try:
        return KeywordFilterSettings(
            include_keywords=tuple(payload.include_keywords),
            exclude_keywords=tuple(payload.exclude_keywords),
            match_title=payload.match_title,
            match_location=payload.match_location,
            match_company_name=payload.match_company_name,
        )
    except ValueError as exc:
        message = str(exc)

        if "at least one enabled match field" in message.lower():
            message = "At least one keyword filter field must be enabled."

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc


def _build_app_settings_from_request(
    payload: AdminSettingsUpdateRequest,
) -> AppSettings:
    keyword_filter = _build_keyword_filter_settings(payload.keyword_filter)
    notifications = NotificationsSettings(
        apply_keyword_filter_to_digest=(
            payload.notifications.apply_keyword_filter_to_digest
        )
    )
    return AppSettings(
        keyword_filter=keyword_filter,
        notifications=notifications,
    )


def _serialize_settings(
    *,
    settings: AppSettings,
    settings_path: str,
) -> AdminSettingsResponse:
    keyword_filter = settings.keyword_filter

    return AdminSettingsResponse(
        settings_path=settings_path,
        keyword_filter=AdminSettingsKeywordFilterResponse(
            include_keywords=list(keyword_filter.include_keywords),
            exclude_keywords=list(keyword_filter.exclude_keywords),
            match_title=keyword_filter.match_title,
            match_location=keyword_filter.match_location,
            match_company_name=keyword_filter.match_company_name,
            enabled=keyword_filter.is_enabled(),
            active_fields=list(keyword_filter.active_fields()),
        ),
        notifications={
            "apply_keyword_filter_to_digest": (
                settings.notifications.apply_keyword_filter_to_digest
            )
        },
    )


def _serialize_filter_match(match) -> AdminFilterPreviewFieldMatchResponse:
    return AdminFilterPreviewFieldMatchResponse(
        field_name=match.field_name,
        keyword=match.keyword,
        field_value=match.field_value,
    )


def _serialize_filter_sample(
    decision: JobFilterDecision,
) -> AdminFilterPreviewSampleResponse:
    return AdminFilterPreviewSampleResponse(
        job_id=decision.job.id,
        title=decision.job.title,
        company_name=decision.job.company_name,
        location=decision.job.location,
        canonical_url=decision.job.canonical_url,
        include_matches=[
            _serialize_filter_match(match)
            for match in decision.evaluation.include_matches
        ],
        exclude_matches=[
            _serialize_filter_match(match)
            for match in decision.evaluation.exclude_matches
        ],
    )


@router.get("", response_model=AdminSettingsResponse)
def admin_get_settings(
    admin_session: AdminSessionDep,
    settings: AppSettingsDep,
    settings_path: SettingsPathDep,
) -> AdminSettingsResponse:
    _ = admin_session
    return _serialize_settings(settings=settings, settings_path=settings_path)


@router.put("", response_model=AdminSettingsResponse)
def admin_update_settings(
    payload: AdminSettingsUpdateRequest,
    admin_session: AdminSessionDep,
    settings_path: SettingsPathDep,
) -> AdminSettingsResponse:
    _ = admin_session

    settings = _build_app_settings_from_request(payload)
    write_app_settings(settings_path, settings)

    return _serialize_settings(
        settings=settings,
        settings_path=settings_path,
    )


@router.post(
    "/filter-preview",
    response_model=AdminSettingsFilterPreviewResponse,
)
def admin_filter_preview(
    payload: AdminSettingsFilterPreviewRequest,
    admin_session: AdminSessionDep,
    repository: RepositoryDep,
) -> AdminSettingsFilterPreviewResponse:
    _ = admin_session

    keyword_filter = _build_keyword_filter_settings(payload.keyword_filter)
    jobs = repository.list_active_jobs() if payload.active_only else repository.list_jobs()
    result = filter_jobs_by_keyword_settings(
        jobs=jobs,
        settings=keyword_filter,
    )

    passed_samples = result.passed_decisions[: payload.sample_limit]
    rejected_samples = result.rejected_decisions[: payload.sample_limit]

    return AdminSettingsFilterPreviewResponse(
        jobs_scope="active_only" if payload.active_only else "all_jobs",
        filter_enabled=keyword_filter.is_enabled(),
        include_keywords=list(keyword_filter.include_keywords),
        exclude_keywords=list(keyword_filter.exclude_keywords),
        active_fields=list(keyword_filter.active_fields()),
        total_jobs=result.total_jobs,
        passed_jobs=result.passed_count,
        rejected_jobs=result.rejected_count,
        sample_limit=payload.sample_limit,
        passed_samples=[
            _serialize_filter_sample(decision)
            for decision in passed_samples
        ],
        rejected_samples=[
            _serialize_filter_sample(decision)
            for decision in rejected_samples
        ],
    )