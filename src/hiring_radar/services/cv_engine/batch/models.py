from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BatchParseStatus(StrEnum):
    """Execution outcome for one batch parse request."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"


class ProgressEventType(StrEnum):
    """Supported progress event types for streaming batch execution."""

    STARTED = "started"
    ITEM_COMPLETED = "item_completed"
    ITEM_FAILED = "item_failed"
    FINISHED = "finished"


class BatchRetryPolicy(BaseModel):
    """Deterministic retry policy for batch parsing."""

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=2, ge=1, le=10)
    base_delay_seconds: float = Field(default=0.0, ge=0.0, le=60.0)
    max_delay_seconds: float = Field(default=1.0, ge=0.0, le=600.0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0)
    retryable_exception_names: tuple[str, ...] = (
        "TimeoutError",
        "ConnectionError",
        "RecoverableStageError",
        "RuntimeError",
    )


class BatchParseRequest(BaseModel):
    """One source document queued for batch parsing."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    source_path: str
    priority: int = Field(default=100, ge=0, le=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchParseResult(BaseModel):
    """Streaming result emitted for one batch parse request."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    source_path: str
    status: BatchParseStatus
    attempts: int = Field(default=1, ge=1)
    duration_ms: float = Field(default=0.0, ge=0.0)
    output: Any = None
    warnings: list[str] = Field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeadLetterRecord(BaseModel):
    """Persistent description of an item that exhausted retries."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    source_path: str
    error_type: str
    error_message: str
    attempts_exhausted: int = Field(default=1, ge=1)
    reason_code: str = "batch_parse_failed"
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProgressEvent(BaseModel):
    """Structured progress event for UI or orchestration callbacks."""

    model_config = ConfigDict(extra="forbid")

    event_type: ProgressEventType
    completed_items: int = Field(default=0, ge=0)
    total_items: int = Field(default=0, ge=0)
    succeeded_items: int = Field(default=0, ge=0)
    failed_items: int = Field(default=0, ge=0)
    current_request_id: str | None = None
    current_source_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchRunSummary(BaseModel):
    """Terminal summary of one full batch execution."""

    model_config = ConfigDict(extra="forbid")

    total_items: int = Field(default=0, ge=0)
    succeeded_items: int = Field(default=0, ge=0)
    failed_items: int = Field(default=0, ge=0)
    partial_items: int = Field(default=0, ge=0)
    duration_ms: float = Field(default=0.0, ge=0.0)
    dead_letters: list[DeadLetterRecord] = Field(default_factory=list)
