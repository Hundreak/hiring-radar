from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_admin_session, get_repository
from hiring_radar.api.security import AdminSession
from hiring_radar.models import CrawlRun, NotificationRun


class FakeRepository:
    def list_crawl_runs_paginated(
        self,
        *,
        source_name: str | None = None,
        success: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ):
        assert source_name == "trendyol-lever"
        assert success is True
        assert page == 1
        assert page_size == 10

        return (
            [
                CrawlRun(
                    id=11,
                    source_name="trendyol-lever",
                    started_at="2026-04-04T10:00:00Z",
                    finished_at="2026-04-04T10:02:00Z",
                    success=True,
                    notes="ok",
                )
            ],
            1,
        )

    def list_notification_runs_paginated(
        self,
        *,
        notification_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ):
        assert notification_type == "digest_email"
        assert status == "sent"
        assert page == 1
        assert page_size == 10

        return (
            [
                NotificationRun(
                    id=22,
                    notification_type="digest_email",
                    started_at="2026-04-04T10:05:00Z",
                    finished_at="2026-04-04T10:05:10Z",
                    status="sent",
                    recipient_count=3,
                    new_jobs_count=11,
                    since="2026-04-04T04:00:00Z",
                    subject="Digest",
                    error_message=None,
                )
            ],
            1,
        )


def _make_admin_session() -> AdminSession:
    return AdminSession(
        email="admin@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T22:00:00Z",
    )


def test_admin_crawl_runs_endpoint_returns_paginated_runs() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.get(
        "/api/admin/crawl-runs",
        params={
            "source_name": "trendyol-lever",
            "success": "true",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 11,
                "source_name": "trendyol-lever",
                "started_at": "2026-04-04T10:00:00Z",
                "finished_at": "2026-04-04T10:02:00Z",
                "success": True,
                "notes": "ok",
            }
        ],
        "page": 1,
        "page_size": 10,
        "total_items": 1,
        "total_pages": 1,
    }


def test_admin_notification_runs_endpoint_returns_paginated_runs() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.get(
        "/api/admin/notification-runs",
        params={
            "notification_type": "digest_email",
            "status": "sent",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 22,
                "notification_type": "digest_email",
                "started_at": "2026-04-04T10:05:00Z",
                "finished_at": "2026-04-04T10:05:10Z",
                "status": "sent",
                "recipient_count": 3,
                "new_jobs_count": 11,
                "since": "2026-04-04T04:00:00Z",
                "subject": "Digest",
                "error_message": None,
            }
        ],
        "page": 1,
        "page_size": 10,
        "total_items": 1,
        "total_pages": 1,
    }
