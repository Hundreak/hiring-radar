from __future__ import annotations

from pydantic import BaseModel


class AdminCrawlRunListItemResponse(BaseModel):
    id: int
    source_name: str
    started_at: str
    finished_at: str | None
    success: bool | None
    notes: str | None


class AdminCrawlRunListResponse(BaseModel):
    items: list[AdminCrawlRunListItemResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AdminNotificationRunListItemResponse(BaseModel):
    id: int
    notification_type: str
    started_at: str
    finished_at: str | None
    status: str
    recipient_count: int
    new_jobs_count: int
    since: str | None
    subject: str | None
    error_message: str | None


class AdminNotificationRunListResponse(BaseModel):
    items: list[AdminNotificationRunListItemResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
