from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import CanonicalJob, JobSource, JobSourceRecord
from hiring_radar.services.jobs.canonicalization import refresh_canonical_jobs
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "job_feature_engine.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


def test_refresh_matching_readiness_features_extracts_taxonomy_and_skills(
    repository: HiringRadarRepository,
) -> None:
    source = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="nova-greenhouse",
            account_slug="nova",
            base_url="https://boards.greenhouse.io/nova",
            trust_score=0.96,
            country_scope="Germany",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )
    repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="gh-ml-1",
            raw_payload_json="{\"description\":\"<p>We need a Senior Machine Learning Engineer with 4+ years of experience building Python services, LLM features and AWS-based platforms. Strong English communication is required. Bachelor\'s degree preferred. Remote across Germany.</p>\"}",
            raw_payload_hash="gh-ml-1",
            canonical_url="https://boards.greenhouse.io/nova/jobs/ml-1",
            title="Senior Machine Learning Engineer",
            company_name="Nova",
            location_text="Berlin, Germany / Remote",
            posted_at="2026-04-18",
            apply_url="https://apply.nova.example/ml-1",
            fetched_at="2026-04-18T09:10:00Z",
            is_active=True,
        )
    )

    refresh_canonical_jobs(repository, refreshed_at="2026-04-18T10:00:00Z")
    result = refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T10:05:00Z",
    )

    assert result.total_jobs_considered == 1
    assert result.refreshed_features == 1
    assert result.pruned_features == 0

    features = repository.list_canonical_job_features(active_only=True)
    assert len(features) == 1
    feature = features[0]
    assert feature.role_family == "data"
    assert feature.department_family == "engineering"
    assert feature.job_discipline == "machine_learning"
    assert "python" in feature.skill_terms
    assert "aws" in feature.skill_terms
    assert "english" in feature.language_requirements
    assert feature.education_level_hint == "bachelor"
    assert feature.years_experience_min == 4
    assert feature.management_track is False
    assert feature.individual_contributor is True
    assert feature.match_readiness_score >= 0.8

    canonical_job = repository.list_canonical_jobs(active_only=True)[0]
    assert canonical_job.category == "data"
    assert canonical_job.department == "engineering"


def test_refresh_matching_readiness_features_prunes_inactive_jobs(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_canonical_job(
        CanonicalJob(
            canonical_key="waiter-istanbul",
            normalized_title="waiter",
            normalized_company_name="cafe luna",
            display_title="Waiter",
            display_company_name="Cafe Luna",
            location_city="Istanbul",
            country="Türkiye",
            workplace_type="onsite",
            employment_type="full_time",
            seniority="mid",
            category="hospitality_service",
            department="hospitality",
            description_text="Guest service, food service, POS usage and weekend shifts.",
            posted_at="2026-04-18",
            apply_url="https://cafeluna.example/jobs/waiter",
            trust_score=0.9,
            freshness_score=0.95,
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )

    first = refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T10:00:00Z",
    )
    assert first.refreshed_features == 1
    assert len(repository.list_canonical_job_features(active_only=True)) == 1

    repository.mark_missing_canonical_jobs_inactive(
        seen_canonical_keys=[],
        updated_at="2026-04-18T11:00:00Z",
    )

    second = refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T11:05:00Z",
    )
    assert second.total_jobs_considered == 0
    assert second.refreshed_features == 0
    assert second.pruned_features == 1
    assert repository.list_canonical_job_features(active_only=True) == []
