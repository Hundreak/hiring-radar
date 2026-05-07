from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from hiring_radar.api.job_identity import resolve_job_reference
from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering.engine import evaluate_job_text_against_keyword_filter
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.filtering.service import build_filterable_job_text
from hiring_radar.services.ai.contracts import CopilotGroundingSource
from hiring_radar.services.ai.web_context import WebContextService
from hiring_radar.services.matching import ExplanationGenerator, score_canonical_job_for_subscriber
from hiring_radar.services.matching.contracts import ExternalSourceInsights, MatchExplanationPayload
from hiring_radar.services.matching.profile_features import refresh_subscriber_profile_features


@dataclass(slots=True, frozen=True)
class JobAnalysisStructuredContext:
    job_kind: str
    job_title: str
    company_name: str
    location_text: str
    workplace_type: str | None
    employment_type: str | None
    seniority: str | None
    fit_score_percent: int
    catalog_score_percent: int
    final_score_percent: int
    behavioral_score_percent: int | None
    explanation_summary: str
    top_reasons: tuple[str, ...]
    evidence_details: tuple[str, ...]
    gap_details: tuple[str, ...]
    matched_skill_terms: tuple[str, ...]
    missing_skill_terms: tuple[str, ...]
    profile_headline: str | None
    profile_target_roles: tuple[str, ...]
    profile_top_skills: tuple[str, ...]
    profile_preferred_locations: tuple[str, ...]
    profile_work_modes: tuple[str, ...]
    description_excerpt: str | None
    external_requirements: tuple[str, ...]
    external_culture_clues: tuple[str, ...]
    external_responsibilities: tuple[str, ...]
    external_technology_terms: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class JobAnalysisGroundingBundle:
    job_analysis_summary: str
    sources: list[CopilotGroundingSource]
    warnings: list[str]
    external_source_insights: ExternalSourceInsights
    analysis_context: JobAnalysisStructuredContext


_EXPLANATION_GENERATOR = ExplanationGenerator()


