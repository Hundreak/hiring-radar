from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import JobRecord
from hiring_radar.services.user_auth import UserSession


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / "saved_jobs_pagination.db"))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


@pytest.fixture()
def client(repository: HiringRadarRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = lambda: UserSession(
        subscriber_id=1,
        email="alice@example.com",
        issued_at="2026-04-18T10:00:00Z",
        expires_at="2026-04-18T11:00:00Z",
    )
    app.dependency_overrides[get_repository] = lambda: repository
    return TestClient(app)


def _seed(repository: HiringRadarRepository) -> None:
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-18T10:00:00Z",
    )
    for index in range(3):
        repository.upsert_job(
            JobRecord(
                source_name="unit",
                title=f"Backend Engineer {index}",
                company_name="Acme",
                location="Remote",
                canonical_url=f"https://example.com/jobs/{index}",
                source_type="unit",
                source_job_id=str(index),
                raw_posted_at="2026-04-18",
                posted_at="2026-04-18",
                fingerprint=f"saved-unit-{index}",
                first_seen_at=f"2026-04-18T10:0{index}:00Z",
                last_seen_at=f"2026-04-18T10:0{index}:00Z",
                is_active=True,
                scraped_at="2026-04-18T10:00:00Z",
            )
        )
        repository.save_job(
            subscriber_id=subscriber.id or 0,
            job_id=index + 1,
            api_job_id=index + 1,
            match_score=80 - index,
            now=f"2026-04-18T10:1{index}:00Z",
        )


def test_saved_jobs_supports_pagination_metadata(repository: HiringRadarRepository, client: TestClient) -> None:
    _seed(repository)

    response = client.get("/api/user/saved-jobs?page=1&page_size=2")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert payload["total_items"] == 3
    assert payload["total_pages"] == 2
    assert response.headers["X-Total-Items"] == "3"


def test_saved_jobs_rejects_invalid_status_filter(client: TestClient) -> None:
    response = client.get("/api/user/saved-jobs?status=wishlist")

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_saved_job_status"
