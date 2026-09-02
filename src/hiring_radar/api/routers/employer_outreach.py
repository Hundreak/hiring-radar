"""Employer outreach and candidate workflow persistence endpoints."""
from __future__ import annotations

from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException

from hiring_radar.api.employer_dependencies import (
    get_current_employer_session,
    get_employer_repository,
)
from hiring_radar.api.schemas.employer_outreach import (
    EmployerCandidateBulkNoteRequest,
    EmployerCandidateBulkTagRequest,
    EmployerCandidateStageUpdateRequest,
    EmployerOutreachCampaignCreateRequest,
    EmployerSendQueueItemUpdateRequest,
    EmployerSendQueuePrepareRequest,
)
from hiring_radar.db.employer_repository import (
    EmployerOutreachCampaign,
    EmployerRepository,
    EmployerSendQueueItem,
)
from hiring_radar.services.employer_auth import EmployerSession

router = APIRouter(prefix="/api/employer", tags=["employer-outreach"])


def _workflow(repository: EmployerRepository, company_id: int) -> dict[str, dict]:
    return repository.get_candidate_workflow(company_id)


def _ensure_candidates(repository: EmployerRepository, company_id: int, candidate_ids: list[int]) -> None:
    for candidate_id in candidate_ids:
        repository.ensure_candidate_placeholder(company_id=company_id, candidate_id=candidate_id)


def _campaign_to_api(campaign: EmployerOutreachCampaign) -> dict:
    metadata = dict(campaign.metadata or {})
    include_salary = bool(metadata.pop("include_salary", True))
    include_calendar = bool(metadata.pop("include_calendar", True))
    if campaign.subject_preview and "subject_preview" not in metadata:
        metadata["subject_preview"] = campaign.subject_preview
    return {
        "id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "candidate_ids": campaign.candidate_ids,
        "channel": campaign.channel,
        "tone": campaign.tone or "warm",
        "template": campaign.template_key or "role-fit",
        "include_salary": include_salary,
        "include_calendar": include_calendar,
        "message_preview": campaign.message_preview or "",
        "response_rate": campaign.response_rate,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
        "metadata": metadata,
    }


def _queue_stats(items: list[EmployerSendQueueItem]) -> dict[str, int]:
    return {
        "ready_count": sum(1 for item in items if item.status == "ready"),
        "review_count": sum(1 for item in items if item.status == "review"),
        "blocked_count": sum(1 for item in items if item.status == "blocked"),
    }


def _queue_item_to_api(item: EmployerSendQueueItem) -> dict:
    return {
        "id": item.id,
        "candidate_id": item.candidate_id,
        "subject": item.subject,
        "message": item.message,
        "response_score": item.response_score,
        "status": item.status,
        "checks": item.checks,
        "metadata": item.metadata,
        "updated_at": item.updated_at,
    }


def _queue_to_api(
    *,
    repository: EmployerRepository,
    company_id: int,
    campaign: EmployerOutreachCampaign,
    items: list[EmployerSendQueueItem],
) -> dict:
    stats = _queue_stats(items)
    status = "blocked" if stats["blocked_count"] else "ready_for_review"
    audit = repository.list_outreach_audit_events(company_id=company_id, campaign_id=campaign.id)
    prepared_times = [item.prepared_at for item in items if item.prepared_at]
    updated_times = [item.updated_at for item in items if item.updated_at]
    return {
        "id": f"queue_{campaign.id}",
        "campaign_id": campaign.id,
        "employer_id": str(company_id),
        "status": status,
        "channel": campaign.channel,
        "items": [_queue_item_to_api(item) for item in items],
        **stats,
        "created_at": min(prepared_times) if prepared_times else campaign.created_at,
        "updated_at": max(updated_times) if updated_times else campaign.updated_at,
        "audit": audit,
    }