def _human_join(values: Iterable[str]) -> str:
    cleaned = [str(value).replace("_", " ").strip() for value in values if str(value).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _clip_text(value: str | None, *, limit: int) -> str:
    normalized = " ".join((value or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)].rstrip() + "..."


def _build_profile_snapshot(profile: CandidateProfileAggregate) -> str:
    lines: list[str] = []
    if profile.headline.value:
        lines.append(f"Headline: {profile.headline.value}")
    if profile.preferences.target_roles:
        lines.append("Target roles: " + ", ".join(profile.preferences.target_roles[:4]))
    if profile.skills:
        lines.append(
            "Skills: "
            + ", ".join(
                item.skill_name
                for item in profile.skills[:10]
                if item.skill_name.strip()
            )
        )
    if profile.preferences.preferred_locations:
        lines.append(
            "Preferred locations: " + ", ".join(profile.preferences.preferred_locations[:4])
        )
    if profile.preferences.work_modes:
        lines.append(
            "Workplace preference: "
            + ", ".join(
                str(item.value if hasattr(item, "value") else item)
                for item in profile.preferences.work_modes[:3]
            )
        )
    return "\n".join(lines)


def _build_legacy_match_info(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    job,
) -> tuple[bool, int | None, tuple[str, ...]]:
    preference = repository.get_subscriber_keyword_preference(subscriber_id)
    if not preference.is_enabled():
        return False, None, ()

    settings = KeywordFilterSettings(
        include_keywords=preference.include_keywords,
        exclude_keywords=preference.exclude_keywords,
        match_title=preference.match_title,
        match_location=preference.match_location,
        match_company_name=preference.match_company_name,
    )
    evaluation = evaluate_job_text_against_keyword_filter(
        job=build_filterable_job_text(job=job),
        settings=settings,
    )
    matched_keywords = tuple(sorted({item.keyword for item in evaluation.include_matches}))
    total_include = len(settings.include_keywords)
    if not evaluation.passed:
        return False, 0, matched_keywords
    score = round(len(matched_keywords) / total_include * 100) if total_include > 0 else 0
    return True, max(score, 1), matched_keywords


async def _load_external_source_insights(
    *,
    repository: HiringRadarRepository,
    source_url: str,
    observed_at: str,
    refresh_external_context: bool,
) -> ExternalSourceInsights:
    if not source_url.strip():
        return ExternalSourceInsights()
    service = WebContextService(repository=repository)
    return await service.get_external_source_insights(
        source_url=source_url,
        observed_at=observed_at,
        force_refresh=refresh_external_context,
    )


def _append_external_context_lines(
    lines: list[str],
    *,
    insights: ExternalSourceInsights,
) -> None:
    metadata = insights.original_source_metadata
    if metadata.source_url:
        lines.append("External source context:")
        lines.append(f"- Enrichment status: {insights.enrichment_status}")
        lines.append(f"- Source URL: {metadata.source_url}")
        if metadata.final_url and metadata.final_url != metadata.source_url:
            lines.append(f"- Final URL: {metadata.final_url}")
        if metadata.page_title:
            lines.append(f"- Source title: {metadata.page_title}")
        if metadata.site_name:
            lines.append(f"- Source site: {metadata.site_name}")
        if insights.site_specific_requirements:
            lines.append("- Site-specific requirements: " + _human_join(insights.site_specific_requirements[:5]))
        if insights.responsibility_clues:
            lines.append("- Source responsibilities: " + _human_join(insights.responsibility_clues[:4]))
        if insights.company_culture_clues:
            lines.append("- Culture clues: " + _human_join(insights.company_culture_clues[:4]))
        if insights.technology_stack_terms:
            lines.append("- Technology stack clues: " + _human_join(insights.technology_stack_terms[:8]))
        if insights.warning:
            lines.append(f"- External context warning: {insights.warning}")


def _build_external_sources(insights: ExternalSourceInsights) -> list[CopilotGroundingSource]:
    metadata = insights.original_source_metadata
    if not metadata.source_url:
        return []

    snippets: list[CopilotGroundingSource] = [
        CopilotGroundingSource(
            label="External source context",
            source_type="job_source_page",
            title=metadata.page_title or metadata.site_name or metadata.source_domain,
            snippet=_clip_text(
                " | ".join(
                    part
                    for part in (
                        "; ".join(insights.site_specific_requirements[:2]),
                        "; ".join(insights.company_culture_clues[:2]),
                        "; ".join(insights.technology_stack_terms[:4]),
                    )
                    if part
                )
                or metadata.source_url,
                limit=220,
            ),
            trust_level="source_page",
            freshness_label=insights.enrichment_status,
        )
    ]
    return snippets


def _build_structured_context(
    *,
    profile: CandidateProfileAggregate,
    job_kind: str,
    job_title: str,
    company_name: str,
    location_text: str,
    workplace_type: str | None,
    employment_type: str | None,
    seniority: str | None,
    explanation: MatchExplanationPayload,
    description_excerpt: str | None,
    external_insights: ExternalSourceInsights,
) -> JobAnalysisStructuredContext:
    behavioral_score = None
    if explanation.behavioral_affinity_score is not None:
        behavioral_score = round(explanation.behavioral_affinity_score * 100)

    return JobAnalysisStructuredContext(
        job_kind=job_kind,
        job_title=job_title,
        company_name=company_name,
        location_text=location_text,
        workplace_type=workplace_type,
        employment_type=employment_type,
        seniority=seniority,
        fit_score_percent=round(explanation.fit_score * 100),
        catalog_score_percent=round(explanation.catalog_score * 100),
        final_score_percent=round(explanation.final_score * 100),
        behavioral_score_percent=behavioral_score,
        explanation_summary=explanation.summary,
        top_reasons=explanation.top_reasons,
        evidence_details=tuple(point.detail for point in explanation.key_evidence_points),
        gap_details=tuple(gap.detail for gap in explanation.gap_analysis),
        matched_skill_terms=explanation.matched_skill_terms,
        missing_skill_terms=explanation.missing_skill_terms,
        profile_headline=profile.headline.value,
        profile_target_roles=tuple(profile.preferences.target_roles),
        profile_top_skills=tuple(item.skill_name for item in profile.skills[:10] if item.skill_name.strip()),
        profile_preferred_locations=tuple(profile.preferences.preferred_locations),
        profile_work_modes=tuple(
            str(item.value if hasattr(item, 'value') else item)
            for item in profile.preferences.work_modes
        ),
        description_excerpt=_clip_text(description_excerpt, limit=900) if description_excerpt else None,
        external_requirements=external_insights.site_specific_requirements,
        external_culture_clues=external_insights.company_culture_clues,
        external_responsibilities=external_insights.responsibility_clues,
        external_technology_terms=external_insights.technology_stack_terms,
    )



async def build_job_analysis_grounding_bundle(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    profile: CandidateProfileAggregate,
    api_job_id: int,
    observed_at: str,
    refresh_external_context: bool = True,
) -> JobAnalysisGroundingBundle:
    resolved = resolve_job_reference(repository, api_job_id=api_job_id)
    if resolved is None:
        raise ValueError("Job could not be found for AI analysis.")

    warnings: list[str] = []
    sources: list[CopilotGroundingSource] = []
    profile_snapshot = _build_profile_snapshot(profile)
    external_insights = await _load_external_source_insights(
        repository=repository,
        source_url=resolved.canonical_url,
        observed_at=observed_at,
        refresh_external_context=refresh_external_context,
    )
    if external_insights.warning:
        warnings.append(external_insights.warning)
    sources.extend(_build_external_sources(external_insights))

    if resolved.job_kind == "canonical" and resolved.canonical_job is not None:
        canonical_job = resolved.canonical_job
        if canonical_job.id is None:
            raise ValueError("Canonical job is missing a persisted identifier.")

        job_feature = repository.get_canonical_job_feature(canonical_job_id=canonical_job.id)
        if job_feature is None:
            raise ValueError("Canonical job features are not available for this listing yet.")

        refresh_result = refresh_subscriber_profile_features(
            repository,
            subscriber_id=subscriber_id,
            refreshed_at=observed_at,
        )
        behavioral_affinity = repository.list_subscriber_job_behavioral_affinity_scores(
            subscriber_id=subscriber_id,
            canonical_job_ids=[canonical_job.id],
            active_only=True,
        ).get(canonical_job.id)
        match_result = score_canonical_job_for_subscriber(
            subscriber_id=subscriber_id,
            profile_feature=refresh_result.profile_feature,
            job=canonical_job,
            job_feature=job_feature,
            behavioral_affinity_score=behavioral_affinity,
        )
        ranked_match = type(
            "RankedMatchProxy",
            (),
            {
                "job": canonical_job,
                "job_feature": job_feature,
                "profile_feature": refresh_result.profile_feature,
                "result": match_result,
            },
        )()
        explanation = _EXPLANATION_GENERATOR.with_external_source_insights(
            _EXPLANATION_GENERATOR.generate_for_ranked_match(ranked_match),
            external_insights,
        )

        lines = [
            "Task mode: job_analysis",
            f"Profile snapshot:\n{profile_snapshot or '(no structured profile summary)'}",
            f"Job title: {canonical_job.display_title}",
            f"Company: {canonical_job.display_company_name}",
            f"Location: {', '.join(part for part in (canonical_job.location_city, canonical_job.country) if part) or '(not specified)'}",
            f"Workplace type: {canonical_job.workplace_type or '(not specified)'}",
            f"Employment type: {canonical_job.employment_type or '(not specified)'}",
            f"Seniority: {canonical_job.seniority or '(not specified)'}",
            f"Deterministic fit score: {round(match_result.fit_score * 100)} / 100",
            f"Catalog quality score: {round(match_result.catalog_score * 100)} / 100",
            f"Final ranking score: {round(match_result.final_score * 100)} / 100",
            f"Behavioral affinity score: {round((match_result.behavioral_affinity_score or 0.0) * 100)} / 100",
            "Top recommendation reasons:",
        ]
        lines.extend(f"- {reason}" for reason in explanation.top_reasons[:3])
        if explanation.gap_analysis:
            lines.append("Gaps or cautions:")
            lines.extend(f"- {gap.title}: {gap.detail}" for gap in explanation.gap_analysis[:3])
        if explanation.key_evidence_points:
            lines.append("Positive evidence:")
            lines.extend(f"- {point.title}: {point.detail}" for point in explanation.key_evidence_points[:4])
        if explanation.matched_skill_terms:
            lines.append(f"Matched skill terms: {_human_join(explanation.matched_skill_terms[:8])}")
        if explanation.missing_skill_terms:
            lines.append(f"Missing skill terms: {_human_join(explanation.missing_skill_terms[:8])}")
        if canonical_job.description_text:
            lines.append("Job description excerpt:")
            lines.append(_clip_text(canonical_job.description_text, limit=900))
        _append_external_context_lines(lines, insights=external_insights)

        sources.extend(
            [
                CopilotGroundingSource(
                    label="Job analysis context",
                    source_type="job",
                    title=canonical_job.display_title,
                    snippet=_clip_text(canonical_job.description_text or canonical_job.display_title, limit=220),
                    trust_level="canonical",
                    freshness_label="live",
                ),
                CopilotGroundingSource(
                    label="Deterministic match evidence",
                    source_type="matching",
                    title=f"{canonical_job.display_title} match evidence",
                    snippet=_clip_text(explanation.summary, limit=220),
                    trust_level="deterministic",
                    freshness_label="live",
                ),
            ]
        )
        return JobAnalysisGroundingBundle(
            job_analysis_summary="\n".join(lines),
            sources=sources,
            warnings=warnings,
            external_source_insights=external_insights,
            analysis_context=_build_structured_context(
                profile=profile,
                job_kind="canonical",
                job_title=canonical_job.display_title,
                company_name=canonical_job.display_company_name,
                location_text=", ".join(part for part in (canonical_job.location_city, canonical_job.country) if part) or "(not specified)",
                workplace_type=canonical_job.workplace_type,
                employment_type=canonical_job.employment_type,
                seniority=canonical_job.seniority,
                explanation=explanation,
                description_excerpt=canonical_job.description_text,
                external_insights=external_insights,
            ),
        )

    legacy_job = resolved.legacy_job
    if legacy_job is None:
        raise ValueError("Legacy job record could not be loaded for AI analysis.")

    matched, score, matched_keywords = _build_legacy_match_info(
        repository=repository,
        subscriber_id=subscriber_id,
        job=legacy_job,
    )
    explanation = _EXPLANATION_GENERATOR.with_external_source_insights(
        _EXPLANATION_GENERATOR.generate_for_legacy_job(
            title=legacy_job.title,
            company_name=legacy_job.company_name,
            matched=matched,
            match_score=score,
            matched_keywords=matched_keywords,
        ),
        external_insights,
    )
    warnings.append(
        "This job is being analyzed with legacy keyword-based ranking because canonical match features are not available yet."
    )
    lines = [
        "Task mode: job_analysis",
        f"Profile snapshot:\n{profile_snapshot or '(no structured profile summary)'}",
        f"Job title: {legacy_job.title}",
        f"Company: {legacy_job.company_name}",
        f"Location: {legacy_job.location or '(not specified)'}",
        f"Legacy keyword score: {score or 0} / 100",
        "Legacy explanation:",
    ]
    lines.extend(f"- {reason}" for reason in explanation.top_reasons[:2])
    if explanation.key_evidence_points:
        lines.extend(f"- {point.title}: {point.detail}" for point in explanation.key_evidence_points[:2])
    if matched_keywords:
        lines.append(f"Matched saved-interest keywords: {_human_join(matched_keywords[:8])}")
    _append_external_context_lines(lines, insights=external_insights)

    sources.extend(
        [
            CopilotGroundingSource(
                label="Job analysis context",
                source_type="job",
                title=legacy_job.title,
                snippet=_clip_text(legacy_job.title, limit=220),
                trust_level="legacy_job",
                freshness_label="live",
            ),
            CopilotGroundingSource(
                label="Legacy match evidence",
                source_type="matching",
                title=f"{legacy_job.title} legacy evidence",
                snippet=_clip_text(explanation.summary, limit=220),
                trust_level="fallback",
                freshness_label="rolling",
            ),
        ]
    )
    return JobAnalysisGroundingBundle(
        job_analysis_summary="\n".join(lines),
        sources=sources,
        warnings=warnings,
        external_source_insights=external_insights,
        analysis_context=_build_structured_context(
            profile=profile,
            job_kind="legacy",
            job_title=legacy_job.title,
            company_name=legacy_job.company_name,
            location_text=legacy_job.location or "(not specified)",
            workplace_type=None,
            employment_type=None,
            seniority=None,
            explanation=explanation,
            description_excerpt=legacy_job.description,
            external_insights=external_insights,
        ),
    )
