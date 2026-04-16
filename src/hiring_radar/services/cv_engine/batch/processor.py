from __future__ import annotations

import inspect
import time
from collections.abc import AsyncIterator, Iterable
from typing import Any, Awaitable, Callable

from hiring_radar.services.cv_engine.batch.models import (
    BatchParseRequest,
    BatchParseResult,
    BatchParseStatus,
    BatchRetryPolicy,
    BatchRunSummary,
    DeadLetterRecord,
    ProgressEvent,
    ProgressEventType,
)
from hiring_radar.services.cv_engine.batch.progress import ProgressCallback, emit_progress
from hiring_radar.services.cv_engine.batch.queueing import BatchRequestPriorityQueue
from hiring_radar.services.cv_engine.batch.retry import (
    compute_retry_delay_seconds,
    is_retryable_exception,
)

ParserCallable = Callable[[str], Any | Awaitable[Any]]


class CvBatchProcessor:
    """Streaming batch processor for CV parsing workloads."""

    def __init__(
        self,
        *,
        parser: ParserCallable,
        retry_policy: BatchRetryPolicy | None = None,
    ) -> None:
        self._parser = parser
        self._retry_policy = retry_policy or BatchRetryPolicy()
        self.dead_letters: list[DeadLetterRecord] = []

    async def parse_many(
        self,
        requests: Iterable[BatchParseRequest],
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> AsyncIterator[BatchParseResult]:
        """Yield batch results in priority order as they complete."""
        queue = BatchRequestPriorityQueue()
        items = list(requests)
        for request in items:
            queue.push(request)

        total_items = len(items)
        succeeded_items = 0
        failed_items = 0
        partial_items = 0
        started_at = time.perf_counter()

        await emit_progress(
            progress_callback,
            ProgressEvent(
                event_type=ProgressEventType.STARTED,
                completed_items=0,
                total_items=total_items,
            ),
        )

        while len(queue):
            request = queue.pop()
            result = await self._parse_one(request)

            if result.status == BatchParseStatus.SUCCEEDED:
                succeeded_items += 1
                event_type = ProgressEventType.ITEM_COMPLETED
            elif result.status == BatchParseStatus.PARTIAL:
                partial_items += 1
                event_type = ProgressEventType.ITEM_COMPLETED
            else:
                failed_items += 1
                event_type = ProgressEventType.ITEM_FAILED

            completed_items = succeeded_items + failed_items + partial_items
            await emit_progress(
                progress_callback,
                ProgressEvent(
                    event_type=event_type,
                    completed_items=completed_items,
                    total_items=total_items,
                    succeeded_items=succeeded_items,
                    failed_items=failed_items,
                    current_request_id=result.request_id,
                    current_source_path=result.source_path,
                ),
            )
            yield result

        total_duration_ms = (time.perf_counter() - started_at) * 1000.0
        await emit_progress(
            progress_callback,
            ProgressEvent(
                event_type=ProgressEventType.FINISHED,
                completed_items=total_items,
                total_items=total_items,
                succeeded_items=succeeded_items,
                failed_items=failed_items,
                metadata={
                    "partial_items": partial_items,
                    "duration_ms": round(total_duration_ms, 3),
                },
            ),
        )

    async def collect_many(
        self,
        requests: Iterable[BatchParseRequest],
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[list[BatchParseResult], BatchRunSummary]:
        """Collect all parse results and return a terminal summary."""
        started_at = time.perf_counter()
        results: list[BatchParseResult] = []
        async for result in self.parse_many(
            requests,
            progress_callback=progress_callback,
        ):
            results.append(result)

        succeeded = sum(1 for item in results if item.status == BatchParseStatus.SUCCEEDED)
        partial = sum(1 for item in results if item.status == BatchParseStatus.PARTIAL)
        failed = sum(1 for item in results if item.status == BatchParseStatus.FAILED)
        summary = BatchRunSummary(
            total_items=len(results),
            succeeded_items=succeeded,
            partial_items=partial,
            failed_items=failed,
            duration_ms=(time.perf_counter() - started_at) * 1000.0,
            dead_letters=list(self.dead_letters),
        )
        return results, summary

    async def _parse_one(self, request: BatchParseRequest) -> BatchParseResult:
        attempts = 0
        started_at = time.perf_counter()
        while attempts < self._retry_policy.max_attempts:
            attempts += 1
            try:
                output = self._parser(request.source_path)
                if inspect.isawaitable(output):
                    output = await output
                return BatchParseResult(
                    request_id=request.request_id,
                    source_path=request.source_path,
                    status=BatchParseStatus.SUCCEEDED,
                    attempts=attempts,
                    duration_ms=(time.perf_counter() - started_at) * 1000.0,
                    output=output,
                    metadata=dict(request.metadata),
                )
            except BaseException as exc:  # pragma: no cover - exercised by tests
                can_retry = (
                    attempts < self._retry_policy.max_attempts
                    and is_retryable_exception(exc, self._retry_policy)
                )
                if can_retry:
                    delay = compute_retry_delay_seconds(attempts - 1, self._retry_policy)
                    if delay > 0:
                        await self._sleep(delay)
                    continue

                dead_letter = DeadLetterRecord(
                    request_id=request.request_id,
                    source_path=request.source_path,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    attempts_exhausted=attempts,
                    metadata=dict(request.metadata),
                )
                self.dead_letters.append(dead_letter)
                return BatchParseResult(
                    request_id=request.request_id,
                    source_path=request.source_path,
                    status=BatchParseStatus.FAILED,
                    attempts=attempts,
                    duration_ms=(time.perf_counter() - started_at) * 1000.0,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    metadata=dict(request.metadata),
                )

        raise AssertionError("unreachable")

    async def _sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        import asyncio

        await asyncio.sleep(seconds)
