from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.schemas.profile_contract import UserProfileAggregateResponse
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.profile_aggregate import build_user_profile_aggregate_response
from hiring_radar.services.user_auth import UserSession

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


def get_user_profile_aggregate_response(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
) -> UserProfileAggregateResponse:
    """Build the canonical profile aggregate for split profile routers."""

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
