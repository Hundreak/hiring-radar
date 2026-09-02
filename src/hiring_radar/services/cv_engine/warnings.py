from __future__ import annotations

from enum import StrEnum
from typing import Any

from hiring_radar.services.cv_engine.models import (
    ParserStageName,
    ParseWarning,
    WarningSeverity,
)


class WarningCode(StrEnum):
    """Canonical warning codes for the v2 parser engine."""

    EXTRACTION_EMPTY = "extraction_empty"
    NORMALIZATION_EMPTY = "normalization_empty"
    LANGUAGE_DETECTION_FALLBACK = "language_detection_fallback"
    SECTION_DETECTION_SPARSE = "section_detection_sparse"
    ENTITY_EXTRACTION_PARTIAL = "entity_extraction_partial"
    QUALITY_LOW = "quality_low"
    STAGE_RECOVERED = "stage_recovered"
    STAGE_SKIPPED = "stage_skipped"
    UNSUPPORTED_LAYOUT = "unsupported_layout"



def build_warning(
    *,
    code: WarningCode | str,
    message: str,
    stage: ParserStageName,
    severity: WarningSeverity = WarningSeverity.WARNING,
    context: dict[str, Any] | None = None,
) -> ParseWarning:
    """Create a structured parse warning."""
    code_value = code.value if isinstance(code, WarningCode) else code
    return ParseWarning(
        code=code_value,
        message=message,
        stage=stage,
        severity=severity,
        context=context or {},
    )
