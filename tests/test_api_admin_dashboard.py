from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import (
    get_app_settings,
    get_current_admin_session,
    get_repository,
)
from hiring_radar.api.security import AdminSession
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.models import CrawlRun, NotificationRun
from hiring_radar.settings import AppSettings, NotificationsSettings


class FakeRepository:
    def get_job_counts(self) -> dict[str, int]:
        return {
            "total_jobs": 142,
            "active_jobs": 140,
            "inactive_jobs": 2,
        }

    def get_subscriber_counts(self) -> dict[str, int]:
        return {
            "total_subscribers": 8,
            "active_subscribers": 7,
            "digest_enabled_subscribers": 6,
        }

    def get_latest_crawl_run(self) -> CrawlRun:
        return CrawlRun(
            id=11,
            source_name="trendyol-lever",
            started_at="2026-04-04T10:00:00Z",
            finished_at="2026-04-04T10:02:00Z",
            success=True,
            notes="ok",
        )

    def get_latest_notification_run(
        self,
        *,
        notification_type: str | None = None,
    ) -> NotificationRun:
        assert notification_type == "digest_email"
        return NotificationRun(
            id=22,
            notification_type="digest_email",
            started_at="2026-04-04T10:05:00Z",
            finished_at="2026-04-04T10:05:10Z",
            status="sent",
            recipient_count=3,
            new_jobs_count=11,
            since="2026-04-04T04:00:00Z",
            subject="Hiring Radar Digest: 11 new jobs since 2026-04-04T04:00:00Z",
            error_message=None,
        )


def _make_app_settings() -> AppSettings:
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


def _make_admin_session() -> AdminSession:
    return AdminSession(
        email="admin@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T22:00:00Z",
    )


def test_admin_dashboard_summary_returns_operational_snapshot() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_app_settings] = _make_app_settings
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.get("/api/admin/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "jobs": {
            "total_jobs": 142,
            "active_jobs": 140,
            "inactive_jobs": 2,
        },
        "subscribers": {
            "total_subscribers": 8,
            "active_subscribers": 7,
            "digest_enabled_subscribers": 6,
        },
        "latest_crawl_run": {
            "id": 11,
            "source_name": "trendyol-lever",
            "notification_type": None,
            "started_at": "2026-04-04T10:00:00Z",
            "finished_at": "2026-04-04T10:02:00Z",
            "success": True,
            "status": None,
            "notes": "ok",
            "recipient_count": None,
            "new_jobs_count": None,
            "since": None,
            "subject": None,
            "error_message": None,
        },
        "latest_notification_run": {
            "id": 22,
            "source_name": None,
            "notification_type": "digest_email",
            "started_at": "2026-04-04T10:05:00Z",
            "finished_at": "2026-04-04T10:05:10Z",
            "success": None,
            "status": "sent",
            "notes": None,
            "recipient_count": 3,
            "new_jobs_count": 11,
            "since": "2026-04-04T04:00:00Z",
            "subject": "Hiring Radar Digest: 11 new jobs since 2026-04-04T04:00:00Z",
            "error_message": None,
        },
        "digest_filter_policy": {
            "filter_enabled": True,
            "apply_keyword_filter_to_digest": True,
            "include_keywords": ["engineer"],
            "exclude_keywords": ["intern"],
            "active_fields": ["title"],
        },
    }