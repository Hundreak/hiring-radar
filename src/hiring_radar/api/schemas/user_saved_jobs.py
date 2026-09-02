from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SaveJobRequest(BaseModel):
    job_id: int
    match_score: int | None = None


class UpdateSavedJobStatusRequest(BaseModel):
    status: str
    deadline_at: str | None = None
    interview_at: str | None = None


class AddNoteRequest(BaseModel):
    content: str


class SavedJobNoteResponse(BaseModel):
    id: int
    saved_job_id: int
    content: str
    created_at: str | None


class SavedJobResponse(BaseModel):
    id: int
    job_id: int
    job_kind: Literal["legacy", "canonical"] = "legacy"
    status: str
    match_score: int | None
    deadline_at: str | None
    interview_at: str | None
    created_at: str | None
    updated_at: str | None
    title: str = ""
    company_name: str = ""
    location: str | None = None
    canonical_url: str = ""
    source_name: str = ""
    matched_keywords: list[str] = Field(default_factory=list)
    notes: list[SavedJobNoteResponse] = Field(default_factory=list)


class SavedJobListResponse(BaseModel):
    items: list[SavedJobResponse]
    page: int = 1
    page_size: int = 100
    total_items: int = 0
    total_pages: int = 0
    status: str | None = None
