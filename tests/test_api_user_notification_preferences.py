from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.models import Subscriber, SubscriberNotificationPreference
from hiring_radar.services.user_auth import UserSession


class FakeRepository:
    def __init__(self) -> None:
        self.digest_updates: list[dict[str, object]] = []
        self.preference_updates: list[dict[str, object]] = []

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

    def get_subscriber_notification_preference(self, subscriber_id: int):
        if subscriber_id != 7:
            return None
        return SubscriberNotificationPreference(
            subscriber_id=7,
            job_digest_enabled=True,
            product_updates_enabled=False,
            employer_messages_enabled=True,
            security_alerts_enabled=True,
            quiet_hours_enabled=False,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            timezone="Europe/Istanbul",
            updated_at="2026-04-04T10:10:00Z",
        )

    def update_subscriber_fields_by_id(self, subscriber_id: int, *, fields: dict[str, object], updated_at: str):
        self.digest_updates.append({"subscriber_id": subscriber_id, "fields": fields, "updated_at": updated_at})
        return self.get_subscriber_by_id(subscriber_id)

    def upsert_subscriber_notification_preference(self, subscriber_id: int, **kwargs):
        self.preference_updates.append({"subscriber_id": subscriber_id, **kwargs})
        return SubscriberNotificationPreference(
            subscriber_id=subscriber_id,
            job_digest_enabled=False,
            product_updates_enabled=bool(kwargs.get("product_updates_enabled")),
            employer_messages_enabled=bool(kwargs.get("employer_messages_enabled", True)),
            security_alerts_enabled=bool(kwargs.get("security_alerts_enabled", True)),
            quiet_hours_enabled=bool(kwargs.get("quiet_hours_enabled")),
            quiet_hours_start=str(kwargs.get("quiet_hours_start") or "22:00"),
            quiet_hours_end=str(kwargs.get("quiet_hours_end") or "08:00"),
            timezone=str(kwargs.get("timezone") or "Europe/Istanbul"),
            updated_at=str(kwargs.get("updated_at")),
        )


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=7,
        email="alice@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T11:00:00Z",
    )


def test_user_notification_preferences_get_returns_defaults() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.get("/api/user/me/notification-preferences")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_digest_enabled"] is True
    assert payload["employer_messages_enabled"] is True
    assert payload["security_alerts_enabled"] is True
    assert payload["quiet_hours_start"] == "22:00"


def test_user_notification_preferences_patch_syncs_digest_and_preferences() -> None:
    repository = FakeRepository()
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: repository

    client = TestClient(app)
    response = client.patch(
        "/api/user/me/notification-preferences",
        json={
            "job_digest_enabled": False,
            "product_updates_enabled": True,
            "employer_messages_enabled": False,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "21:30",
            "quiet_hours_end": "07:15",
            "timezone": "Europe/Istanbul",
        },
    )

    assert response.status_code == 200
    assert repository.digest_updates[0]["fields"] == {"digest_enabled": False}
    assert repository.preference_updates[0]["product_updates_enabled"] is True
    assert response.json()["quiet_hours_start"] == "21:30"


def test_user_notification_preferences_rejects_invalid_quiet_hours() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.patch(
        "/api/user/me/notification-preferences",
        json={"quiet_hours_start": "99:99"},
    )

    assert response.status_code == 400
