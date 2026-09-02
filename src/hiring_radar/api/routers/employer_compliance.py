"""Employer compliance and audit-log export endpoints."""
from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from hiring_radar.api.employer_dependencies import (
    get_current_employer_session,
    get_employer_repository,
)
from hiring_radar.api.pagination import (
    EMPLOYER_LIST_BOUNDS,
    normalize_page_contract,
    set_pagination_headers,
)
from hiring_radar.api.schemas.employer_audit import (
    EmployerAuditActor,
    EmployerAuditEventDetailResponse,
    EmployerAuditEventListResponse,
    EmployerAuditEventResponse,
    EmployerAuditExportResponse,
)
from hiring_radar.db.employer_repository import EmployerAuditEvent, EmployerRepository
from hiring_radar.services.employer_auth import EmployerSession

router = APIRouter(prefix="/api/employer/compliance", tags=["employer-compliance"])

_AUDIT_MANAGER_ROLES = {"owner", "admin"}
_HIGH_SENSITIVITY_PREFIXES = (
    "employer.auth.",
    "employer.team.",
    "employer.settings.",
    "employer.audit.",
)
_MEDIUM_SENSITIVITY_RESOURCE_TYPES = {
    "candidate",
    "candidate_note",
    "candidate_tag",
    "candidate_stage",
    "send_queue",
    "send_queue_item",
    "outreach_campaign",
}


def _require_audit_manager(session: EmployerSession) -> None:
    if session.role_key not in _AUDIT_MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="employer_audit_forbidden")


def _sensitivity(event: EmployerAuditEvent) -> Literal["low", "medium", "high"]:
    if event.event_type.startswith(_HIGH_SENSITIVITY_PREFIXES):
        return "high"
    if event.resource_type in _MEDIUM_SENSITIVITY_RESOURCE_TYPES:
        return "medium"
    return "low"


def _serialize_event(event: EmployerAuditEvent) -> EmployerAuditEventResponse:
    return EmployerAuditEventResponse(
        id=event.id,
        company_id=event.company_id,
        actor=EmployerAuditActor(
            user_id=event.actor_user_id,
            name=event.actor_name,
            email=event.actor_email,
        ),
        event_type=event.event_type,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        before=event.before,
        after=event.after,
        metadata=event.metadata,
        sensitivity=_sensitivity(event),
        created_at=event.created_at,
    )


