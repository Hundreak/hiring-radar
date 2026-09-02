from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app

_STRONG_SECRET = "x" * 48


def test_employer_demo_dashboard_accepts_mock_token_in_local_demo(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HIRING_RADAR_ENV", "development")
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(tmp_path / "local-demo.db"))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_DEMO_MODE", "true")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH", "true")

    client = TestClient(create_app())

    response = client.get(
        "/api/employer/dashboard/stats",
        headers={"Authorization": "Bearer mock_token_demo"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True


def test_employer_mock_token_is_rejected_when_demo_mode_is_off(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HIRING_RADAR_ENV", "development")
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(tmp_path / "demo-off.db"))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_DEMO_MODE", "false")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH", "true")

    client = TestClient(create_app())

    response = client.get(
        "/api/employer/dashboard/stats",
        headers={"Authorization": "Bearer mock_token_demo"},
    )

    assert response.status_code == 401


def test_employer_dashboard_uses_real_empty_state_in_production(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(tmp_path / "production.db"))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", _STRONG_SECRET)
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_DEMO_MODE", "true")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH", "true")

    client = TestClient(create_app())
    register = client.post(
        "/api/employer/auth/register",
        json={
            "company_name": "Production Co",
            "company_email": "owner@production.example",
            "password": "Admin12345!",
            "password_confirmation": "Admin12345!",
            "full_name": "Owner User",
        },
    )
    assert register.status_code == 200, register.text
    token = register.json()["access_token"]

    response = client.get(
        "/api/employer/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["stats"]["active_jobs"] == 0
    assert response.json()["stats"]["total_applications"] == 0

    mock_response = client.get(
        "/api/employer/dashboard/stats",
        headers={"Authorization": "Bearer mock_token_demo"},
    )
    assert mock_response.status_code == 401


def test_employer_runtime_endpoint_reports_safe_flags(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(tmp_path / "runtime.db"))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_DEMO_MODE", "true")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH", "true")

    client = TestClient(create_app())
    response = client.get("/api/employer/runtime")

    assert response.status_code == 200
    assert response.json()["production"] is True
    assert response.json()["demo_mode_enabled"] is False
    assert response.json()["mock_auth_enabled"] is False
    assert response.json()["data_mode"] == "production"
