from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering.engine import evaluate_job_text_against_keyword_filter
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.filtering.service import build_filterable_job_text
from hiring_radar.services.matching import build_deterministic_match_catalog
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user/match-insights", tags=["user-match-insights"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]

_GENERIC_TERMS = {
    "engineer",
    "developer",
    "manager",
    "specialist",
    "lead",
    "intern",
    "analyst",
    "software",
    "platform",
    "cloud",
    "backend",
    "frontend",
    "fullstack",
    "full-stack",
    "senior",
    "junior",
    "mid",
    "staff",
    "principal",
    "associate",
    "consultant",
}


class SkillStrength(BaseModel):
    keyword: str
    match_count: int
    total_jobs: int


class SkillGap(BaseModel):
    keyword: str
    demand_count: int
    demand_pct: int


class MatchInsightsResponse(BaseModel):
    total_matched: int
    remote_count: int
    strengths: list[SkillStrength]
    gaps: list[SkillGap]



def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()



def _clean_terms(terms: tuple[str, ...] | list[str], *, limit: int = 8) -> list[str]:
    cleaned: list[str] = []
    for raw_term in terms:
        term = raw_term.replace("_", " ").strip().casefold()
        if not term or term in _GENERIC_TERMS:
            continue
        if term in cleaned:
            continue
        cleaned.append(term)
        if len(cleaned) >= limit:
            break
    return cleaned



def _build_deterministic_match_insights(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
) -> MatchInsightsResponse | None:
    if not repository.list_canonical_jobs(active_only=True):
        return None

    catalog = build_deterministic_match_catalog(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=_utc_now_iso(),
        limit=40,
        minimum_score=0.0,
        active_only=True,
    )
    if catalog is None or not catalog.ranked_matches:
        return MatchInsightsResponse(total_matched=0, remote_count=0, strengths=[], gaps=[])

    matched_jobs = [match for match in catalog.ranked_matches if match.result.matched]
    considered_for_gaps = [match for match in catalog.ranked_matches if match.result.final_score >= 0.45][:20]

    strengths_counter: Counter[str] = Counter()
    for match in matched_jobs:
        for term in _clean_terms(match.result.matched_skill_terms):
            strengths_counter[term] += 1

    gaps_counter: Counter[str] = Counter()
    for match in considered_for_gaps:
        blocker_terms = _clean_terms(match.result.blocker_terms)
        if blocker_terms:
            for term in blocker_terms:
                gaps_counter[term] += 2
            continue
        for term in _clean_terms(match.result.missing_skill_terms, limit=6):
            gaps_counter[term] += 1

    remote_count = sum(
        1
        for match in matched_jobs
        if (match.job.workplace_type or "").casefold() in {"remote", "hybrid"}
        or "remote" in (match.job.location_city or "").casefold()
    )

    total_matched = len(matched_jobs)
    strengths = [
        SkillStrength(keyword=keyword, match_count=count, total_jobs=total_matched)
        for keyword, count in strengths_counter.most_common(5)
    ]

    gap_denominator = max(1, len(considered_for_gaps))
    gaps = [
        SkillGap(
            keyword=keyword,
            demand_count=count,
            demand_pct=min(100, round((count / gap_denominator) * 100)),
        )
        for keyword, count in gaps_counter.most_common(5)
    ]

    return MatchInsightsResponse(
        total_matched=total_matched,
        remote_count=remote_count,
        strengths=strengths,
        gaps=gaps,
    )


@router.get("", response_model=MatchInsightsResponse)
def get_match_insights(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> MatchInsightsResponse:
    deterministic = _build_deterministic_match_insights(
        repository=repository,
        subscriber_id=user_session.subscriber_id,
    )
    if deterministic is not None:
        return deterministic

    preference = repository.get_subscriber_keyword_preference(user_session.subscriber_id)
    if not preference.is_enabled():
        return MatchInsightsResponse(
            total_matched=0, remote_count=0, strengths=[], gaps=[]
        )

    settings = KeywordFilterSettings(
        include_keywords=preference.include_keywords,
        exclude_keywords=preference.exclude_keywords,
        match_title=preference.match_title,
        match_location=preference.match_location,
        match_company_name=preference.match_company_name,
    )

    jobs = repository.list_active_jobs()
    matched_count = 0
    remote_count = 0
    keyword_hits: Counter[str] = Counter()
    keyword_demand: Counter[str] = Counter()

    for job in jobs:
        filterable = build_filterable_job_text(job=job)
        evaluation = evaluate_job_text_against_keyword_filter(
            job=filterable, settings=settings
        )
        if not evaluation.passed:
            continue

        matched_count += 1
        if job.location and "remote" in job.location.lower():
            remote_count += 1

        matched_kws = {m.keyword for m in evaluation.include_matches}
        for kw in matched_kws:
            keyword_hits[kw] += 1

    all_include = set(settings.include_keywords)
    gap_keywords = all_include - set(keyword_hits.keys())

    for kw in all_include:
        job_text_sample = " ".join(
            (j.title + " " + (j.location or "")).lower() for j in jobs[:200]
        )
        if kw.lower() in job_text_sample:
            keyword_demand[kw] += 1

    strengths = [
        SkillStrength(keyword=kw, match_count=count, total_jobs=matched_count)
        for kw, count in keyword_hits.most_common(5)
    ]

    gaps = []
    for kw in gap_keywords:
        demand = keyword_demand.get(kw, 0)
        gaps.append(SkillGap(
            keyword=kw,
            demand_count=demand,
            demand_pct=min(100, demand * 15) if demand > 0 else 0,
        ))
    gaps.sort(key=lambda g: g.demand_count, reverse=True)
    gaps = gaps[:5]

    return MatchInsightsResponse(
        total_matched=matched_count,
        remote_count=remote_count,
        strengths=strengths,
        gaps=gaps,
    )
