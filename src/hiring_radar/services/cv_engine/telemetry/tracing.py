from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass(slots=True)
class TraceSpan:
    """One recorded in-memory trace span."""

    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


class InMemoryTracer:
    """Very small tracing helper for local parser instrumentation."""

    def __init__(self) -> None:
        self.spans: list[TraceSpan] = []

    def start_span(self, name: str, **attributes: Any):
        """Create a context manager that records one span."""
        tracer = self

        class _SpanContextManager:
            def __enter__(self) -> TraceSpan:
                self._started_at = perf_counter()
                self._span = TraceSpan(name=name, attributes=dict(attributes))
                return self._span

            def __exit__(self, exc_type, exc, tb) -> None:
                self._span.duration_ms = (perf_counter() - self._started_at) * 1000.0
                if exc is not None:
                    self._span.attributes["error_type"] = exc.__class__.__name__
                tracer.spans.append(self._span)
                return None

        return _SpanContextManager()
