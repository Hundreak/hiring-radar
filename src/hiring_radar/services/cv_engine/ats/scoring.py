from __future__ import annotations

from hiring_radar.services.cv_engine.ats.models import (
    AtsCompatibilityReport,
    AtsIssue,
    AtsIssueSeverity,
    AtsLevel,
)
from hiring_radar.services.cv_engine.ats.rules import (
    average_skill_confidence,
    collect_present_sections,
    count_dated_experiences,
    has_contact_bundle,
    has_layout_complexity,
    quality_band,
)
from hiring_radar.services.cv_engine.config import AtsScoringConfig
from hiring_radar.services.cv_engine.models import (
    ExtractionArtifact,
    ParsedCvData,
    QualityBand,
    QualityScoreResult,
    SectionBlock,
)


def score_ats_compatibility(
    parsed_data: ParsedCvData,
    *,
    sections: list[SectionBlock] | None = None,
    extraction: ExtractionArtifact | None = None,
    quality: QualityScoreResult | None = None,
    config: AtsScoringConfig | None = None,
) -> AtsCompatibilityReport:
    """Score ATS friendliness using deterministic parser outputs."""
    runtime_config = config or AtsScoringConfig()
    score = runtime_config.base_score
    issues: list[AtsIssue] = []
    positives: list[str] = []
    contributing_factors: dict[str, int] = {}

    present_sections = collect_present_sections(parsed_data, sections)
    for required_section in runtime_config.required_sections:
        if required_section in present_sections:
            score += runtime_config.moderate_bonus
            contributing_factors[f"section:{required_section}"] = runtime_config.moderate_bonus
        else:
            penalty = runtime_config.missing_section_penalty
            score -= penalty
            contributing_factors[f"section:{required_section}"] = -penalty
            issues.append(
                AtsIssue(
                    code=f"missing_section_{required_section}",
                    message=f"Standard ATS section missing: {required_section}.",
                    severity=AtsIssueSeverity.WARNING,
                    penalty=penalty,
                    recommendation=(
                        f"Add a clear {required_section} section heading to improve parser reliability."
                    ),
                )
            )

    if has_contact_bundle(parsed_data):
        score += runtime_config.strong_bonus
        contributing_factors["contact_bundle"] = runtime_config.strong_bonus
        positives.append("Contact details are present and machine-readable.")
    else:
        penalty = runtime_config.missing_contact_penalty
        score -= penalty
        contributing_factors["contact_bundle"] = -penalty
        issues.append(
            AtsIssue(
                code="missing_contact_bundle",
                message="The CV does not expose a reliable name + contact bundle.",
                severity=AtsIssueSeverity.ERROR,
                penalty=penalty,
                recommendation="Add your full name and at least one email address or phone number.",
            )
        )

    if parsed_data.summary:
        score += runtime_config.moderate_bonus
        contributing_factors["summary"] = runtime_config.moderate_bonus
        positives.append("A professional summary improves keyword readability.")

    if parsed_data.skills:
        skill_bonus = min(runtime_config.strong_bonus, max(2, len(parsed_data.skills) // 3))
        score += skill_bonus
        contributing_factors["skills"] = skill_bonus
        positives.append("Skill content is explicitly listed.")
    else:
        penalty = runtime_config.low_skill_density_penalty
        score -= penalty
        contributing_factors["skills"] = -penalty
        issues.append(
            AtsIssue(
                code="missing_explicit_skills",
                message="No explicit skills section or skill content was detected.",
                severity=AtsIssueSeverity.WARNING,
                penalty=penalty,
                recommendation="Add a dedicated skills section with machine-readable terms.",
            )
        )

    avg_skill_confidence = average_skill_confidence(parsed_data)
    if avg_skill_confidence is not None and avg_skill_confidence >= 0.75:
        score += runtime_config.moderate_bonus
        contributing_factors["skill_confidence"] = runtime_config.moderate_bonus
    elif avg_skill_confidence is not None and avg_skill_confidence < 0.5:
        penalty = runtime_config.low_skill_density_penalty // 2
        score -= penalty
        contributing_factors["skill_confidence"] = -penalty
        issues.append(
            AtsIssue(
                code="low_skill_confidence",
                message="Skill extraction confidence is low, which can hurt ATS readability.",
                severity=AtsIssueSeverity.WARNING,
                penalty=penalty,
                recommendation="Use clearer, standardized skill names in a dedicated skills section.",
            )
        )

    if parsed_data.experience_lines:
        dated_experiences = count_dated_experiences(parsed_data)
        if dated_experiences:
            score += runtime_config.strong_bonus
            contributing_factors["dated_experience"] = runtime_config.strong_bonus
            positives.append("Experience entries include parseable date information.")
        else:
            penalty = runtime_config.no_dates_penalty
            score -= penalty
            contributing_factors["dated_experience"] = -penalty
            issues.append(
                AtsIssue(
                    code="experience_without_dates",
                    message="Experience entries are present but date ranges are missing or unclear.",
                    severity=AtsIssueSeverity.WARNING,
                    penalty=penalty,
                    recommendation="Add explicit start and end dates for work experience entries.",
                )
            )
    else:
        penalty = runtime_config.sparse_experience_penalty
        score -= penalty
        contributing_factors["experience_lines"] = -penalty
        issues.append(
            AtsIssue(
                code="missing_experience",
                message="No machine-readable experience entries were detected.",
                severity=AtsIssueSeverity.ERROR,
                penalty=penalty,
                recommendation="Use clear job title, company and date lines in your experience section.",
            )
        )

    if extraction is not None and extraction.used_ocr:
        penalty = runtime_config.ocr_penalty
        score -= penalty
        contributing_factors["ocr_penalty"] = -penalty
        issues.append(
            AtsIssue(
                code="ocr_source",
                message="The CV appears to rely on OCR, which can reduce ATS extraction quality.",
                severity=AtsIssueSeverity.WARNING,
                penalty=penalty,
                recommendation="Prefer a digital PDF or DOCX export instead of an image-based CV.",
            )
        )

    if has_layout_complexity(extraction):
        penalty = runtime_config.multi_column_penalty
        score -= penalty
        contributing_factors["layout_complexity"] = -penalty
        issues.append(
            AtsIssue(
                code="multi_column_layout",
                message="Complex or multi-column layout can reduce ATS reading accuracy.",
                severity=AtsIssueSeverity.WARNING,
                penalty=penalty,
                recommendation="Use a simpler one-column layout for maximum ATS compatibility.",
            )
        )

    band = quality_band(quality)
    if band == QualityBand.HIGH:
        score += runtime_config.moderate_bonus
        contributing_factors["quality_band"] = runtime_config.moderate_bonus
        positives.append("Overall parser quality is high.")
    elif band == QualityBand.MEDIUM:
        penalty = runtime_config.medium_quality_penalty
        score -= penalty
        contributing_factors["quality_band"] = -penalty
        issues.append(
            AtsIssue(
                code="medium_quality_parse",
                message="Overall extraction quality is only moderate.",
                severity=AtsIssueSeverity.INFO,
                penalty=penalty,
                recommendation="Simplify formatting and reduce decorative layout elements.",
            )
        )
    elif band == QualityBand.LOW:
        penalty = runtime_config.low_quality_penalty
        score -= penalty
        contributing_factors["quality_band"] = -penalty
        issues.append(
            AtsIssue(
                code="low_quality_parse",
                message="Overall extraction quality is low for this CV.",
                severity=AtsIssueSeverity.ERROR,
                penalty=penalty,
                recommendation="Export the CV as a text-based PDF or DOCX and use explicit section headings.",
            )
        )

    clamped_score = max(0, min(100, score))
    if clamped_score >= runtime_config.high_threshold:
        level = AtsLevel.HIGH
    elif clamped_score >= runtime_config.medium_threshold:
        level = AtsLevel.MEDIUM
    else:
        level = AtsLevel.LOW

    recommendations: list[str] = []
    for issue in issues:
        if issue.recommendation and issue.recommendation not in recommendations:
            recommendations.append(issue.recommendation)

    return AtsCompatibilityReport(
        score=clamped_score,
        level=level,
        positives=positives,
        issues=issues,
        recommendations=recommendations,
        contributing_factors=contributing_factors,
    )
