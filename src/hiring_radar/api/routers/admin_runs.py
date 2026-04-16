from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from hiring_radar.api.dependencies import get_current_admin_session, get_repository
from hiring_radar.api.schemas.runs import (
    AdminCrawlRunListItemResponse,
    AdminCrawlRunListResponse,
    AdminNotificationRunListItemResponse,
    AdminNotificationRunListResponse,
)
from hiring_radar.api.security import AdminSession
from hiring_radar.db.repository import HiringRadarRepository

router = APIRouter(prefix="/api/admin", tags=["admin-runs"])

AdminSessionDep = Annotated[AdminSession, Depends(get_current_admin_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


def _total_pages(*, total_items: int, page_size: int) -> int:
    if total_items == 0:
        return 0
    return (total_items + page_size - 1) // page_size


@router.get("/crawl-runs", response_model=AdminCrawlRunListResponse)
def admin_list_crawl_runs(
    admin_session: AdminSessionDep,
    repository: RepositoryDep,
    source_name: str | None = None,
    success: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> AdminCrawlRunListResponse:
    _ = admin_session

    runs, total_items = repository.list_crawl_runs_paginated(
        source_name=source_name,
        success=success,
        page=page,
        page_size=page_size,
    )

    return AdminCrawlRunListResponse(
        items=[
            AdminCrawlRunListItemResponse(
                id=run.id or 0,
                source_name=run.source_name,
                started_at=run.started_at,
                finished_at=run.finished_at,
                success=run.success,
                notes=run.notes,
            )
            for run in runs
        ],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=_total_pages(total_items=total_items, page_size=page_size),
    )


@router.get("/notification-runs", response_model=AdminNotificationRunListResponse)
def admin_list_notification_runs(
    admin_session: AdminSessionDep,
    repository: RepositoryDep,
    notification_type: str | None = None,
    status: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> AdminNotificationRunListResponse:
    _ = admin_session

    runs, total_items = repository.list_notification_runs_paginated(
        notification_type=notification_type,
        status=status,
        page=page,
        page_size=page_size,
    )

    return AdminNotificationRunListResponse(
        items=[
            AdminNotificationRunListItemResponse(
                id=run.id or 0,
                notification_type=run.notification_type,
                started_at=run.started_at,
                finished_at=run.finished_at,
                status=run.status,
                recipient_count=run.recipient_count,
                new_jobs_count=run.new_jobs_count,
                since=run.since,
                subject=run.subject,
                error_message=run.error_message,
            )
            for run in runs
        ],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=_total_pages(total_items=total_items, page_size=page_size),
    )
