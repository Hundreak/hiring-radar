from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_admin_auth_settings
from hiring_radar.api.security import AdminAuthSettings


def _make_auth_settings() -> AdminAuthSettings:
    return AdminAuthSettings(
        email="admin@example.com",
        password="super-secret",
        session_secret="test-session-secret",
        session_ttl_seconds=3600,
    )


def test_admin_login_sets_session_cookie_and_me_returns_identity() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)

    login_response = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "super-secret"},
    )

    assert login_response.status_code == 200
    assert login_response.json() == {
        "email": "admin@example.com",
        "authenticated": True,
    }

    me_response = client.get("/api/admin/auth/me")

    assert me_response.status_code == 200
    assert me_response.json() == {
        "email": "admin@example.com",
        "authenticated": True,
    }


def test_admin_login_rejects_invalid_credentials() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)

    response = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid admin credentials."}


def test_admin_logout_invalidates_session() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)

    client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "super-secret"},
    )
    logout_response = client.post("/api/admin/auth/logout")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"ok": True}

    me_response = client.get("/api/admin/auth/me")
    assert me_response.status_code == 401
    assert me_response.json() == {"detail": "Not authenticated."}


def test_admin_me_requires_authentication() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)

    response = client.get("/api/admin/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}
