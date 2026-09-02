from __future__ import annotations

from typing import Literal

from hiring_radar.models import CanonicalJob, CanonicalJobFeature
from hiring_radar.services.jobs.normalization import normalize_text, strip_html
from hiring_radar.services.matching.contracts import JobAnalysisCoverage

_ANALYSIS_SOURCE_LABELS: dict[str, str] = {
    "canonical_description": "canonical_description",
    "original_source_page": "original_source_page",
    "structured_requirements": "structured_requirements",
    "responsibility_signals": "responsibility_signals",
    "technology_signals": "technology_signals",
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _description_char_count(job: CanonicalJob) -> int:
    return len(normalize_text(strip_html(job.description_text) or strip_html(job.description_html) or ""))


def compute_job_analysis_score(job: CanonicalJob, job_feature: CanonicalJobFeature) -> float:
    description_chars = _description_char_count(job)
    external_status = (job_feature.external_context_status or "").casefold()
    has_external_context = external_status not in {"", "unavailable", "error"}

    score = 0.0
    if description_chars >= 1200:
        score += 0.28
    elif description_chars >= 700:
        score += 0.24
    elif description_chars >= 350:
        score += 0.20
    elif description_chars >= 180:
        score += 0.14
    elif description_chars >= 80:
        score += 0.08

    if has_external_context:
        score += 0.20
        if job_feature.external_requirement_terms:
            score += min(0.08, len(job_feature.external_requirement_terms) * 0.02)
        if job_feature.external_technology_terms:
            score += min(0.06, len(job_feature.external_technology_terms) * 0.015)
        if job_feature.external_responsibility_terms:
            score += min(0.06, len(job_feature.external_responsibility_terms) * 0.02)

    if job_feature.required_skill_terms:
        score += min(0.14, len(job_feature.required_skill_terms) * 0.02)
    elif job_feature.skill_terms:
        score += min(0.08, len(job_feature.skill_terms) * 0.01)

    if job_feature.preferred_skill_terms:
        score += min(0.05, len(job_feature.preferred_skill_terms) * 0.0125)
    if job_feature.responsibility_scope is not None:
        score += 0.05
    if job_feature.years_experience_min is not None:
        score += 0.04
    if job_feature.language_requirements:
        score += min(0.04, len(job_feature.language_requirements) * 0.02)
    if job_feature.domain_signals:
        score += min(0.04, len(job_feature.domain_signals) * 0.015)
    if job_feature.role_family is not None:
        score += 0.03
    if job_feature.job_discipline is not None:
        score += 0.03

    return round(_clamp(score), 4)


def _build_content_sources(job: CanonicalJob, job_feature: CanonicalJobFeature) -> tuple[str, ...]:
    sources: list[str] = []
    if _description_char_count(job) > 0:
        sources.append(_ANALYSIS_SOURCE_LABELS["canonical_description"])
    external_status = (job_feature.external_context_status or "").casefold()
    if external_status not in {"", "unavailable", "error"}:
        sources.append(_ANALYSIS_SOURCE_LABELS["original_source_page"])
    if job_feature.required_skill_terms or job_feature.preferred_skill_terms:
        sources.append(_ANALYSIS_SOURCE_LABELS["structured_requirements"])
    if job_feature.responsibility_scope is not None or job_feature.external_responsibility_terms:
        sources.append(_ANALYSIS_SOURCE_LABELS["responsibility_signals"])
    if job_feature.external_technology_terms or job_feature.skill_terms:
        sources.append(_ANALYSIS_SOURCE_LABELS["technology_signals"])
    return tuple(dict.fromkeys(sources))


def _build_detected_signal_types(job_feature: CanonicalJobFeature) -> tuple[str, ...]:
    signals: list[str] = []
    if job_feature.required_skill_terms:
        signals.append("required_skills")
    if job_feature.preferred_skill_terms:
        signals.append("preferred_skills")
    if job_feature.external_requirement_terms:
        signals.append("source_requirements")
    if job_feature.external_technology_terms:
        signals.append("source_technology")
    if job_feature.responsibility_scope is not None or job_feature.external_responsibility_terms:
        signals.append("responsibilities")
    if job_feature.years_experience_min is not None:
        signals.append("experience_requirement")
    if job_feature.language_requirements:
        signals.append("languages")
    if job_feature.domain_signals:
        signals.append("domain")
    if job_feature.role_family is not None:
        signals.append("role_family")
    if job_feature.job_discipline is not None:
        signals.append("discipline")
    return tuple(signals)


def _analysis_level(score: float) -> Literal["strong", "moderate", "limited"]:
    if score >= 0.66:
        return "strong"
    if score >= 0.40:
        return "moderate"
    return "limited"


def build_job_analysis_coverage(job: CanonicalJob, job_feature: CanonicalJobFeature) -> JobAnalysisCoverage:
    score = compute_job_analysis_score(job, job_feature)
    level = _analysis_level(score)
    content_sources = _build_content_sources(job, job_feature)
    detected_signal_types = _build_detected_signal_types(job_feature)

    if level == "strong":
        summary = (
            "This recommendation is backed by a clear job-content packet with structured requirements, role signals, "
            "and enough source material for deterministic analysis."
        )
        warning = None
    elif level == "moderate":
        summary = (
            "The job content is usable for deterministic analysis, but some sections are thinner than ideal or the "
            "original source context is only partially available."
        )
        warning = None
    else:
        summary = (
            "This listing is being ranked from partial content. The title and basic description are available, but the "
            "full requirement packet or original source context is still limited."
        )
        warning = (
            "Treat the score more cautiously until richer job content or original-source evidence is available."
        )

    return JobAnalysisCoverage(
        score=score,
        level=level,
        summary=summary,
        content_sources=content_sources,
        detected_signal_types=detected_signal_types,
        warning=warning,
    )
