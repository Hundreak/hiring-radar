from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.job_identity import resolve_job_reference
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
from hiring_radar.models import JobRecord
from hiring_radar.services.matching import get_ranked_match_for_canonical_job, score_legacy_job_for_subscriber
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user/saved-jobs", tags=["user-saved-jobs"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]

VALID_STATUSES = {"reviewing", "applied", "interview", "archived"}




def _compute_saved_job_match_snapshot(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    api_job_id: int,
) -> tuple[int | None, list[str]]:
    resolved = resolve_job_reference(repository, api_job_id=api_job_id)
    if resolved is None:
        return None, []

    if resolved.job_kind == "canonical" and resolved.canonical_job is not None:
        ranked_match = get_ranked_match_for_canonical_job(
            repository,
            subscriber_id=subscriber_id,
            canonical_job_id=resolved.canonical_job.id or 0,
            refreshed_at=_now_iso(),
            active_only=True,
        )
        if ranked_match is None:
            return None, []
        return round(ranked_match.result.final_score * 100), list(ranked_match.result.matched_skill_terms)

    if resolved.legacy_job is not None and resolved.legacy_job.id is not None:
        ranked_match = score_legacy_job_for_subscriber(
            repository,
            subscriber_id=subscriber_id,
            legacy_job=resolved.legacy_job,
            refreshed_at=_now_iso(),
        )
        return round(ranked_match.result.final_score * 100), list(ranked_match.result.matched_skill_terms)

    return None, []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def _compute_matched_keywords_for_resolved_job(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    api_job_id: int,
) -> list[str]:
    score, matched_keywords = _compute_saved_job_match_snapshot(
        repository=repository,
        subscriber_id=subscriber_id,
        api_job_id=api_job_id,
    )
    if matched_keywords:
        return matched_keywords

    resolved = resolve_job_reference(repository, api_job_id=api_job_id)
    if resolved is None or resolved.legacy_job is None:
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
    filterable_job_text = build_filterable_job_text(job=resolved.legacy_job)
    evaluation = evaluate_job_text_against_keyword_filter(
        job=filterable_job_text,
        settings=settings,
    )
    return sorted({match.keyword for match in evaluation.include_matches})



def _enrich_saved_job(
    saved_job,
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    matched_keywords: list[str] | None = None,
) -> SavedJobResponse:
    public_job_id = saved_job.api_job_id or saved_job.job_id
    resolved = resolve_job_reference(repository, api_job_id=public_job_id)
    notes = repository.list_saved_job_notes(saved_job.id, subscriber_id=subscriber_id)
    live_match_score, live_matched_keywords = _compute_saved_job_match_snapshot(
        repository=repository,
        subscriber_id=subscriber_id,
        api_job_id=public_job_id,
    )
    if matched_keywords is None:
        matched_keywords = live_matched_keywords or _compute_matched_keywords_for_resolved_job(
            repository=repository,
            subscriber_id=subscriber_id,
            api_job_id=public_job_id,
        )

    return SavedJobResponse(
        id=saved_job.id,
        job_id=public_job_id,
        job_kind=resolved.job_kind if resolved is not None else "legacy",
        status=saved_job.status,
        match_score=live_match_score if live_match_score is not None else saved_job.match_score,
        deadline_at=saved_job.deadline_at,
        interview_at=saved_job.interview_at,
        created_at=saved_job.created_at,
        updated_at=saved_job.updated_at,
        title=resolved.title if resolved is not None else "",
        company_name=resolved.company_name if resolved is not None else "",
        location=resolved.location if resolved is not None else None,
        canonical_url=resolved.canonical_url if resolved is not None else "",
        source_name=resolved.source_name if resolved is not None else "",
        matched_keywords=matched_keywords,
        notes=[
            SavedJobNoteResponse(
                id=note.id,
                saved_job_id=note.saved_job_id,
                content=note.content,
                created_at=note.created_at,
            )
            for note in notes
        ],
    )



