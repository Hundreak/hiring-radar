from __future__ import annotations

from pydantic import BaseModel


class UserJobListItemResponse(BaseModel):
    id: int
    source_name: str
    title: str
    company_name: str
    location: str | None
    canonical_url: str
    is_active: bool
    first_seen_at: str | None
    last_seen_at: str | None
    matched: bool
    match_score: int | None = None
    matched_keywords: list[str] = []


class UserJobListResponse(BaseModel):
    items: list[UserJobListItemResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    query: str | None
    only_matched: bool
    active_only: bool
