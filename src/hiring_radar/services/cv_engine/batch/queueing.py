from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from hiring_radar.services.cv_engine.batch.models import BatchParseRequest


@dataclass(order=True)
class _PrioritizedRequest:
    priority: int
    ordinal: int
    request: BatchParseRequest = field(compare=False)


class BatchRequestPriorityQueue:
    """Stable priority queue for batch parse requests."""

    def __init__(self) -> None:
        self._heap: list[_PrioritizedRequest] = []
        self._ordinal = 0

    def push(self, request: BatchParseRequest) -> None:
        heapq.heappush(
            self._heap,
            _PrioritizedRequest(
                priority=request.priority,
                ordinal=self._ordinal,
                request=request,
            ),
        )
        self._ordinal += 1

    def pop(self) -> BatchParseRequest:
        item = heapq.heappop(self._heap)
        return item.request

    def __len__(self) -> int:
        return len(self._heap)
