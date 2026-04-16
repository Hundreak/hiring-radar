from __future__ import annotations

from pydantic import BaseModel


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
    status: str
    match_score: int | None
    deadline_at: str | None
    interview_at: str | None
    created_at: str | None
    updated_at: str | None
    # Denormalized job fields for frontend display
    title: str = ""
    company_name: str = ""
    location: str | None = None
    canonical_url: str = ""
    source_name: str = ""
    matched_keywords: list[str] = []
    notes: list[SavedJobNoteResponse] = []


class SavedJobListResponse(BaseModel):
    items: list[SavedJobResponse]
