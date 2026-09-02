from __future__ import annotations

import logging
from dataclasses import dataclass

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.retrieval.ingestion import (
    INGESTION_ACTION_SKIPPED,
    PreparedRetrievalDocument,
    RetrievalIngestionResult,
    build_ai_audit_prepared_document,
    build_cv_prepared_document,
    build_profile_prepared_document,
    ingest_prepared_document,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RetrievalRefreshResult:
    source_type: str
    source_ref: str
    action: str
    source_status: str | None
    document_status: str | None
    chunk_count: int
    reason: str | None = None

    @classmethod
    def from_ingestion(
        cls,
        *,
        prepared: PreparedRetrievalDocument,
        result: RetrievalIngestionResult,
    ) -> RetrievalRefreshResult:
        return cls(
            source_type=prepared.source_type,
            source_ref=prepared.source_ref,
            action=result.action,
            source_status=result.source.status if result.source is not None else None,
            document_status=result.document.status if result.document is not None else None,
            chunk_count=result.chunk_count,
            reason=result.reason,
        )



def refresh_profile_retrieval(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    locale: str | None = None,
) -> RetrievalRefreshResult:
    prepared = build_profile_prepared_document(
        repository,
        subscriber_id=subscriber_id,
        locale=locale,
    )
    result = ingest_prepared_document(repository, prepared)
    return RetrievalRefreshResult.from_ingestion(prepared=prepared, result=result)



def refresh_cv_upload_retrieval(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload_id: int,
    locale: str | None = None,
) -> RetrievalRefreshResult:
    prepared = build_cv_prepared_document(
        repository,
        subscriber_id=subscriber_id,
        cv_upload_id=cv_upload_id,
        locale=locale,
    )
    if prepared is None:
        return RetrievalRefreshResult(
            source_type="cv_upload",
            source_ref=f"cv_upload:{cv_upload_id}",
            action=INGESTION_ACTION_SKIPPED,
            source_status=None,
            document_status=None,
            chunk_count=0,
            reason="upload_not_found",
        )
    result = ingest_prepared_document(repository, prepared)
    return RetrievalRefreshResult.from_ingestion(prepared=prepared, result=result)



def refresh_ai_audit_retrieval(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    locale: str | None = None,
) -> RetrievalRefreshResult:
    prepared = build_ai_audit_prepared_document(
        repository,
        subscriber_id=subscriber_id,
        locale=locale,
    )
    if prepared is None:
        return RetrievalRefreshResult(
            source_type="ai_audit",
            source_ref=f"subscriber:{subscriber_id}:ai-audit",
            action=INGESTION_ACTION_SKIPPED,
            source_status=None,
            document_status=None,
            chunk_count=0,
            reason="no_audit_events",
        )
    result = ingest_prepared_document(repository, prepared)
    return RetrievalRefreshResult.from_ingestion(prepared=prepared, result=result)



def refresh_profile_retrieval_safe(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    locale: str | None = None,
) -> RetrievalRefreshResult | None:
    try:
        return refresh_profile_retrieval(
            repository,
            subscriber_id=subscriber_id,
            locale=locale,
        )
    except Exception:
        logger.exception(
            "Profile retrieval refresh failed.",
            extra={"subscriber_id": subscriber_id},
        )
        return None



def refresh_cv_upload_retrieval_safe(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload_id: int,
    locale: str | None = None,
) -> RetrievalRefreshResult | None:
    try:
        return refresh_cv_upload_retrieval(
            repository,
            subscriber_id=subscriber_id,
            cv_upload_id=cv_upload_id,
            locale=locale,
        )
    except Exception:
        logger.exception(
            "CV retrieval refresh failed.",
            extra={"subscriber_id": subscriber_id, "cv_upload_id": cv_upload_id},
        )
        return None



def refresh_profile_and_cv_retrieval_safe(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload_id: int | None = None,
    locale: str | None = None,
) -> tuple[RetrievalRefreshResult | None, RetrievalRefreshResult | None]:
    profile_result = refresh_profile_retrieval_safe(
        repository,
        subscriber_id=subscriber_id,
        locale=locale,
    )
    cv_result: RetrievalRefreshResult | None = None
    if cv_upload_id is not None:
        cv_result = refresh_cv_upload_retrieval_safe(
            repository,
            subscriber_id=subscriber_id,
            cv_upload_id=cv_upload_id,
            locale=locale,
        )
    return profile_result, cv_result
