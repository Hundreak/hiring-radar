from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from hiring_radar.api.dependencies import (
    get_app_settings,
    get_current_admin_session,
    get_repository,
)
from hiring_radar.api.schemas.dashboard import (
    DashboardDigestFilterPolicyResponse,
    DashboardJobCountsResponse,
    DashboardLatestRunResponse,
    DashboardSubscriberCountsResponse,
    DashboardSummaryResponse,
)
from hiring_radar.api.security import AdminSession
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.settings import AppSettings

DIGEST_EMAIL_NOTIFICATION_TYPE = "digest_email"

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


def _map_latest_crawl_run(run) -> DashboardLatestRunResponse | None:
    if run is None:
        return None

    return DashboardLatestRunResponse(
        id=run.id,
        source_name=run.source_name,
        started_at=run.started_at,
        finished_at=run.finished_at,
        success=run.success,
        notes=run.notes,
    )


def _map_latest_notification_run(run) -> DashboardLatestRunResponse | None:
    if run is None:
        return None

    return DashboardLatestRunResponse(
        id=run.id,
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


@router.get("/summary", response_model=DashboardSummaryResponse)
def admin_dashboard_summary(
    admin_session: Annotated[AdminSession, Depends(get_current_admin_session)],
    repository: Annotated[HiringRadarRepository, Depends(get_repository)],
    settings: Annotated[AppSettings, Depends(get_app_settings)],
) -> DashboardSummaryResponse:
    _ = admin_session

    job_counts = repository.get_job_counts()
    subscriber_counts = repository.get_subscriber_counts()
    latest_crawl_run = repository.get_latest_crawl_run()
    latest_notification_run = repository.get_latest_notification_run(
        notification_type=DIGEST_EMAIL_NOTIFICATION_TYPE,
    )

    keyword_filter = settings.keyword_filter

    return DashboardSummaryResponse(
        jobs=DashboardJobCountsResponse(**job_counts),
        subscribers=DashboardSubscriberCountsResponse(**subscriber_counts),
        latest_crawl_run=_map_latest_crawl_run(latest_crawl_run),
        latest_notification_run=_map_latest_notification_run(latest_notification_run),
        digest_filter_policy=DashboardDigestFilterPolicyResponse(
            filter_enabled=keyword_filter.is_enabled(),
            apply_keyword_filter_to_digest=(settings.notifications.apply_keyword_filter_to_digest),
            include_keywords=list(keyword_filter.include_keywords),
            exclude_keywords=list(keyword_filter.exclude_keywords),
            active_fields=list(keyword_filter.active_fields()),
        ),
    )
