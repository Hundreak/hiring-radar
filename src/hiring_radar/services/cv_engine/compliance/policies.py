from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DataRetentionPolicy(BaseModel):
    """Retention rules for parser artifacts and audit records."""

    model_config = ConfigDict(extra="forbid")

    raw_document_days: int = Field(default=30, ge=0, le=3650)
    parsed_output_days: int = Field(default=180, ge=0, le=3650)
    audit_log_days: int = Field(default=365, ge=0, le=3650)
    redacted_artifact_days: int = Field(default=365, ge=0, le=3650)
    cache_entry_days: int = Field(default=14, ge=0, le=3650)


class CompliancePolicy(BaseModel):
    """Top-level compliance policy used by enterprise parser features."""

    model_config = ConfigDict(extra="forbid")

    enable_parse_audit: bool = True
    enable_data_minimization: bool = True
    enable_redaction_artifact: bool = True
    pii_strict_mode: bool = False
    retention: DataRetentionPolicy = Field(default_factory=DataRetentionPolicy)