@router.get("/outreach/campaigns")
def list_outreach_campaigns(
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    campaigns = repository.list_outreach_campaigns(session.company_id)
    return {"ok": True, "items": [_campaign_to_api(campaign) for campaign in campaigns]}


@router.post("/outreach/campaigns")
def create_outreach_campaign(
    payload: EmployerOutreachCampaignCreateRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    _ensure_candidates(repository, session.company_id, payload.candidate_ids)
    metadata = dict(payload.metadata or {})
    metadata.setdefault("include_salary", payload.include_salary)
    metadata.setdefault("include_calendar", payload.include_calendar)
    campaign = repository.create_outreach_campaign(
        company_id=session.company_id,
        created_by_user_id=session.user_id,
        name=payload.name or "Davet kampanyası",
        channel=payload.channel,
        tone=payload.tone,
        template_key=payload.template,
        candidate_ids=payload.candidate_ids,
        message_preview=payload.message_preview or "",
        response_rate=payload.response_rate,
        metadata=metadata,
    )
    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="campaign.created",
        resource_type="outreach_campaign",
        resource_id=campaign.id,
        after={"status": campaign.status, "candidate_ids": campaign.candidate_ids},
        metadata={"action": "campaign_created", "note": f"{campaign.name} kampanyası oluşturuldu."},
    )
    for candidate_id in payload.candidate_ids:
        repository.add_candidate_tag(
            company_id=session.company_id,
            candidate_id=candidate_id,
            tag="Davet gönderilecek",
            created_by_user_id=session.user_id,
        )
        repository.add_candidate_note(
            company_id=session.company_id,
            candidate_id=candidate_id,
            author_user_id=session.user_id,
            body=(
                f"{campaign.name} taslağına eklendi. "
                f"Kanal: {campaign.channel}, şablon: {campaign.template_key}."
            ),
            tone="ai",
        )
        repository.create_audit_event(
            company_id=session.company_id,
            actor_user_id=session.user_id,
            event_type="candidate.workflow.campaign_tagged",
            resource_type="candidate",
            resource_id=str(candidate_id),
            after={"tag": "Davet gönderilecek", "campaign_id": campaign.id},
        )
    return {"ok": True, "campaign": _campaign_to_api(campaign), "workflow": _workflow(repository, session.company_id)}


@router.get("/talent/workflow")
def get_talent_workflow(
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    return {"ok": True, "workflow": _workflow(repository, session.company_id)}


@router.post("/talent/workflow/bulk-tags")
def add_candidate_tags(
    payload: EmployerCandidateBulkTagRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    _ensure_candidates(repository, session.company_id, payload.candidate_ids)
    for candidate_id in payload.candidate_ids:
        repository.add_candidate_tag(
            company_id=session.company_id,
            candidate_id=candidate_id,
            tag=payload.tag,
            created_by_user_id=session.user_id,
        )
        repository.create_audit_event(
            company_id=session.company_id,
            actor_user_id=session.user_id,
            event_type="candidate.tag.added",
            resource_type="candidate",
            resource_id=str(candidate_id),
            after={"tag": payload.tag},
        )
    return {"ok": True, "workflow": _workflow(repository, session.company_id)}


@router.post("/talent/workflow/bulk-notes")
def add_candidate_notes(
    payload: EmployerCandidateBulkNoteRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    _ensure_candidates(repository, session.company_id, payload.candidate_ids)
    for candidate_id in payload.candidate_ids:
        note_id = repository.add_candidate_note(
            company_id=session.company_id,
            candidate_id=candidate_id,
            author_user_id=session.user_id,
            body=payload.note,
            tone=payload.tone,
        )
        repository.create_audit_event(
            company_id=session.company_id,
            actor_user_id=session.user_id,
            event_type="candidate.note.added",
            resource_type="candidate_note",
            resource_id=str(note_id),
            after={"candidate_id": candidate_id, "tone": payload.tone},
        )
    return {"ok": True, "workflow": _workflow(repository, session.company_id)}


@router.patch("/talent/workflow/stage")
def update_candidate_stage(
    payload: EmployerCandidateStageUpdateRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    result = repository.update_candidate_stage(
        company_id=session.company_id,
        candidate_id=payload.candidate_id,
        stage_key=payload.stage_key,
        job_id=payload.job_id,
        changed_by_user_id=session.user_id,
        note=payload.note,
    )
    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="candidate.stage.updated",
        resource_type="candidate",
        resource_id=str(payload.candidate_id),
        before={"stage": result["from_stage"]},
        after={"stage": result["to_stage"], "job_id": result["job_id"]},
        metadata={"note": payload.note} if payload.note else {},
    )
    return {"ok": True, "stage": result, "workflow": _workflow(repository, session.company_id)}


@router.delete("/talent/workflow/candidates/{candidate_id}/tags/{tag}")
def delete_candidate_tag(
    candidate_id: int,
    tag: str,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    repository.remove_candidate_tag(
        company_id=session.company_id,
        candidate_id=candidate_id,
        tag=unquote(tag),
    )
    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="candidate.tag.removed",
        resource_type="candidate",
        resource_id=str(candidate_id),
        before={"tag": unquote(tag)},
    )
    return {"ok": True, "workflow": _workflow(repository, session.company_id)}


@router.get("/outreach/campaigns/{campaign_id}/send-queue")
def get_campaign_send_queue(
    campaign_id: str,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    campaign = repository.get_outreach_campaign_for_company(
        company_id=session.company_id,
        campaign_id=campaign_id,
    )
    if campaign is None:
        return {"ok": True, "queue": None}
    items = repository.list_send_queue_items(company_id=session.company_id, campaign_id=campaign_id) or []
    if not items:
        return {"ok": True, "queue": None}
    return {"ok": True, "queue": _queue_to_api(repository=repository, company_id=session.company_id, campaign=campaign, items=items)}


@router.post("/outreach/campaigns/{campaign_id}/send-queue/prepare")
def prepare_campaign_send_queue(
    campaign_id: str,
    payload: EmployerSendQueuePrepareRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    campaign = repository.get_outreach_campaign_for_company(
        company_id=session.company_id,
        campaign_id=campaign_id,
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    items = repository.replace_campaign_send_queue(
        company_id=session.company_id,
        campaign_id=campaign_id,
        items=[item.model_dump() for item in payload.items],
        prepared_by_user_id=session.user_id,
    )
    if items is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    stats = _queue_stats(items)
    queue_status = "blocked" if stats["blocked_count"] else "ready_for_review"
    campaign_status = "draft" if stats["blocked_count"] else "queued"
    updated_campaign = repository.update_outreach_campaign(
        company_id=session.company_id,
        campaign_id=campaign_id,
        status=campaign_status,
        metadata={"send_queue": {"status": queue_status, **stats}},
    ) or campaign
    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="send_queue.prepared",
        resource_type="send_queue",
        resource_id=f"queue_{campaign_id}",
        after={"status": queue_status, **stats},
        metadata={
            "action": "queue_prepared",
            "note": payload.note or f"{len(items)} aday için gönderim kuyruğu hazırlandı.",
            "campaign_id": campaign_id,
            **stats,
        },
    )
    for item in items:
        if item.status == "ready":
            repository.add_candidate_tag(
                company_id=session.company_id,
                candidate_id=item.candidate_id,
                tag="Gönderim kuyruğunda",
                created_by_user_id=session.user_id,
            )
        repository.add_candidate_note(
            company_id=session.company_id,
            candidate_id=item.candidate_id,
            author_user_id=session.user_id,
            body=f"{campaign.name} gönderim kuyruğunda: {item.status}.",
            tone="ai",
        )
    return {"ok": True, "queue": _queue_to_api(repository=repository, company_id=session.company_id, campaign=updated_campaign, items=items)}


@router.patch("/outreach/campaigns/{campaign_id}/send-queue/items/{item_id}")
def update_campaign_send_queue_item(
    campaign_id: str,
    item_id: str,
    payload: EmployerSendQueueItemUpdateRequest,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    campaign = repository.get_outreach_campaign_for_company(
        company_id=session.company_id,
        campaign_id=campaign_id,
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    updated_item = repository.update_send_queue_item(
        company_id=session.company_id,
        campaign_id=campaign_id,
        item_id=item_id,
        status=payload.status,
        checks=payload.checks,
    )
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Send queue item not found")
    items = repository.list_send_queue_items(company_id=session.company_id, campaign_id=campaign_id) or []
    stats = _queue_stats(items)
    queue_status = "blocked" if stats["blocked_count"] else "ready_for_review"
    updated_campaign = repository.update_outreach_campaign(
        company_id=session.company_id,
        campaign_id=campaign_id,
        status="draft" if stats["blocked_count"] else "queued",
        metadata={"send_queue": {"status": queue_status, **stats}},
    ) or campaign
    repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="send_queue.item.updated",
        resource_type="send_queue_item",
        resource_id=item_id,
        after={"status": updated_item.status, "checks": updated_item.checks},
        metadata={
            "action": "queue_item_updated",
            "note": payload.note or f"{updated_item.candidate_id} adayının kuyruk durumu güncellendi.",
            "campaign_id": campaign_id,
            "item_id": item_id,
        },
    )
    return {"ok": True, "queue": _queue_to_api(repository=repository, company_id=session.company_id, campaign=updated_campaign, items=items)}
