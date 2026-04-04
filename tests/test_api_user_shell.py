from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app


def test_root_redirects_to_app_login() -> None:
    client = TestClient(create_app())

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/app/login"


def test_user_login_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/app/login")

    assert response.status_code == 200
    assert "Sign in to your dashboard" in response.text
    assert "Light" in response.text
    assert "Dark" in response.text


def test_user_preferences_page_renders() -> None:
    client = TestClient(create_app())

    response = client.get("/app/preferences")

    assert response.status_code == 200
    assert "Your Preferences" in response.text
    assert "Current filter policy" in response.text