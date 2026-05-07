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
    connection = initialize_database(str(tmp_path / "api_user_match_insights.db"))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


@pytest.fixture()
def user_session() -> UserSession:
    return UserSession(
        subscriber_id=1,
        email="alice@example.com",
        issued_at="2026-04-18T10:00:00Z",
        expires_at="2026-04-18T11:00:00Z",
    )


@pytest.fixture()
def client(repository: HiringRadarRepository, user_session: UserSession) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = lambda: user_session
    app.dependency_overrides[get_repository] = lambda: repository
    return TestClient(app)



def _seed_subscriber(repository: HiringRadarRepository) -> int:
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-18T10:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Backend Engineer",
        summary="Python API engineer working on FastAPI services and Docker deployments.",
        target_roles=("Backend Engineer",),
        skills=("Python", "FastAPI"),
        preferred_locations=("Remote",),
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
    return subscriber_id



def _seed_jobs(repository: HiringRadarRepository) -> None:
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

    def persist_job(*, external_job_id: str, title: str, description_text: str) -> CanonicalJob:
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
        job = repository.upsert_canonical_job(
            CanonicalJob(
                canonical_key=f"acme|{external_job_id}",
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
                canonical_job_id=job.id or 0,
                source_job_id=source_record.id or 0,
                merge_reason="unit_test_link",
                confidence=0.99,
                created_at="2026-04-18T09:13:00Z",
                updated_at="2026-04-18T09:13:00Z",
            )
        )
        return job

    strong_job = persist_job(
        external_job_id="backend-1",
        title="Senior Backend Engineer",
        description_text="Required: Python, FastAPI, Docker. Preferred: Kubernetes. Remote role.",
    )
    gap_job = persist_job(
        external_job_id="platform-1",
        title="Senior Platform Engineer",
        description_text="Required: Python, Kubernetes, Terraform, Docker. Preferred: AWS. Remote role.",
    )
    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:14:00Z",
        canonical_job_ids=[strong_job.id or 0, gap_job.id or 0],
    )



def test_match_insights_use_deterministic_strengths_and_gaps(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    _seed_subscriber(repository)
    _seed_jobs(repository)

    response = client.get("/api/user/match-insights")

    assert response.status_code == 200
    data = response.json()
    assert data["total_matched"] >= 1
    assert data["strengths"]
    strength_terms = {item["keyword"] for item in data["strengths"]}
    assert "python" in strength_terms or "fastapi" in strength_terms
    gap_terms = {item["keyword"] for item in data["gaps"]}
    assert "kubernetes" in gap_terms or "terraform" in gap_terms
