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


def test_get_job_counts_returns_overall_totals(repository: HiringRadarRepository) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-1",
            source_name="corelight-greenhouse",
            company_name="Corelight",
            source_type="greenhouse",
            title="Security Engineer",
            canonical_url="https://boards.greenhouse.io/corelight/jobs/7751102",
            source_job_id="7751102",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-2",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Data Engineer",
            canonical_url="https://jobs.lever.co/trendyol/data-engineer-001",
            source_job_id="data-engineer-001",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-3",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Backend Engineer",
            canonical_url="https://jobs.lever.co/trendyol/backend-engineer-001",
            source_job_id="backend-engineer-001",
        )
    )

    repository.mark_missing_jobs_inactive(
        source_name="trendyol-lever",
        seen_fingerprints=["fp-2"],
        updated_at="2026-04-03T13:00:00Z",
    )

    counts = repository.get_job_counts()

    assert counts == {
        "total_jobs": 3,
        "active_jobs": 2,
        "inactive_jobs": 1,
    }


def test_summary_rows_group_by_source_and_company(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-1",
            source_name="corelight-greenhouse",
            company_name="Corelight",
            source_type="greenhouse",
            title="Security Engineer",
            canonical_url="https://boards.greenhouse.io/corelight/jobs/7751102",
            source_job_id="7751102",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-2",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Data Engineer",
            canonical_url="https://jobs.lever.co/trendyol/data-engineer-001",
            source_job_id="data-engineer-001",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-3",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Backend Engineer",
            canonical_url="https://jobs.lever.co/trendyol/backend-engineer-001",
            source_job_id="backend-engineer-001",
        )
    )

    repository.mark_missing_jobs_inactive(
        source_name="trendyol-lever",
        seen_fingerprints=["fp-2"],
        updated_at="2026-04-03T13:05:00Z",
    )

    source_rows = repository.get_source_summary_rows()
    company_rows = repository.get_company_summary_rows()

    assert source_rows == [
        {
            "source_name": "corelight-greenhouse",
            "source_type": "greenhouse",
            "total_jobs": 1,
            "active_jobs": 1,
            "inactive_jobs": 0,
        },
        {
            "source_name": "trendyol-lever",
            "source_type": "lever",
            "total_jobs": 2,
            "active_jobs": 1,
            "inactive_jobs": 1,
        },
    ]

    assert company_rows == [
        {
            "company_name": "Corelight",
            "total_jobs": 1,
            "active_jobs": 1,
            "inactive_jobs": 0,
        },
        {
            "company_name": "Trendyol",
            "total_jobs": 2,
            "active_jobs": 1,
            "inactive_jobs": 1,
        },
    ]


def test_list_jobs_first_seen_since_returns_new_jobs_in_sorted_order(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-early",
            source_name="corelight-greenhouse",
            company_name="Corelight",
            source_type="greenhouse",
            title="Security Engineer",
            canonical_url="https://boards.greenhouse.io/corelight/jobs/7751102",
            source_job_id="7751102",
            scraped_at="2026-04-03T09:00:00Z",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-new-1",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Data Engineer",
            canonical_url="https://jobs.lever.co/trendyol/data-engineer-001",
            source_job_id="data-engineer-001",
            scraped_at="2026-04-03T11:00:00Z",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-new-2",
            source_name="threee-lever",
            company_name="3E",
            source_type="lever",
            title="Product Security Engineer",
            canonical_url="https://jobs.lever.co/3eco/product-security-engineer-001",
            source_job_id="product-security-engineer-001",
            scraped_at="2026-04-03T12:00:00Z",
        )
    )

    repository.mark_missing_jobs_inactive(
        source_name="threee-lever",
        seen_fingerprints=[],
        updated_at="2026-04-03T13:00:00Z",
    )

    jobs = repository.list_jobs_first_seen_since("2026-04-03T11:00:00Z")

    assert len(jobs) == 2
    assert [job.fingerprint for job in jobs] == ["fp-new-1", "fp-new-2"]
    assert [job.company_name for job in jobs] == ["Trendyol", "3E"]
    assert [job.first_seen_at for job in jobs] == [
        "2026-04-03T11:00:00Z",
        "2026-04-03T12:00:00Z",
    ]
    assert [job.is_active for job in jobs] == [True, False]


