from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import JobRecord
from hiring_radar.services.summary import build_summary


def make_job(
    *,
    fingerprint: str,
    source_name: str,
    company_name: str,
    source_type: str,
    title: str,
    canonical_url: str,
    source_job_id: str,
    location: str = "Remote",
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
        raw_posted_at=None,
        posted_at=None,
        fingerprint=fingerprint,
        scraped_at=scraped_at,
    )


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "test_summary_service.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)

    yield repo

    repo.close()


def test_build_summary_returns_expected_overall_source_and_company_counts(
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
        updated_at="2026-04-03T13:10:00Z",
    )

    summary = build_summary(repository)

    assert summary.overall.total_jobs == 3
    assert summary.overall.active_jobs == 2
    assert summary.overall.inactive_jobs == 1

    assert len(summary.by_source) == 2

    assert summary.by_source[0].source_name == "corelight-greenhouse"
    assert summary.by_source[0].source_type == "greenhouse"
    assert summary.by_source[0].total_jobs == 1
    assert summary.by_source[0].active_jobs == 1
    assert summary.by_source[0].inactive_jobs == 0

    assert summary.by_source[1].source_name == "trendyol-lever"
    assert summary.by_source[1].source_type == "lever"
    assert summary.by_source[1].total_jobs == 2
    assert summary.by_source[1].active_jobs == 1
    assert summary.by_source[1].inactive_jobs == 1

    assert summary.by_source[0].source_name == "corelight-greenhouse"
    assert summary.by_source[0].source_type == "greenhouse"
    assert summary.by_source[0].total_jobs == 1
    assert summary.by_source[0].active_jobs == 1
    assert summary.by_source[0].inactive_jobs == 0

    assert summary.by_source[1].source_name == "trendyol-lever"
    assert summary.by_source[1].source_type == "lever"
    assert summary.by_source[1].total_jobs == 2
    assert summary.by_source[1].active_jobs == 1
    assert summary.by_source[1].inactive_jobs == 1

    assert summary.by_company[0].company_name == "Corelight"
    assert summary.by_company[0].total_jobs == 1
    assert summary.by_company[0].active_jobs == 1
    assert summary.by_company[0].inactive_jobs == 0

    assert summary.by_company[1].company_name == "Trendyol"
    assert summary.by_company[1].total_jobs == 2
    assert summary.by_company[1].active_jobs == 1
    assert summary.by_company[1].inactive_jobs == 1


def test_build_summary_returns_zero_counts_for_empty_repository(
    repository: HiringRadarRepository,
) -> None:
    summary = build_summary(repository)

    assert summary.overall.total_jobs == 0
    assert summary.overall.active_jobs == 0
    assert summary.overall.inactive_jobs == 0
    assert summary.by_source == []
    assert summary.by_company == []
