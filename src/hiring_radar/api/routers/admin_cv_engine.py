from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from hiring_radar.api.dependencies import get_current_admin_session
from hiring_radar.api.schemas.cv_engine_admin import (
    AdminCvEngineBatchCreateRequest,
    AdminCvEngineBatchListItemResponse,
    AdminCvEngineBatchListResponse,
    AdminCvEngineBatchResultEnvelopeResponse,
    AdminCvEngineBatchResultResponse,
    AdminCvEngineBatchSummaryResponse,
    AdminCvEngineCompliancePolicyResponse,
    AdminCvEngineDeadLetterResponse,
    AdminCvEngineHealthResponse,
    AdminCvEngineMetricsResponse,
)
from hiring_radar.api.security import AdminSession
from hiring_radar.services.cv_engine.batch import (
    BatchParseRequest,
    get_batch_run_registry,
    run_admin_batch_parse,
)
from hiring_radar.services.cv_engine.batch.admin_runtime import StoredBatchRun
from hiring_radar.services.cv_engine.compliance.policies import CompliancePolicy
from hiring_radar.services.cv_engine.telemetry.health import build_cv_engine_health_report
from hiring_radar.services.cv_engine.telemetry.metrics import get_cv_engine_metrics_registry

router = APIRouter(prefix="/api/admin/cv-engine", tags=["admin-cv-engine"])

AdminSessionDep = Annotated[AdminSession, Depends(get_current_admin_session)]


def _serialize_batch_summary(
    stored: StoredBatchRun,
) -> AdminCvEngineBatchSummaryResponse | None:
    if stored.summary is None:
        return None
    return AdminCvEngineBatchSummaryResponse(
        total_items=stored.summary.total_items,
        succeeded_items=stored.summary.succeeded_items,
        failed_items=stored.summary.failed_items,
        partial_items=stored.summary.partial_items,
        duration_ms=stored.summary.duration_ms,
    )


def _serialize_batch_response(batch_id: str) -> AdminCvEngineBatchResultEnvelopeResponse:
    stored = get_batch_run_registry().get(batch_id)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV engine batch not found.",
        )
    return AdminCvEngineBatchResultEnvelopeResponse(
        batch_id=stored.batch_id,
        created_at=stored.created_at,
        finished_at=stored.finished_at,
        request_count=stored.request_count,
        status=stored.status,
        summary=_serialize_batch_summary(stored),
        results=[
            AdminCvEngineBatchResultResponse(
                request_id=item.request_id,
                source_path=item.source_path,
                status=item.status.value,
                attempts=item.attempts,
                duration_ms=item.duration_ms,
                error_type=item.error_type,
                error_message=item.error_message,
                output=item.output if isinstance(item.output, dict) else None,
            )
            for item in stored.results
        ],
    )


@router.post("/batches", response_model=AdminCvEngineBatchResultEnvelopeResponse)
async def create_cv_engine_batch(
    payload: AdminCvEngineBatchCreateRequest,
    _admin_session: AdminSessionDep,
) -> AdminCvEngineBatchResultEnvelopeResponse:
    requests = [
        BatchParseRequest(
            request_id=item.request_id,
            source_path=item.source_path,
            priority=item.priority,
            metadata=dict(item.metadata),
        )
        for item in payload.items
    ]
    run = await run_admin_batch_parse(
        requests=requests,
        retry_policy=payload.retry_policy,
    )
    return _serialize_batch_response(run.batch_id)


@router.get("/batches", response_model=AdminCvEngineBatchListResponse)
def list_cv_engine_batches(
    _admin_session: AdminSessionDep,
) -> AdminCvEngineBatchListResponse:
    items = get_batch_run_registry().list_recent(limit=20)
    return AdminCvEngineBatchListResponse(
        batches=[
            AdminCvEngineBatchListItemResponse(
                batch_id=item.batch_id,
                created_at=item.created_at,
                finished_at=item.finished_at,
                request_count=item.request_count,
                status=item.status,
                total_items=(
                    None if item.summary is None else item.summary.total_items
                ),
                succeeded_items=(
                    None if item.summary is None else item.summary.succeeded_items
                ),
                failed_items=(
                    None if item.summary is None else item.summary.failed_items
                ),
                partial_items=(
                    None if item.summary is None else item.summary.partial_items
                ),
                duration_ms=(
                    None if item.summary is None else item.summary.duration_ms
                ),
            )
            for item in items
        ]
    )


@router.get("/batches/{batch_id}", response_model=AdminCvEngineBatchResultEnvelopeResponse)
def get_cv_engine_batch(
    batch_id: str,
    _admin_session: AdminSessionDep,
) -> AdminCvEngineBatchResultEnvelopeResponse:
    return _serialize_batch_response(batch_id)


@router.get(
    "/batches/{batch_id}/dead-letters",
    response_model=list[AdminCvEngineDeadLetterResponse],
)
def get_cv_engine_batch_dead_letters(
    batch_id: str,
    _admin_session: AdminSessionDep,
) -> list[AdminCvEngineDeadLetterResponse]:
    stored = get_batch_run_registry().get(batch_id)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV engine batch not found.",
        )
    if stored.summary is None:
        return []
    return [
        AdminCvEngineDeadLetterResponse.model_validate(item.model_dump(mode="json"))
        for item in stored.summary.dead_letters
    ]


@router.get("/health", response_model=AdminCvEngineHealthResponse)
def get_cv_engine_health(
    _admin_session: AdminSessionDep,
) -> AdminCvEngineHealthResponse:
    return AdminCvEngineHealthResponse(
        health=build_cv_engine_health_report(),
        metrics=get_cv_engine_metrics_registry().snapshot(),
    )


@router.get("/metrics", response_model=AdminCvEngineMetricsResponse)
def get_cv_engine_metrics(
    _admin_session: AdminSessionDep,
) -> AdminCvEngineMetricsResponse:
    return AdminCvEngineMetricsResponse(
        metrics=get_cv_engine_metrics_registry().snapshot()
    )


@router.get(
    "/compliance/policy",
    response_model=AdminCvEngineCompliancePolicyResponse,
)
def get_cv_engine_compliance_policy(
    _admin_session: AdminSessionDep,
) -> AdminCvEngineCompliancePolicyResponse:
    return AdminCvEngineCompliancePolicyResponse(policy=CompliancePolicy())