def test_list_jobs_first_seen_since_can_filter_by_source(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-a",
            source_name="corelight-greenhouse",
            company_name="Corelight",
            source_type="greenhouse",
            title="Security Engineer",
            canonical_url="https://boards.greenhouse.io/corelight/jobs/7751102",
            source_job_id="7751102",
            scraped_at="2026-04-03T11:00:00Z",
        )
    )
    repository.upsert_job(
        make_job(
            fingerprint="fp-b",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Data Engineer",
            canonical_url="https://jobs.lever.co/trendyol/data-engineer-001",
            source_job_id="data-engineer-001",
            scraped_at="2026-04-03T11:05:00Z",
        )
    )

    jobs = repository.list_jobs_first_seen_since(
        "2026-04-03T10:30:00Z",
        source_name="corelight-greenhouse",
    )

    assert len(jobs) == 1
    assert jobs[0].fingerprint == "fp-a"
    assert jobs[0].source_name == "corelight-greenhouse"


def test_upsert_subscriber_inserts_new_subscriber(
    repository: HiringRadarRepository,
) -> None:
    subscriber, created = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-04T09:00:00Z",
    )

    stored = repository.get_subscriber_by_email("alice@example.com")

    assert created is True
    assert subscriber.email == "alice@example.com"
    assert subscriber.full_name == "Alice Example"
    assert subscriber.is_active is True
    assert subscriber.digest_enabled is True
    assert subscriber.created_at == "2026-04-04T09:00:00Z"
    assert subscriber.updated_at == "2026-04-04T09:00:00Z"

    assert stored is not None
    assert stored.email == "alice@example.com"


def test_upsert_subscriber_updates_existing_and_reactivates(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-04T09:00:00Z",
    )
    repository.set_subscriber_active(
        email="alice@example.com",
        is_active=False,
        updated_at="2026-04-04T09:10:00Z",
    )
    repository.set_subscriber_digest_enabled(
        email="alice@example.com",
        digest_enabled=False,
        updated_at="2026-04-04T09:11:00Z",
    )

    subscriber, created = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Updated",
        updated_at="2026-04-04T09:20:00Z",
    )

    assert created is False
    assert subscriber.email == "alice@example.com"
    assert subscriber.full_name == "Alice Updated"
    assert subscriber.is_active is True
    assert subscriber.digest_enabled is True
    assert subscriber.created_at == "2026-04-04T09:00:00Z"
    assert subscriber.updated_at == "2026-04-04T09:20:00Z"


def test_list_subscribers_and_digest_enabled_subscribers(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_subscriber(
        email="zeta@example.com",
        full_name="Zeta User",
        updated_at="2026-04-04T09:00:00Z",
    )
    repository.upsert_subscriber(
        email="alpha@example.com",
        full_name="Alpha User",
        updated_at="2026-04-04T09:01:00Z",
    )
    repository.upsert_subscriber(
        email="beta@example.com",
        full_name="Beta User",
        updated_at="2026-04-04T09:02:00Z",
    )

    repository.set_subscriber_digest_enabled(
        email="beta@example.com",
        digest_enabled=False,
        updated_at="2026-04-04T09:10:00Z",
    )
    repository.set_subscriber_active(
        email="zeta@example.com",
        is_active=False,
        updated_at="2026-04-04T09:11:00Z",
    )

    all_subscribers = repository.list_subscribers()
    digest_enabled_subscribers = repository.list_digest_enabled_subscribers()

    assert [subscriber.email for subscriber in all_subscribers] == [
        "alpha@example.com",
        "beta@example.com",
        "zeta@example.com",
    ]
    assert [subscriber.email for subscriber in digest_enabled_subscribers] == [
        "alpha@example.com",
    ]


def test_set_subscriber_flags_returns_false_for_missing_email(
    repository: HiringRadarRepository,
) -> None:
    active_updated = repository.set_subscriber_active(
        email="missing@example.com",
        is_active=False,
        updated_at="2026-04-04T09:30:00Z",
    )
    digest_updated = repository.set_subscriber_digest_enabled(
        email="missing@example.com",
        digest_enabled=False,
        updated_at="2026-04-04T09:31:00Z",
    )

    assert active_updated is False
    assert digest_updated is False
