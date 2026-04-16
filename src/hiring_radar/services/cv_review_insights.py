from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.services.cv_profile_confidence import (
    CV_CONFIDENCE_HIGH,
    CV_CONFIDENCE_LOW,
    CV_CONFIDENCE_MEDIUM,
    CvFieldConfidence,
    CvProfileConfidenceReport,
)

CV_FIELD_REVIEW_SEVERITY_SAFE = "safe"
CV_FIELD_REVIEW_SEVERITY_REVIEW_RECOMMENDED = "review_recommended"
CV_FIELD_REVIEW_SEVERITY_REVIEW_REQUIRED = "review_required"

_REASON_LOW_CONFIDENCE = "low_confidence"
_REASON_MEDIUM_CONFIDENCE = "medium_confidence"
_REASON_HIGH_CONFIDENCE = "high_confidence"
_REASON_MISSING_VALUE = "missing_value"
_REASON_SPARSE_CONTENT = "sparse_content"
_REASON_OCR_SOURCE = "ocr_source"
_REASON_MANUAL_REVIEW_FLOW = "manual_review_flow"
_REASON_LOW_TEXT_VOLUME = "low_text_volume"
_REASON_MEDIUM_TEXT_VOLUME = "medium_text_volume"
_REASON_REVIEW_HINT = "extraction_review_hint"

_SEVERITY_ORDER: dict[str, int] = {
    CV_FIELD_REVIEW_SEVERITY_SAFE: 0,
    CV_FIELD_REVIEW_SEVERITY_REVIEW_RECOMMENDED: 1,
    CV_FIELD_REVIEW_SEVERITY_REVIEW_REQUIRED: 2,
}


@dataclass(slots=True, frozen=True)
class CvFieldReviewInsight:
    """Normalized field-level review metadata.

    Attributes:
        field_name: Canonical profile field identifier.
        severity: Review severity for the field.
        reason_codes: Stable reason codes supporting the severity.
        confidence_level: Original confidence level for the field.
        has_value: Whether the parsed field contains a usable value.
        item_count: Number of contributing parsed items.
    """

    field_name: str
    severity: str
    reason_codes: tuple[str, ...]
    confidence_level: str
    has_value: bool
    item_count: int


@dataclass(slots=True, frozen=True)
class CvReviewSummary:
    """Aggregate summary of field-level review severities."""

    total_field_count: int
    safe_field_count: int
    review_recommended_count: int
    review_required_count: int
    highest_severity: str
    focus_field_names: tuple[str, ...]
    manual_review_flow: bool


def build_cv_field_review_insights(
    *,
    confidence_report: CvProfileConfidenceReport,
    needs_manual_review: bool,
    uses_ocr: bool,
    review_hints: tuple[str, ...] = (),
) -> tuple[CvFieldReviewInsight, ...]:
    """Build deterministic field-level review insights.

    Args:
        confidence_report: Confidence report for the parsed CV draft.
        needs_manual_review: Whether extraction requires manual review.
        uses_ocr: Whether the source relied on OCR.
        review_hints: Extraction review hint codes.

    Returns:
        Ordered field review insights aligned with the confidence report.
    """
    return tuple(
        _build_single_field_review_insight(
            field=field,
            needs_manual_review=needs_manual_review,
            uses_ocr=uses_ocr,
            review_hints=review_hints,
        )
        for field in _iter_confidence_fields(confidence_report)
    )


def build_cv_review_summary(
    *,
    insights: tuple[CvFieldReviewInsight, ...],
    manual_review_flow: bool,
) -> CvReviewSummary:
    """Build an aggregate summary from field review insights."""
    safe_count = sum(
        1 for item in insights if item.severity == CV_FIELD_REVIEW_SEVERITY_SAFE
    )
    review_recommended_count = sum(
        1
        for item in insights
        if item.severity == CV_FIELD_REVIEW_SEVERITY_REVIEW_RECOMMENDED
    )
    review_required_count = sum(
        1
        for item in insights
        if item.severity == CV_FIELD_REVIEW_SEVERITY_REVIEW_REQUIRED
    )

    highest_severity = CV_FIELD_REVIEW_SEVERITY_SAFE
    for item in insights:
        if _SEVERITY_ORDER[item.severity] > _SEVERITY_ORDER[highest_severity]:
            highest_severity = item.severity

    focus_field_names = tuple(
        item.field_name
        for item in insights
        if item.severity != CV_FIELD_REVIEW_SEVERITY_SAFE
    )

    return CvReviewSummary(
        total_field_count=len(insights),
        safe_field_count=safe_count,
        review_recommended_count=review_recommended_count,
        review_required_count=review_required_count,
        highest_severity=highest_severity,
        focus_field_names=focus_field_names,
        manual_review_flow=manual_review_flow,
    )


