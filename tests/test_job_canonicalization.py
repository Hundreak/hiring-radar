from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import JobSource, JobSourceRecord
from hiring_radar.services.jobs.canonicalization import refresh_canonical_jobs


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "job_canonicalization.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


def test_refresh_canonical_jobs_merges_cross_source_duplicates(
    repository: HiringRadarRepository,
) -> None:
    greenhouse = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme",
            trust_score=0.94,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )
    lever = repository.upsert_job_source(
        JobSource(
            source_type="lever",
            source_name="acme-lever",
            account_slug="acme",
            base_url="https://jobs.lever.co/acme",
            trust_score=0.97,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )

    repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=greenhouse.id or 0,
            external_job_id="gh-1",
            raw_payload_json='{"description":"<p>Build reliable pipelines.</p>"}',
            raw_payload_hash="gh-hash-1",
            canonical_url="https://boards.greenhouse.io/acme/jobs/1",
            title="Data Engineer",
            company_name="Acme",
            location_text="Berlin, Germany",
            posted_at="2026-04-18",
            apply_url="https://apply.acme.com/jobs/data-engineer",
            fetched_at="2026-04-18T09:15:00Z",
            is_active=True,
        )
    )
    repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=lever.id or 0,
            external_job_id="lv-9",
            raw_payload_json='{"description":"<div>Build reliable pipelines and analytics products.</div>"}',
            raw_payload_hash="lv-hash-9",
            canonical_url="https://jobs.lever.co/acme/data-engineer",
            title="Data Engineer",
            company_name="Acme",
            location_text="Berlin, Germany",
            posted_at="2026-04-18",
            apply_url="https://apply.acme.com/jobs/data-engineer",
            fetched_at="2026-04-18T09:18:00Z",
            is_active=True,
        )
    )

    result = refresh_canonical_jobs(repository, refreshed_at="2026-04-18T10:00:00Z")

    assert result.total_active_records == 2
    assert result.grouped_jobs == 1
    assert result.upserted_jobs == 1
    assert result.deactivated_jobs == 0
    assert result.links_upserted == 2
    assert result.links_pruned == 0

    stored_jobs = repository.list_canonical_jobs(active_only=True)
    assert len(stored_jobs) == 1
    stored = stored_jobs[0]
    assert stored.display_title == "Data Engineer"
    assert stored.display_company_name == "Acme"
    assert stored.location_city == "Berlin"
    assert stored.apply_url == "https://apply.acme.com/jobs/data-engineer"
    assert stored.trust_score == pytest.approx(1.0)
    assert stored.description_text == "Build reliable pipelines and analytics products."

    links = repository.list_canonical_job_links(canonical_job_id=stored.id or 0)
    assert len(links) == 2
    assert {link.merge_reason for link in links} == {"exact_apply_url_and_title"}
    assert all(link.confidence == pytest.approx(0.99) for link in links)


def test_refresh_canonical_jobs_deactivates_missing_groups_and_prunes_links(
    repository: HiringRadarRepository,
) -> None:
    source = repository.upsert_job_source(
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
    record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="gh-2",
            raw_payload_json='{"description":"<p>Run platform systems.</p>"}',
            raw_payload_hash="gh-hash-2",
            canonical_url="https://boards.greenhouse.io/acme/jobs/2",
            title="Platform Engineer",
            company_name="Acme",
            location_text="Remote - Europe",
            posted_at="2026-04-18",
            apply_url="https://apply.acme.com/jobs/platform-engineer",
            fetched_at="2026-04-18T09:15:00Z",
            is_active=True,
        )
    )

    first_result = refresh_canonical_jobs(repository, refreshed_at="2026-04-18T10:00:00Z")
    assert first_result.grouped_jobs == 1
    first_jobs = repository.list_canonical_jobs(active_only=True)
    assert len(first_jobs) == 1
    first_links = repository.list_canonical_job_links(canonical_job_id=first_jobs[0].id or 0)
    assert len(first_links) == 1
    assert first_links[0].source_job_id == record.id

    deactivated_records = repository.mark_missing_job_source_records_inactive(
        source_id=source.id or 0,
        seen_external_job_ids=[],
        updated_at="2026-04-18T11:00:00Z",
    )
    assert deactivated_records == 1

    second_result = refresh_canonical_jobs(repository, refreshed_at="2026-04-18T11:05:00Z")
    assert second_result.total_active_records == 0
    assert second_result.grouped_jobs == 0
    assert second_result.upserted_jobs == 0
    assert second_result.deactivated_jobs == 1
    assert second_result.links_pruned == 1

    assert repository.list_canonical_jobs(active_only=True) == []
    all_jobs = repository.list_canonical_jobs(active_only=False)
    assert len(all_jobs) == 1
    assert all_jobs[0].is_active is False



