from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import JobRecord
from hiring_radar.services.digest import (
    build_digest,
    render_digest_subject,
    render_digest_text,
)


def make_job(
    *,
    fingerprint: str,
    source_name: str,
    company_name: str,
    source_type: str,
    title: str,
    canonical_url: str,
    source_job_id: str,
    location: str | None = "Remote",
    scraped_at: str,
) -> JobRecord:
    return JobRecord(
        source_name=source_name,
        title=title,
        company_name=company_name,
        location=location,
        canonical_url=canonical_url,
        source_type=source_type,
        source_job_id=source_job_id,
        raw_posted_at=None,
        posted_at=None,
        fingerprint=fingerprint,
        scraped_at=scraped_at,
    )


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "test_digest_service.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)

    yield repo

    repo.close()


def test_build_digest_groups_new_jobs_by_source(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-old",
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
    repository.upsert_job(
        make_job(
            fingerprint="fp-new-3",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Backend Engineer",
            canonical_url="https://jobs.lever.co/trendyol/backend-engineer-001",
            source_job_id="backend-engineer-001",
            scraped_at="2026-04-03T12:30:00Z",
        )
    )

    repository.mark_missing_jobs_inactive(
        source_name="threee-lever",
        seen_fingerprints=[],
        updated_at="2026-04-03T13:00:00Z",
    )

    digest = build_digest(
        repository,
        since="2026-04-03T11:00:00Z",
        generated_at="2026-04-04T00:00:00Z",
    )

    assert digest.generated_at == "2026-04-04T00:00:00Z"
    assert digest.since == "2026-04-03T11:00:00Z"
    assert digest.total_new_jobs == 3
    assert len(digest.sections) == 2

    first_section = digest.sections[0]
    second_section = digest.sections[1]

    assert first_section.source_name == "trendyol-lever"
    assert first_section.source_type == "lever"
    assert first_section.new_jobs_count == 2
    assert [job.title for job in first_section.jobs] == [
        "Data Engineer",
        "Backend Engineer",
    ]

    assert second_section.source_name == "threee-lever"
    assert second_section.source_type == "lever"
    assert second_section.new_jobs_count == 1
    assert [job.title for job in second_section.jobs] == [
        "Product Security Engineer",
    ]
    assert second_section.jobs[0].company_name == "3E"
    assert second_section.jobs[0].location == "Remote"


def test_build_digest_can_filter_by_source(
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

    digest = build_digest(
        repository,
        since="2026-04-03T10:30:00Z",
        generated_at="2026-04-04T00:00:00Z",
        source_name="corelight-greenhouse",
    )

    assert digest.total_new_jobs == 1
    assert len(digest.sections) == 1
    assert digest.sections[0].source_name == "corelight-greenhouse"
    assert digest.sections[0].source_type == "greenhouse"
    assert digest.sections[0].new_jobs_count == 1
    assert digest.sections[0].jobs[0].title == "Security Engineer"


def test_build_digest_returns_empty_sections_for_empty_window(
    repository: HiringRadarRepository,
) -> None:
    digest = build_digest(
        repository,
        since="2026-04-03T10:30:00Z",
        generated_at="2026-04-04T00:00:00Z",
    )

    assert digest.generated_at == "2026-04-04T00:00:00Z"
    assert digest.since == "2026-04-03T10:30:00Z"
    assert digest.total_new_jobs == 0
    assert digest.sections == []


def test_render_digest_subject_and_text_for_non_empty_digest(
    repository: HiringRadarRepository,
) -> None:
    repository.upsert_job(
        make_job(
            fingerprint="fp-new-1",
            source_name="threee-lever",
            company_name="3E",
            source_type="lever",
            title="Growth Marketing Manager",
            canonical_url="https://jobs.lever.co/3eco/1b69296f-f446-49e6-80d6-e73fe19f2ccc",
            source_job_id="1b69296f-f446-49e6-80d6-e73fe19f2ccc",
            location="Bethesda, Maryland",
            scraped_at="2026-04-03T15:51:23Z",
        )
    )

    digest = build_digest(
        repository,
        since="2026-04-03T15:00:00Z",
        generated_at="2026-04-04T00:00:00Z",
    )

    subject = render_digest_subject(digest)
    body = render_digest_text(digest)

    assert subject == "Hiring Radar Digest: 1 new job since 2026-04-03T15:00:00Z"
    assert "Hiring Radar Digest" in body
    assert "since=2026-04-03T15:00:00Z" in body
    assert "generated_at=2026-04-04T00:00:00Z" in body
    assert "threee-lever (lever): 1" in body
    assert "Growth Marketing Manager — Bethesda, Maryland" in body
    assert "3E | first_seen_at=2026-04-03T15:51:23Z" in body
    assert "https://jobs.lever.co/3eco/1b69296f-f446-49e6-80d6-e73fe19f2ccc" in body


def test_render_digest_text_for_empty_digest(
    repository: HiringRadarRepository,
) -> None:
    digest = build_digest(
        repository,
        since="2026-04-03T15:00:00Z",
        generated_at="2026-04-04T00:00:00Z",
    )

    subject = render_digest_subject(digest)
    body = render_digest_text(digest)

    assert subject == "Hiring Radar Digest: 0 new jobs since 2026-04-03T15:00:00Z"
    assert "New jobs" in body
    assert "  total=0" in body
    assert "  no new jobs in this window" in body