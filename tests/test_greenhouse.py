"""Placeholder module for the bootstrap phase."""
from __future__ import annotations

from pathlib import Path

from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.greenhouse import GreenhouseScraper


def test_greenhouse_scraper_parses_fixture() -> None:
    fixture_path = Path("tests/fixtures/greenhouse_sample.html")
    html = fixture_path.read_text(encoding="utf-8")

    config = ScraperSourceConfig(
        source_name="demo-greenhouse",
        company_name="Demo Company",
        source_type="greenhouse",
        url="https://boards.greenhouse.io/demo-company",
    )
    scraper = GreenhouseScraper(config)

    jobs = scraper.parse(html, scraped_at="2026-04-03T15:30:00Z")

    assert len(jobs) == 2

    first_job = jobs[0]
    second_job = jobs[1]

    assert first_job.source_name == "demo-greenhouse"
    assert first_job.title == "Backend Engineer"
    assert first_job.company_name == "Demo Company"
    assert first_job.location == "Remote - Turkey"
    assert first_job.canonical_url == "https://boards.greenhouse.io/demo-company/jobs/123456"
    assert first_job.source_type == "greenhouse"
    assert first_job.source_job_id == "123456"
    assert first_job.scraped_at == "2026-04-03T15:30:00Z"
    assert first_job.is_active is True
    assert first_job.fingerprint

    assert second_job.title == "Data Engineer"
    assert second_job.location == "Istanbul, Turkey"
    assert second_job.canonical_url == "https://boards.greenhouse.io/demo-company/jobs/789012"
    assert second_job.source_job_id == "789012"