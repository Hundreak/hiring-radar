from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_admin_session, get_repository
from hiring_radar.api.security import AdminSession
from hiring_radar.models import Subscriber, SubscriberKeywordPreference


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

    def get_subscriber_keyword_preference(self, subscriber_id: int):
        return SubscriberKeywordPreference(
            subscriber_id=subscriber_id,
            include_keywords=("engineer",),
            exclude_keywords=("intern",),
            match_title=True,
            match_location=False,
            match_company_name=False,
            updated_at="2026-04-04T10:20:00Z",
        )


def _make_admin_session() -> AdminSession:
    return AdminSession(
        email="admin@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T22:00:00Z",
    )


def test_admin_can_view_subscriber_keyword_profile() -> None:
    app = create_app()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.get("/api/admin/subscribers/7/keyword-preferences")

    assert response.status_code == 200
    assert response.json() == {
        "subscriber_id": 7,
        "include_keywords": ["engineer"],
        "exclude_keywords": ["intern"],
        "match_title": True,
        "match_location": False,
        "match_company_name": False,
        "enabled": True,
        "active_fields": ["title"],
        "updated_at": "2026-04-04T10:20:00Z",
    }
