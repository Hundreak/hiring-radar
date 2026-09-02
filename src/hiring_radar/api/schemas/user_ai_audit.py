from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from hiring_radar.api.schemas.profile_contract import StrictSchema

AiAuditActionType = Literal["replace", "append"]
AiAuditPersistenceStatus = Literal["unsaved", "saved", "reverted"]
AiAuditEvaluationStatus = Literal["pending", "accepted", "rejected", "modified", "reverted"]


class AiAuditFinalizeContext(StrictSchema):
    audit_event_ids: list[str] = Field(default_factory=list)


class CreateUserAiAuditEventRequest(StrictSchema):
    telemetry_ref: str | None = None
    target_field: str = Field(min_length=1, max_length=160)
    target_entity_id: str | None = Field(default=None, max_length=120)
    action_type: AiAuditActionType
    source_panel: str = Field(min_length=1, max_length=80)
    suggestion_kind: str | None = Field(default=None, max_length=80)
    suggestion_text: str | None = None
    suggestion_index: int | None = Field(default=None, ge=0)
    before_snapshot: dict[str, Any] = Field(default_factory=dict)
    after_snapshot: dict[str, Any] = Field(default_factory=dict)
    interaction_status: Literal["applied", "rejected"] = "applied"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RejectUserAiAuditEventRequest(StrictSchema):
    reason: str | None = Field(default=None, max_length=240)


class UserAiAuditEventResponse(StrictSchema):
    id: str
    event_ref: str
    telemetry_ref: str | None = None
    target_field: str
    target_entity_id: str | None = None
    action_type: AiAuditActionType
    source_panel: str
    suggestion_kind: str | None = None
    suggestion_text: str | None = None
    suggestion_index: int | None = None
    before_snapshot: dict[str, Any] = Field(default_factory=dict)
    after_snapshot: dict[str, Any] = Field(default_factory=dict)
    persistence_status: AiAuditPersistenceStatus
    evaluation_status: AiAuditEvaluationStatus
    evaluation_score: float | None = None
    manual_edit_distance: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None
    saved_at: str | None = None
    reverted_at: str | None = None


class UserAiAuditMarkerResponse(StrictSchema):
    id: str
    target_field: str
    target_entity_id: str | None = None
    source_panel: str
    action_type: AiAuditActionType
    persistence_status: AiAuditPersistenceStatus
    evaluation_status: AiAuditEvaluationStatus
    suggestion_kind: str | None = None
    telemetry_ref: str | None = None
    updated_at: str | None = None
    saved_at: str | None = None
    reverted_at: str | None = None
    can_revert: bool = False
    label: str


class RevertUserAiAuditEventResponse(StrictSchema):
    reverted_event: UserAiAuditEventResponse
    replacement_event: UserAiAuditEventResponse
