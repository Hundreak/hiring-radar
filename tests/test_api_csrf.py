from __future__ import annotations

from fastapi import APIRouter
from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    GENERIC_CSRF_DETAIL,
)
from hiring_radar.api.dependencies import get_admin_auth_settings
from hiring_radar.api.security import ADMIN_SESSION_COOKIE_NAME, AdminAuthSettings


def _make_auth_settings() -> AdminAuthSettings:
    return AdminAuthSettings(
        email="admin@example.com",
        password="super-secret",
        session_secret="test-session-secret",
        session_ttl_seconds=3600,
    )


def _login_admin(client: TestClient) -> None:
    response = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "super-secret"},
    )
    assert response.status_code == 200, response.text
    assert client.cookies.get(ADMIN_SESSION_COOKIE_NAME)
    assert client.cookies.get(CSRF_COOKIE_NAME)


def _csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token
    return {CSRF_HEADER_NAME: token}


def test_session_creation_attaches_browser_readable_csrf_cookie() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)

    response = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "super-secret"},
    )

    assert response.status_code == 200
    assert client.cookies.get(CSRF_COOKIE_NAME)
    csrf_set_cookie = [
        value
        for value in response.headers.get_list("set-cookie")
        if value.startswith(f"{CSRF_COOKIE_NAME}=")
    ]
    assert csrf_set_cookie
    assert "HttpOnly" not in csrf_set_cookie[0]
    assert "SameSite=lax" in csrf_set_cookie[0]


def test_cookie_authenticated_mutation_requires_csrf_header() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)
    _login_admin(client)

    response = client.post("/api/admin/auth/logout")

    assert response.status_code == 403
    assert response.json() == {"detail": GENERIC_CSRF_DETAIL}


def test_cookie_authenticated_mutation_accepts_matching_csrf_header() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)
    _login_admin(client)

    response = client.post("/api/admin/auth/logout", headers=_csrf_headers(client))

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_logout_clears_csrf_cookie() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)
    _login_admin(client)

    response = client.post("/api/admin/auth/logout", headers=_csrf_headers(client))

    assert response.status_code == 200
    assert not client.cookies.get(CSRF_COOKIE_NAME)


def test_safe_request_backfills_csrf_cookie_for_existing_session() -> None:
    app = create_app()
    app.dependency_overrides[get_admin_auth_settings] = _make_auth_settings
    client = TestClient(app)
    _login_admin(client)
    session_cookie = client.cookies.get(ADMIN_SESSION_COOKIE_NAME)
    assert session_cookie

    client.cookies.clear()
    client.cookies.set(ADMIN_SESSION_COOKIE_NAME, session_cookie)

    response = client.get("/api/admin/auth/me")

    assert response.status_code == 200
    assert client.cookies.get(CSRF_COOKIE_NAME)


def test_mutation_without_session_cookie_does_not_require_csrf_header() -> None:
    router = APIRouter()

    @router.post("/api/internal-test/open-mutation")
    def open_mutation() -> dict[str, bool]:
        return {"ok": True}

    app = create_app()
    app.include_router(router)
    client = TestClient(app)

    response = client.post("/api/internal-test/open-mutation")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
