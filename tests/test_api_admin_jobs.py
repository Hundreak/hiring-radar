from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_admin_session, get_repository
from hiring_radar.api.security import AdminSession
from hiring_radar.models import JobRecord


class FakeRepository:
    def list_jobs_paginated(
        self,
        *,
        q: str | None = None,
        source_name: str | None = None,
        company_name: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ):
        assert q == "Engineer"
        assert source_name == "trendyol-lever"
        assert company_name == "Trendyol"
        assert is_active is True
        assert page == 2
        assert page_size == 10

        return (
            [
                JobRecord(
                    id=101,
                    source_name="trendyol-lever",
                    title="Data Engineer",
                    company_name="Trendyol",
                    location="Istanbul",
                    canonical_url="https://example.com/jobs/101",
                    source_type="lever",
                    source_job_id="101",
                    raw_posted_at=None,
                    posted_at=None,
                    fingerprint="fp-101",
                    first_seen_at="2026-04-04T10:00:00Z",
                    last_seen_at="2026-04-04T10:30:00Z",
                    is_active=True,
                    scraped_at="2026-04-04T10:30:00Z",
                )
            ],
            11,
        )


def _make_admin_session() -> AdminSession:
    return AdminSession(
        email="admin@example.com",
        issued_at="2026-04-04T10:00:00Z",
        expires_at="2026-04-04T22:00:00Z",
    )


def test_admin_jobs_endpoint_returns_paginated_jobs() -> None:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_current_admin_session] = _make_admin_session

    client = TestClient(app)
    response = client.get(
        "/api/admin/jobs",
        params={
            "q": "Engineer",
            "source_name": "trendyol-lever",
            "company_name": "Trendyol",
            "is_active": "true",
            "page": 2,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 101,
                "source_name": "trendyol-lever",
                "company_name": "Trendyol",
                "source_type": "lever",
                "title": "Data Engineer",
                "location": "Istanbul",
                "canonical_url": "https://example.com/jobs/101",
                "posted_at": None,
                "first_seen_at": "2026-04-04T10:00:00Z",
                "last_seen_at": "2026-04-04T10:30:00Z",
                "is_active": True,
            }
        ],
        "page": 2,
        "page_size": 10,
        "total_items": 11,
        "total_pages": 2,
    }