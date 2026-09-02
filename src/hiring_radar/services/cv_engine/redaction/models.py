from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PiiType(StrEnum):
    """Personally identifiable information categories used by redaction."""

    FULL_NAME = "full_name"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    ADDRESS = "address"
    SOCIAL_PROFILE = "social_profile"
    URL = "url"


class PiiFinding(BaseModel):
    """One matched PII fragment that may be redacted."""

    model_config = ConfigDict(extra="forbid")

    pii_type: PiiType
    raw_text: str
    replacement_text: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)


class RedactionResult(BaseModel):
    """Structured output of text redaction."""

    model_config = ConfigDict(extra="forbid")

    original_text: str
    redacted_text: str
    findings: list[PiiFinding] = Field(default_factory=list)
    redaction_map: dict[str, list[str]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
