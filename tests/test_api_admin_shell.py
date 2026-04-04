from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app


def test_admin_login_shell_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/login")

    assert response.status_code == 200
    assert "Hiring Radar Admin Login" in response.text


def test_admin_dashboard_shell_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/dashboard")

    assert response.status_code == 200
    assert "Hiring Radar Admin Dashboard" in response.text