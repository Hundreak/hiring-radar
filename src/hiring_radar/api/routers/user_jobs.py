from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.schemas.user_jobs import UserJobListItemResponse, UserJobListResponse
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering import filter_jobs_by_keyword_settings
from hiring_radar.filtering.engine import evaluate_job_text_against_keyword_filter
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.filtering.service import build_filterable_job_text
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user", tags=["user-jobs"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


def _total_pages(*, total_items: int, page_size: int) -> int:
    if total_items == 0:
        return 0
    return (total_items + page_size - 1) // page_size


def _matches_query(job, query: str | None) -> bool:
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


@dataclass(frozen=True)
class _JobMatchInfo:
    matched: bool
    score: int
    matched_keywords: tuple[str, ...]


def _compute_match_info(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    jobs: list,
) -> dict[int, _JobMatchInfo]:
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
    result: dict[int, _JobMatchInfo] = {}

    for job in jobs:
        job_id = job.id or 0
        filterable = build_filterable_job_text(job=job)
        evaluation = evaluate_job_text_against_keyword_filter(
            job=filterable,
            settings=settings,
        )
        if not evaluation.passed:
            continue

        matched_kws = tuple(
            sorted({m.keyword for m in evaluation.include_matches})
        )
        score = (
            round(len(matched_kws) / total_include * 100)
            if total_include > 0
            else 0
        )
        result[job_id] = _JobMatchInfo(
            matched=True,
            score=max(score, 1) if evaluation.passed else 0,
            matched_keywords=matched_kws,
        )

    return result


def _serialize_jobs(
    *,
    jobs: list,
    match_info: dict[int, _JobMatchInfo],
    page: int,
    page_size: int,
    query: str | None,
    only_matched: bool,
    active_only: bool,
) -> UserJobListResponse:

    total_items = len(jobs)
    start = (page - 1) * page_size
    stop = start + page_size
    page_jobs = jobs[start:stop]

    items: list[UserJobListItemResponse] = []
    for job in page_jobs:
        job_id = job.id or 0
        info = match_info.get(job_id)
        items.append(
            UserJobListItemResponse(
                id=job_id,
                source_name=job.source_name,
                title=job.title,
                company_name=job.company_name,
                location=job.location,
                canonical_url=job.canonical_url,
                is_active=job.is_active,
                first_seen_at=job.first_seen_at,
                last_seen_at=job.last_seen_at,
                matched=info is not None,
                match_score=info.score if info else None,
                matched_keywords=list(info.matched_keywords) if info else [],
            )
        )

    return UserJobListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=_total_pages(total_items=total_items, page_size=page_size),
        query=query,
        only_matched=only_matched,
        active_only=active_only,
    )


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
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    jobs = repository.list_active_jobs() if active_only else repository.list_jobs()
    jobs = [job for job in jobs if _matches_query(job, q)]
    jobs.sort(key=lambda item: item.first_seen_at or "", reverse=True)

    match_info = _compute_match_info(
        repository=repository,
        subscriber_id=user_session.subscriber_id,
        jobs=jobs,
    )
    if only_matched:
        jobs = [job for job in jobs if (job.id or 0) in match_info]

    return _serialize_jobs(
        jobs=jobs,
        match_info=match_info,
        page=page,
        page_size=page_size,
        query=q,
        only_matched=only_matched,
        active_only=active_only,
    )


@router.get("/matches", response_model=UserJobListResponse)
def user_matches(
    user_session: UserSessionDep,
    repository: RepositoryDep,
    q: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> UserJobListResponse:
    return user_jobs(
        user_session=user_session,
        repository=repository,
        q=q,
        active_only=True,
        only_matched=True,
        page=page,
        page_size=page_size,
    )