def test_refresh_canonical_jobs_prefers_high_quality_primary_record_and_computes_quality_signals(
    repository: HiringRadarRepository,
) -> None:
    greenhouse = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="nova-greenhouse",
            account_slug="nova",
            base_url="https://boards.greenhouse.io/nova",
            trust_score=0.94,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )
    custom = repository.upsert_job_source(
        JobSource(
            source_type="custom_static",
            source_name="nova-careers",
            account_slug="nova",
            base_url="https://careers.nova.example",
            trust_score=0.9,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )

    repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=custom.id or 0,
            external_job_id="custom-1",
            raw_payload_json='{"description":"<p>Senior platform role.</p>"}',
            raw_payload_hash="custom-hash-1",
            canonical_url="https://careers.nova.example/jobs/platform",
            title="Senior Platform Engineer",
            company_name="Nova",
            location_text="Berlin, Germany",
            posted_at="2026-04-12",
            apply_url="https://apply.nova.example/jobs/platform",
            fetched_at="2026-04-18T09:05:00Z",
            is_active=True,
        )
    )
    repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=greenhouse.id or 0,
            external_job_id="gh-77",
            raw_payload_json='{"description":"<p>Senior Platform Engineer role. Build and operate distributed systems across Europe. Full-time position partnering with product, security, data and developer experience teams. You will lead reliability improvements, mentor engineers, own incident response and deliver platform foundations for multi-region services.</p>"}',
            raw_payload_hash="gh-hash-77",
            canonical_url="https://boards.greenhouse.io/nova/jobs/77",
            title="Senior Platform Engineer",
            company_name="Nova",
            location_text="Berlin, Germany",
            posted_at="2026-04-18",
            apply_url="https://apply.nova.example/jobs/platform",
            fetched_at="2026-04-18T09:10:00Z",
            is_active=True,
        )
    )

    result = refresh_canonical_jobs(repository, refreshed_at="2026-04-18T10:00:00Z")

    assert result.grouped_jobs == 1
    assert result.source_links_total == 2

    stored = repository.list_canonical_jobs(active_only=True)[0]
    assert stored.display_title == "Senior Platform Engineer"
    assert stored.country == "Germany"
    assert stored.seniority == "senior"
    assert stored.employment_type == "full_time"
    assert stored.trust_score >= 0.96
    assert stored.freshness_score >= 0.9
    assert stored.description_text is not None
    assert "distributed systems" in stored.description_text


def test_refresh_canonical_jobs_uses_last_seen_when_posted_at_is_stale(
    repository: HiringRadarRepository,
) -> None:
    source = repository.upsert_job_source(
        JobSource(
            source_type="lever",
            source_name="orbit-lever",
            account_slug="orbit",
            base_url="https://jobs.lever.co/orbit",
            trust_score=0.95,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )
    repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="orbit-1",
            raw_payload_json='{"description":"<p>Lead backend systems.</p>"}',
            raw_payload_hash="orbit-hash-1",
            canonical_url="https://jobs.lever.co/orbit/backend",
            title="Lead Backend Engineer",
            company_name="Orbit",
            location_text="Remote",
            posted_at="2026-02-01",
            apply_url="https://jobs.lever.co/orbit/backend",
            fetched_at="2026-04-18T09:20:00Z",
            is_active=True,
        )
    )

    refresh_canonical_jobs(repository, refreshed_at="2026-04-18T10:00:00Z")
    stored = repository.list_canonical_jobs(active_only=True)[0]

    assert stored.freshness_score >= 0.35
    assert stored.workplace_type == "remote"
    assert stored.seniority == "lead"
