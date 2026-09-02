from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from hiring_radar.services.cv_engine.compliance.policies import DataRetentionPolicy


class RetentionDisposition(StrEnum):
    """Retention outcome for one artifact class."""

    KEEP = "keep"
    EXPIRE = "expire"


class RetentionDecision(BaseModel):
    """Retention evaluation result for one artifact timestamp."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str
    disposition: RetentionDisposition
    expires_at: str
    evaluated_at: str
    reason: str
    remaining_days: int = Field(default=0)


def _parse_utc(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(UTC)


def evaluate_retention(
    *,
    artifact_kind: str,
    created_at: str,
    policy: DataRetentionPolicy,
    now: datetime | None = None,
) -> RetentionDecision:
    """Evaluate whether an artifact should be retained or expired."""
    now_utc = now.astimezone(UTC) if now is not None else datetime.now(UTC)
    created_dt = _parse_utc(created_at)
    retention_days_by_kind = {
        "raw_document": policy.raw_document_days,
        "parsed_output": policy.parsed_output_days,
        "audit_log": policy.audit_log_days,
        "redacted_artifact": policy.redacted_artifact_days,
        "cache_entry": policy.cache_entry_days,
    }
    retention_days = retention_days_by_kind.get(artifact_kind, policy.parsed_output_days)
    expires_at = created_dt + timedelta(days=retention_days)
    disposition = (
        RetentionDisposition.EXPIRE if now_utc >= expires_at else RetentionDisposition.KEEP
    )
    remaining_days = max((expires_at - now_utc).days, 0)
    reason = (
        f"{artifact_kind}_retention_elapsed" if disposition == RetentionDisposition.EXPIRE
        else f"{artifact_kind}_retention_active"
    )
    return RetentionDecision(
        artifact_kind=artifact_kind,
        disposition=disposition,
        expires_at=expires_at.replace(microsecond=0).isoformat(),
        evaluated_at=now_utc.replace(microsecond=0).isoformat(),
        reason=reason,
        remaining_days=remaining_days,
    )
