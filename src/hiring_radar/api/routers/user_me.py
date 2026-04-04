from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from hiring_radar.api.dependencies import (
    get_app_settings,
    get_current_user_session,
    get_repository,
)
from hiring_radar.api.schemas.user_me import (
    UserFilterPolicyResponse,
    UserMeResponse,
    UserPreferencesUpdateRequest,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.user_auth import UserSession
from hiring_radar.settings import AppSettings

router = APIRouter(prefix="/api/user/me", tags=["user-me"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]
AppSettingsDep = Annotated[AppSettings, Depends(get_app_settings)]


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


@router.get("/filter-policy", response_model=UserFilterPolicyResponse)
def user_filter_policy(
    user_session: UserSessionDep,
    settings: AppSettingsDep,
) -> UserFilterPolicyResponse:
    _ = user_session

    keyword_filter = settings.keyword_filter
    return UserFilterPolicyResponse(
        filter_enabled=keyword_filter.is_enabled(),
        apply_keyword_filter_to_digest=(
            settings.notifications.apply_keyword_filter_to_digest
        ),
        include_keywords=list(keyword_filter.include_keywords),
        exclude_keywords=list(keyword_filter.exclude_keywords),
        active_fields=list(keyword_filter.active_fields()),
    )