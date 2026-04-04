from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import (
    get_app_settings,
    get_current_user_session,
    get_repository,
)
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.models import Subscriber
from hiring_radar.services.user_auth import UserSession
from hiring_radar.settings import AppSettings, NotificationsSettings


class FakeRepository:
    def get_subscriber_by_id(self, subscriber_id: int):
        if subscriber_id != 7:
            return None

        return Subscriber(
            id=7,
            email="alice@example.com",
            full_name="Alice Example",
            is_active=True,
            digest_enabled=True,
            created_at="2026-04-04T10:00:00Z",
            updated_at="2026-04-04T10:10:00Z",
        )

    def update_subscriber_fields_by_id(
        self,
        subscriber_id: int,
        *,
        fields: dict[str, object],
        updated_at: str,
    ):
        assert subscriber_id == 7
        return Subscriber(
            id=7,
            email="alice@example.com",
            full_name=fields.get("full_name", "Alice Example"),
            is_active=fields.get("is_active", True),
            digest_enabled=fields.get("digest_enabled", True),
            created_at="2026-04-04T10:00:00Z",
            updated_at=updated_at,
        )


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=7,
        email="alice@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T11:00:00Z",
    )


def _make_settings() -> AppSettings:
    return AppSettings(
        keyword_filter=KeywordFilterSettings(
            include_keywords=("engineer",),
            exclude_keywords=("intern",),
            match_title=True,
            match_location=False,
            match_company_name=False,
        ),
        notifications=NotificationsSettings(
            apply_keyword_filter_to_digest=True,
        ),
    )


def test_user_me_returns_current_subscriber() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.get("/api/user/me")

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


def test_user_preferences_patch_updates_current_subscriber() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.patch(
        "/api/user/me/preferences",
        json={
            "full_name": "Alice Updated",
            "is_active": True,
            "digest_enabled": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Alice Updated"
    assert response.json()["digest_enabled"] is False


def test_user_filter_policy_returns_global_policy() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_app_settings] = _make_settings

    client = TestClient(app)
    response = client.get("/api/user/me/filter-policy")

    assert response.status_code == 200
    assert response.json() == {
        "filter_enabled": True,
        "apply_keyword_filter_to_digest": True,
        "include_keywords": ["engineer"],
        "exclude_keywords": ["intern"],
        "active_fields": ["title"],
    }