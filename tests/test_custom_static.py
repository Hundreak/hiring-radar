from __future__ import annotations

from pathlib import Path

from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.custom_static import CustomStaticScraper


def test_custom_static_scraper_parses_fixture() -> None:
    fixture_path = Path("tests/fixtures/custom_static_sample.html")
    html = fixture_path.read_text(encoding="utf-8")

    config = ScraperSourceConfig(
        source_name="demo-custom-static",
        company_name="Example Company",
        source_type="custom_static",
        url="https://example.com/careers",
    )
    scraper = CustomStaticScraper(config)

    jobs = scraper.parse(html, scraped_at="2026-04-03T16:30:00Z")

    assert len(jobs) == 2

    first_job = jobs[0]
    second_job = jobs[1]

    assert first_job.source_name == "demo-custom-static"
    assert first_job.title == "Senior Backend Engineer"
    assert first_job.company_name == "Example Company"
    assert first_job.location == "Remote - Europe"
    assert first_job.canonical_url == "https://example.com/careers/senior-backend-engineer-001"
    assert first_job.source_type == "custom_static"
    assert first_job.source_job_id == "senior-backend-engineer-001"
    assert first_job.scraped_at == "2026-04-03T16:30:00Z"
    assert first_job.is_active is True
    assert first_job.fingerprint

    assert second_job.title == "Data Platform Engineer"
    assert second_job.location == "Istanbul, Turkey"
    assert second_job.canonical_url == "https://example.com/careers/data-platform-engineer-002"
    assert second_job.source_job_id == "data-platform-engineer-002"
