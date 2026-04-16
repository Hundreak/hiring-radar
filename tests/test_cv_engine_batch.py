from __future__ import annotations

import asyncio

from hiring_radar.services.cv_engine.batch.models import (
    BatchParseRequest,
    BatchRetryPolicy,
)
from hiring_radar.services.cv_engine.batch.processor import CvBatchProcessor


def test_batch_processor_respects_priority_order() -> None:
    processed: list[str] = []

    async def _parser(source_path: str) -> dict[str, str]:
        processed.append(source_path)
        return {"source_path": source_path}

    processor = CvBatchProcessor(parser=_parser)
    requests = [
        BatchParseRequest(request_id="normal", source_path="normal.pdf", priority=50),
        BatchParseRequest(request_id="urgent", source_path="urgent.pdf", priority=10),
    ]

    results, summary = asyncio.run(processor.collect_many(requests))

    assert [item.source_path for item in results] == ["urgent.pdf", "normal.pdf"]
    assert processed == ["urgent.pdf", "normal.pdf"]
    assert summary.succeeded_items == 2
    assert summary.failed_items == 0


def test_batch_processor_retries_retryable_failures() -> None:
    attempts = {"count": 0}

    async def _parser(source_path: str) -> dict[str, str]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary parser failure")
        return {"source_path": source_path}

    processor = CvBatchProcessor(
        parser=_parser,
        retry_policy=BatchRetryPolicy(max_attempts=2, base_delay_seconds=0.0),
    )

    results, summary = asyncio.run(
        processor.collect_many(
            [BatchParseRequest(request_id="one", source_path="cv.pdf")]
        )
    )

    assert attempts["count"] == 2
    assert results[0].status.value == "succeeded"
    assert results[0].attempts == 2
    assert summary.succeeded_items == 1
    assert summary.failed_items == 0


def test_batch_processor_creates_dead_letter_after_exhausted_retries() -> None:
    async def _parser(_source_path: str) -> dict[str, str]:
        raise ValueError("non-retryable parser failure")

    processor = CvBatchProcessor(
        parser=_parser,
        retry_policy=BatchRetryPolicy(max_attempts=3, base_delay_seconds=0.0),
    )

    results, summary = asyncio.run(
        processor.collect_many(
            [BatchParseRequest(request_id="broken", source_path="broken.pdf")]
        )
    )

    assert results[0].status.value == "failed"
    assert results[0].attempts == 1
    assert summary.failed_items == 1
    assert len(summary.dead_letters) == 1
    assert summary.dead_letters[0].request_id == "broken"


def test_batch_processor_emits_progress_events() -> None:
    progress_events: list[str] = []

    async def _parser(source_path: str) -> dict[str, str]:
        return {"source_path": source_path}

    async def _progress_callback(event) -> None:
        progress_events.append(event.event_type.value)

    processor = CvBatchProcessor(parser=_parser)
    asyncio.run(
        processor.collect_many(
            [BatchParseRequest(request_id="one", source_path="one.pdf")],
            progress_callback=_progress_callback,
        )
    )

    assert progress_events[0] == "started"
    assert "item_completed" in progress_events
    assert progress_events[-1] == "finished"