from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

AiRuntimeStatus = Literal["disabled", "ready", "unreachable", "misconfigured", "error"]
AiRole = Literal["system", "user", "assistant"]


class AiHealthCheckResult(BaseModel):
    enabled: bool
    runtime: str
    base_url: str
    configured_model: str | None = None
    runtime_status: AiRuntimeStatus
    reachable: bool
    local_only_guard: bool
    response_time_ms: int | None = None
    available_models: list[str] = Field(default_factory=list)
    running_models: list[str] = Field(default_factory=list)
    message: str


class AiChatMessage(BaseModel):
    role: AiRole
    content: str


class AiStructuredGenerationRequest(BaseModel):
    model: str
    messages: list[AiChatMessage] = Field(default_factory=list)
    output_json_schema: dict[str, Any]
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_retries: int = Field(default=1, ge=0)
    prompt_name: str | None = None
    prompt_version: str | None = None
    schema_name: str | None = None
    schema_version: str | None = None


class AiStructuredGenerationResponse(BaseModel):
    model: str
    content: dict[str, Any]
    response_time_ms: int | None = None
    done: bool = True
    done_reason: str | None = None


class HeadlineSuggestion(BaseModel):
    title: str
    rationale: str | None = None


class SummarySuggestion(BaseModel):
    text: str
    rationale: str | None = None


class HeadlineSummarySuggestionResponse(BaseModel):
    headline_options: list[HeadlineSuggestion] = Field(default_factory=list)
    summary_options: list[SummarySuggestion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence_band: Literal["low", "medium", "high"] = "medium"


class RoleFocusSuggestion(BaseModel):
    role_name: str
    fit_reason: str
    missing_signals: list[str] = Field(default_factory=list)
    priority: int = Field(ge=1, le=10)


class RoleFocusSuggestionResponse(BaseModel):
    role_suggestions: list[RoleFocusSuggestion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SkillGroup(BaseModel):
    group_name: str
    skills: list[str] = Field(default_factory=list)
    notes: str | None = None


class SkillGroupingSuggestionResponse(BaseModel):
    groups: list[SkillGroup] = Field(default_factory=list)
    duplicates: list[str] = Field(default_factory=list)
    normalization_suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AiAuditRecord(BaseModel):
    telemetry_ref: str
    task_name: str
    endpoint_name: str
    runtime: str
    model: str | None = None
    locale: str
    subscriber_id: int | None = None
    success: bool
    response_valid: bool
    warning_count: int = 0
    duration_ms: int | None = None
    response_time_ms: int | None = None
    started_at: str
    completed_at: str
    error_type: str | None = None
    error_message: str | None = None
    prompt_name: str | None = None
    prompt_version: str | None = None
    schema_name: str | None = None
    schema_version: str | None = None
    response_preview: str | None = None
