from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.exceptions import FatalStageError, RecoverableStageError
from hiring_radar.services.cv_engine.models import (
    ParseContext,
    ParserResult,
    ParserStageName,
    ParserStatus,
    StageTelemetry,
    WarningSeverity,
)
from hiring_radar.services.cv_engine.protocols import (
    EntityExtractionStrategy,
    ExtractionStrategy,
    IngestionStrategy,
    LanguageDetectionStrategy,
    LayoutAnalysisStrategy,
    NormalizationStrategy,
    QualityScoringStrategy,
    SectionDetectionStrategy,
)
from hiring_radar.services.cv_engine.warnings import WarningCode, build_warning

T = TypeVar("T")


class CvParserOrchestrator:
    """Coordinate the stage-based v2 CV parser pipeline."""

    def __init__(
        self,
        *,
        ingestion_strategy: IngestionStrategy,
        extraction_strategy: ExtractionStrategy,
        normalization_strategy: NormalizationStrategy,
        language_detection_strategy: LanguageDetectionStrategy,
        section_detection_strategy: SectionDetectionStrategy,
        entity_extraction_strategy: EntityExtractionStrategy,
        quality_scoring_strategy: QualityScoringStrategy,
        layout_analysis_strategy: LayoutAnalysisStrategy | None = None,
        config: ParserRuntimeConfig | None = None,
    ) -> None:
        self._ingestion_strategy = ingestion_strategy
        self._layout_analysis_strategy = layout_analysis_strategy
        self._extraction_strategy = extraction_strategy
        self._normalization_strategy = normalization_strategy
        self._language_detection_strategy = language_detection_strategy
        self._section_detection_strategy = section_detection_strategy
        self._entity_extraction_strategy = entity_extraction_strategy
        self._quality_scoring_strategy = quality_scoring_strategy
        self._config = config or ParserRuntimeConfig()

    def parse(self, *, source_path: str) -> ParserResult:
        """Run the configured parser pipeline for one document."""
        ingestion, ingestion_telemetry = self._timed_stage(
            stage=ParserStageName.INGESTION,
            operation=lambda: self._ingestion_strategy.ingest(
                source_path=source_path,
                config=self._config,
            ),
        )
        context = ParseContext(ingestion=ingestion)
        context.stage_telemetry.append(ingestion_telemetry)

        try:
            if self._layout_analysis_strategy is not None:
                context.layout = self._run_recoverable_stage(
                    stage=ParserStageName.LAYOUT_ANALYSIS,
                    context=context,
                    operation=lambda: self._layout_analysis_strategy.analyze_layout(
                        context=context,
                        config=self._config,
                    ),
                )
            context.extraction = self._run_success_stage(
                stage=ParserStageName.EXTRACTION,
                context=context,
                operation=lambda: self._extraction_strategy.extract(
                    context=context,
                    config=self._config,
                ),
            )
            context.normalized = self._run_recoverable_stage(
                stage=ParserStageName.NORMALIZATION,
                context=context,
                operation=lambda: self._normalization_strategy.normalize(
                    context=context,
                    config=self._config,
                ),
            )
            context.detected_language = self._run_recoverable_stage(
                stage=ParserStageName.LANGUAGE_DETECTION,
                context=context,
                operation=lambda: self._language_detection_strategy.detect(
                    context=context,
                    config=self._config,
                ),
            )
            context.sections = self._run_recoverable_stage(
                stage=ParserStageName.SECTION_DETECTION,
                context=context,
                operation=lambda: self._section_detection_strategy.detect_sections(
                    context=context,
                    config=self._config,
                ),
            )
            context.parsed_data = self._run_recoverable_stage(
                stage=ParserStageName.ENTITY_EXTRACTION,
                context=context,
                operation=lambda: self._entity_extraction_strategy.extract_entities(
                    context=context,
                    config=self._config,
                ),
            )
            context.quality = self._run_recoverable_stage(
                stage=ParserStageName.QUALITY_SCORING,
                context=context,
                operation=lambda: self._quality_scoring_strategy.score(
                    context=context,
                    config=self._config,
                ),
            )
        except FatalStageError as exc:
            context.warnings.append(
                build_warning(
                    code=WarningCode.STAGE_RECOVERED,
                    message=exc.message,
                    stage=exc.stage,
                    severity=WarningSeverity.ERROR,
                    context={"fatal": True},
                )
            )
            return ParserResult(status=ParserStatus.FAILED, context=context)

        return ParserResult(status=self._derive_status(context), context=context)

    def _run_success_stage(
        self,
        *,
        stage: ParserStageName,
        context: ParseContext,
        operation: Callable[[], T],
    ) -> T:
        result, telemetry = self._timed_stage(stage=stage, operation=operation)
        context.stage_telemetry.append(telemetry)
        return result

    def _run_recoverable_stage(
        self,
        *,
        stage: ParserStageName,
        context: ParseContext,
        operation: Callable[[], T],
    ) -> T | None:
        start = time.perf_counter()
        try:
            result = operation()
        except RecoverableStageError as exc:
            duration_ms = (time.perf_counter() - start) * 1000.0
            context.stage_telemetry.append(
                StageTelemetry(
                    stage=stage,
                    duration_ms=duration_ms,
                    succeeded=False,
                    skipped=False,
                    metadata={"error": exc.message},
                )
            )
            context.warnings.append(
                build_warning(
                    code=WarningCode.STAGE_RECOVERED,
                    message=exc.message,
                    stage=stage,
                    severity=WarningSeverity.WARNING,
                    context={"recoverable": True},
                )
            )
            if self._config.continue_on_recoverable_errors:
                return None
            raise
        except FatalStageError:
            raise
        duration_ms = (time.perf_counter() - start) * 1000.0
        context.stage_telemetry.append(
            StageTelemetry(stage=stage, duration_ms=duration_ms, succeeded=True)
        )
        return result

    @staticmethod
    def _timed_stage(
        *,
        stage: ParserStageName,
        operation: Callable[[], T],
    ) -> tuple[T, StageTelemetry]:
        start = time.perf_counter()
        result = operation()
        duration_ms = (time.perf_counter() - start) * 1000.0
        return (
            result,
            StageTelemetry(stage=stage, duration_ms=duration_ms, succeeded=True),
        )

    @staticmethod
    def _derive_status(context: ParseContext) -> ParserStatus:
        if any(item.severity == WarningSeverity.ERROR for item in context.warnings):
            return ParserStatus.PARTIAL
        if any(item.severity == WarningSeverity.WARNING for item in context.warnings):
            return ParserStatus.PARTIAL
        if context.parsed_data is None:
            return ParserStatus.PARTIAL
        return ParserStatus.SUCCEEDED
