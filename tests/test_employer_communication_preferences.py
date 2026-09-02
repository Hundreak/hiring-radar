from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from hiring_radar.db.employer_repository import EmployerRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.employer_auth import hash_password


def _csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token
    return {CSRF_HEADER_NAME: token}


def _register_owner(client: TestClient, *, company: str = "Comms Co") -> dict:
    response = client.post(
        "/api/employer/auth/register",
        json={
            "company_name": company,
            "company_email": f"owner@{company.lower().replace(' ', '')}.example",
            "password": "Admin12345!",
            "password_confirmation": "Admin12345!",
            "full_name": "Owner User",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_employer_communication_preferences_default_and_update(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-communication-preferences.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())
    auth = _register_owner(client)

    initial = client.get("/api/employer/settings/communication-preferences")
    assert initial.status_code == 200, initial.text
    payload = initial.json()
    assert payload["company_id"] == auth["company_id"]
    assert payload["preferences"]["candidate_alerts_enabled"] is True
    assert payload["preferences"]["security_alerts_enabled"] is True
    assert payload["preferences"]["route_weekly_digest_to"] == "owner"
    assert payload["team_summary"]["active_members"] == 1
    assert payload["team_summary"]["roles"]["owner"] == 1

    updated = client.patch(
        "/api/employer/settings/communication-preferences",
        json={
            "weekly_leadership_digest_enabled": True,
            "security_alerts_enabled": False,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "21:30",
            "quiet_hours_end": "08:15",
            "timezone": "Europe/Istanbul",
            "default_channel": "email_and_in_app",
            "notification_emails": ["People@Example.com"],
            "route_campaign_review_to": "admin",
        },
        headers=_csrf_headers(client),
    )
    assert updated.status_code == 200, updated.text
    preferences = updated.json()["preferences"]
    assert preferences["weekly_leadership_digest_enabled"] is True
    assert preferences["security_alerts_enabled"] is True
    assert preferences["quiet_hours_enabled"] is True
    assert preferences["quiet_hours_start"] == "21:30"
    assert preferences["quiet_hours_end"] == "08:15"
    assert preferences["default_channel"] == "email_and_in_app"
    assert preferences["notification_emails"] == ["people@example.com"]
    assert preferences["route_campaign_review_to"] == "admin"

    connection = initialize_database(db_path)
    repository = EmployerRepository(connection)
    try:
        persisted = repository.get_company_communication_preferences(auth["company_id"])
        assert persisted is not None
        assert persisted["weekly_leadership_digest_enabled"] is True
        assert persisted["security_alerts_enabled"] is True
        activity = repository.list_dashboard_activity(auth["company_id"], limit=5)
        assert any(item["event_type"] == "employer.settings.communication_preferences.updated" for item in activity)
    finally:
        close_connection(connection)


def test_employer_communication_preferences_requires_manager_role(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-communication-preferences-rbac.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    owner_client = TestClient(create_app())
    auth = _register_owner(owner_client, company="Comms RBAC")

    connection = initialize_database(db_path)
    repository = EmployerRepository(connection)
    try:
        viewer = repository.create_user(
            email="viewer@commsrbac.example",
            full_name="Viewer User",
            password_hash=hash_password("Viewer12345!"),
        )
        repository.add_team_member(
            company_id=auth["company_id"],
            user_id=viewer.id,
            role_key="viewer",
            status="active",
        )
    finally:
        close_connection(connection)

    viewer_client = TestClient(create_app())
    login = viewer_client.post(
        "/api/employer/auth/login",
        json={"email": "viewer@commsrbac.example", "password": "Viewer12345!"},
    )
    assert login.status_code == 200, login.text

    readable = viewer_client.get("/api/employer/settings/communication-preferences")
    assert readable.status_code == 200, readable.text

    denied = viewer_client.patch(
        "/api/employer/settings/communication-preferences",
        json={"weekly_leadership_digest_enabled": True},
        headers=_csrf_headers(viewer_client),
    )
    assert denied.status_code == 403
