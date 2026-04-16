from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import (
    get_app_settings,
    get_current_admin_session,
    get_repository,
    get_settings_path,
)
from hiring_radar.api.security import AdminSession
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.models import JobRecord
from hiring_radar.settings import AppSettings, NotificationsSettings


def _make_admin_session() -> AdminSession:
    return AdminSession(
        email="admin@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T22:00:00Z",
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


def _job(
    *,
    job_id: int,
    title: str,
    company_name: str,
    canonical_url: str,
) -> JobRecord:
    return JobRecord(
        id=job_id,
        source_name="trendyol-lever",
        title=title,
        company_name=company_name,
        location="Istanbul",
        canonical_url=canonical_url,
        source_type="lever",
        source_job_id=str(job_id),
        raw_posted_at=None,
        posted_at=None,
        fingerprint=f"fp-{job_id}",
        first_seen_at="2026-04-04T10:00:00Z",
        last_seen_at="2026-04-04T10:00:00Z",
        is_active=True,
        scraped_at="2026-04-04T10:00:00Z",
    )


class FakePreviewRepository:
    def list_active_jobs(self) -> list[JobRecord]:
        return [
            _job(
                job_id=1,
                title="Security Engineer",
                company_name="Corelight",
                canonical_url="https://example.com/jobs/1",
            ),
            _job(
                job_id=2,
                title="Security Intern",
                company_name="Corelight",
                canonical_url="https://example.com/jobs/2",
            ),
            _job(
                job_id=3,
                title="Growth Marketing Manager",
                company_name="Trendyol",
                canonical_url="https://example.com/jobs/3",
            ),
        ]

    def list_jobs(self) -> list[JobRecord]:
        return self.list_active_jobs()


def test_admin_get_settings_returns_current_settings() -> None:
    app = create_app()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session
    app.dependency_overrides[get_app_settings] = _make_settings
    app.dependency_overrides[get_settings_path] = lambda: "config/settings.local.yml"

    client = TestClient(app)
    response = client.get("/api/admin/settings")

    assert response.status_code == 200
    assert response.json() == {
        "settings_path": "config/settings.local.yml",
        "keyword_filter": {
            "include_keywords": ["engineer"],
            "exclude_keywords": ["intern"],
            "match_title": True,
            "match_location": False,
            "match_company_name": False,
            "enabled": True,
            "active_fields": ["title"],
        },
        "notifications": {
            "apply_keyword_filter_to_digest": True,
        },
    }


def test_admin_update_settings_writes_and_returns_saved_settings(monkeypatch) -> None:
    written: dict[str, object] = {}

    def fake_write_app_settings(config_path: str, settings: AppSettings) -> None:
        written["config_path"] = config_path
        written["settings"] = settings

    monkeypatch.setattr(
        "hiring_radar.api.routers.admin_settings.write_app_settings",
        fake_write_app_settings,
    )

    app = create_app()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session
    app.dependency_overrides[get_settings_path] = lambda: "config/settings.local.yml"

    client = TestClient(app)
    response = client.put(
        "/api/admin/settings",
        json={
            "keyword_filter": {
                "include_keywords": ["python"],
                "exclude_keywords": ["intern"],
                "match_title": True,
                "match_location": True,
                "match_company_name": False,
            },
            "notifications": {
                "apply_keyword_filter_to_digest": False,
            },
        },
    )

    assert response.status_code == 200
    assert written["config_path"] == "config/settings.local.yml"

    saved_settings = written["settings"]
    assert isinstance(saved_settings, AppSettings)
    assert saved_settings.keyword_filter.include_keywords == ("python",)
    assert saved_settings.keyword_filter.exclude_keywords == ("intern",)
    assert saved_settings.keyword_filter.match_title is True
    assert saved_settings.keyword_filter.match_location is True
    assert saved_settings.keyword_filter.match_company_name is False
    assert saved_settings.notifications.apply_keyword_filter_to_digest is False

    assert response.json()["notifications"] == {"apply_keyword_filter_to_digest": False}


def test_admin_filter_preview_returns_summary_and_samples() -> None:
    app = create_app()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session
    app.dependency_overrides[get_repository] = lambda: FakePreviewRepository()

    client = TestClient(app)
    response = client.post(
        "/api/admin/settings/filter-preview",
        json={
            "keyword_filter": {
                "include_keywords": ["engineer"],
                "exclude_keywords": ["intern"],
                "match_title": True,
                "match_location": False,
                "match_company_name": False,
            },
            "active_only": True,
            "sample_limit": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["jobs_scope"] == "active_only"
    assert data["filter_enabled"] is True
    assert data["include_keywords"] == ["engineer"]
    assert data["exclude_keywords"] == ["intern"]
    assert data["active_fields"] == ["title"]
    assert data["total_jobs"] == 3
    assert data["passed_jobs"] == 1
    assert data["rejected_jobs"] == 2
    assert len(data["passed_samples"]) == 1
    assert data["passed_samples"][0]["title"] == "Security Engineer"
    assert data["passed_samples"][0]["include_matches"] == [
        {
            "field_name": "title",
            "keyword": "engineer",
            "field_value": "Security Engineer",
        }
    ]


def test_admin_filter_preview_rejects_invalid_keyword_filter() -> None:
    app = create_app()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session
    app.dependency_overrides[get_repository] = lambda: FakePreviewRepository()

    client = TestClient(app)
    response = client.post(
        "/api/admin/settings/filter-preview",
        json={
            "keyword_filter": {
                "include_keywords": [],
                "exclude_keywords": [],
                "match_title": False,
                "match_location": False,
                "match_company_name": False,
            },
            "active_only": True,
            "sample_limit": 5,
        },
    )

    assert response.status_code == 400
    assert "At least one keyword filter field must be enabled." in response.json()["detail"]
