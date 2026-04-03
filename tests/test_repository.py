from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import JobRecord


def make_job(
    *,
    fingerprint: str,
    source_name: str = "demo-greenhouse",
    title: str = "Backend Engineer",
    company_name: str = "Demo Company",
    location: str = "Remote",
    canonical_url: str = "https://boards.greenhouse.io/demo/jobs/123",
    source_type: str = "greenhouse",
    source_job_id: str | None = "123",
    raw_posted_at: str | None = "2026-04-03",
    posted_at: str | None = "2026-04-03",
    scraped_at: str = "2026-04-03T10:00:00Z",
) -> JobRecord:
    return JobRecord(
        source_name=source_name,
        title=title,
        company_name=company_name,
        location=location,
        canonical_url=canonical_url,
        source_type=source_type,
        source_job_id=source_job_id,
        raw_posted_at=raw_posted_at,
        posted_at=posted_at,
        fingerprint=fingerprint,
        scraped_at=scraped_at,
    )


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "test_hiring_radar.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)

    yield repo

    repo.close()


def test_start_and_finish_crawl_run(repository: HiringRadarRepository) -> None:
    run_id = repository.start_crawl_run(
        source_name="demo-greenhouse",
        started_at="2026-04-03T10:00:00Z",
    )
    repository.finish_crawl_run(
        run_id=run_id,
        finished_at="2026-04-03T10:01:00Z",
        success=True,
        notes="completed successfully",
    )

    crawl_run = repository.get_crawl_run(run_id)

    assert crawl_run is not None
    assert crawl_run.id == run_id
    assert crawl_run.source_name == "demo-greenhouse"
    assert crawl_run.started_at == "2026-04-03T10:00:00Z"
    assert crawl_run.finished_at == "2026-04-03T10:01:00Z"
    assert crawl_run.success is True
    assert crawl_run.notes == "completed successfully"


def test_upsert_job_inserts_new_record(repository: HiringRadarRepository) -> None:
    created = repository.upsert_job(make_job(fingerprint="fp-1"))

    stored = repository.get_job_by_fingerprint("fp-1")

    assert created is True
    assert stored is not None
    assert stored.title == "Backend Engineer"
    assert stored.first_seen_at == "2026-04-03T10:00:00Z"
    assert stored.last_seen_at == "2026-04-03T10:00:00Z"
    assert stored.is_active is True


def test_upsert_job_updates_existing_record_without_duplicate(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-1",
            raw_posted_at="2026-04-03",
            posted_at="2026-04-03",
            scraped_at="2026-04-03T10:00:00Z",
        )
    )

    created = repository.upsert_job(
        make_job(
            fingerprint="fp-1",
            raw_posted_at="3 days ago",
            posted_at=None,
            scraped_at="2026-04-03T11:00:00Z",
        )
    )

    stored = repository.get_job_by_fingerprint("fp-1")
    active_jobs = repository.list_active_jobs()

    assert created is False
    assert stored is not None
    assert stored.first_seen_at == "2026-04-03T10:00:00Z"
    assert stored.last_seen_at == "2026-04-03T11:00:00Z"
    assert stored.raw_posted_at == "3 days ago"
    assert stored.posted_at is None
    assert stored.is_active is True
    assert len(active_jobs) == 1


def test_mark_missing_jobs_inactive_marks_only_missing_jobs_for_source(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(make_job(fingerprint="fp-1", source_name="demo-greenhouse"))
    repository.upsert_job(
        make_job(
            fingerprint="fp-2",
            source_name="demo-greenhouse",
            canonical_url="https://boards.greenhouse.io/demo/jobs/456",
            source_job_id="456",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-3",
            source_name="demo-lever",
            source_type="lever",
            canonical_url="https://jobs.lever.co/demo/789",
            source_job_id="789",
        )
    )

    updated_count = repository.mark_missing_jobs_inactive(
        source_name="demo-greenhouse",
        seen_fingerprints=["fp-1"],
        updated_at="2026-04-03T12:00:00Z",
    )

    job_1 = repository.get_job_by_fingerprint("fp-1")
    job_2 = repository.get_job_by_fingerprint("fp-2")
    job_3 = repository.get_job_by_fingerprint("fp-3")
    active_greenhouse_jobs = repository.list_active_jobs(source_name="demo-greenhouse")

    assert updated_count == 1
    assert job_1 is not None and job_1.is_active is True
    assert job_2 is not None and job_2.is_active is False
    assert job_3 is not None and job_3.is_active is True
    assert [job.fingerprint for job in active_greenhouse_jobs] == ["fp-1"]


def test_list_jobs_returns_all_jobs_including_inactive_in_sorted_order(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-b",
            source_name="demo-lever",
            source_type="lever",
            company_name="Alpha Company",
            title="Site Reliability Engineer",
            canonical_url="https://jobs.lever.co/demo/sre-001",
            source_job_id="sre-001",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-a",
            source_name="demo-greenhouse",
            source_type="greenhouse",
            company_name="Alpha Company",
            title="Backend Engineer",
            canonical_url="https://boards.greenhouse.io/demo/jobs/123",
            source_job_id="123",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-c",
            source_name="demo-custom-static",
            source_type="custom_static",
            company_name="Beta Company",
            title="Data Analyst",
            canonical_url="https://example.com/careers/data-analyst-001",
            source_job_id="data-analyst-001",
        )
    )

    updated_count = repository.mark_missing_jobs_inactive(
        source_name="demo-custom-static",
        seen_fingerprints=[],
        updated_at="2026-04-03T12:30:00Z",
    )

    jobs = repository.list_jobs()

    assert updated_count == 1
    assert len(jobs) == 3
    assert [job.company_name for job in jobs] == [
        "Alpha Company",
        "Alpha Company",
        "Beta Company",
    ]
    assert [job.source_name for job in jobs] == [
        "demo-greenhouse",
        "demo-lever",
        "demo-custom-static",
    ]
    assert [job.title for job in jobs] == [
        "Backend Engineer",
        "Site Reliability Engineer",
        "Data Analyst",
    ]
    assert [job.is_active for job in jobs] == [True, True, False]