def _iter_confidence_fields(
    confidence_report: CvProfileConfidenceReport,
) -> tuple[CvFieldConfidence, ...]:
    return (
        confidence_report.headline,
        confidence_report.summary,
        confidence_report.skills,
        confidence_report.target_roles,
        confidence_report.preferred_locations,
        confidence_report.remote_preference,
        confidence_report.education_entries,
        confidence_report.experience_entries,
        confidence_report.language_entries,
    )


def _build_single_field_review_insight(
    *,
    field: CvFieldConfidence,
    needs_manual_review: bool,
    uses_ocr: bool,
    review_hints: tuple[str, ...],
) -> CvFieldReviewInsight:
    severity = _derive_field_review_severity(
        confidence_level=field.level,
        needs_manual_review=needs_manual_review,
    )
    reason_codes = _derive_reason_codes(
        field=field,
        needs_manual_review=needs_manual_review,
        uses_ocr=uses_ocr,
        review_hints=review_hints,
    )

    return CvFieldReviewInsight(
        field_name=field.field_name,
        severity=severity,
        reason_codes=reason_codes,
        confidence_level=field.level,
        has_value=field.has_value,
        item_count=field.item_count,
    )


def _derive_field_review_severity(
    *,
    confidence_level: str,
    needs_manual_review: bool,
) -> str:
    if confidence_level == CV_CONFIDENCE_LOW:
        return CV_FIELD_REVIEW_SEVERITY_REVIEW_REQUIRED

    if confidence_level == CV_CONFIDENCE_MEDIUM:
        if needs_manual_review:
            return CV_FIELD_REVIEW_SEVERITY_REVIEW_REQUIRED
        return CV_FIELD_REVIEW_SEVERITY_REVIEW_RECOMMENDED

    if needs_manual_review:
        return CV_FIELD_REVIEW_SEVERITY_REVIEW_RECOMMENDED

    return CV_FIELD_REVIEW_SEVERITY_SAFE


def _derive_reason_codes(
    *,
    field: CvFieldConfidence,
    needs_manual_review: bool,
    uses_ocr: bool,
    review_hints: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []

    if field.level == CV_CONFIDENCE_LOW:
        reason_codes.append(_REASON_LOW_CONFIDENCE)
    elif field.level == CV_CONFIDENCE_MEDIUM:
        reason_codes.append(_REASON_MEDIUM_CONFIDENCE)
    elif field.level == CV_CONFIDENCE_HIGH:
        reason_codes.append(_REASON_HIGH_CONFIDENCE)

    if not field.has_value:
        reason_codes.append(_REASON_MISSING_VALUE)

    if field.item_count <= 1 and field.field_name not in {"headline", "remote_preference"}:
        reason_codes.append(_REASON_SPARSE_CONTENT)

    if uses_ocr:
        reason_codes.append(_REASON_OCR_SOURCE)

    if needs_manual_review:
        reason_codes.append(_REASON_MANUAL_REVIEW_FLOW)

    if "low_text_volume" in review_hints:
        reason_codes.append(_REASON_LOW_TEXT_VOLUME)
    elif "medium_text_volume" in review_hints:
        reason_codes.append(_REASON_MEDIUM_TEXT_VOLUME)

    if any(
        hint in review_hints
        for hint in (
            "manual_review_recommended",
            "ocr_no_text_detected",
            "extraction_failed",
        )
    ):
        reason_codes.append(_REASON_REVIEW_HINT)

    return tuple(dict.fromkeys(reason_codes))