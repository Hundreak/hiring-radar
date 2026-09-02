from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from hiring_radar.api.dependencies import get_current_admin_session, get_repository
from hiring_radar.api.pagination import (
    ADMIN_LIST_BOUNDS,
    normalize_page_contract,
    set_pagination_headers,
    total_pages,
)
from hiring_radar.api.schemas.jobs import AdminJobListItemResponse, AdminJobListResponse
from hiring_radar.api.security import AdminSession
from hiring_radar.db.repository import HiringRadarRepository

router = APIRouter(prefix="/api/admin/jobs", tags=["admin-jobs"])

AdminSessionDep = Annotated[AdminSession, Depends(get_current_admin_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


@router.get("", response_model=AdminJobListResponse)
def admin_list_jobs(
    admin_session: AdminSessionDep,
    repository: RepositoryDep,
    response: Response,
    q: Annotated[str | None, Query(max_length=160)] = None,
    source_name: str | None = None,
    company_name: str | None = None,
    is_active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> AdminJobListResponse:
    _ = admin_session

    jobs, total_items = repository.list_jobs_paginated(
        q=q,
        source_name=source_name,
        company_name=company_name,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    meta = normalize_page_contract(page=page, page_size=page_size, total_items=total_items, bounds=ADMIN_LIST_BOUNDS)
    set_pagination_headers(response, meta=meta)

    return AdminJobListResponse(
        items=[
            AdminJobListItemResponse(
                id=job.id or 0,
                source_name=job.source_name,
                company_name=job.company_name,
                source_type=job.source_type,
                title=job.title,
                location=job.location,
                canonical_url=job.canonical_url,
                posted_at=job.posted_at,
                first_seen_at=job.first_seen_at,
                last_seen_at=job.last_seen_at,
                is_active=job.is_active,
            )
            for job in jobs
        ],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages(total_items=total_items, page_size=page_size),
    )
