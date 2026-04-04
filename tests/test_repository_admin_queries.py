from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import JobRecord


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "test.db"))
    return HiringRadarRepository(connection), connection


def _job(
    *,
    title: str,
    company_name: str,
    source_name: str,
    canonical_url: str,
    is_active: bool = True,
    first_seen_at: str = "2026-04-04T10:00:00Z",
) -> JobRecord:
    return JobRecord(
        source_name=source_name,
        title=title,
        company_name=company_name,
        location="Remote",
        canonical_url=canonical_url,
        source_type="lever",
        source_job_id=canonical_url.rsplit("/", maxsplit=1)[-1],
        raw_posted_at=None,
        posted_at=None,
        fingerprint=canonical_url,
        first_seen_at=first_seen_at,
        last_seen_at=first_seen_at,
        is_active=is_active,
        scraped_at=first_seen_at,
    )


def test_list_jobs_paginated_filters_and_counts(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        repo.upsert_job(
            _job(
                title="Security Engineer",
                company_name="Corelight",
                source_name="corelight-greenhouse",
                canonical_url="https://example.com/jobs/1",
            )
        )
        repo.upsert_job(
            _job(
                title="Growth Marketing Manager",
                company_name="Corelight",
                source_name="corelight-greenhouse",
                canonical_url="https://example.com/jobs/2",
            )
        )
        repo.upsert_job(
            _job(
                title="Backend Engineer",
                company_name="Trendyol",
                source_name="trendyol-lever",
                canonical_url="https://example.com/jobs/3",
            )
        )
        repo.mark_missing_jobs_inactive(
            "corelight-greenhouse",
            seen_fingerprints=("https://example.com/jobs/1",),
            updated_at="2026-04-04T11:00:00Z",
        )

        jobs, total_items = repo.list_jobs_paginated(
            q="Engineer",
            source_name="corelight-greenhouse",
            is_active=True,
            page=1,
            page_size=10,
        )

        assert total_items == 1
        assert [job.title for job in jobs] == ["Security Engineer"]
    finally:
        close_connection(connection)


def test_list_crawl_runs_notification_runs_and_subscribers_paginated(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        run_id_1 = repo.start_crawl_run("trendyol-lever", "2026-04-04T10:00:00Z")
        repo.finish_crawl_run(run_id_1, "2026-04-04T10:01:00Z", True, "ok")

        run_id_2 = repo.start_crawl_run("corelight-greenhouse", "2026-04-04T11:00:00Z")
        repo.finish_crawl_run(run_id_2, "2026-04-04T11:01:00Z", False, "429")

        notification_run_id = repo.start_notification_run(
            notification_type="digest_email",
            started_at="2026-04-04T12:00:00Z",
            since="2026-04-04T06:00:00Z",
        )
        repo.finish_notification_run(
            notification_run_id,
            finished_at="2026-04-04T12:00:10Z",
            status="sent",
            recipient_count=2,
            new_jobs_count=5,
            subject="Digest",
        )

        subscriber_1, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice",
            updated_at="2026-04-04T13:00:00Z",
        )
        repo.upsert_subscriber(
            email="bob@example.com",
            full_name="Bob",
            updated_at="2026-04-04T13:05:00Z",
        )
        updated_subscriber = repo.update_subscriber_fields_by_id(
            subscriber_1.id or 0,
            fields={
                "full_name": None,
                "is_active": False,
                "digest_enabled": False,
            },
            updated_at="2026-04-04T14:00:00Z",
        )

        crawl_runs, crawl_total = repo.list_crawl_runs_paginated(
            success=False,
            page=1,
            page_size=10,
        )
        notification_runs, notification_total = repo.list_notification_runs_paginated(
            notification_type="digest_email",
            status="sent",
            page=1,
            page_size=10,
        )
        subscribers, subscriber_total = repo.list_subscribers_paginated(
            email_query="bob",
            page=1,
            page_size=10,
        )

        assert crawl_total == 1
        assert crawl_runs[0].source_name == "corelight-greenhouse"

        assert notification_total == 1
        assert notification_runs[0].status == "sent"

        assert subscriber_total == 1
        assert subscribers[0].email == "bob@example.com"

        assert updated_subscriber is not None
        assert updated_subscriber.full_name is None
        assert updated_subscriber.is_active is False
        assert updated_subscriber.digest_enabled is False
    finally:
        close_connection(connection)