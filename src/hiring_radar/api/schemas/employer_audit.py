from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EmployerAuditActor(BaseModel):
    user_id: int | None = None
    name: str | None = None
    email: str | None = None


class EmployerAuditEventResponse(BaseModel):
    id: int
    company_id: int
    actor: EmployerAuditActor
    event_type: str
    resource_type: str
    resource_id: str
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    sensitivity: Literal["low", "medium", "high"]
    created_at: str


class EmployerAuditEventListResponse(BaseModel):
    ok: bool = True
    items: list[EmployerAuditEventResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    filters: dict[str, Any] = Field(default_factory=dict)


class EmployerAuditEventDetailResponse(BaseModel):
    ok: bool = True
    item: EmployerAuditEventResponse


class EmployerAuditExportResponse(BaseModel):
    ok: bool = True
    format: Literal["json", "csv"]
    exported_items: int
    generated_at: str
    items: list[EmployerAuditEventResponse] | None = None