def _export_rows(items: list[EmployerAuditEventResponse]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in items:
        rows.append(
            {
                "id": str(item.id),
                "created_at": item.created_at,
                "event_type": item.event_type,
                "resource_type": item.resource_type,
                "resource_id": item.resource_id,
                "sensitivity": item.sensitivity,
                "actor_user_id": "" if item.actor.user_id is None else str(item.actor.user_id),
                "actor_name": item.actor.name or "",
                "actor_email": item.actor.email or "",
                "before_json": json.dumps(item.before, ensure_ascii=False, sort_keys=True),
                "after_json": json.dumps(item.after, ensure_ascii=False, sort_keys=True),
                "metadata_json": json.dumps(item.metadata, ensure_ascii=False, sort_keys=True),
            }
        )
    return rows


def _make_csv(items: list[EmployerAuditEventResponse]) -> str:
    rows = _export_rows(items)
    output = io.StringIO()
    fieldnames = [
        "id",
        "created_at",
        "event_type",
        "resource_type",
        "resource_id",
        "sensitivity",
        "actor_user_id",
        "actor_name",
        "actor_email",
        "before_json",
        "after_json",
        "metadata_json",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _clean_text_filter(value: str | None, *, max_length: int = 96) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_length]


@router.get("/audit-events", response_model=EmployerAuditEventListResponse)
def list_employer_audit_events(
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    event_type: str | None = Query(None, max_length=120),
    resource_type: str | None = Query(None, max_length=80),
    resource_id: str | None = Query(None, max_length=120),
    actor_user_id: int | None = Query(None, ge=1),
    created_from: str | None = Query(None, max_length=80),
    created_to: str | None = Query(None, max_length=80),
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> EmployerAuditEventListResponse:
    _require_audit_manager(session)
    filters = {
        "event_type": _clean_text_filter(event_type),
        "resource_type": _clean_text_filter(resource_type),
        "resource_id": _clean_text_filter(resource_id),
        "actor_user_id": actor_user_id,
        "created_from": _clean_text_filter(created_from),
        "created_to": _clean_text_filter(created_to),
    }
    total = repository.count_audit_events(company_id=session.company_id, **filters)
    meta = normalize_page_contract(
        page=page,
        page_size=page_size,
        total_items=total,
        bounds=EMPLOYER_LIST_BOUNDS,
    )
    events = repository.list_audit_events(
        company_id=session.company_id,
        limit=meta.page_size,
        offset=(meta.page - 1) * meta.page_size,
        **filters,
    )
    set_pagination_headers(response, meta=meta)
    return EmployerAuditEventListResponse(
        items=[_serialize_event(item) for item in events],
        page=meta.page,
        page_size=meta.page_size,
        total_items=meta.total_items,
        total_pages=meta.total_pages,
        filters={key: value for key, value in filters.items() if value is not None},
    )


@router.get("/audit-events/export")
def export_employer_audit_events(
    response: Response,
    format: Literal["json", "csv"] = Query("csv"),
    event_type: str | None = Query(None, max_length=120),
    resource_type: str | None = Query(None, max_length=80),
    resource_id: str | None = Query(None, max_length=120),
    actor_user_id: int | None = Query(None, ge=1),
    created_from: str | None = Query(None, max_length=80),
    created_to: str | None = Query(None, max_length=80),
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
):
    _require_audit_manager(session)
    filters = {
        "event_type": _clean_text_filter(event_type),
        "resource_type": _clean_text_filter(resource_type),
        "resource_id": _clean_text_filter(resource_id),
        "actor_user_id": actor_user_id,
        "created_from": _clean_text_filter(created_from),
        "created_to": _clean_text_filter(created_to),
    }
    # Export is intentionally bounded; larger compliance evidence packages should be
    # generated asynchronously in a future job queue patch.
    events = repository.list_audit_events(company_id=session.company_id, limit=500, offset=0, **filters)
    items = [_serialize_event(item) for item in events]
    generated_at = datetime.now(UTC).isoformat()
    export_id = repository.create_audit_event(
        company_id=session.company_id,
        actor_user_id=session.user_id,
        event_type="employer.audit.exported",
        resource_type="audit_log",
        resource_id=f"export_{format}",
        metadata={
            "format": format,
            "exported_items": len(items),
            "filters": {key: value for key, value in filters.items() if value is not None},
            "generated_at": generated_at,
        },
    )
    response.headers["X-Audit-Export-ID"] = str(export_id)
    response.headers["X-Audit-Export-Items"] = str(len(items))

    if format == "json":
        return EmployerAuditExportResponse(
            format="json",
            exported_items=len(items),
            generated_at=generated_at,
            items=items,
        )

    csv_body = _make_csv(items)
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="employer-audit-log.csv"',
            "X-Audit-Export-ID": str(export_id),
            "X-Audit-Export-Items": str(len(items)),
        },
    )


@router.get("/audit-events/{event_id}", response_model=EmployerAuditEventDetailResponse)
def get_employer_audit_event(
    event_id: int,
    session: EmployerSession = Depends(get_current_employer_session),
    repository: EmployerRepository = Depends(get_employer_repository),
) -> EmployerAuditEventDetailResponse:
    _require_audit_manager(session)
    event = repository.get_audit_event(company_id=session.company_id, event_id=event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="employer_audit_event_not_found")
    return EmployerAuditEventDetailResponse(item=_serialize_event(event))
