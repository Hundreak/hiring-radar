from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.job_identity import (
    encode_canonical_job_api_id,
    resolve_job_reference,
)
from hiring_radar.api.schemas.user_jobs import (
    UserJobInteractionRequest,
    UserJobInteractionResponse,
    UserJobAnalysisCoverageResponse,
    UserJobListItemResponse,
    UserJobListResponse,
    UserJobMatchComponentResponse,
    UserJobMatchEvidencePointResponse,
    UserJobMatchExplanationResponse,
    UserJobMatchGapResponse,
    UserJobMatchScoreBreakdownResponse,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering.engine import evaluate_job_text_against_keyword_filter
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.filtering.service import build_filterable_job_text
from hiring_radar.services.matching import (
    ExplanationGenerator,
    build_cached_external_source_insights,
    build_deterministic_match_catalog,
    rank_legacy_jobs_for_subscriber,
)
from hiring_radar.services.matching.contracts import RankedJobMatch
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user", tags=["user-jobs"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]

_LOGGER = logging.getLogger(__name__)
_EXPLANATION_GENERATOR = ExplanationGenerator()

_GENERIC_DISPLAY_TERMS = {
    "engineer", "developer", "manager", "specialist", "lead", "intern", "analyst",
    "software", "platform", "cloud", "backend", "frontend", "fullstack", "full-stack",
    "senior", "junior", "mid", "staff", "principal", "associate", "consultant",
}


def _meaningful_display_terms(terms: tuple[str, ...] | list[str], *, limit: int = 4) -> list[str]:
    meaningful: list[str] = []
    for term in terms:
        cleaned = term.replace('_', ' ').strip().casefold()
        if not cleaned or cleaned in _GENERIC_DISPLAY_TERMS:
            continue
        if cleaned in meaningful:
            continue
        meaningful.append(cleaned)
        if len(meaningful) >= limit:
            break
    return meaningful



@dataclass(frozen=True)
class _LegacyJobMatchInfo:
    matched: bool
    score: int
    matched_keywords: tuple[str, ...]


@dataclass(frozen=True)
class _CanonicalJobListContext:
    items: tuple[UserJobListItemResponse, ...]
    ranking_mode: str


@dataclass(frozen=True)
class _LegacyJobListContext:
    items: tuple[UserJobListItemResponse, ...]
    ranking_mode: str


class _LegacyFilterableJobAdapter:
    __slots__ = ("title", "company_name", "location")

    def __init__(self, *, title: str, company_name: str, location: str | None) -> None:
        self.title = title
        self.company_name = company_name
        self.location = location



def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def _total_pages(*, total_items: int, page_size: int) -> int:
    if total_items == 0:
        return 0
    return (total_items + page_size - 1) // page_size



def _matches_legacy_query(job, query: str | None) -> bool:
    if not query:
        return True

    haystack = " ".join(
        part
        for part in (
            job.title,
            job.company_name,
            job.location or "",
            job.canonical_url,
            job.source_name,
        )
        if part
    ).lower()
    return query.lower() in haystack



def _matches_canonical_query(match: RankedJobMatch, query: str | None) -> bool:
    if not query:
        return True

    lowered = query.strip().casefold()
    haystack = " ".join(
        part
        for part in (
            match.job.display_title,
            match.job.display_company_name,
            match.job.location_city or "",
            match.job.country or "",
            match.job.category or "",
            match.job.department or "",
            match.job.apply_url,
            match.result.explanation_summary,
            " ".join(match.result.matched_skill_terms),
            " ".join(match.result.missing_skill_terms),
        )
        if part
    ).casefold()
    return lowered in haystack



def _calibrate_legacy_match_score(*, matched_keyword_count: int, total_include_keywords: int) -> int:
    """Return a cautious display score for legacy keyword-only matching.

    Legacy keyword overlap is intentionally capped below deterministic scoring so the UI
    does not present fallback results as fully verified profile-to-job matches.
    """
    if matched_keyword_count <= 0 or total_include_keywords <= 0:
        return 0

    ratio = min(1.0, matched_keyword_count / max(1, total_include_keywords))
    score = 42 + round(ratio * 32)
    return max(42, min(74, score))


def _compute_legacy_match_info(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    jobs: list,
) -> dict[int, _LegacyJobMatchInfo]:
    preference = repository.get_subscriber_keyword_preference(subscriber_id)
    if not preference.is_enabled():
        return {}

    settings = KeywordFilterSettings(
        include_keywords=preference.include_keywords,
        exclude_keywords=preference.exclude_keywords,
        match_title=preference.match_title,
        match_location=preference.match_location,
        match_company_name=preference.match_company_name,
    )

    total_include = len(settings.include_keywords)
    result: dict[int, _LegacyJobMatchInfo] = {}

    for job in jobs:
        job_id = job.id or 0
        filterable = build_filterable_job_text(job=job)
        evaluation = evaluate_job_text_against_keyword_filter(
            job=filterable,
            settings=settings,
        )
        if not evaluation.passed:
            continue

        matched_kws = tuple(sorted({match.keyword for match in evaluation.include_matches}))
        score = _calibrate_legacy_match_score(
            matched_keyword_count=len(matched_kws),
            total_include_keywords=total_include,
        )
        result[job_id] = _LegacyJobMatchInfo(
            matched=True,
            score=max(score, 1) if evaluation.passed else 0,
            matched_keywords=matched_kws,
        )

    return result



def _serialize_match_explanation(
    *,
    repository: HiringRadarRepository,
    match: RankedJobMatch,
) -> UserJobMatchExplanationResponse:
    payload = _EXPLANATION_GENERATOR.generate_for_ranked_match(match)
    payload = _EXPLANATION_GENERATOR.with_external_source_insights(
        payload,
        build_cached_external_source_insights(
            repository,
            source_url=match.job.apply_url,
        ),
    )
    return UserJobMatchExplanationResponse(
        summary=payload.summary,
        fit_score=payload.fit_score,
        catalog_score=payload.catalog_score,
        final_score=payload.final_score,
        behavioral_affinity_score=payload.behavioral_affinity_score,
        matched_skill_terms=list(payload.matched_skill_terms),
        missing_skill_terms=list(payload.missing_skill_terms),
        matched_location_terms=list(payload.matched_location_terms),
        matching_score_breakdown=[
            UserJobMatchScoreBreakdownResponse(
                component_key=item.component_key,
                label=item.label,
                weight=item.weight,
                raw_score=item.raw_score,
                weighted_score=item.weighted_score,
                impact=item.impact,
                summary=item.summary,
                evidence_terms=list(item.evidence_terms),
                missing_terms=list(item.missing_terms),
            )
            for item in payload.matching_score_breakdown
        ],
        key_evidence_points=[
            UserJobMatchEvidencePointResponse(
                code=item.code,
                title=item.title,
                detail=item.detail,
                supporting_terms=list(item.supporting_terms),
            )
            for item in payload.key_evidence_points
        ],
        gap_analysis=[
            UserJobMatchGapResponse(
                code=item.code,
                title=item.title,
                detail=item.detail,
                severity=item.severity,
                missing_terms=list(item.missing_terms),
            )
            for item in payload.gap_analysis
        ],
        top_reasons=list(payload.top_reasons),
        analysis_coverage=UserJobAnalysisCoverageResponse(
            score=payload.analysis_coverage.score,
            level=payload.analysis_coverage.level,
            summary=payload.analysis_coverage.summary,
            content_sources=list(payload.analysis_coverage.content_sources),
            detected_signal_types=list(payload.analysis_coverage.detected_signal_types),
            warning=payload.analysis_coverage.warning,
        ),
        external_source_insights={
            "enrichment_status": payload.external_source_insights.enrichment_status,
            "site_specific_requirements": list(payload.external_source_insights.site_specific_requirements),
            "company_culture_clues": list(payload.external_source_insights.company_culture_clues),
            "responsibility_clues": list(payload.external_source_insights.responsibility_clues),
            "technology_stack_terms": list(payload.external_source_insights.technology_stack_terms),
            "original_source_metadata": {
                "source_url": payload.external_source_insights.original_source_metadata.source_url,
                "final_url": payload.external_source_insights.original_source_metadata.final_url,
                "source_domain": payload.external_source_insights.original_source_metadata.source_domain,
                "fetch_status": payload.external_source_insights.original_source_metadata.fetch_status,
                "http_status": payload.external_source_insights.original_source_metadata.http_status,
                "page_title": payload.external_source_insights.original_source_metadata.page_title,
                "site_name": payload.external_source_insights.original_source_metadata.site_name,
                "fetched_at": payload.external_source_insights.original_source_metadata.fetched_at,
                "content_digest": payload.external_source_insights.original_source_metadata.content_digest,
                "text_char_count": payload.external_source_insights.original_source_metadata.text_char_count,
            },
            "warning": payload.external_source_insights.warning,
        },
        components=[
            UserJobMatchComponentResponse(
                name=component.name,
                weight=component.weight,
                raw_score=component.raw_score,
                weighted_score=component.weighted_score,
                summary=component.summary,
                matched_terms=list(component.matched_terms),
                missing_terms=list(component.missing_terms),
            )
            for component in match.result.components
        ],
    )



def _serialize_legacy_explanation(
    *,
    title: str,
    company_name: str,
    matched: bool,
    score: int | None,
    matched_keywords: tuple[str, ...],
) -> UserJobMatchExplanationResponse:
    payload = _EXPLANATION_GENERATOR.generate_for_legacy_job(
        title=title,
        company_name=company_name,
        matched=matched,
        match_score=score,
        matched_keywords=matched_keywords,
    )
    return UserJobMatchExplanationResponse(
        summary=payload.summary,
        fit_score=payload.fit_score,
        catalog_score=payload.catalog_score,
        final_score=payload.final_score,
        behavioral_affinity_score=payload.behavioral_affinity_score,
        matched_skill_terms=list(payload.matched_skill_terms),
        missing_skill_terms=list(payload.missing_skill_terms),
        matched_location_terms=list(payload.matched_location_terms),
        matching_score_breakdown=[
            UserJobMatchScoreBreakdownResponse(
                component_key=item.component_key,
                label=item.label,
                weight=item.weight,
                raw_score=item.raw_score,
                weighted_score=item.weighted_score,
                impact=item.impact,
                summary=item.summary,
                evidence_terms=list(item.evidence_terms),
                missing_terms=list(item.missing_terms),
            )
            for item in payload.matching_score_breakdown
        ],
        key_evidence_points=[
            UserJobMatchEvidencePointResponse(
                code=item.code,
                title=item.title,
                detail=item.detail,
                supporting_terms=list(item.supporting_terms),
            )
            for item in payload.key_evidence_points
        ],
        gap_analysis=[
            UserJobMatchGapResponse(
                code=item.code,
                title=item.title,
                detail=item.detail,
                severity=item.severity,
                missing_terms=list(item.missing_terms),
            )
            for item in payload.gap_analysis
        ],
        top_reasons=list(payload.top_reasons),
        analysis_coverage=UserJobAnalysisCoverageResponse(
            score=payload.analysis_coverage.score,
            level=payload.analysis_coverage.level,
            summary=payload.analysis_coverage.summary,
            content_sources=list(payload.analysis_coverage.content_sources),
            detected_signal_types=list(payload.analysis_coverage.detected_signal_types),
            warning=payload.analysis_coverage.warning,
        ),
        external_source_insights={
            "enrichment_status": payload.external_source_insights.enrichment_status,
            "site_specific_requirements": list(payload.external_source_insights.site_specific_requirements),
            "company_culture_clues": list(payload.external_source_insights.company_culture_clues),
            "responsibility_clues": list(payload.external_source_insights.responsibility_clues),
            "technology_stack_terms": list(payload.external_source_insights.technology_stack_terms),
            "original_source_metadata": {
                "source_url": payload.external_source_insights.original_source_metadata.source_url,
                "final_url": payload.external_source_insights.original_source_metadata.final_url,
                "source_domain": payload.external_source_insights.original_source_metadata.source_domain,
                "fetch_status": payload.external_source_insights.original_source_metadata.fetch_status,
                "http_status": payload.external_source_insights.original_source_metadata.http_status,
                "page_title": payload.external_source_insights.original_source_metadata.page_title,
                "site_name": payload.external_source_insights.original_source_metadata.site_name,
                "fetched_at": payload.external_source_insights.original_source_metadata.fetched_at,
                "content_digest": payload.external_source_insights.original_source_metadata.content_digest,
                "text_char_count": payload.external_source_insights.original_source_metadata.text_char_count,
            },
            "warning": payload.external_source_insights.warning,
        },
        components=[],
    )



def _build_canonical_context(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    active_only: bool,
    only_matched: bool,
    query: str | None,
) -> _CanonicalJobListContext | None:
    has_canonical_jobs = bool(repository.list_canonical_jobs(active_only=active_only))
    if not has_canonical_jobs:
        return None

    catalog = build_deterministic_match_catalog(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=_utc_now_iso(),
        limit=None,
        minimum_score=0.0,
        active_only=active_only,
    )
    if catalog is None:
        return None

    filtered_matches = [match for match in catalog.ranked_matches if _matches_canonical_query(match, query)]
    if only_matched:
        filtered_matches = [match for match in filtered_matches if match.result.matched]

    items = tuple(
        UserJobListItemResponse(
            id=encode_canonical_job_api_id(match.job.id or 0),
            job_kind="canonical",
            source_name="canonical-job-corpus",
            title=match.job.display_title,
            company_name=match.job.display_company_name,
            location=", ".join(part for part in (match.job.location_city, match.job.country) if part) or None,
            canonical_url=match.job.apply_url,
            is_active=match.job.is_active,
            first_seen_at=match.job.created_at,
            last_seen_at=match.job.updated_at,
            matched=match.result.matched,
            match_score=round(match.result.final_score * 100),
            matched_keywords=_meaningful_display_terms(match.result.matched_skill_terms),
            workplace_type=match.job.workplace_type,
            employment_type=match.job.employment_type,
            seniority=match.job.seniority,
            posted_at=match.job.posted_at,
            explanation=_serialize_match_explanation(repository=repository, match=match),
        )
        for match in filtered_matches
    )
    return _CanonicalJobListContext(items=items, ranking_mode="deterministic_matching")



def _build_legacy_context(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    active_only: bool,
    only_matched: bool,
    query: str | None,
) -> _LegacyJobListContext:
    source_jobs = repository.list_active_jobs() if active_only else repository.list_jobs()
    jobs = [job for job in source_jobs if _matches_legacy_query(job, query)]
    refreshed_at = _utc_now_iso()
    legacy_lookup = {job.id or 0: job for job in jobs if job.id is not None}

    ranked_matches = list(
        rank_legacy_jobs_for_subscriber(
            repository,
            subscriber_id=subscriber_id,
            refreshed_at=refreshed_at,
            jobs=jobs,
            minimum_score=0.0,
            active_only=False,
        )
    )

    if only_matched:
        ranked_matches = [match for match in ranked_matches if match.result.matched]

    items = tuple(
        UserJobListItemResponse(
            id=legacy_job.id or 0,
            job_kind="legacy",
            source_name=legacy_job.source_name,
            title=legacy_job.title,
            company_name=legacy_job.company_name,
            location=legacy_job.location,
            canonical_url=legacy_job.canonical_url,
            is_active=legacy_job.is_active,
            first_seen_at=legacy_job.first_seen_at,
            last_seen_at=legacy_job.last_seen_at,
            matched=match.result.matched,
            match_score=round(match.result.final_score * 100),
            matched_keywords=_meaningful_display_terms(match.result.matched_skill_terms),
            workplace_type=match.job.workplace_type,
            employment_type=match.job.employment_type,
            seniority=match.job.seniority,
            posted_at=match.job.posted_at,
            explanation=_serialize_match_explanation(repository=repository, match=match),
        )
        for match in ranked_matches
        if (legacy_job := legacy_lookup.get(match.job.id or 0)) is not None
    )
    return _LegacyJobListContext(items=items, ranking_mode="deterministic_matching")



def _record_job_interaction_response(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    api_job_id: int,
    interaction_type: str,
    source_surface: str,
    dwell_seconds: int | None = None,
) -> UserJobInteractionResponse:
    resolved = resolve_job_reference(repository, api_job_id=api_job_id)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if interaction_type == "dwell" and dwell_seconds is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="dwell_seconds is required for dwell interactions.",
        )

    interaction = repository.record_subscriber_job_interaction(
        subscriber_id=subscriber_id,
        api_job_id=api_job_id,
        job_kind=resolved.job_kind,
        canonical_job_id=resolved.canonical_job.id if resolved.canonical_job is not None else None,
        legacy_job_id=resolved.legacy_job.id if resolved.legacy_job is not None else None,
        interaction_type=interaction_type,
        interacted_at=_utc_now_iso(),
        source_surface=source_surface,
        dwell_seconds=dwell_seconds,
        metadata={"source": "user_jobs_router"},
    )
    return UserJobInteractionResponse(
        job_id=api_job_id,
        job_kind=resolved.job_kind,
        canonical_job_id=interaction.canonical_job_id,
        interaction_type=interaction_type,
        affinity_score=interaction.affinity_score,
        impression_count=interaction.impression_count,
        open_count=interaction.open_count,
        save_count=interaction.save_count,
        apply_click_count=interaction.apply_click_count,
        total_dwell_seconds=interaction.total_dwell_seconds,
        max_dwell_seconds=interaction.max_dwell_seconds,
        last_interacted_at=interaction.last_interacted_at,
    )



