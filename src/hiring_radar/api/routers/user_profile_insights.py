from __future__ import annotations

from fastapi import APIRouter

from hiring_radar.api.routers.user_profile_modules.shared import (
    RepositoryDep,
    UserSessionDep,
    get_user_profile_aggregate_response,
)
from hiring_radar.api.schemas.profile_contract import ProfileSuggestionsBundle

router = APIRouter()


@router.get(
    "/suggestions",
    response_model=ProfileSuggestionsBundle,
)
def get_user_profile_suggestions(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> ProfileSuggestionsBundle:
    aggregate = get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )
    return aggregate.suggestions
