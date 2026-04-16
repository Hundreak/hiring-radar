from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from hiring_radar.services.cv_engine.batch.models import (
    BatchParseRequest,
    BatchParseResult,
    BatchRetryPolicy,
    BatchRunSummary,
    ProgressEvent,
)
from hiring_radar.services.cv_engine.batch.processor import CvBatchProcessor
from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.enterprise.runtime import (
    enrich_and_store_parser_result,
    get_cached_parser_result_for_text,
)
from hiring_radar.services.cv_engine.legacy_runtime import (
    build_foundation_parser_result_from_text,
)

FOUNDATION_PARSER_VERSION = "cv_engine_v2"
from hiring_radar.services.cv_engine.telemetry.metrics import get_cv_engine_metrics_registry
from hiring_radar.services.cv_extraction import (
    extract_text_from_cv_file,
    normalize_extracted_text,
)


class StoredBatchRun(BaseModel):
    """Persisted in-memory representation of one admin batch execution."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str
    created_at: str
    finished_at: str | None = None
    request_count: int = 0
    status: str = "running"
    results: list[BatchParseResult] = Field(default_factory=list)
    summary: BatchRunSummary | None = None
    progress_events: list[ProgressEvent] = Field(default_factory=list)


class InMemoryBatchRunRegistry:
    """Thread-safe in-memory registry for recent admin batch runs."""

    def __init__(self) -> None:
        self._items: dict[str, StoredBatchRun] = {}
        self._lock = Lock()

    def put(self, run: StoredBatchRun) -> None:
        with self._lock:
            self._items[run.batch_id] = run

    def get(self, batch_id: str) -> StoredBatchRun | None:
        with self._lock:
            item = self._items.get(batch_id)
            if item is None:
                return None
            return item.model_copy(deep=True)

    def list_recent(self, limit: int = 20) -> list[StoredBatchRun]:
        with self._lock:
            items = list(self._items.values())
        items.sort(key=lambda item: item.created_at, reverse=True)
        return [item.model_copy(deep=True) for item in items[:limit]]


_BATCH_REGISTRY = InMemoryBatchRunRegistry()


def get_batch_run_registry() -> InMemoryBatchRunRegistry:
    """Return singleton registry for admin batch operations."""
    return _BATCH_REGISTRY


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


async def _parse_cv_source_path(source_path: str) -> dict[str, Any]:
    """Parse one file path using the current enterprise-aware foundation runtime."""
    extraction_result = extract_text_from_cv_file(source_path)
    normalized_text = normalize_extracted_text(extraction_result.extracted_text)
    if normalized_text is None:
        return {
            "filename": Path(source_path).name,
            "parser_version": FOUNDATION_PARSER_VERSION,
            "parse_status": extraction_result.parse_status,
            "quality_band": "low",
            "warning_codes": ["no_text_detected"],
            "enterprise": {},
        }

    config = ParserRuntimeConfig()
    cached = get_cached_parser_result_for_text(
        extracted_text=normalized_text,
        config=config,
    )
    result = cached
    if result is None:
        result = build_foundation_parser_result_from_text(
            extracted_text=normalized_text,
            filename=Path(source_path).name,
            used_ocr=bool(extraction_result.page_count == 1 and Path(source_path).suffix.lower() in {".png", ".jpg", ".jpeg"}),
            extraction_method="admin_batch_runtime",
            page_count=extraction_result.page_count,
            config=config,
        )
        result = enrich_and_store_parser_result(
            result=result,
            extracted_text=normalized_text,
            config=config,
        )

    quality_band = (
        result.context.quality.quality_band if result.context.quality is not None else None
    )
    warning_codes = [item.code for item in result.context.warnings]
    parsed = result.context.parsed_data
    enterprise = dict(result.context.metadata.get("enterprise", {}))
    return {
        "filename": Path(source_path).name,
        "parser_version": FOUNDATION_PARSER_VERSION,
        "parse_status": extraction_result.parse_status,
        "quality_band": quality_band,
        "warning_codes": warning_codes,
        "full_name": parsed.full_name if parsed is not None else None,
        "skill_count": len(parsed.skills) if parsed is not None else 0,
        "enterprise": enterprise,
    }


async def run_admin_batch_parse(
    *,
    requests: list[BatchParseRequest],
    retry_policy: BatchRetryPolicy | None = None,
) -> StoredBatchRun:
    """Execute one admin batch parse and store its terminal result."""
    batch_id = uuid4().hex
    created_at = _utc_now_iso()
    run = StoredBatchRun(
        batch_id=batch_id,
        created_at=created_at,
        request_count=len(requests),
    )
    registry = get_batch_run_registry()
    registry.put(run)

    progress_events: list[ProgressEvent] = []

    async def _progress_callback(event: ProgressEvent) -> None:
        progress_events.append(event)

    processor = CvBatchProcessor(
        parser=_parse_cv_source_path,
        retry_policy=retry_policy,
    )
    results, summary = await processor.collect_many(
        requests,
        progress_callback=_progress_callback,
    )
    finished_at = _utc_now_iso()
    final_run = StoredBatchRun(
        batch_id=batch_id,
        created_at=created_at,
        finished_at=finished_at,
        request_count=len(requests),
        status="completed",
        results=results,
        summary=summary,
        progress_events=progress_events,
    )
    registry.put(final_run)

    metrics = get_cv_engine_metrics_registry()
    metrics.increment("cv_engine.admin_batch_runs_total")
    metrics.increment("cv_engine.admin_batch_items_total", len(requests))
    metrics.increment("cv_engine.admin_batch_succeeded_total", summary.succeeded_items)
    metrics.increment("cv_engine.admin_batch_failed_total", summary.failed_items)
    metrics.observe("cv_engine.admin_batch_duration_ms", summary.duration_ms)
    return final_run