def _record_page_impressions(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    items: list[UserJobListItemResponse],
    source_surface: str,
) -> None:
    for item in items:
        try:
            repository.record_subscriber_job_interaction(
                subscriber_id=subscriber_id,
                api_job_id=item.id,
                job_kind=item.job_kind,
                canonical_job_id=(item.id - 1_000_000_000) if item.job_kind == "canonical" else None,
                legacy_job_id=item.id if item.job_kind == "legacy" else None,
                interaction_type="impression",
                interacted_at=_utc_now_iso(),
                source_surface=source_surface,
                metadata={"source": "jobs_listing"},
            )
        except (RuntimeError, ValueError) as exc:
            _LOGGER.warning(
                "Failed to record impression for subscriber_id=%s job_id=%s: %s",
                subscriber_id,
                item.id,
                exc,
            )



def _paginate_items(
    *,
    items: tuple[UserJobListItemResponse, ...],
    page: int,
    page_size: int,
    query: str | None,
    only_matched: bool,
    active_only: bool,
    ranking_mode: str,
) -> UserJobListResponse:
    total_items = len(items)
    start = (page - 1) * page_size
    stop = start + page_size
    page_items = list(items[start:stop])
    return UserJobListResponse(
        items=page_items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=_total_pages(total_items=total_items, page_size=page_size),
        query=query,
        only_matched=only_matched,
        active_only=active_only,
        ranking_mode=ranking_mode,
    )



