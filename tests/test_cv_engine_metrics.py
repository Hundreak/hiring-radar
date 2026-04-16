from __future__ import annotations

from hiring_radar.services.cv_engine.telemetry.health import build_cv_engine_health_report
from hiring_radar.services.cv_engine.telemetry.metrics import InMemoryMetricsRegistry
from hiring_radar.services.cv_engine.telemetry.tracing import InMemoryTracer


def test_metrics_registry_collects_counters_and_timings() -> None:
    registry = InMemoryMetricsRegistry()
    registry.increment("parse_status_total")
    registry.increment("parse_status_total", 2)
    registry.observe("parse_duration_ms", 100.0)
    registry.observe("parse_duration_ms", 50.0)

    snapshot = registry.snapshot()

    assert snapshot["parse_status_total"]["count"] == 3
    assert snapshot["parse_duration_ms"]["count"] == 2
    assert snapshot["parse_duration_ms"]["average"] == 75.0


def test_in_memory_tracer_records_span_duration() -> None:
    tracer = InMemoryTracer()

    with tracer.start_span("entity_extraction", stage="entity_extraction") as span:
        assert span.name == "entity_extraction"

    assert len(tracer.spans) == 1
    assert tracer.spans[0].duration_ms >= 0.0
    assert tracer.spans[0].attributes["stage"] == "entity_extraction"


def test_health_report_contains_required_dependency_checks() -> None:
    report = build_cv_engine_health_report()

    assert report.status in {"healthy", "degraded"}
    dependency_names = {item.dependency_name for item in report.dependency_checks}
    assert "pydantic" in dependency_names
