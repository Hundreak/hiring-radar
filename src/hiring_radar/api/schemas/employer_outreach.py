from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

OutreachChannel = Literal["email", "linkedin", "whatsapp"]
OutreachTone = Literal["warm", "direct", "premium", "technical"]
OutreachTemplate = Literal["role-fit", "quick-intro", "technical-depth", "salary-transparent"]


class EmployerOutreachCampaignCreateRequest(BaseModel):
    name: str | None = None
    candidate_ids: list[int] = Field(default_factory=list, min_length=1)
    channel: OutreachChannel
    tone: OutreachTone
    template: OutreachTemplate
    include_salary: bool = True
    include_calendar: bool = True
    message_preview: str | None = None
    response_rate: int = Field(default=0, ge=0, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmployerCandidateBulkTagRequest(BaseModel):
    candidate_ids: list[int] = Field(default_factory=list, min_length=1)
    tag: str = Field(min_length=1, max_length=64)


class EmployerCandidateBulkNoteRequest(BaseModel):
    candidate_ids: list[int] = Field(default_factory=list, min_length=1)
    note: str = Field(min_length=1, max_length=2000)
    tone: Literal["neutral", "success", "warning", "ai"] = "neutral"

QueueItemStatus = Literal["ready", "review", "blocked"]


class EmployerSendQueueItemCreateRequest(BaseModel):
    candidate_id: int
    subject: str = Field(min_length=1, max_length=240)
    message: str = Field(min_length=1, max_length=6000)
    response_score: int = Field(default=0, ge=0, le=100)
    status: QueueItemStatus = "review"
    checks: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmployerSendQueuePrepareRequest(BaseModel):
    items: list[EmployerSendQueueItemCreateRequest] = Field(default_factory=list, min_length=1)
    actor: str = Field(default="Sen", min_length=1, max_length=120)
    note: str | None = Field(default=None, max_length=1000)


class EmployerSendQueueItemUpdateRequest(BaseModel):
    status: QueueItemStatus | None = None
    checks: list[str] | None = None
    actor: str = Field(default="Sen", min_length=1, max_length=120)
    note: str | None = Field(default=None, max_length=1000)


class EmployerCandidateStageUpdateRequest(BaseModel):
    candidate_id: int = Field(ge=1)
    stage_key: Literal["new", "reviewed", "shortlist", "interview", "offer", "hired", "archived"]
    job_id: int | None = Field(default=None, ge=1)
    note: str | None = Field(default=None, max_length=1000)
