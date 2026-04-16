from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import (
    get_current_user_session,
    get_repository,
)
from hiring_radar.models import JobRecord, Subscriber, SubscriberKeywordPreference
from hiring_radar.services.user_auth import UserSession


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

    def upsert_subscriber_keyword_preference(
        self,
        subscriber_id: int,
        *,
        include_keywords: tuple[str, ...],
        exclude_keywords: tuple[str, ...],
        match_title: bool,
        match_location: bool,
        match_company_name: bool,
        updated_at: str,
    ):
        return SubscriberKeywordPreference(
            subscriber_id=subscriber_id,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
            match_title=match_title,
            match_location=match_location,
            match_company_name=match_company_name,
            updated_at=updated_at,
        )

    def list_active_jobs(self) -> list[JobRecord]:
        return [
            JobRecord(
                id=1,
                source_name="trendyol-lever",
                title="Security Engineer",
                company_name="Trendyol",
                location="Istanbul",
                canonical_url="https://example.com/jobs/1",
                source_type="lever",
                source_job_id="1",
                raw_posted_at=None,
                posted_at=None,
                fingerprint="fp-1",
                first_seen_at="2026-04-04T10:00:00Z",
                last_seen_at="2026-04-04T10:00:00Z",
                is_active=True,
                scraped_at="2026-04-04T10:00:00Z",
            ),
            JobRecord(
                id=2,
                source_name="trendyol-lever",
                title="Security Intern",
                company_name="Trendyol",
                location="Istanbul",
                canonical_url="https://example.com/jobs/2",
                source_type="lever",
                source_job_id="2",
                raw_posted_at=None,
                posted_at=None,
                fingerprint="fp-2",
                first_seen_at="2026-04-04T10:00:00Z",
                last_seen_at="2026-04-04T10:00:00Z",
                is_active=True,
                scraped_at="2026-04-04T10:00:00Z",
            ),
        ]

    def list_jobs(self) -> list[JobRecord]:
        return self.list_active_jobs()


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=7,
        email="alice@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T11:00:00Z",
    )


def test_user_keyword_preferences_get_returns_saved_profile() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.get("/api/user/me/keyword-preferences")

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


def test_user_keyword_preferences_put_saves_profile() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.put(
        "/api/user/me/keyword-preferences",
        json={
            "include_keywords": ["python"],
            "exclude_keywords": ["intern"],
            "match_title": True,
            "match_location": True,
            "match_company_name": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["include_keywords"] == ["python"]
    assert response.json()["exclude_keywords"] == ["intern"]
    assert response.json()["active_fields"] == ["title", "location"]


def test_user_keyword_preferences_preview_returns_matches() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.post(
        "/api/user/me/keyword-preferences/preview",
        json={
            "keyword_preference": {
                "include_keywords": ["engineer"],
                "exclude_keywords": ["intern"],
                "match_title": True,
                "match_location": False,
                "match_company_name": False,
            },
            "active_only": True,
            "sample_limit": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["jobs_scope"] == "active_only"
    assert data["passed_jobs"] == 1
    assert data["rejected_jobs"] == 1
    assert data["passed_samples"][0]["title"] == "Security Engineer"
