from __future__ import annotations

from pydantic import BaseModel


class DashboardJobCountsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    inactive_jobs: int


class DashboardSubscriberCountsResponse(BaseModel):
    total_subscribers: int
    active_subscribers: int
    digest_enabled_subscribers: int


class DashboardLatestRunResponse(BaseModel):
    id: int | None
    source_name: str | None = None
    notification_type: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    success: bool | None = None
    status: str | None = None
    notes: str | None = None
    recipient_count: int | None = None
    new_jobs_count: int | None = None
    since: str | None = None
    subject: str | None = None
    error_message: str | None = None


class DashboardDigestFilterPolicyResponse(BaseModel):
    filter_enabled: bool
    apply_keyword_filter_to_digest: bool
    include_keywords: list[str]
    exclude_keywords: list[str]
    active_fields: list[str]


class DashboardSummaryResponse(BaseModel):
    jobs: DashboardJobCountsResponse
    subscribers: DashboardSubscriberCountsResponse
    latest_crawl_run: DashboardLatestRunResponse | None
    latest_notification_run: DashboardLatestRunResponse | None
    digest_filter_policy: DashboardDigestFilterPolicyResponse
