from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AtsIssueSeverity(str, Enum):
    """Severity level for ATS compatibility findings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AtsLevel(str, Enum):
    """Coarse ATS compatibility band."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AtsIssue(BaseModel):
    """One user-facing ATS scoring issue or recommendation."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    severity: AtsIssueSeverity
    penalty: int = Field(default=0, ge=0, le=100)
    recommendation: str | None = None


class AtsCompatibilityReport(BaseModel):
    """Structured ATS compatibility output for one parsed CV."""

    model_config = ConfigDict(extra="forbid")

    score: int = Field(default=0, ge=0, le=100)
    level: AtsLevel = AtsLevel.LOW
    positives: list[str] = Field(default_factory=list)
    issues: list[AtsIssue] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    contributing_factors: dict[str, int] = Field(default_factory=dict)
