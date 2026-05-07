from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.job_identity import decode_canonical_job_api_id, is_canonical_job_api_id
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import CanonicalJob, CanonicalJobLink, JobExternalContextSnapshot, JobRecord, JobSource, JobSourceRecord
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.user_auth import UserSession


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / "api_user_jobs.db"))
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
        headline="Senior Backend Engineer",
        summary="Python backend engineer with FastAPI, Docker and cloud platform delivery experience.",
        target_roles=("Backend Engineer", "Platform Engineer"),
        skills=("Python", "FastAPI", "Docker", "Kubernetes"),
        preferred_locations=("Istanbul", "Remote"),
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



def _seed_canonical_jobs(repository: HiringRadarRepository) -> tuple[int, int]:
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

    def persist_job(*, external_job_id: str, title: str, location_text: str, description_text: str) -> CanonicalJob:
        source_record = repository.upsert_job_source_record(
            JobSourceRecord(
                source_id=source.id or 0,
                external_job_id=external_job_id,
                raw_payload_json='{"title":"placeholder"}',
                raw_payload_hash=f"hash-{external_job_id}",
                canonical_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
                title=title,
                company_name="Acme",
                location_text=location_text,
                posted_at="2026-04-18",
                apply_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
                fetched_at="2026-04-18T09:10:00Z",
                is_active=True,
            )
        )
        job = repository.upsert_canonical_job(
            CanonicalJob(
                canonical_key=f"acme|{title.casefold()}|{location_text.casefold()}|{external_job_id}",
                normalized_title=title.casefold(),
                normalized_company_name="acme",
                display_title=title,
                display_company_name="Acme",
                location_city=location_text.split(",")[0],
                country="Turkey" if "Turkey" in location_text else "Germany",
                workplace_type="remote" if "Remote" in location_text else "onsite",
                employment_type="full_time",
                seniority="senior" if "Senior" in title else "junior",
                category="software_engineering" if "Engineer" in title else "sales",
                department="engineering" if "Engineer" in title else "commercial",
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
        location_text="Remote, Turkey",
        description_text="Python FastAPI Docker Kubernetes and English communication required. Minimum 4 years of backend API experience.",
    )
    weak_job = persist_job(
        external_job_id="sales-1",
        title="Retail Sales Associate",
        location_text="Berlin, Germany",
        description_text="Retail sales, cash handling, on-site work and German language required.",
    )
    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:14:00Z",
        canonical_job_ids=[strong_job.id or 0, weak_job.id or 0],
    )
    return strong_job.id or 0, weak_job.id or 0



