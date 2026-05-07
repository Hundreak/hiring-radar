from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import CanonicalJob, CanonicalJobLink, JobSource, JobSourceRecord
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.user_auth import UserSession


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / "api_user_job_interactions.db"))
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
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Senior Backend Engineer",
        summary="Python backend engineer with FastAPI, Docker and platform delivery experience.",
        target_roles=("Backend Engineer", "Platform Engineer"),
        skills=("Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL"),
        preferred_locations=("Remote", "Turkey"),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T10:01:00Z",
    )
    repository.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[],
        updated_at="2026-04-18T10:02:00Z",
    )
    repository.replace_subscriber_language_entries(
        subscriber_id,
        entries=[],
        updated_at="2026-04-18T10:03:00Z",
    )

    source = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme",
            trust_score=0.97,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )

    def persist_job(*, external_job_id: str, title: str, description_text: str) -> None:
        source_record = repository.upsert_job_source_record(
            JobSourceRecord(
                source_id=source.id or 0,
                external_job_id=external_job_id,
                raw_payload_json='{"title":"placeholder"}',
                raw_payload_hash=f"hash-{external_job_id}",
                canonical_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
                title=title,
                company_name="Acme",
                location_text="Remote, Turkey",
                posted_at="2026-04-18",
                apply_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
                fetched_at="2026-04-18T09:10:00Z",
                is_active=True,
            )
        )
        canonical_job = repository.upsert_canonical_job(
            CanonicalJob(
                canonical_key=f"acme|{title.casefold()}|remote|{external_job_id}",
                normalized_title=title.casefold(),
                normalized_company_name="acme",
                display_title=title,
                display_company_name="Acme",
                location_city="Remote",
                country="Turkey",
                workplace_type="remote",
                employment_type="full_time",
                seniority="senior",
                category="software_engineering",
                department="engineering",
                description_text=description_text,
                posted_at="2026-04-18",
                apply_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
                trust_score=0.97,
                freshness_score=0.92,
                is_active=True,
                created_at="2026-04-18T09:12:00Z",
                updated_at="2026-04-18T09:12:00Z",
            )
        )
        repository.upsert_canonical_job_link(
            CanonicalJobLink(
                canonical_job_id=canonical_job.id or 0,
                source_job_id=source_record.id or 0,
                merge_reason="unit_test_link",
                confidence=0.99,
                created_at="2026-04-18T09:13:00Z",
                updated_at="2026-04-18T09:13:00Z",
            )
        )
        refresh_matching_readiness_features(
            repository,
            refreshed_at="2026-04-18T09:14:00Z",
            canonical_job_ids=[canonical_job.id or 0],
        )

    persist_job(
        external_job_id="backend-1",
        title="Senior Backend Engineer",
        description_text="Python FastAPI Docker Kubernetes PostgreSQL and English communication required. Minimum 4 years of backend API experience.",
    )
    persist_job(
        external_job_id="platform-1",
        title="Senior Platform Engineer",
        description_text="Python Docker Kubernetes PostgreSQL platform engineering and English communication required. Minimum 4 years of infrastructure experience.",
    )



def test_user_job_interactions_raise_behavioral_affinity_and_personalized_score(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    _seed(repository)

    initial = client.get("/api/user/jobs")
    assert initial.status_code == 200
    initial_payload = initial.json()
    assert len(initial_payload["items"]) == 2
    target_job = initial_payload["items"][1]
    baseline_rank = next(index for index, item in enumerate(initial_payload["items"]) if item["id"] == target_job["id"])

    open_response = client.post(
        f"/api/user/jobs/{target_job['id']}/open",
        json={"source_surface": "jobs"},
    )
    assert open_response.status_code == 200
    assert open_response.json()["open_count"] == 1

    dwell_response = client.post(
        f"/api/user/jobs/{target_job['id']}/dwell",
        json={"source_surface": "jobs", "dwell_seconds": 420},
    )
    assert dwell_response.status_code == 200
    assert dwell_response.json()["total_dwell_seconds"] == 420

    apply_response = client.post(
        f"/api/user/jobs/{target_job['id']}/apply-click",
        json={"source_surface": "jobs"},
    )
    assert apply_response.status_code == 200
    assert apply_response.json()["apply_click_count"] == 1
    assert apply_response.json()["affinity_score"] > 0.0

    refreshed = client.get("/api/user/jobs")
    assert refreshed.status_code == 200
    refreshed_payload = refreshed.json()
    target_after = next(item for item in refreshed_payload["items"] if item["id"] == target_job["id"])
    refreshed_rank = next(index for index, item in enumerate(refreshed_payload["items"]) if item["id"] == target_job["id"])
    assert refreshed_rank < baseline_rank
    assert target_after["explanation"]["behavioral_affinity_score"] is not None
    assert target_after["explanation"]["behavioral_affinity_score"] > 0.0
