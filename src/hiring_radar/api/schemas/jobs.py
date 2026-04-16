from __future__ import annotations

from pydantic import BaseModel


class AdminJobListItemResponse(BaseModel):
    id: int
    source_name: str
    company_name: str
    source_type: str
    title: str
    location: str | None
    canonical_url: str
    posted_at: str | None
    first_seen_at: str | None
    last_seen_at: str | None
    is_active: bool


class AdminJobListResponse(BaseModel):
    items: list[AdminJobListItemResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
