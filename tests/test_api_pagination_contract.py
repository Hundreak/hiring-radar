from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.pagination import (
    EMPLOYER_LIST_BOUNDS,
    normalize_page_contract,
    normalize_query_text,
    total_pages,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import JobRecord
from hiring_radar.services.user_auth import UserSession


def test_pagination_helpers_normalize_bounds_and_totals() -> None:
    meta = normalize_page_contract(
        page="-2",
        page_size="999",
        total_items=101,
        bounds=EMPLOYER_LIST_BOUNDS,
    )

    assert meta.page == 1
    assert meta.page_size == 100
    assert meta.total_items == 101
    assert meta.total_pages == 2
    assert total_pages(total_items=0, page_size=25) == 0


def test_query_text_normalizes_blank_and_rejects_large_values() -> None:
    assert normalize_query_text("   ") is None
    assert normalize_query_text("  backend  ") == "backend"

    with pytest.raises(HTTPException) as excinfo:
        normalize_query_text("x" * 161, max_length=160)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "query_too_long_max_160"


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / "pagination_contract.db"))
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


def _seed_legacy_jobs(repository: HiringRadarRepository, count: int = 3) -> None:
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-18T10:00:00Z",
    )
    repository.upsert_subscriber_profile(
        subscriber.id or 0,
        phone=None,
        headline="Backend Engineer",
        summary="Python backend engineer.",
        target_roles=("Backend Engineer",),
        skills=("Python", "FastAPI"),
        preferred_locations=("Remote",),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T10:01:00Z",
    )
    for index in range(count):
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
                fingerprint=f"unit-{index}",
                first_seen_at=f"2026-04-18T10:0{index}:00Z",
                last_seen_at=f"2026-04-18T10:0{index}:00Z",
                is_active=True,
                scraped_at="2026-04-18T10:00:00Z",
            )
        )


def test_user_jobs_exposes_pagination_headers(repository: HiringRadarRepository, client: TestClient) -> None:
    _seed_legacy_jobs(repository, count=3)

    response = client.get("/api/user/jobs?page=1&page_size=2")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert payload["total_items"] == 3
    assert payload["total_pages"] == 2
    assert response.headers["X-Page"] == "1"
    assert response.headers["X-Page-Size"] == "2"
    assert response.headers["X-Total-Items"] == "3"


def test_user_jobs_rejects_oversized_page_size(client: TestClient) -> None:
    response = client.get("/api/user/jobs?page_size=51")

    assert response.status_code == 422