def _build_jobs_response(
    *,
    user_session: UserSession,
    repository: HiringRadarRepository,
    q: str | None,
    active_only: bool,
    only_matched: bool,
    page: int,
    page_size: int,
    source_surface: str,
) -> UserJobListResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    canonical_context: _CanonicalJobListContext | None = None
    try:
        canonical_context = _build_canonical_context(
            repository=repository,
            subscriber_id=user_session.subscriber_id,
            active_only=active_only,
            only_matched=only_matched,
            query=q,
        )
    except (RuntimeError, ValueError) as exc:
        _LOGGER.warning(
            "Falling back to legacy jobs listing because deterministic ranking failed for subscriber_id=%s: %s",
            user_session.subscriber_id,
            exc,
        )

    if canonical_context is not None:
        response = _paginate_items(
            items=canonical_context.items,
            page=page,
            page_size=page_size,
            query=q,
            only_matched=only_matched,
            active_only=active_only,
            ranking_mode=canonical_context.ranking_mode,
        )
        _record_page_impressions(
            repository=repository,
            subscriber_id=user_session.subscriber_id,
            items=response.items,
            source_surface=source_surface,
        )
        return response

    legacy_context = _build_legacy_context(
        repository=repository,
        subscriber_id=user_session.subscriber_id,
        active_only=active_only,
        only_matched=only_matched,
        query=q,
    )
    response = _paginate_items(
        items=legacy_context.items,
        page=page,
        page_size=page_size,
        query=q,
        only_matched=only_matched,
        active_only=active_only,
        ranking_mode=legacy_context.ranking_mode,
    )
    _record_page_impressions(
        repository=repository,
        subscriber_id=user_session.subscriber_id,
        items=response.items,
        source_surface=source_surface,
    )
    return response


