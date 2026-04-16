from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from hiring_radar.services.cv_engine.batch.models import BatchRetryPolicy
from hiring_radar.services.cv_engine.compliance.policies import CompliancePolicy
from hiring_radar.services.cv_engine.telemetry.health import CvEngineHealthReport


class AdminCvEngineBatchItemRequest(BaseModel):
    """One source file submitted for internal batch parsing."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    source_path: str
    priority: int = Field(default=100, ge=0, le=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdminCvEngineBatchCreateRequest(BaseModel):
    """Request payload for one internal batch parse execution."""

    model_config = ConfigDict(extra="forbid")

    items: list[AdminCvEngineBatchItemRequest] = Field(
        default_factory=list,
        min_length=1,
    )
    retry_policy: BatchRetryPolicy | None = None


class AdminCvEngineBatchResultResponse(BaseModel):
    """Compact batch item result surfaced to admin clients."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    source_path: str
    status: str
    attempts: int
    duration_ms: float
    error_type: str | None = None
    error_message: str | None = None
    output: dict[str, Any] | None = None


class AdminCvEngineDeadLetterResponse(BaseModel):
    """Dead-letter representation for one failed batch item."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    source_path: str
    error_type: str
    error_message: str
    attempts_exhausted: int
    reason_code: str
    created_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdminCvEngineBatchSummaryResponse(BaseModel):
    """Terminal summary of one completed admin batch."""

    model_config = ConfigDict(extra="forbid")

    total_items: int
    succeeded_items: int
    failed_items: int
    partial_items: int
    duration_ms: float


class AdminCvEngineBatchResultEnvelopeResponse(BaseModel):
    """Stored admin batch execution record."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str
    created_at: str
    finished_at: str | None = None
    request_count: int
    status: str
    summary: AdminCvEngineBatchSummaryResponse | None = None
    results: list[AdminCvEngineBatchResultResponse] = Field(default_factory=list)


class AdminCvEngineBatchListItemResponse(BaseModel):
    """Lightweight list response for recent batch executions."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str
    created_at: str
    finished_at: str | None = None
    request_count: int
    status: str
    total_items: int | None = None
    succeeded_items: int | None = None
    failed_items: int | None = None
    partial_items: int | None = None
    duration_ms: float | None = None


class AdminCvEngineBatchListResponse(BaseModel):
    """Collection of recent admin batch execution records."""

    model_config = ConfigDict(extra="forbid")

    batches: list[AdminCvEngineBatchListItemResponse] = Field(default_factory=list)


class AdminCvEngineMetricsResponse(BaseModel):
    """Metrics snapshot response for the internal CV engine surface."""

    model_config = ConfigDict(extra="forbid")

    metrics: dict[str, dict[str, float | int]] = Field(default_factory=dict)


class AdminCvEngineCompliancePolicyResponse(BaseModel):
    """Compliance policy snapshot for internal operations."""

    model_config = ConfigDict(extra="forbid")

    policy: CompliancePolicy


class AdminCvEngineHealthResponse(BaseModel):
    """Health payload combining parser dependency checks and metrics."""

    model_config = ConfigDict(extra="forbid")

    health: CvEngineHealthReport
    metrics: dict[str, dict[str, float | int]] = Field(default_factory=dict)
