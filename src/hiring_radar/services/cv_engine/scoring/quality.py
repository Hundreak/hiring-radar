from __future__ import annotations

from collections.abc import Iterable

from hiring_radar.services.cv_engine.config import (
    ParserRuntimeConfig,
    QualityScoringConfig,
)
from hiring_radar.services.cv_engine.models import (
    ParseContext,
    ParsedCvData,
    QualityBand,
    QualityScoreResult,
    SectionDetectionArtifact,
)
from hiring_radar.services.cv_engine.protocols import QualityScoringStrategy


def clamp_quality_score(value: int) -> int:
    """Clamp a raw quality score to the supported 0-100 range."""
    return max(0, min(100, value))


def derive_quality_band(score: int, config: QualityScoringConfig) -> QualityBand:
    """Map a numeric quality score to a coarse quality band."""
    if score >= config.high_threshold:
        return QualityBand.HIGH
    if score >= config.medium_threshold:
        return QualityBand.MEDIUM
    return QualityBand.LOW


def score_thresholds(value: int, thresholds: Iterable[tuple[int, int]]) -> int:
    """Return the first matching threshold score for a numeric signal."""
    for minimum, points in thresholds:
        if value >= minimum:
            return points
    return 0


class DeterministicQualityScoringStrategy(QualityScoringStrategy):
    """Compute a deterministic parse quality score from current pipeline signals."""

    def score(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> QualityScoreResult:
        scoring_config = config.quality_scoring
        contributions: dict[str, int] = {}
        notes: list[str] = []

        normalized_text = context.normalized.text if context.normalized is not None else ""
        normalized_lines = context.normalized.lines if context.normalized is not None else []
        sections = context.sections if context.sections is not None else SectionDetectionArtifact()
        parsed_data = context.parsed_data if context.parsed_data is not None else ParsedCvData()

        text_length_points = score_thresholds(
            len(normalized_text),
            scoring_config.text_length_thresholds,
        )
        contributions["text_length"] = text_length_points
        if text_length_points == 0:
            notes.append("Normalized text length is below the minimum confidence threshold.")

        line_count_points = score_thresholds(
            len(normalized_lines),
            scoring_config.line_count_thresholds,
        )
        contributions["line_count"] = line_count_points
        if line_count_points == 0:
            notes.append("Document contains very few normalized lines.")

        detected_sections = [section for section in sections.sections if section.lines]
        section_points = score_thresholds(
            len(detected_sections),
            scoring_config.section_count_thresholds,
        )
        contributions["section_count"] = section_points
        if section_points == 0:
            notes.append("Logical section coverage is sparse.")

        field_contributions = _score_structured_fields(
            parsed_data=parsed_data,
            scoring_config=scoring_config,
        )
        contributions.update(field_contributions)

        average_confidence = _compute_average_confidence(parsed_data)
        if average_confidence is not None:
            contributions["average_confidence"] = int(round(average_confidence * 12))
            if average_confidence < 0.45:
                contributions["average_confidence_penalty"] = (
                    -scoring_config.low_average_confidence_penalty
                )
                notes.append(
                    "Average semantic field confidence is low; downstream review is recommended."
                )
            elif average_confidence < 0.62:
                contributions["average_confidence_penalty"] = (
                    -scoring_config.medium_average_confidence_penalty
                )
                notes.append(
                    "Average semantic field confidence is moderate; verify key role and skill fields."
                )

        if parsed_data.links or parsed_data.projects or parsed_data.certifications:
            contributions["semantic_richness_bonus"] = scoring_config.semantic_richness_bonus

        warning_penalty = len(context.warnings) * scoring_config.warning_penalty
        if warning_penalty:
            contributions["warning_penalty"] = -warning_penalty
            notes.append(
                f"{len(context.warnings)} structured parser warning(s) reduced the score."
            )

        if context.extraction is not None and context.extraction.used_ocr:
            contributions["ocr_penalty"] = -scoring_config.ocr_penalty
            notes.append("OCR extraction path introduced a quality penalty.")

        raw_score = sum(contributions.values())
        score = clamp_quality_score(raw_score)
        band = derive_quality_band(score, scoring_config)
        if band == QualityBand.LOW:
            notes.append("Overall parse quality is low; manual review is recommended.")

        return QualityScoreResult(
            score=score,
            band=band,
            contributing_factors=contributions,
            notes=notes,
        )


def _score_structured_fields(
    *,
    parsed_data: ParsedCvData,
    scoring_config: QualityScoringConfig,
) -> dict[str, int]:
    """Score high-value structured fields with configurable weights."""
    field_signals = {
        "full_name": bool(parsed_data.full_name),
        "emails": bool(parsed_data.emails),
        "phone_numbers": bool(parsed_data.phone_numbers),
        "summary": bool(parsed_data.summary),
        "skills": bool(parsed_data.skills),
        "experience_lines": bool(parsed_data.experience_lines),
        "section_names": bool(parsed_data.section_names),
        "links": bool(parsed_data.links),
        "projects": bool(parsed_data.projects),
    }
    return {
        field_name: weight
        for field_name, weight in scoring_config.field_weights.items()
        if field_signals.get(field_name, False)
    }


def _compute_average_confidence(parsed_data: ParsedCvData) -> float | None:
    confidence_values: list[float] = []
    confidence_values.extend(skill.confidence for skill in parsed_data.skills)
    confidence_values.extend(
        line.confidence for line in parsed_data.experience_lines if line.confidence > 0.0
    )
    if not confidence_values:
        return None
    return sum(confidence_values) / len(confidence_values)
