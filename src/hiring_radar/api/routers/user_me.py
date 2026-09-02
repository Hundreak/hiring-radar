from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from hiring_radar.api.dependencies import (
    get_app_settings,
    get_current_user_session,
    get_repository,
)
from hiring_radar.api.schemas.keyword_preferences import (
    KeywordPreferenceFieldMatchResponse,
    KeywordPreferenceSampleResponse,
    SubscriberKeywordPreferencePreviewRequest,
    SubscriberKeywordPreferencePreviewResponse,
    SubscriberKeywordPreferenceResponse,
    SubscriberKeywordPreferenceUpdateRequest,
)
from hiring_radar.api.schemas.user_me import (
    UserFilterPolicyResponse,
    UserMeResponse,
    UserNotificationPreferenceResponse,
    UserNotificationPreferenceUpdateRequest,
    UserPreferencesUpdateRequest,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering import JobFilterDecision, filter_jobs_by_keyword_settings
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.services.user_auth import UserSession
from hiring_radar.settings import AppSettings

router = APIRouter(prefix="/api/user/me", tags=["user-me"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
AppSettingsDep = Annotated[AppSettings, Depends(get_app_settings)]


_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")




def _map_notification_preference(preference) -> UserNotificationPreferenceResponse:
    return UserNotificationPreferenceResponse(
        subscriber_id=preference.subscriber_id,
        job_digest_enabled=preference.job_digest_enabled,
        product_updates_enabled=preference.product_updates_enabled,
        employer_messages_enabled=preference.employer_messages_enabled,
        security_alerts_enabled=preference.security_alerts_enabled,
        quiet_hours_enabled=preference.quiet_hours_enabled,
        quiet_hours_start=preference.quiet_hours_start,
        quiet_hours_end=preference.quiet_hours_end,
        timezone=preference.timezone,
        updated_at=preference.updated_at,
    )


def _validate_notification_preference_fields(fields: dict[str, object]) -> None:
    for field_name in ("job_digest_enabled", "product_updates_enabled", "employer_messages_enabled", "security_alerts_enabled", "quiet_hours_enabled"):
        if field_name in fields and fields[field_name] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{field_name}' cannot be null.",
            )

    for field_name in ("quiet_hours_start", "quiet_hours_end"):
        value = fields.get(field_name)
        if value is not None and not _TIME_RE.match(str(value)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{field_name}' must use HH:MM 24-hour format.",
            )

    timezone = fields.get("timezone")
    if timezone is not None:
        cleaned = str(timezone).strip()
        if not cleaned or len(cleaned) > 64 or " " in cleaned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'timezone' must be a compact IANA timezone name.",
            )


def _map_subscriber(subscriber) -> UserMeResponse:
    return UserMeResponse(
        id=subscriber.id or 0,
        email=subscriber.email,
        full_name=subscriber.full_name,
        is_active=subscriber.is_active,
        digest_enabled=subscriber.digest_enabled,
        created_at=subscriber.created_at,
        updated_at=subscriber.updated_at,
    )


def _map_keyword_preference(preference) -> SubscriberKeywordPreferenceResponse:
    return SubscriberKeywordPreferenceResponse(
        subscriber_id=preference.subscriber_id,
        include_keywords=list(preference.include_keywords),
        exclude_keywords=list(preference.exclude_keywords),
        match_title=preference.match_title,
        match_location=preference.match_location,
        match_company_name=preference.match_company_name,
        enabled=preference.is_enabled(),
        active_fields=list(preference.active_fields()),
        updated_at=preference.updated_at,
    )


def _build_keyword_filter_settings_from_payload(
    payload: SubscriberKeywordPreferenceUpdateRequest,
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
            message = "At least one match field must be enabled."

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc


def _serialize_filter_match(match) -> KeywordPreferenceFieldMatchResponse:
    return KeywordPreferenceFieldMatchResponse(
        field_name=match.field_name,
        keyword=match.keyword,
        field_value=match.field_value,
    )


def _serialize_filter_sample(
    decision: JobFilterDecision,
) -> KeywordPreferenceSampleResponse:
    return KeywordPreferenceSampleResponse(
        job_id=decision.job.id,
        title=decision.job.title,
        company_name=decision.job.company_name,
        location=decision.job.location,
        canonical_url=decision.job.canonical_url,
        include_matches=[
            _serialize_filter_match(match) for match in decision.evaluation.include_matches
        ],
        exclude_matches=[
            _serialize_filter_match(match) for match in decision.evaluation.exclude_matches
        ],
    )


@router.get("", response_model=UserMeResponse)
def user_me(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserMeResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    return _map_subscriber(subscriber)


@router.patch("/preferences", response_model=UserMeResponse)
def update_user_preferences(
    payload: UserPreferencesUpdateRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserMeResponse:
    fields = payload.provided_update_fields()
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )

    if "is_active" in fields and fields["is_active"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'is_active' cannot be null.",
        )

    if "digest_enabled" in fields and fields["digest_enabled"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'digest_enabled' cannot be null.",
        )

    subscriber = repository.update_subscriber_fields_by_id(
        user_session.subscriber_id,
        fields=fields,
        updated_at=_utc_now_iso(),
    )
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    return _map_subscriber(subscriber)


@router.get(
    "/notification-preferences",
    response_model=UserNotificationPreferenceResponse,
)
def user_notification_preferences(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserNotificationPreferenceResponse:
    preference = repository.get_subscriber_notification_preference(user_session.subscriber_id)
    if preference is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    return _map_notification_preference(preference)


@router.patch(
    "/notification-preferences",
    response_model=UserNotificationPreferenceResponse,
)
def update_user_notification_preferences(
    payload: UserNotificationPreferenceUpdateRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserNotificationPreferenceResponse:
    fields = payload.provided_update_fields()
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )

    _validate_notification_preference_fields(fields)
    updated_at = _utc_now_iso()

    if "job_digest_enabled" in fields:
        subscriber = repository.update_subscriber_fields_by_id(
            user_session.subscriber_id,
            fields={"digest_enabled": bool(fields["job_digest_enabled"])},
            updated_at=updated_at,
        )
        if subscriber is None:
            raise HTTPException(status_code=404, detail="Subscriber not found.")

    preference = repository.upsert_subscriber_notification_preference(
        user_session.subscriber_id,
        product_updates_enabled=fields.get("product_updates_enabled"),
        employer_messages_enabled=fields.get("employer_messages_enabled"),
        security_alerts_enabled=fields.get("security_alerts_enabled"),
        quiet_hours_enabled=fields.get("quiet_hours_enabled"),
        quiet_hours_start=fields.get("quiet_hours_start"),
        quiet_hours_end=fields.get("quiet_hours_end"),
        timezone=fields.get("timezone"),
        updated_at=updated_at,
    )
    if preference is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    return _map_notification_preference(preference)


@router.get("/filter-policy", response_model=UserFilterPolicyResponse)
def user_filter_policy(
    user_session: UserSessionDep,
    settings: AppSettingsDep,
) -> UserFilterPolicyResponse:
    _ = user_session

    keyword_filter = settings.keyword_filter
    return UserFilterPolicyResponse(
        filter_enabled=keyword_filter.is_enabled(),
        apply_keyword_filter_to_digest=(settings.notifications.apply_keyword_filter_to_digest),
        include_keywords=list(keyword_filter.include_keywords),
        exclude_keywords=list(keyword_filter.exclude_keywords),
        active_fields=list(keyword_filter.active_fields()),
    )


@router.get(
    "/keyword-preferences",
    response_model=SubscriberKeywordPreferenceResponse,
)
def user_keyword_preferences(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SubscriberKeywordPreferenceResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    preference = repository.get_subscriber_keyword_preference(user_session.subscriber_id)
    return _map_keyword_preference(preference)


@router.put(
    "/keyword-preferences",
    response_model=SubscriberKeywordPreferenceResponse,
)
def update_user_keyword_preferences(
    payload: SubscriberKeywordPreferenceUpdateRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SubscriberKeywordPreferenceResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    keyword_filter = _build_keyword_filter_settings_from_payload(payload)

    preference = repository.upsert_subscriber_keyword_preference(
        user_session.subscriber_id,
        include_keywords=keyword_filter.include_keywords,
        exclude_keywords=keyword_filter.exclude_keywords,
        match_title=keyword_filter.match_title,
        match_location=keyword_filter.match_location,
        match_company_name=keyword_filter.match_company_name,
        updated_at=_utc_now_iso(),
    )

    return _map_keyword_preference(preference)


@router.post(
    "/keyword-preferences/preview",
    response_model=SubscriberKeywordPreferencePreviewResponse,
)
def preview_user_keyword_preferences(
    payload: SubscriberKeywordPreferencePreviewRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SubscriberKeywordPreferencePreviewResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    keyword_filter = _build_keyword_filter_settings_from_payload(payload.keyword_preference)

    jobs = repository.list_active_jobs() if payload.active_only else repository.list_jobs()
    result = filter_jobs_by_keyword_settings(
        jobs=jobs,
        settings=keyword_filter,
    )

    return SubscriberKeywordPreferencePreviewResponse(
        jobs_scope="active_only" if payload.active_only else "all_jobs",
        filter_enabled=bool(keyword_filter.is_enabled()),
        include_keywords=list(keyword_filter.include_keywords),
        exclude_keywords=list(keyword_filter.exclude_keywords),
        active_fields=list(keyword_filter.active_fields()),
        total_jobs=result.total_jobs,
        passed_jobs=result.passed_count,
        rejected_jobs=result.rejected_count,
        sample_limit=payload.sample_limit,
        passed_samples=[
            _serialize_filter_sample(decision)
            for decision in result.passed_decisions[: payload.sample_limit]
        ],
        rejected_samples=[
            _serialize_filter_sample(decision)
            for decision in result.rejected_decisions[: payload.sample_limit]
        ],
    )