def test_user_jobs_returns_deterministic_ranked_canonical_jobs_with_explanations(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    _seed_subscriber(repository)
    strong_job_id, weak_job_id = _seed_canonical_jobs(repository)

    response = client.get("/api/user/jobs")

    assert response.status_code == 200
    data = response.json()
    assert data["ranking_mode"] == "deterministic_matching"
    assert data["total_items"] == 2
    assert data["items"][0]["job_kind"] == "canonical"
    assert is_canonical_job_api_id(data["items"][0]["id"])
    assert decode_canonical_job_api_id(data["items"][0]["id"]) == strong_job_id
    assert data["items"][0]["title"] == "Senior Backend Engineer"
    assert data["items"][0]["matched"] is True
    assert data["items"][0]["match_score"] > data["items"][1]["match_score"]
    assert data["items"][0]["explanation"]["summary"]
    assert data["items"][0]["explanation"]["matching_score_breakdown"]
    assert data["items"][0]["explanation"]["key_evidence_points"]
    assert data["items"][0]["explanation"]["gap_analysis"]
    assert data["items"][0]["explanation"]["top_reasons"]
    assert data["items"][0]["explanation"]["analysis_coverage"]["level"] in {"strong", "moderate", "limited"}
    assert data["items"][0]["explanation"]["analysis_coverage"]["content_sources"]
    assert "python" in data["items"][0]["explanation"]["matched_skill_terms"]
    assert decode_canonical_job_api_id(data["items"][1]["id"]) == weak_job_id



def test_user_matches_returns_only_deterministic_positive_matches(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    _seed_subscriber(repository)
    _seed_canonical_jobs(repository)

    response = client.get("/api/user/matches")

    assert response.status_code == 200
    data = response.json()
    assert data["ranking_mode"] == "deterministic_matching"
    assert data["total_items"] == 1
    assert data["items"][0]["title"] == "Senior Backend Engineer"
    assert data["items"][0]["matched"] is True



def test_user_jobs_falls_back_to_deterministic_legacy_runtime_when_canonical_corpus_is_absent(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    subscriber_id = _seed_subscriber(repository)
    repository.upsert_subscriber_keyword_preference(
        subscriber_id,
        include_keywords=("engineer",),
        exclude_keywords=(),
        match_title=True,
        match_location=False,
        match_company_name=False,
        updated_at="2026-04-18T08:05:00Z",
    )
    repository.upsert_job(
        JobRecord(
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
            first_seen_at="2026-04-18T08:00:00Z",
            last_seen_at="2026-04-18T08:00:00Z",
            is_active=True,
            scraped_at="2026-04-18T08:00:00Z",
        )
    )

    response = client.get("/api/user/jobs")

    assert response.status_code == 200
    data = response.json()
    assert data["ranking_mode"] == "deterministic_matching"
    assert data["total_items"] == 1
    assert data["items"][0]["job_kind"] == "legacy"
    assert data["items"][0]["match_score"] is not None
    assert data["items"][0]["explanation"]["matching_score_breakdown"]
    assert data["items"][0]["explanation"]["matching_score_breakdown"][0]["component_key"] != "legacy_keyword_alignment"
    assert data["items"][0]["explanation"]["top_reasons"]
    assert data["items"][0]["explanation"]["analysis_coverage"]["level"] in {"strong", "moderate", "limited"}




def test_user_jobs_enriches_deterministic_explanations_with_cached_external_context(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    _seed_subscriber(repository)
    strong_job_id, _ = _seed_canonical_jobs(repository)
    strong_job = repository.get_canonical_job_by_id(strong_job_id)
    assert strong_job is not None

    repository.upsert_job_external_context_snapshot(
        JobExternalContextSnapshot(
            source_url=strong_job.apply_url,
            final_url=strong_job.apply_url,
            source_domain="boards.greenhouse.io",
            fetch_status="ok",
            http_status=200,
            page_title="Senior Backend Engineer – Acme",
            site_name="Greenhouse",
            clean_text="Python FastAPI Docker Kubernetes required",
            content_digest="digest-1",
            site_specific_requirements=("Design APIs", "Own services"),
            company_culture_clues=("Remote-friendly",),
            responsibility_clues=("Own backend services",),
            technology_stack_terms=("kubernetes", "docker"),
            source_metadata_json={"text_char_count": 128},
            warning=None,
            fetched_at="2026-04-18T09:20:00Z",
            expires_at="2026-04-19T09:20:00Z",
            updated_at="2026-04-18T09:20:00Z",
        )
    )

    response = client.get("/api/user/jobs")

    assert response.status_code == 200
    payload = response.json()
    explanation = payload["items"][0]["explanation"]
    assert explanation["external_source_insights"]["enrichment_status"] == "cached"
    assert explanation["external_source_insights"]["site_specific_requirements"] == ["Design APIs", "Own services"]
    assert explanation["external_source_insights"]["technology_stack_terms"] == ["kubernetes", "docker"]


def test_user_jobs_auto_builds_canonical_features_before_falling_back(
    repository: HiringRadarRepository,
    client: TestClient,
) -> None:
    _seed_subscriber(repository)
    _seed_canonical_jobs(repository)
    repository.connection.execute("DELETE FROM canonical_job_features")
    repository.connection.commit()

    response = client.get("/api/user/jobs")

    assert response.status_code == 200
    data = response.json()
    assert data["ranking_mode"] == "deterministic_matching"
    assert data["total_items"] == 2
    assert data["items"][0]["job_kind"] == "canonical"
    assert data["items"][0]["match_score"] > data["items"][1]["match_score"]
    assert repository.list_canonical_job_features(active_only=True)
