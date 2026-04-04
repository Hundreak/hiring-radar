from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_admin_session, get_repository
from hiring_radar.api.security import AdminSession
from hiring_radar.models import Subscriber


class FakeRepository:
    def list_subscribers_paginated(
        self,
        *,
        email_query: str | None = None,
        is_active: bool | None = None,
        digest_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ):
        assert email_query == "alice"
        assert is_active is True
        assert digest_enabled is True
        assert page == 1
        assert page_size == 10

        return (
            [
                Subscriber(
                    id=7,
                    email="alice@example.com",
                    full_name="Alice Example",
                    is_active=True,
                    digest_enabled=True,
                    created_at="2026-04-04T10:00:00Z",
                    updated_at="2026-04-04T10:10:00Z",
                )
            ],
            1,
        )

    def update_subscriber_fields_by_id(
        self,
        subscriber_id: int,
        *,
        fields: dict[str, object],
        updated_at: str,
    ):
        assert subscriber_id == 7
        assert fields == {"digest_enabled": False}

        return Subscriber(
            id=7,
            email="alice@example.com",
            full_name="Alice Example",
            is_active=True,
            digest_enabled=False,
            created_at="2026-04-04T10:00:00Z",
            updated_at=updated_at,
        )


class NotFoundRepository(FakeRepository):
    def update_subscriber_fields_by_id(
        self,
        subscriber_id: int,
        *,
        fields: dict[str, object],
        updated_at: str,
    ):
        return None


def _make_admin_session() -> AdminSession:
    return AdminSession(
        email="admin@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T22:00:00Z",
    )


def test_admin_subscribers_endpoint_returns_paginated_subscribers() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.get(
        "/api/admin/subscribers",
        params={
            "email_query": "alice",
            "is_active": "true",
            "digest_enabled": "true",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 7,
                "email": "alice@example.com",
                "full_name": "Alice Example",
                "is_active": True,
                "digest_enabled": True,
                "created_at": "2026-04-04T10:00:00Z",
                "updated_at": "2026-04-04T10:10:00Z",
            }
        ],
        "page": 1,
        "page_size": 10,
        "total_items": 1,
        "total_pages": 1,
    }


def test_admin_subscriber_patch_updates_fields() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.patch(
        "/api/admin/subscribers/7",
        json={"digest_enabled": False},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 7
    assert response.json()["digest_enabled"] is False


def test_admin_subscriber_patch_requires_at_least_one_field() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.patch(
        "/api/admin/subscribers/7",
        json={},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "At least one field must be provided."}


def test_admin_subscriber_patch_returns_404_when_missing() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: NotFoundRepository()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.patch(
        "/api/admin/subscribers/7",
        json={"digest_enabled": False},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Subscriber not found."}