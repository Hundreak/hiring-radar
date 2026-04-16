from __future__ import annotations

from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.filtering.service import (
    build_filterable_job_text,
    filter_jobs_by_keyword_settings,
)
from hiring_radar.models import JobRecord


def _job(
    *,
    title: str,
    company_name: str,
    location: str | None,
    canonical_url: str,
) -> JobRecord:
    return JobRecord(
        source_name="example-source",
        title=title,
        company_name=company_name,
        location=location,
        canonical_url=canonical_url,
        source_type="lever",
        source_job_id=canonical_url.rsplit("/", maxsplit=1)[-1],
        raw_posted_at=None,
        posted_at=None,
        fingerprint=canonical_url,
        first_seen_at="2026-04-04T10:00:00Z",
        last_seen_at="2026-04-04T10:00:00Z",
        is_active=True,
        scraped_at="2026-04-04T10:00:00Z",
    )


def test_build_filterable_job_text_maps_job_record_fields() -> None:
    job = _job(
        title="Senior Python Engineer",
        company_name="Trendyol",
        location="Istanbul",
        canonical_url="https://example.com/jobs/1",
    )

    result = build_filterable_job_text(job=job)

    assert result.title == "Senior Python Engineer"
    assert result.company_name == "Trendyol"
    assert result.location == "Istanbul"


def test_filter_jobs_by_keyword_settings_partitions_jobs() -> None:
    jobs = [
        _job(
            title="Senior Python Engineer",
            company_name="Trendyol",
            location="Istanbul",
            canonical_url="https://example.com/jobs/1",
        ),
        _job(
            title="Python Intern",
            company_name="ExampleCo",
            location="Remote",
            canonical_url="https://example.com/jobs/2",
        ),
        _job(
            title="Frontend Engineer",
            company_name="ExampleCo",
            location="Ankara",
            canonical_url="https://example.com/jobs/3",
        ),
    ]
    settings = KeywordFilterSettings(
        include_keywords=("python",),
        exclude_keywords=("intern",),
        match_title=True,
        match_location=False,
        match_company_name=False,
    )

    result = filter_jobs_by_keyword_settings(
        jobs=jobs,
        settings=settings,
    )

    assert result.total_jobs == 3
    assert result.passed_count == 1
    assert result.rejected_count == 2
    assert tuple(job.title for job in result.passed_jobs) == ("Senior Python Engineer",)
    assert tuple(job.title for job in result.rejected_jobs) == (
        "Python Intern",
        "Frontend Engineer",
    )


def test_filter_jobs_by_keyword_settings_returns_all_jobs_as_passed_when_disabled() -> None:
    jobs = [
        _job(
            title="Data Engineer",
            company_name="ExampleCo",
            location=None,
            canonical_url="https://example.com/jobs/1",
        ),
        _job(
            title="Backend Engineer",
            company_name="ExampleCo",
            location="Remote",
            canonical_url="https://example.com/jobs/2",
        ),
    ]
    settings = KeywordFilterSettings()

    result = filter_jobs_by_keyword_settings(
        jobs=jobs,
        settings=settings,
    )

    assert result.total_jobs == 2
    assert result.passed_count == 2
    assert result.rejected_count == 0
