from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME


def _csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token
    return {CSRF_HEADER_NAME: token}


def test_employer_register_login_me_and_logout(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-auth.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())

    register = client.post(
        "/api/employer/auth/register",
        json={
            "company_name": "NoyTera Teknoloji",
            "company_email": "owner@noytera.com",
            "password": "Admin12345!",
            "password_confirmation": "Admin12345!",
            "full_name": "Owner User",
            "default_locale": "tr",
        },
    )
    assert register.status_code == 200, register.text
    data = register.json()
    assert data["ok"] is True
    assert data["company_id"] > 0
    assert data["role_key"] == "owner"
    assert "hiring_radar_employer_session" in register.cookies

    me = client.get("/api/employer/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "owner@noytera.com"
    assert me.json()["company"]["name"] == "NoyTera Teknoloji"

    logout = client.post("/api/employer/auth/logout", headers=_csrf_headers(client))
    assert logout.status_code == 200

    denied = client.get("/api/employer/auth/me")
    assert denied.status_code == 401

    login = client.post(
        "/api/employer/auth/login",
        json={"email": "owner@noytera.com", "password": "Admin12345!"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["role_key"] == "owner"

    dashboard = client.get("/api/employer/dashboard/stats")
    assert dashboard.status_code == 200, dashboard.text


def test_employer_team_invite_and_role_update(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-team.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())
    response = client.post(
        "/api/employer/auth/register",
        json={
            "company_name": "Radar Labs",
            "company_email": "owner@radarlabs.com",
            "password": "Admin12345!",
            "password_confirmation": "Admin12345!",
        },
    )
    assert response.status_code == 200, response.text

    team = client.get("/api/employer/team")
    assert team.status_code == 200, team.text
    payload = team.json()
    assert {role["role_key"] for role in payload["roles"]} >= {"owner", "admin", "recruiter", "viewer"}
    assert len(payload["members"]) == 1
    assert payload["members"][0]["role_key"] == "owner"

    invited = client.post(
        "/api/employer/team/invitations",
        json={"email": "recruiter@radarlabs.com", "role_key": "recruiter"},
        headers=_csrf_headers(client),
    )
    assert invited.status_code == 200, invited.text
    invited_member = invited.json()["member"]
    assert invited_member["status"] == "invited"
    assert invited_member["role_key"] == "recruiter"

    updated = client.patch(
        f"/api/employer/team/members/{invited_member['id']}",
        json={"role_key": "hiring_manager", "status": "disabled"},
        headers=_csrf_headers(client),
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["member"]["role_key"] == "hiring_manager"
    assert updated.json()["member"]["status"] == "disabled"


def test_employer_auth_rejects_duplicate_and_invalid_password(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-duplicates.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())
    payload = {
        "company_name": "Acme",
        "company_email": "owner@acme.com",
        "password": "Admin12345!",
        "password_confirmation": "Admin12345!",
    }
    assert client.post("/api/employer/auth/register", json=payload).status_code == 200
    assert client.post("/api/employer/auth/register", json=payload).status_code == 409

    bad_login = client.post(
        "/api/employer/auth/login",
        json={"email": "owner@acme.com", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401
