from __future__ import annotations

from typing import Protocol, runtime_checkable

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.models import (
    DocumentIngestionArtifact,
    ExtractionArtifact,
    LayoutAnalysisArtifact,
    NormalizedTextArtifact,
    ParseContext,
    ParsedCvData,
    QualityScoreResult,
    SectionDetectionArtifact,
)


@runtime_checkable
class IngestionStrategy(Protocol):
    """Protocol for document ingestion metadata collection."""

    def ingest(
        self,
        *,
        source_path: str,
        config: ParserRuntimeConfig,
    ) -> DocumentIngestionArtifact:
        """Build document ingestion metadata for a source file."""


@runtime_checkable
class LayoutAnalysisStrategy(Protocol):
    """Protocol for layout-aware block analysis."""

    def analyze_layout(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> LayoutAnalysisArtifact:
        """Analyze document layout and produce reading-order hints."""


@runtime_checkable
class ExtractionStrategy(Protocol):
    """Protocol for raw text extraction backends."""

    def extract(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> ExtractionArtifact:
        """Extract raw text from the ingested document."""


@runtime_checkable
class NormalizationStrategy(Protocol):
    """Protocol for extraction text normalization."""

    def normalize(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> NormalizedTextArtifact:
        """Normalize extracted raw text for downstream stages."""


@runtime_checkable
class LanguageDetectionStrategy(Protocol):
    """Protocol for language detection over normalized text."""

    def detect(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> str:
        """Detect the primary CV language."""


@runtime_checkable
class SectionDetectionStrategy(Protocol):
    """Protocol for mapping normalized lines into logical sections."""

    def detect_sections(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> SectionDetectionArtifact:
        """Detect logical CV sections."""


@runtime_checkable
class EntityExtractionStrategy(Protocol):
    """Protocol for producing structured CV data."""

    def extract_entities(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> ParsedCvData:
        """Extract structured CV entities from sections and normalized text."""


@runtime_checkable
class QualityScoringStrategy(Protocol):
    """Protocol for deterministic parse quality scoring."""

    def score(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> QualityScoreResult:
        """Compute a parse quality score for the current pipeline context."""
