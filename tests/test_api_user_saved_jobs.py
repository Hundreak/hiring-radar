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
    connection = initialize_database(str(tmp_path / "api_user_saved_jobs.db"))
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
        summary="Python backend engineer focused on APIs.",
        target_roles=("Backend Engineer",),
        skills=("Python", "FastAPI", "Docker"),
        preferred_locations=("Remote",),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T10:01:00Z",
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
    source_record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="backend-1",
            raw_payload_json='{"title":"placeholder"}',
            raw_payload_hash="hash-backend-1",
            canonical_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            title="Senior Backend Engineer",
            company_name="Acme",
            location_text="Remote, Turkey",
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            fetched_at="2026-04-18T09:10:00Z",
            is_active=True,
        )
    )
    canonical_job = repository.upsert_canonical_job(
        CanonicalJob(
            canonical_key="acme|senior backend engineer|remote|backend-1",
            normalized_title="senior backend engineer",
            normalized_company_name="acme",
            display_title="Senior Backend Engineer",
            display_company_name="Acme",
            location_city="Remote",
            country="Turkey",
            workplace_type="remote",
            employment_type="full_time",
            seniority="senior",
            category="software_engineering",
            department="engineering",
            description_text="Python FastAPI Docker required.",
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
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





def test_saved_jobs_rehydrates_canonical_match_keywords_when_features_are_missing(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    _seed(repository)

    matches_response = client.get("/api/user/matches")
    assert matches_response.status_code == 200
    match_payload = matches_response.json()
    job_id = match_payload["items"][0]["id"]
    match_score = match_payload["items"][0]["match_score"]

    save_response = client.post(
        "/api/user/saved-jobs",
        json={"job_id": job_id, "match_score": match_score},
    )
    assert save_response.status_code == 201

    repository.connection.execute("DELETE FROM canonical_job_features")
    repository.connection.commit()

    list_response = client.get("/api/user/saved-jobs")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["items"][0]["matched_keywords"]
    assert "python" in payload["items"][0]["matched_keywords"]


def test_user_can_save_and_list_canonical_job_matches(repository: HiringRadarRepository, client: TestClient) -> None:
    _seed(repository)

    matches_response = client.get("/api/user/matches")
    assert matches_response.status_code == 200
    match_payload = matches_response.json()
    assert match_payload["items"]
    job_id = match_payload["items"][0]["id"]
    match_score = match_payload["items"][0]["match_score"]

    save_response = client.post(
        "/api/user/saved-jobs",
        json={"job_id": job_id, "match_score": match_score},
    )
    assert save_response.status_code == 201
    saved_payload = save_response.json()
    assert saved_payload["job_kind"] == "canonical"
    assert saved_payload["title"] == "Senior Backend Engineer"
    assert "python" in saved_payload["matched_keywords"]

    list_response = client.get("/api/user/saved-jobs")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload["items"]) == 1
    assert list_payload["items"][0]["job_id"] == job_id

    delete_response = client.delete(f"/api/user/saved-jobs/{job_id}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
