from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.schemas.user_saved_jobs import (
    AddNoteRequest,
    SavedJobListResponse,
    SavedJobNoteResponse,
    SavedJobResponse,
    SaveJobRequest,
    UpdateSavedJobStatusRequest,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.filtering.engine import evaluate_job_text_against_keyword_filter
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.filtering.service import build_filterable_job_text
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user/saved-jobs", tags=["user-saved-jobs"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]

VALID_STATUSES = {"reviewing", "applied", "interview", "archived"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_matched_keywords(
    job,
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
) -> list[str]:
    if job is None:
        return []
    preference = repository.get_subscriber_keyword_preference(subscriber_id)
    if not preference.is_enabled():
        return []
    settings = KeywordFilterSettings(
        include_keywords=preference.include_keywords,
        exclude_keywords=preference.exclude_keywords,
        match_title=preference.match_title,
        match_location=preference.match_location,
        match_company_name=preference.match_company_name,
    )
    filterable = build_filterable_job_text(job=job)
    evaluation = evaluate_job_text_against_keyword_filter(job=filterable, settings=settings)
    return sorted({m.keyword for m in evaluation.include_matches})


def _enrich_saved_job(
    saved_job,
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    matched_keywords: list[str] | None = None,
) -> SavedJobResponse:
    job = repository.get_job_by_id(saved_job.job_id)
    notes = repository.list_saved_job_notes(
        saved_job.id, subscriber_id=subscriber_id
    )
    if matched_keywords is None:
        matched_keywords = _compute_matched_keywords(
            job, repository=repository, subscriber_id=subscriber_id
        )
    return SavedJobResponse(
        id=saved_job.id,
        job_id=saved_job.job_id,
        status=saved_job.status,
        match_score=saved_job.match_score,
        deadline_at=saved_job.deadline_at,
        interview_at=saved_job.interview_at,
        created_at=saved_job.created_at,
        updated_at=saved_job.updated_at,
        title=job.title if job else "",
        company_name=job.company_name if job else "",
        location=job.location if job else None,
        canonical_url=job.canonical_url if job else "",
        source_name=job.source_name if job else "",
        matched_keywords=matched_keywords,
        notes=[
            SavedJobNoteResponse(
                id=n.id,
                saved_job_id=n.saved_job_id,
                content=n.content,
                created_at=n.created_at,
            )
            for n in notes
        ],
    )


@router.get("", response_model=SavedJobListResponse)
def list_saved_jobs(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobListResponse:
    saved = repository.list_saved_jobs(user_session.subscriber_id)
    items = [
        _enrich_saved_job(s, repository=repository, subscriber_id=user_session.subscriber_id)
        for s in saved
    ]
    return SavedJobListResponse(items=items)


@router.post("", response_model=SavedJobResponse, status_code=201)
def save_job(
    body: SaveJobRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobResponse:
    existing = repository.get_saved_job(
        subscriber_id=user_session.subscriber_id, job_id=body.job_id
    )
    if existing:
        raise HTTPException(status_code=409, detail="Job already saved.")

    job = repository.get_job_by_id(body.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    saved = repository.save_job(
        subscriber_id=user_session.subscriber_id,
        job_id=body.job_id,
        match_score=body.match_score,
        now=_now_iso(),
    )
    return _enrich_saved_job(
        saved, repository=repository, subscriber_id=user_session.subscriber_id
    )


@router.delete("/{job_id}", status_code=204)
def unsave_job(
    job_id: int,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> None:
    deleted = repository.unsave_job(
        subscriber_id=user_session.subscriber_id, job_id=job_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved job not found.")


@router.patch("/{saved_job_id}/status", response_model=SavedJobResponse)
def update_status(
    saved_job_id: int,
    body: UpdateSavedJobStatusRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobResponse:
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    updated = repository.update_saved_job_status(
        saved_job_id,
        subscriber_id=user_session.subscriber_id,
        status=body.status,
        now=_now_iso(),
        deadline_at=body.deadline_at,
        interview_at=body.interview_at,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Saved job not found.")

    saved = repository.get_saved_job_by_id(
        saved_job_id, subscriber_id=user_session.subscriber_id
    )
    if saved is None:
        raise HTTPException(status_code=404, detail="Saved job not found.")

    return _enrich_saved_job(
        saved, repository=repository, subscriber_id=user_session.subscriber_id
    )


@router.post("/{saved_job_id}/notes", response_model=SavedJobNoteResponse, status_code=201)
def add_note(
    saved_job_id: int,
    body: AddNoteRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobNoteResponse:
    saved = repository.get_saved_job_by_id(
        saved_job_id, subscriber_id=user_session.subscriber_id
    )
    if saved is None:
        raise HTTPException(status_code=404, detail="Saved job not found.")

    note = repository.add_saved_job_note(
        saved_job_id=saved_job_id,
        subscriber_id=user_session.subscriber_id,
        content=body.content,
        now=_now_iso(),
    )
    return SavedJobNoteResponse(
        id=note.id,
        saved_job_id=note.saved_job_id,
        content=note.content,
        created_at=note.created_at,
    )


@router.patch("/{saved_job_id}/notes/{note_id}", response_model=SavedJobNoteResponse)
def update_note(
    saved_job_id: int,
    note_id: int,
    body: AddNoteRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobNoteResponse:
    saved = repository.get_saved_job_by_id(
        saved_job_id, subscriber_id=user_session.subscriber_id
    )
    if saved is None:
        raise HTTPException(status_code=404, detail="Saved job not found.")

    updated = repository.update_saved_job_note(
        note_id=note_id,
        subscriber_id=user_session.subscriber_id,
        content=body.content,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Note not found.")

    return SavedJobNoteResponse(
        id=note_id,
        saved_job_id=saved_job_id,
        content=body.content,
        created_at=None,
    )
