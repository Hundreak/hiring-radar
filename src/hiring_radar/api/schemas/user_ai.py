from __future__ import annotations

from pydantic import BaseModel, Field

from hiring_radar.services.ai.contracts import (
    CopilotChatResponse,
    HeadlineSummarySuggestionResponse,
    RoleFocusSuggestionResponse,
    SkillEvidenceSuggestionResponse,
    SkillGroupingSuggestionResponse,
)


class UserAiHealthResponse(BaseModel):
    enabled: bool
    runtime: str
    base_url: str
    configured_model: str | None = None
    runtime_status: str
    reachable: bool
    local_only_guard: bool
    response_time_ms: int | None = None
    available_models: list[str] = Field(default_factory=list)
    running_models: list[str] = Field(default_factory=list)
    message: str


class UserAiHeadlineSummaryRequest(BaseModel):
    locale: str = "tr"
    headline_option_count: int = Field(default=3, ge=1, le=5)
    summary_option_count: int = Field(default=3, ge=1, le=5)


class UserAiHeadlineSummaryResponse(HeadlineSummarySuggestionResponse):
    telemetry_ref: str | None = None


class UserAiRoleFocusRequest(BaseModel):
    locale: str = "tr"
    suggestion_count: int = Field(default=4, ge=1, le=6)


class UserAiRoleFocusResponse(RoleFocusSuggestionResponse):
    telemetry_ref: str | None = None


class UserAiSkillGroupingRequest(BaseModel):
    locale: str = "tr"
    group_limit: int = Field(default=5, ge=1, le=8)
    skill_limit_per_group: int = Field(default=8, ge=1, le=12)


class UserAiSkillGroupingResponse(SkillGroupingSuggestionResponse):
    telemetry_ref: str | None = None


class UserAiSkillEvidenceRequest(BaseModel):
    locale: str = "tr"
    skill_name: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    existing_evidence_note: str | None = Field(default=None, max_length=2000)


class UserAiSkillEvidenceResponse(SkillEvidenceSuggestionResponse):
    telemetry_ref: str | None = None


class UserAiCopilotChatRequest(BaseModel):
    locale: str = "tr"
    message: str = Field(min_length=1, max_length=6000)
    conversation_id: str | None = Field(default=None, max_length=64)


class UserAiCopilotChatResponse(CopilotChatResponse):
    conversation_id: str | None = None
    message_id: str | None = None
    telemetry_ref: str | None = None
