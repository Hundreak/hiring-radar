from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from hiring_radar.api.routers.user_ai import router as user_ai_router
from hiring_radar.services.ai.contracts import AiHealthCheckResult


def test_user_ai_health_endpoint_returns_disabled_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_ENABLED", "false")

    app = FastAPI()
    app.include_router(user_ai_router)
    client = TestClient(app)

    response = client.get("/api/user/ai/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is False
    assert payload["runtime_status"] == "disabled"
    assert payload["reachable"] is False


def test_user_ai_health_endpoint_maps_runtime_health(monkeypatch: pytest.MonkeyPatch) -> None:
    from hiring_radar.api.routers import user_ai as user_ai_module

    class StubService:
        def health(self) -> AiHealthCheckResult:
            return AiHealthCheckResult(
                enabled=True,
                runtime="ollama",
                base_url="http://127.0.0.1:11434",
                configured_model="llama3.1:8b",
                runtime_status="ready",
                reachable=True,
                local_only_guard=True,
                response_time_ms=42,
                available_models=["llama3.1:8b"],
                running_models=["llama3.1:8b"],
                message="Local Ollama runtime is reachable.",
            )

    monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: StubService())

    app = FastAPI()
    app.include_router(user_ai_router)
    client = TestClient(app)

    response = client.get("/api/user/ai/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_status"] == "ready"
    assert payload["reachable"] is True
    assert payload["configured_model"] == "llama3.1:8b"
    assert payload["response_time_ms"] == 42
