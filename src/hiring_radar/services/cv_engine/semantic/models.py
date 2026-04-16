from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FieldSource(str, Enum):
    """Normalized source category for semantic field extraction."""

    RULE = "rule"
    HEURISTIC = "heuristic"
    CATALOG = "catalog"
    CONTEXT = "context"
    SECTION = "section"
    LAYOUT = "layout"
    LEGACY_BRIDGE = "legacy_bridge"
    MULTI_SIGNAL = "multi_signal"


class ConfidenceLevel(str, Enum):
    """Coarse confidence band for downstream consumers."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SemanticEvidence(BaseModel):
    """Evidence fragment that supports an extracted semantic field."""

    model_config = ConfigDict(extra="forbid")

    text: str
    normalized_text: str | None = None
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    line_index: int | None = Field(default=None, ge=0)
    page_number: int | None = Field(default=None, ge=0)
    section_name: str | None = None
    matched_alias: str | None = None
    bounding_box: tuple[float, float, float, float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FieldProvenance(BaseModel):
    """Explain how a semantic field was derived."""

    model_config = ConfigDict(extra="forbid")

    source: FieldSource
    extractor: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    evidences: list[SemanticEvidence] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FieldConfidenceAssessment(BaseModel):
    """Numeric and categorical confidence representation."""

    model_config = ConfigDict(extra="forbid")

    score: float = Field(default=0.0, ge=0.0, le=1.0)
    level: ConfidenceLevel = ConfidenceLevel.LOW
    reasons: list[str] = Field(default_factory=list)
    bonuses: list[str] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)


class SemanticCandidate(BaseModel):
    """Intermediate semantic candidate prior to final field resolution."""

    model_config = ConfigDict(extra="forbid")

    value: str
    normalized_value: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    section_name: str | None = None
    source: FieldSource = FieldSource.HEURISTIC
    evidence: SemanticEvidence | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResolvedSkill(BaseModel):
    """Canonical semantic skill with provenance and categorization."""

    model_config = ConfigDict(extra="forbid")

    canonical_name: str
    display_name: str
    matched_alias: str
    category: str
    skill_type: str = "hard_skill"
    source_section: str | None = None
    ambiguous: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_assessment: FieldConfidenceAssessment | None = None
    provenance: FieldProvenance | None = None


class ResolvedRoleSignal(BaseModel):
    """Structured role/title signal."""

    model_config = ConfigDict(extra="forbid")

    title: str
    seniority: str | None = None
    function_family: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_assessment: FieldConfidenceAssessment | None = None
    provenance: FieldProvenance | None = None


class ResolvedOrganizationSignal(BaseModel):
    """Structured organization/company signal."""

    model_config = ConfigDict(extra="forbid")

    organization_name: str
    organization_type: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_assessment: FieldConfidenceAssessment | None = None
    provenance: FieldProvenance | None = None


class ResolvedLocationSignal(BaseModel):
    """Structured location signal."""

    model_config = ConfigDict(extra="forbid")

    location_name: str
    normalized_country: str | None = None
    normalized_city: str | None = None
    remote_hint: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_assessment: FieldConfidenceAssessment | None = None
    provenance: FieldProvenance | None = None
