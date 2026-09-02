from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from hiring_radar.api.dependencies import get_current_admin_session, get_repository
from hiring_radar.api.pagination import (
    ADMIN_LIST_BOUNDS,
    normalize_page_contract,
    set_pagination_headers,
    total_pages,
)
from hiring_radar.api.schemas.keyword_preferences import (
    SubscriberKeywordPreferenceResponse,
)
from hiring_radar.api.schemas.subscribers import (
    AdminSubscriberListItemResponse,
    AdminSubscriberListResponse,
    AdminSubscriberUpdateRequest,
)
from hiring_radar.api.security import AdminSession
from hiring_radar.db.repository import HiringRadarRepository

router = APIRouter(prefix="/api/admin/subscribers", tags=["admin-subscribers"])

AdminSessionDep = Annotated[AdminSession, Depends(get_current_admin_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _map_subscriber(subscriber) -> AdminSubscriberListItemResponse:
    return AdminSubscriberListItemResponse(
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


@router.get("", response_model=AdminSubscriberListResponse)
def admin_list_subscribers(
    admin_session: AdminSessionDep,
    repository: RepositoryDep,
    response: Response,
    email_query: Annotated[str | None, Query(max_length=160)] = None,
    is_active: bool | None = None,
    digest_enabled: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> AdminSubscriberListResponse:
    _ = admin_session

    subscribers, total_items = repository.list_subscribers_paginated(
        email_query=email_query,
        is_active=is_active,
        digest_enabled=digest_enabled,
        page=page,
        page_size=page_size,
    )

    meta = normalize_page_contract(page=page, page_size=page_size, total_items=total_items, bounds=ADMIN_LIST_BOUNDS)
    set_pagination_headers(response, meta=meta)

    return AdminSubscriberListResponse(
        items=[_map_subscriber(subscriber) for subscriber in subscribers],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages(total_items=total_items, page_size=page_size),
    )


@router.patch("/{subscriber_id}", response_model=AdminSubscriberListItemResponse)
def admin_update_subscriber(
    subscriber_id: int,
    payload: AdminSubscriberUpdateRequest,
    admin_session: AdminSessionDep,
    repository: RepositoryDep,
) -> AdminSubscriberListItemResponse:
    _ = admin_session

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
        subscriber_id,
        fields=fields,
        updated_at=_utc_now_iso(),
    )
    if subscriber is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found.",
        )

    return _map_subscriber(subscriber)


@router.get(
    "/{subscriber_id}/keyword-preferences",
    response_model=SubscriberKeywordPreferenceResponse,
)
def admin_get_subscriber_keyword_preferences(
    subscriber_id: int,
    admin_session: AdminSessionDep,
    repository: RepositoryDep,
) -> SubscriberKeywordPreferenceResponse:
    _ = admin_session

    subscriber = repository.get_subscriber_by_id(subscriber_id)
    if subscriber is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found.",
        )

    preference = repository.get_subscriber_keyword_preference(subscriber_id)
    return _map_keyword_preference(preference)
