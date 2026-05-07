from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import CanonicalJob, CanonicalJobLink, JobSource, JobSourceRecord


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "job_corpus.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


def test_upsert_job_source_is_idempotent(repository: HiringRadarRepository) -> None:
    created = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme",
            trust_score=0.95,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )

    updated = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme-tech",
            trust_score=0.97,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T10:00:00Z",
        )
    )

    assert created.id is not None
    assert updated.id == created.id
    assert updated.base_url == "https://boards.greenhouse.io/acme-tech"
    assert updated.trust_score == pytest.approx(0.97)


def test_job_source_record_preserves_first_seen_and_updates_last_seen(
    repository: HiringRadarRepository,
) -> None:
    source = repository.upsert_job_source(
        JobSource(
            source_type="lever",
            source_name="acme-lever",
            account_slug="acme",
            base_url="https://jobs.lever.co/acme",
            trust_score=0.95,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )

    first = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="job-001",
            raw_payload_json='{"title":"Backend Engineer"}',
            raw_payload_hash="hash-1",
            canonical_url="https://jobs.lever.co/acme/job-001",
            title="Backend Engineer",
            company_name="Acme",
            location_text="Istanbul, Türkiye",
            posted_at="2026-04-18",
            apply_url="https://jobs.lever.co/acme/job-001/apply",
            fetched_at="2026-04-18T09:10:00Z",
            is_active=True,
        )
    )

    second = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="job-001",
            raw_payload_json='{"title":"Senior Backend Engineer"}',
            raw_payload_hash="hash-2",
            canonical_url="https://jobs.lever.co/acme/job-001",
            title="Senior Backend Engineer",
            company_name="Acme",
            location_text="Remote",
            posted_at="2026-04-19",
            apply_url="https://jobs.lever.co/acme/job-001/apply",
            fetched_at="2026-04-18T10:10:00Z",
            is_active=True,
        )
    )

    assert first.id == second.id
    assert second.first_seen_at == "2026-04-18T09:10:00Z"
    assert second.last_seen_at == "2026-04-18T10:10:00Z"
    assert second.raw_payload_hash == "hash-2"
    assert second.title == "Senior Backend Engineer"


def test_canonical_job_and_link_roundtrip(repository: HiringRadarRepository) -> None:
    source = repository.upsert_job_source(
        JobSource(
            source_type="smartrecruiters",
            source_name="acme-smartrecruiters",
            account_slug="acme",
            base_url="https://jobs.smartrecruiters.com/Acme",
            trust_score=0.93,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )
    source_record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="sr-77",
            raw_payload_json='{"title":"Data Engineer"}',
            raw_payload_hash="payload-77",
            canonical_url="https://jobs.smartrecruiters.com/Acme/data-engineer-77",
            title="Data Engineer",
            company_name="Acme",
            location_text="Berlin",
            posted_at="2026-04-18",
            apply_url="https://jobs.smartrecruiters.com/Acme/data-engineer-77",
            fetched_at="2026-04-18T09:15:00Z",
            is_active=True,
        )
    )

    canonical = repository.upsert_canonical_job(
        CanonicalJob(
            canonical_key="acme|data engineer|berlin|https://jobs.smartrecruiters.com/Acme/data-engineer-77",
            normalized_title="data engineer",
            normalized_company_name="acme",
            display_title="Data Engineer",
            display_company_name="Acme",
            location_city="Berlin",
            country="Germany",
            workplace_type="hybrid",
            employment_type="full_time",
            seniority="mid",
            category="data",
            department="engineering",
            description_text="Build reliable data pipelines.",
            posted_at="2026-04-18",
            apply_url="https://jobs.smartrecruiters.com/Acme/data-engineer-77",
            trust_score=0.93,
            freshness_score=0.88,
            is_active=True,
            created_at="2026-04-18T09:15:00Z",
            updated_at="2026-04-18T09:15:00Z",
        )
    )

    repository.upsert_canonical_job_link(
        CanonicalJobLink(
            canonical_job_id=canonical.id or 0,
            source_job_id=source_record.id or 0,
            merge_reason="exact_apply_url_and_title",
            confidence=0.98,
            created_at="2026-04-18T09:16:00Z",
            updated_at="2026-04-18T09:16:00Z",
        )
    )

    stored_jobs = repository.list_canonical_jobs(active_only=True)
    links = repository.list_canonical_job_links(canonical_job_id=canonical.id or 0)

    assert len(stored_jobs) == 1
    assert stored_jobs[0].canonical_key == canonical.canonical_key
    assert len(links) == 1
    assert links[0].source_job_id == source_record.id
    assert links[0].confidence == pytest.approx(0.98)
