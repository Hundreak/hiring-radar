from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AiRuntimeStatus = Literal["disabled", "ready", "unreachable", "misconfigured", "error"]


class AiChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class AiChatGenerationRequest(BaseModel):
    model: str | None = None
    messages: list[AiChatMessage] = Field(default_factory=list)
    temperature: float = 0.2
    max_retries: int = 0
    timeout_seconds: int | None = None


class AiChatGenerationResponse(BaseModel):
    model: str | None = None
    content: str = ""
    response_time_ms: int | None = None
    done: bool = True
    done_reason: str | None = None


class AiStructuredGenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: str | None = None
    messages: list[AiChatMessage] = Field(default_factory=list)
    output_json_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")
    temperature: float = 0.2
    max_retries: int = 0
    timeout_seconds: int | None = None

    @property
    def schema(self) -> dict[str, Any]:
        return self.output_json_schema


class AiStructuredGenerationResponse(BaseModel):
    model: str | None = None
    content: Any = None
    response_time_ms: int | None = None
    done: bool = True
    done_reason: str | None = None


AiStructuredGenerationResult = AiStructuredGenerationResponse


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


AiRuntimeHealth = AiHealthCheckResult


class AiAuditRecord(BaseModel):
    telemetry_ref: str
    task_name: str
    endpoint_name: str
    runtime: str
    model: str | None = None
    locale: str | None = None
    subscriber_id: int | None = None
    success: bool
    response_valid: bool
    warning_count: int = 0
    duration_ms: int | None = None
    started_at: str
    completed_at: str
    request_preview: str | None = None
    response_preview: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    prompt_name: str | None = None
    prompt_version: str | None = None
    schema_name: str | None = None
    schema_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HeadlineSuggestion(BaseModel):
    title: str
    rationale: str | None = None


HeadlineOption = HeadlineSuggestion


class SummarySuggestion(BaseModel):
    text: str
    rationale: str | None = None


SummaryOption = SummarySuggestion


class HeadlineSummarySuggestionResponse(BaseModel):
    headline_options: list[HeadlineSuggestion] = Field(default_factory=list)
    summary_options: list[SummarySuggestion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence_band: Literal["low", "medium", "high"] = "medium"
    telemetry_ref: str | None = None


class RoleFocusSuggestion(BaseModel):
    role_name: str
    fit_reason: str
    missing_signals: list[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=10)


class RoleFocusSuggestionResponse(BaseModel):
    role_suggestions: list[RoleFocusSuggestion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence_band: Literal["low", "medium", "high"] = "medium"
    telemetry_ref: str | None = None


class SkillGroup(BaseModel):
    group_name: str
    skills: list[str] = Field(default_factory=list)
    notes: str | None = None


class SkillGroupingSuggestionResponse(BaseModel):
    groups: list[SkillGroup] = Field(default_factory=list)
    duplicates: list[str] = Field(default_factory=list)
    normalization_suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence_band: Literal["low", "medium", "high"] = "medium"
    telemetry_ref: str | None = None


class SkillEvidenceSuggestionResponse(BaseModel):
    description_suggestions: list[str] = Field(default_factory=list)
    evidence_note_suggestions: list[str] = Field(default_factory=list)
    proof_ideas: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)
    strengthening_note: str | None = None
    warnings: list[str] = Field(default_factory=list)
    confidence_band: Literal["low", "medium", "high"] = "medium"
    telemetry_ref: str | None = None


class AiCopilotSource(BaseModel):
    source_type: str
    label: str
    title: str | None = None
    snippet: str | None = None
    trust_level: str | None = None
    freshness_label: str | None = None


CopilotGroundingSource = AiCopilotSource


class AiCopilotChatResponse(BaseModel):
    answer: str
    sources: list[AiCopilotSource] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence_band: Literal["low", "medium", "high"] = "medium"
    follow_up_suggestions: list[str] = Field(default_factory=list)
    learned_memory_notes: list[str] = Field(default_factory=list)
    telemetry_ref: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None


CopilotChatResponse = AiCopilotChatResponse


__all__ = [
    "AiAuditRecord",
    "AiChatGenerationRequest",
    "AiChatGenerationResponse",
    "AiChatMessage",
    "AiCopilotChatResponse",
    "AiCopilotSource",
    "AiHealthCheckResult",
    "AiRuntimeHealth",
    "AiRuntimeStatus",
    "AiStructuredGenerationRequest",
    "AiStructuredGenerationResponse",
    "AiStructuredGenerationResult",
    "CopilotChatResponse",
    "CopilotGroundingSource",
    "HeadlineOption",
    "HeadlineSuggestion",
    "HeadlineSummarySuggestionResponse",
    "RoleFocusSuggestion",
    "RoleFocusSuggestionResponse",
    "SkillEvidenceSuggestionResponse",
    "SkillGroup",
    "SkillGroupingSuggestionResponse",
    "SummaryOption",
    "SummarySuggestion",
]
