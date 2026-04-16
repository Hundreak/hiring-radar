from __future__ import annotations

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.exceptions import RecoverableStageError
from hiring_radar.services.cv_engine.models import (
    DocumentIngestionArtifact,
    ExtractionArtifact,
    LayoutAnalysisArtifact,
    NormalizedTextArtifact,
    ParsedCvData,
    ParserStageName,
    QualityBand,
    QualityScoreResult,
    SectionDetectionArtifact,
)
from hiring_radar.services.cv_engine.orchestrator import CvParserOrchestrator


class DummyIngestionStrategy:
    def ingest(
        self,
        *,
        source_path: str,
        config: ParserRuntimeConfig,
    ) -> DocumentIngestionArtifact:
        return DocumentIngestionArtifact(
            source_path=source_path,
            filename="alice_cv.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
        )




class DummyLayoutAnalysisStrategy:
    def analyze_layout(self, *, context, config: ParserRuntimeConfig) -> LayoutAnalysisArtifact:
        return LayoutAnalysisArtifact(pages=[], reading_order_blocks=[], metadata={"used": True})


class DummyExtractionStrategy:
    def extract(
        self,
        *,
        context,
        config: ParserRuntimeConfig,
    ) -> ExtractionArtifact:
        return ExtractionArtifact(
            text="Alice Example\nSenior Backend Engineer",
            extraction_method="pdf_text",
            used_ocr=False,
            page_count=1,
        )


class DummyNormalizationStrategy:
    def normalize(
        self,
        *,
        context,
        config: ParserRuntimeConfig,
    ) -> NormalizedTextArtifact:
        return NormalizedTextArtifact(
            text=context.extraction.text,
            lines=context.extraction.text.splitlines(),
        )


class DummyLanguageDetectionStrategy:
    def detect(self, *, context, config: ParserRuntimeConfig) -> str:
        return "en"


class DummySectionDetectionStrategy:
    def detect_sections(
        self,
        *,
        context,
        config: ParserRuntimeConfig,
    ) -> SectionDetectionArtifact:
        return SectionDetectionArtifact(sections=[])


class DummyEntityExtractionStrategy:
    def extract_entities(self, *, context, config: ParserRuntimeConfig) -> ParsedCvData:
        return ParsedCvData(full_name="Alice Example")


class DummyQualityScoringStrategy:
    def score(self, *, context, config: ParserRuntimeConfig) -> QualityScoreResult:
        return QualityScoreResult(score=82, band=QualityBand.HIGH)


class RecoverableNormalizationStrategy:
    def normalize(self, *, context, config: ParserRuntimeConfig) -> NormalizedTextArtifact:
        raise RecoverableStageError(
            ParserStageName.NORMALIZATION,
            "Normalization partially failed.",
        )


def test_orchestrator_returns_succeeded_for_happy_path() -> None:
    orchestrator = CvParserOrchestrator(
        ingestion_strategy=DummyIngestionStrategy(),
        extraction_strategy=DummyExtractionStrategy(),
        normalization_strategy=DummyNormalizationStrategy(),
        language_detection_strategy=DummyLanguageDetectionStrategy(),
        section_detection_strategy=DummySectionDetectionStrategy(),
        entity_extraction_strategy=DummyEntityExtractionStrategy(),
        quality_scoring_strategy=DummyQualityScoringStrategy(),
    )

    result = orchestrator.parse(source_path="/tmp/alice_cv.pdf")

    assert result.status.value == "succeeded"
    assert result.context.ingestion.filename == "alice_cv.pdf"
    assert result.context.detected_language == "en"
    assert result.context.quality is not None
    assert result.context.quality.score == 82
    assert len(result.context.stage_telemetry) == 7
    assert result.context.warnings == []


def test_orchestrator_continues_after_recoverable_stage_error() -> None:
    orchestrator = CvParserOrchestrator(
        ingestion_strategy=DummyIngestionStrategy(),
        extraction_strategy=DummyExtractionStrategy(),
        normalization_strategy=RecoverableNormalizationStrategy(),
        language_detection_strategy=DummyLanguageDetectionStrategy(),
        section_detection_strategy=DummySectionDetectionStrategy(),
        entity_extraction_strategy=DummyEntityExtractionStrategy(),
        quality_scoring_strategy=DummyQualityScoringStrategy(),
    )

    result = orchestrator.parse(source_path="/tmp/alice_cv.pdf")

    assert result.status.value == "partial"
    assert result.context.normalized is None
    assert len(result.context.warnings) == 1
    assert result.context.warnings[0].stage == ParserStageName.NORMALIZATION



def test_orchestrator_runs_optional_layout_stage_when_configured() -> None:
    orchestrator = CvParserOrchestrator(
        ingestion_strategy=DummyIngestionStrategy(),
        layout_analysis_strategy=DummyLayoutAnalysisStrategy(),
        extraction_strategy=DummyExtractionStrategy(),
        normalization_strategy=DummyNormalizationStrategy(),
        language_detection_strategy=DummyLanguageDetectionStrategy(),
        section_detection_strategy=DummySectionDetectionStrategy(),
        entity_extraction_strategy=DummyEntityExtractionStrategy(),
        quality_scoring_strategy=DummyQualityScoringStrategy(),
    )

    result = orchestrator.parse(source_path="/tmp/alice_cv.pdf")

    assert result.context.layout is not None
    assert result.context.layout.metadata["used"] is True
    assert len(result.context.stage_telemetry) == 8
    assert result.context.stage_telemetry[1].stage == ParserStageName.LAYOUT_ANALYSIS
