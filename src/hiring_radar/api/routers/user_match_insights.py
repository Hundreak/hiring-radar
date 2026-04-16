from __future__ import annotations

from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering.engine import evaluate_job_text_against_keyword_filter
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.filtering.service import build_filterable_job_text
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user/match-insights", tags=["user-match-insights"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


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


@router.get("", response_model=MatchInsightsResponse)
def get_match_insights(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> MatchInsightsResponse:
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

    # Track which keywords appear in job requirements (approximated from text)
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

    # Gaps: keywords from include_keywords that rarely matched
    all_include = set(settings.include_keywords)
    gap_keywords = all_include - set(keyword_hits.keys())

    # Also scan unmatched jobs for demand of gap keywords
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
