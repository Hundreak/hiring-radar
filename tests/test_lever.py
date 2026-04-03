from __future__ import annotations

from pathlib import Path

from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.lever import LeverScraper


def test_lever_scraper_parses_fixture() -> None:
    fixture_path = Path("tests/fixtures/lever_sample.html")
    html = fixture_path.read_text(encoding="utf-8")

    config = ScraperSourceConfig(
        source_name="demo-lever",
        company_name="Demo Company",
        source_type="lever",
        url="https://jobs.lever.co/demo-company",
    )
    scraper = LeverScraper(config)

    jobs = scraper.parse(html, scraped_at="2026-04-03T16:00:00Z")

    assert len(jobs) == 2

    first_job = jobs[0]
    second_job = jobs[1]

    assert first_job.source_name == "demo-lever"
    assert first_job.title == "Backend Engineer"
    assert first_job.company_name == "Demo Company"
    assert first_job.location == "Remote - Turkey"
    assert first_job.canonical_url == "https://jobs.lever.co/demo-company/backend-engineer-abc123"
    assert first_job.source_type == "lever"
    assert first_job.source_job_id == "backend-engineer-abc123"
    assert first_job.scraped_at == "2026-04-03T16:00:00Z"
    assert first_job.is_active is True
    assert first_job.fingerprint

    assert second_job.title == "Data Engineer"
    assert second_job.location == "Istanbul, Turkey"
    assert second_job.canonical_url == "https://jobs.lever.co/demo-company/data-engineer-def456"
    assert second_job.source_job_id == "data-engineer-def456"