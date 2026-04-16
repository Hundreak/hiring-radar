from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import (
    get_env_path,
    get_repository,
    get_user_auth_settings,
)
from hiring_radar.services.user_auth import UserAuthSettings, UserSession


class FakeRepository:
    def __init__(self) -> None:
        self.magic_link_created_for: str | None = None

    def get_subscriber_by_email(self, email: str):
        if email != "alice@example.com":
            return None

        class SubscriberObj:
            id = 7
            email = "alice@example.com"
            full_name = "Alice"
            is_active = True

        return SubscriberObj()

    def create_subscriber_magic_link(
        self,
        *,
        subscriber_id: int,
        token_hash: str,
        expires_at: str,
        created_at: str,
    ):
        self.magic_link_created_for = "alice@example.com"

        class LinkObj:
            id = 1

        return LinkObj()

    def get_subscriber_magic_link_by_hash(self, token_hash: str):
        if token_hash == "bad":
            return None

        class LinkObj:
            def __init__(self, token_hash_value: str) -> None:
                self.id = 1
                self.subscriber_id = 7
                self.token_hash = token_hash_value
                self.expires_at = "2099-04-04T10:15:00Z"
                self.consumed_at = None
                self.created_at = "2099-04-04T10:00:00Z"

        return LinkObj(token_hash)

    def get_subscriber_by_id(self, subscriber_id: int):
        if subscriber_id != 7:
            return None

        class SubscriberObj:
            id = 7
            email = "alice@example.com"
            full_name = "Alice"
            is_active = True

        return SubscriberObj()

    def consume_subscriber_magic_link(self, link_id: int, *, consumed_at: str) -> bool:
        return True


def _make_user_auth_settings() -> UserAuthSettings:
    return UserAuthSettings(
        secret_key="user-session-secret",
        session_ttl_seconds=3600,
        magic_link_ttl_seconds=900,
    )


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=7,
        email="alice@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T11:00:00Z",
    )


def test_request_magic_link_returns_generic_response(monkeypatch) -> None:
    sent_payloads: list[object] = []

    def fake_load_smtp_settings(env_path: str):
        class SMTPSettings:
            host = "smtp.example.com"
            port = 587
            username = "u"
            password = "p"
            use_tls = True
            email_from = "alerts@example.com"
            default_to = None

        return SMTPSettings()

    def fake_send_email_via_smtp(*, settings, payload, timeout_seconds: float = 20.0):
        sent_payloads.append(payload)

    monkeypatch.setattr(
        "hiring_radar.api.routers.user_auth.load_smtp_settings",
        fake_load_smtp_settings,
    )
    monkeypatch.setattr(
        "hiring_radar.api.routers.user_auth.send_email_via_smtp",
        fake_send_email_via_smtp,
    )

    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_user_auth_settings] = _make_user_auth_settings
    app.dependency_overrides[get_env_path] = lambda: ".env"

    client = TestClient(app)
    response = client.post(
        "/api/user/auth/request-magic-link",
        json={"email": "alice@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "message": "If that address is eligible, we have sent a secure sign-in link.",
    }
    assert len(sent_payloads) == 1
    assert sent_payloads[0].subject == "CoreSift giriş bağlantın"


def test_consume_magic_link_sets_user_session_cookie() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_user_auth_settings] = _make_user_auth_settings

    client = TestClient(app)
    response = client.post(
        "/api/user/auth/consume-magic-link",
        json={"token": "valid-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "subscriber_id": 7,
        "email": "alice@example.com",
        "authenticated": True,
    }

    me_response = client.get("/api/user/auth/me")
    assert me_response.status_code == 200
    assert me_response.json() == {
        "subscriber_id": 7,
        "email": "alice@example.com",
        "authenticated": True,
    }


def test_user_auth_me_requires_session() -> None:
    app = create_app()
    app.dependency_overrides[get_user_auth_settings] = _make_user_auth_settings

    client = TestClient(app)
    response = client.get("/api/user/auth/me")

    assert response.status_code == 401
