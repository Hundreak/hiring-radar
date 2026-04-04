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
    assert "Dashboard" in response.text


def test_admin_jobs_shell_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/jobs")

    assert response.status_code == 200
    assert "Jobs" in response.text


def test_admin_crawl_runs_shell_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/crawl-runs")

    assert response.status_code == 200
    assert "Crawl Runs" in response.text


def test_admin_notification_runs_shell_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/notification-runs")

    assert response.status_code == 200
    assert "Notification Runs" in response.text


def test_admin_subscribers_shell_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/subscribers")

    assert response.status_code == 200
    assert "Subscribers" in response.text


def test_admin_settings_shell_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/admin/settings")

    assert response.status_code == 200
    assert "Settings" in response.text