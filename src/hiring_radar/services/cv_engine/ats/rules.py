from __future__ import annotations

from collections.abc import Iterable

from hiring_radar.services.cv_engine.models import (
    ExtractionArtifact,
    ParsedCvData,
    QualityBand,
    QualityScoreResult,
    SectionBlock,
    SectionName,
)


def collect_present_sections(
    parsed_data: ParsedCvData,
    sections: Iterable[SectionBlock] | None = None,
) -> set[str]:
    """Return normalized section names detected in the CV."""
    present: set[str] = {item.value for item in parsed_data.section_names}
    if sections is not None:
        present.update(item.name.value for item in sections)
    return present


def has_contact_bundle(parsed_data: ParsedCvData) -> bool:
    """Return whether the CV exposes enough contact details."""
    return bool(parsed_data.full_name and (parsed_data.emails or parsed_data.phone_numbers))


def count_dated_experiences(parsed_data: ParsedCvData) -> int:
    """Count experience entries that carry any parseable date signal."""
    return sum(1 for item in parsed_data.experience_lines if item.date_range is not None)


def has_layout_complexity(extraction: ExtractionArtifact | None) -> bool:
    """Return whether extraction metadata suggests layout complexity."""
    if extraction is None:
        return False
    layout_metadata = extraction.layout_metadata
    return bool(
        layout_metadata.get("is_multi_column")
        or layout_metadata.get("sidebar_detected")
        or layout_metadata.get("column_count", 1) > 1
    )


def quality_band(quality: QualityScoreResult | None) -> QualityBand | None:
    """Return the available quality band, if any."""
    return quality.band if quality is not None else None


def average_skill_confidence(parsed_data: ParsedCvData) -> float | None:
    """Return average skill confidence across extracted skills."""
    if not parsed_data.skills:
        return None
    return sum(item.confidence for item in parsed_data.skills) / len(parsed_data.skills)


def section_name_values() -> set[str]:
    """Return all known normalized section names."""
    return {item.value for item in SectionName}
