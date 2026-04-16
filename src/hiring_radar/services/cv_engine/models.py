from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from hiring_radar.services.cv_engine.semantic.models import (
    FieldConfidenceAssessment,
    FieldProvenance,
)


class ParserStageName(str, Enum):
    """Supported CV parser engine pipeline stages."""

    INGESTION = "ingestion"
    LAYOUT_ANALYSIS = "layout_analysis"
    EXTRACTION = "extraction"
    NORMALIZATION = "normalization"
    LANGUAGE_DETECTION = "language_detection"
    SECTION_DETECTION = "section_detection"
    ENTITY_EXTRACTION = "entity_extraction"
    QUALITY_SCORING = "quality_scoring"


class ParserStatus(str, Enum):
    """High-level parse result status."""

    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class QualityBand(str, Enum):
    """Coarse quality label for downstream routing."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SectionName(str, Enum):
    """Normalized CV section names used by the engine."""

    HEADER = "header"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    LANGUAGES = "languages"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    LINKS = "links"
    OTHER = "other"


class WarningSeverity(str, Enum):
    """Severity level for structured parse warnings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ParsedDateRange(BaseModel):
    """Normalized date interval extracted from a CV line."""

    model_config = ConfigDict(extra="forbid")

    start_year: int | None = None
    start_month: int | None = None
    end_year: int | None = None
    end_month: int | None = None
    is_present: bool = False
    raw_text: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_assessment: FieldConfidenceAssessment | None = None
    provenance: FieldProvenance | None = None


class ParsedSkill(BaseModel):
    """Canonicalized skill extracted from a CV."""

    model_config = ConfigDict(extra="forbid")

    canonical_name: str
    matched_text: str
    source_section: SectionName | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    category: str | None = None
    skill_type: str = "hard_skill"
    confidence_assessment: FieldConfidenceAssessment | None = None
    provenance: FieldProvenance | None = None


class ParsedExperienceLine(BaseModel):
    """Structured interpretation of an experience line block."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    company_name: str | None = None
    location: str | None = None
    date_range: ParsedDateRange | None = None
    summary_lines: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_assessment: FieldConfidenceAssessment | None = None
    title_provenance: FieldProvenance | None = None
    company_provenance: FieldProvenance | None = None
    location_provenance: FieldProvenance | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParseWarning(BaseModel):
    """Structured warning emitted by one pipeline stage."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    stage: ParserStageName
    severity: WarningSeverity = WarningSeverity.WARNING
    context: dict[str, Any] = Field(default_factory=dict)


class StageTelemetry(BaseModel):
    """Timing and execution state for a single pipeline stage."""

    model_config = ConfigDict(extra="forbid")

    stage: ParserStageName
    duration_ms: float = Field(default=0.0, ge=0.0)
    succeeded: bool = True
    skipped: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentIngestionArtifact(BaseModel):
    """Document-level metadata collected before parsing."""

    model_config = ConfigDict(extra="forbid")

    source_path: str
    filename: str
    extension: str
    mime_type: str | None = None
    file_size_bytes: int = Field(default=0, ge=0)
    fingerprint_sha256: str | None = None
    encrypted: bool = False

    @property
    def path(self) -> Path:
        """Return the source path as a :class:`~pathlib.Path`."""
        return Path(self.source_path)


class LayoutTextBlock(BaseModel):
    """Normalized text block with geometric coordinates."""

    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(default=0, ge=0)
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    block_index: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field(return_type=float)
    @property
    def width(self) -> float:
        """Return the block width."""
        return max(self.x1 - self.x0, 0.0)

    @computed_field(return_type=float)
    @property
    def height(self) -> float:
        """Return the block height."""
        return max(self.y1 - self.y0, 0.0)

    @computed_field(return_type=float)
    @property
    def center_x(self) -> float:
        """Return the block horizontal center."""
        return self.x0 + (self.width / 2.0)


class LayoutColumn(BaseModel):
    """A cluster of blocks that form one reading column."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(default=0, ge=0)
    x0: float
    x1: float
    blocks: list[LayoutTextBlock] = Field(default_factory=list)
    is_sidebar: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field(return_type=float)
    @property
    def width(self) -> float:
        """Return the total column width."""
        return max(self.x1 - self.x0, 0.0)


class LayoutPage(BaseModel):
    """Layout analysis result for one page."""

    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(default=0, ge=0)
    width: float = Field(default=0.0, ge=0.0)
    height: float = Field(default=0.0, ge=0.0)
    blocks: list[LayoutTextBlock] = Field(default_factory=list)
    columns: list[LayoutColumn] = Field(default_factory=list)
    is_multi_column: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class LayoutAnalysisArtifact(BaseModel):
    """Document-wide layout analysis result."""

    model_config = ConfigDict(extra="forbid")

    pages: list[LayoutPage] = Field(default_factory=list)
    reading_order_blocks: list[LayoutTextBlock] = Field(default_factory=list)
    is_multi_column_document: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractionArtifact(BaseModel):
    """Raw text produced by a document extraction backend."""

    model_config = ConfigDict(extra="forbid")

    text: str
    extraction_method: str
    used_ocr: bool = False
    page_count: int | None = Field(default=None, ge=0)
    layout_metadata: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedTextArtifact(BaseModel):
    """Normalized text and line breakdown ready for segmentation."""

    model_config = ConfigDict(extra="forbid")

    text: str
    lines: list[str] = Field(default_factory=list)
    removed_noise_fragments: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SectionBlock(BaseModel):
    """Detected logical CV section."""

    model_config = ConfigDict(extra="forbid")

    name: SectionName
    heading: str | None = None
    lines: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SectionDetectionArtifact(BaseModel):
    """Output of section detection over normalized text."""

    model_config = ConfigDict(extra="forbid")

    sections: list[SectionBlock] = Field(default_factory=list)
    unassigned_lines: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedCvData(BaseModel):
    """Structured CV payload emitted by the parser engine."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    summary: str | None = None
    skills: list[ParsedSkill] = Field(default_factory=list)
    experience_lines: list[ParsedExperienceLine] = Field(default_factory=list)
    section_names: list[SectionName] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    total_years_experience: float | None = Field(default=None, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityScoreResult(BaseModel):
    """Configurable quality score output."""

    model_config = ConfigDict(extra="forbid")

    score: int = Field(default=0, ge=0, le=100)
    band: QualityBand = QualityBand.LOW
    contributing_factors: dict[str, int] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class ParseContext(BaseModel):
    """Mutable pipeline context shared across stages."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    ingestion: DocumentIngestionArtifact
    layout: LayoutAnalysisArtifact | None = None
    extraction: ExtractionArtifact | None = None
    normalized: NormalizedTextArtifact | None = None
    detected_language: str | None = None
    sections: SectionDetectionArtifact | None = None
    parsed_data: ParsedCvData | None = None
    quality: QualityScoreResult | None = None
    warnings: list[ParseWarning] = Field(default_factory=list)
    stage_telemetry: list[StageTelemetry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParserResult(BaseModel):
    """Final engine result returned to callers."""

    model_config = ConfigDict(extra="forbid")

    status: ParserStatus
    context: ParseContext

    @property
    def warnings(self) -> list[ParseWarning]:
        """Proxy warnings from the embedded parse context."""
        return self.context.warnings
