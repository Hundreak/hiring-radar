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
    connection = initialize_database(str(tmp_path / "saved_pipeline.db"))
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


def _seed_saved_job(repository: HiringRadarRepository) -> int:
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-18T10:00:00Z",
    )
    repository.upsert_job(
        JobRecord(
            source_name="manual",
            title="Frontend Engineer",
            company_name="Acme",
            location="Remote",
            canonical_url="https://example.com/jobs/frontend",
            source_type="manual",
            source_job_id="frontend-1",
            raw_posted_at="2026-04-18T00:00:00+00:00",
            posted_at="2026-04-18T00:00:00+00:00",
            fingerprint="manual-frontend-1",
            first_seen_at="2026-04-18T09:00:00Z",
            last_seen_at="2026-04-18T09:00:00Z",
            is_active=True,
            scraped_at="2026-04-18T09:00:00Z",
        )
    )
    job = repository.get_job_by_fingerprint("manual-frontend-1")
    assert job is not None and job.id is not None
    saved = repository.save_job(
        subscriber_id=subscriber.id or 1,
        job_id=job.id,
        api_job_id=job.id,
        match_score=88,
        now="2026-04-18T10:05:00Z",
    )
    assert saved.id is not None
    return saved.id


@pytest.mark.parametrize("target_status", ["applied", "interview", "offer", "rejected", "archived", "reviewing"])
def test_saved_job_pipeline_accepts_product_statuses(
    repository: HiringRadarRepository,
    client: TestClient,
    target_status: str,
) -> None:
    saved_job_id = _seed_saved_job(repository)

    response = client.patch(
        f"/api/user/saved-jobs/{saved_job_id}/status",
        json={"status": target_status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == target_status


def test_saved_job_pipeline_rejects_unknown_status(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    saved_job_id = _seed_saved_job(repository)

    response = client.patch(
        f"/api/user/saved-jobs/{saved_job_id}/status",
        json={"status": "ghosted-but-not-modeled"},
    )

    assert response.status_code == 422