@router.get("/jobs", response_model=UserJobListResponse)
def user_jobs(
    user_session: UserSessionDep,
    repository: RepositoryDep,
    q: str | None = None,
    active_only: bool = True,
    only_matched: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> UserJobListResponse:
    return _build_jobs_response(
        user_session=user_session,
        repository=repository,
        q=q,
        active_only=active_only,
        only_matched=only_matched,
        page=page,
        page_size=page_size,
        source_surface="jobs",
    )


@router.get("/matches", response_model=UserJobListResponse)
def user_matches(
    user_session: UserSessionDep,
    repository: RepositoryDep,
    q: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> UserJobListResponse:
    return _build_jobs_response(
        user_session=user_session,
        repository=repository,
        q=q,
        active_only=True,
        only_matched=True,
        page=page,
        page_size=page_size,
        source_surface="matches",
    )


@router.post("/jobs/{job_id}/open", response_model=UserJobInteractionResponse)
def record_job_open(
    job_id: int,
    body: UserJobInteractionRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserJobInteractionResponse:
    return _record_job_interaction_response(
        repository=repository,
        subscriber_id=user_session.subscriber_id,
        api_job_id=job_id,
        interaction_type="open",
        source_surface=body.source_surface,
    )


@router.post("/jobs/{job_id}/dwell", response_model=UserJobInteractionResponse)
def record_job_dwell(
    job_id: int,
    body: UserJobInteractionRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserJobInteractionResponse:
    return _record_job_interaction_response(
        repository=repository,
        subscriber_id=user_session.subscriber_id,
        api_job_id=job_id,
        interaction_type="dwell",
        source_surface=body.source_surface,
        dwell_seconds=body.dwell_seconds,
    )


@router.post("/jobs/{job_id}/apply-click", response_model=UserJobInteractionResponse)
def record_job_apply_click(
    job_id: int,
    body: UserJobInteractionRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserJobInteractionResponse:
    return _record_job_interaction_response(
        repository=repository,
        subscriber_id=user_session.subscriber_id,
        api_job_id=job_id,
        interaction_type="apply_click",
        source_surface=body.source_surface,
    )
