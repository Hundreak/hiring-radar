from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(slots=True)
class CounterMetric:
    """Simple monotonically increasing metric."""

    count: int = 0


@dataclass(slots=True)
class TimingMetric:
    """Aggregated timing metric summary."""

    observations: list[float] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(self.observations)

    @property
    def average(self) -> float:
        if not self.observations:
            return 0.0
        return self.total / len(self.observations)


class InMemoryMetricsRegistry:
    """Minimal in-memory metrics registry for parser observability."""

    def __init__(self) -> None:
        self._counters: defaultdict[str, CounterMetric] = defaultdict(CounterMetric)
        self._timings: defaultdict[str, TimingMetric] = defaultdict(TimingMetric)

    def increment(self, name: str, value: int = 1) -> None:
        """Increase a counter metric by the given value."""
        self._counters[name].count += value

    def observe(self, name: str, value: float) -> None:
        """Record one timing observation."""
        self._timings[name].observations.append(value)

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        """Return a JSON-friendly metrics snapshot."""
        payload: dict[str, dict[str, float | int]] = {}
        for name, metric in self._counters.items():
            payload[name] = {"count": metric.count}
        for name, metric in self._timings.items():
            payload[name] = {
                "count": len(metric.observations),
                "total": round(metric.total, 3),
                "average": round(metric.average, 3),
            }
        return payload

    def reset(self) -> None:
        """Clear all in-memory metrics for deterministic tests."""
        self._counters.clear()
        self._timings.clear()


_METRICS_REGISTRY = InMemoryMetricsRegistry()


def get_cv_engine_metrics_registry() -> InMemoryMetricsRegistry:
    """Return the singleton metrics registry used by the CV engine."""
    return _METRICS_REGISTRY
