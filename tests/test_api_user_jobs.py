from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
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
                first_seen_at="2026-04-03T10:00:00Z",
                last_seen_at="2026-04-03T10:00:00Z",
                is_active=True,
                scraped_at="2026-04-03T10:00:00Z",
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


def test_user_jobs_returns_all_with_match_flags() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.get("/api/user/jobs")

    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 2
    assert data["items"][0]["matched"] is True


def test_user_matches_returns_only_matched_items() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()

    client = TestClient(app)
    response = client.get("/api/user/matches")

    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 1
    assert data["items"][0]["title"] == "Security Engineer"