def _ensure_legacy_job_mirror_for_canonical(
    *,
    repository: HiringRadarRepository,
    canonical_job_id: int,
) -> JobRecord:
    canonical_job = repository.get_canonical_job_by_id(canonical_job_id)
    if canonical_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    fingerprint = f"canonical::{canonical_job_id}"
    repository.upsert_job(
        JobRecord(
            source_name="canonical-job-corpus",
            title=canonical_job.display_title,
            company_name=canonical_job.display_company_name,
            location=", ".join(
                part for part in (canonical_job.location_city, canonical_job.country) if part
            )
            or None,
            canonical_url=canonical_job.apply_url,
            source_type="canonical",
            source_job_id=str(canonical_job_id),
            raw_posted_at=canonical_job.posted_at,
            posted_at=canonical_job.posted_at,
            fingerprint=fingerprint,
            first_seen_at=canonical_job.created_at,
            last_seen_at=canonical_job.updated_at,
            is_active=canonical_job.is_active,
            scraped_at=_now_iso(),
        )
    )
    mirrored_job = repository.get_job_by_fingerprint(fingerprint)
    if mirrored_job is None or mirrored_job.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Canonical job mirror could not be created.",
        )
    return mirrored_job


@router.get("", response_model=SavedJobListResponse)
def list_saved_jobs(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobListResponse:
    saved = repository.list_saved_jobs(user_session.subscriber_id)
    items = [
        _enrich_saved_job(
            saved_job,
            repository=repository,
            subscriber_id=user_session.subscriber_id,
        )
        for saved_job in saved
    ]
    return SavedJobListResponse(items=items)


@router.post("", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED)
def save_job(
    body: SaveJobRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobResponse:
    existing = repository.get_saved_job(
        subscriber_id=user_session.subscriber_id,
        job_id=body.job_id,
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job already saved.")

    resolved = resolve_job_reference(repository, api_job_id=body.job_id)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    storage_job_id = body.job_id
    if resolved.job_kind == "canonical":
        canonical_job = resolved.canonical_job
        if canonical_job is None or canonical_job.id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        storage_job_id = _ensure_legacy_job_mirror_for_canonical(
            repository=repository,
            canonical_job_id=canonical_job.id,
        ).id or 0

    now_iso = _now_iso()
    saved = repository.save_job(
        subscriber_id=user_session.subscriber_id,
        job_id=storage_job_id,
        api_job_id=body.job_id,
        match_score=body.match_score,
        now=now_iso,
    )
    repository.record_subscriber_job_interaction(
        subscriber_id=user_session.subscriber_id,
        api_job_id=body.job_id,
        job_kind=resolved.job_kind,
        canonical_job_id=(resolved.canonical_job.id if resolved.canonical_job is not None else None),
        legacy_job_id=(resolved.legacy_job.id if resolved.legacy_job is not None else None),
        interaction_type="save",
        interacted_at=now_iso,
        source_surface="saved_jobs",
        metadata={"source": "user_saved_jobs_router"},
    )
    return _enrich_saved_job(
        saved,
        repository=repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def unsave_job(
    job_id: int,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> Response:
    deleted = repository.unsave_job(
        subscriber_id=user_session.subscriber_id,
        job_id=job_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved job not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{saved_job_id}/status", response_model=SavedJobResponse)
def update_status(
    saved_job_id: int,
    body: UpdateSavedJobStatusRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobResponse:
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved job not found.")

    saved = repository.get_saved_job_by_id(
        saved_job_id,
        subscriber_id=user_session.subscriber_id,
    )
    if saved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved job not found.")

    return _enrich_saved_job(
        saved,
        repository=repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.post("/{saved_job_id}/notes", response_model=SavedJobNoteResponse, status_code=status.HTTP_201_CREATED)
def add_note(
    saved_job_id: int,
    body: AddNoteRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> SavedJobNoteResponse:
    saved = repository.get_saved_job_by_id(
        saved_job_id,
        subscriber_id=user_session.subscriber_id,
    )
    if saved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved job not found.")

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
        saved_job_id,
        subscriber_id=user_session.subscriber_id,
    )
    if saved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved job not found.")

    updated = repository.update_saved_job_note(
        note_id=note_id,
        subscriber_id=user_session.subscriber_id,
        content=body.content,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    return SavedJobNoteResponse(
        id=note_id,
        saved_job_id=saved_job_id,
        content=body.content,
        created_at=None,
    )
