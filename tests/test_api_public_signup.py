from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import (
    get_env_path,
    get_repository,
    get_user_auth_settings,
)
from hiring_radar.services.user_auth import UserAuthSettings


class FakeRepository:
    def __init__(self) -> None:
        self.upserts: list[tuple[str, str]] = []

    def upsert_subscriber(self, *, email: str, full_name: str | None, updated_at: str):
        self.upserts.append((email, full_name or ""))
        return None, True


def _make_user_auth_settings() -> UserAuthSettings:
    return UserAuthSettings(
        app_base_url="http://127.0.0.1:8000",
        session_secret="user-session-secret",
        session_ttl_seconds=3600,
        magic_link_ttl_seconds=900,
    )


def test_public_signup_challenge_returns_token() -> None:
    app = create_app()
    app.dependency_overrides[get_user_auth_settings] = _make_user_auth_settings

    client = TestClient(app)
    response = client.get("/api/public/auth/signup-challenge")

    assert response.status_code == 200
    data = response.json()
    assert len(data["challenge_text"]) == 5
    assert data["challenge_token"]


def test_public_signup_creates_subscriber(monkeypatch) -> None:
    repo = FakeRepository()

    monkeypatch.setattr(
        "hiring_radar.api.routers.public_auth.issue_magic_link_for_email",
        lambda **kwargs: None,
    )

    app = create_app()
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_user_auth_settings] = _make_user_auth_settings
    app.dependency_overrides[get_env_path] = lambda: ".env"

    client = TestClient(app)
    challenge = client.get("/api/public/auth/signup-challenge").json()

    response = client.post(
        "/api/public/auth/signup",
        json={
            "email": "alice@example.com",
            "full_name": "Alice Example",
            "challenge_token": challenge["challenge_token"],
            "challenge_answer": challenge["challenge_text"],
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert repo.upserts == [("alice@example.com", "Alice Example")]
