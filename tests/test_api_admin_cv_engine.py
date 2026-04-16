from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_admin_session
from hiring_radar.api.routers import admin_cv_engine
from hiring_radar.api.security import AdminSession
from hiring_radar.services.cv_engine.batch.admin_runtime import get_batch_run_registry
from hiring_radar.services.cv_engine.batch.models import (
    BatchParseResult,
    BatchParseStatus,
    BatchRunSummary,
)
from hiring_radar.services.cv_engine.telemetry.metrics import (
    get_cv_engine_metrics_registry,
)


def _make_admin_session() -> AdminSession:
    return AdminSession(
        email="admin@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T22:00:00Z",
    )


def test_admin_cv_engine_batch_endpoints_return_summary_and_list(
    monkeypatch: object,
) -> None:
    app = create_app()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    async def _fake_parser(_source_path: str) -> dict[str, object]:
        return {
            "filename": "cv.pdf",
            "parser_version": "cv_engine_v2",
            "parse_status": "parsed",
            "quality_band": "high",
            "warning_codes": [],
            "full_name": "Alice Example",
            "skill_count": 3,
            "enterprise": {"cache": {"status": "miss"}},
        }

    monkeypatch.setattr(admin_cv_engine, "run_admin_batch_parse", None, raising=False)
    from hiring_radar.services.cv_engine.batch import admin_runtime

    async def _run_admin_batch_parse(*, requests, retry_policy=None):
        del retry_policy
        processor_results = []
        for req in requests:
            processor_results.append(
                BatchParseResult(
                    request_id=req.request_id,
                    source_path=req.source_path,
                    status=BatchParseStatus.SUCCEEDED,
                    attempts=1,
                    duration_ms=1.0,
                    output=await _fake_parser(req.source_path),
                )
            )
        summary = BatchRunSummary(
            total_items=len(requests),
            succeeded_items=len(requests),
            failed_items=0,
            partial_items=0,
            duration_ms=1.0,
            dead_letters=[],
        )
        run = admin_runtime.StoredBatchRun(
            batch_id="batch-test-1",
            created_at="2026-04-08T12:00:00Z",
            finished_at="2026-04-08T12:00:01Z",
            request_count=len(requests),
            status="completed",
            results=processor_results,
            summary=summary,
            progress_events=[],
        )
        get_batch_run_registry().put(run)
        get_cv_engine_metrics_registry().increment("cv_engine.admin_batch_runs_total")
        return run

    monkeypatch.setattr(admin_cv_engine, "run_admin_batch_parse", _run_admin_batch_parse)

    client = TestClient(app)
    response = client.post(
        "/api/admin/cv-engine/batches",
        json={
            "items": [
                {
                    "request_id": "one",
                    "source_path": str(Path("/tmp/cv.pdf")),
                    "priority": 50,
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == "batch-test-1"
    assert payload["summary"]["succeeded_items"] == 1
    assert payload["results"][0]["output"]["quality_band"] == "high"

    status_response = client.get("/api/admin/cv-engine/batches/batch-test-1")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    list_response = client.get("/api/admin/cv-engine/batches")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["batches"][0]["batch_id"] == "batch-test-1"
    assert list_payload["batches"][0]["succeeded_items"] == 1


def test_admin_cv_engine_health_metrics_and_compliance_endpoints() -> None:
    app = create_app()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session
    client = TestClient(app)

    health_response = client.get("/api/admin/cv-engine/health")
    assert health_response.status_code == 200
    assert "health" in health_response.json()
    assert "metrics" in health_response.json()

    metrics_response = client.get("/api/admin/cv-engine/metrics")
    assert metrics_response.status_code == 200
    assert "metrics" in metrics_response.json()

    policy_response = client.get("/api/admin/cv-engine/compliance/policy")
    assert policy_response.status_code == 200
    assert policy_response.json()["policy"]["enable_parse_audit"] is True
