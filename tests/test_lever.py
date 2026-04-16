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


def test_lever_scraper_ignores_apply_cta_and_uses_real_title() -> None:
    html = """
    <html>
      <body>
        <section>
          <div class="job-row">
            <h3>Product Security Engineer</h3>
            <p>Bethesda, Maryland</p>
            <a href="https://jobs.lever.co/3eco/1b69296f-f446-49e6-80d6-e73fe19f2ccc">Apply</a>
          </div>

          <div class="job-row">
            <h3>Senior Software Engineer</h3>
            <p>Tokyo, Japan</p>
            <a href="https://jobs.lever.co/3eco/373c9b1f-e960-4674-9767-e55353b85205">Apply</a>
          </div>
        </section>
      </body>
    </html>
    """

    config = ScraperSourceConfig(
        source_name="threee-lever",
        company_name="3E",
        source_type="lever",
        url="https://jobs.lever.co/3eco",
    )
    scraper = LeverScraper(config)

    jobs = scraper.parse(html, scraped_at="2026-04-03T18:40:00Z")

    assert len(jobs) == 2

    first_job = jobs[0]
    second_job = jobs[1]

    assert first_job.title == "Product Security Engineer"
    assert first_job.location == "Bethesda, Maryland"
    assert (
        first_job.canonical_url == "https://jobs.lever.co/3eco/1b69296f-f446-49e6-80d6-e73fe19f2ccc"
    )
    assert first_job.source_job_id == "1b69296f-f446-49e6-80d6-e73fe19f2ccc"

    assert second_job.title == "Senior Software Engineer"
    assert second_job.location == "Tokyo, Japan"
    assert (
        second_job.canonical_url
        == "https://jobs.lever.co/3eco/373c9b1f-e960-4674-9767-e55353b85205"
    )
    assert second_job.source_job_id == "373c9b1f-e960-4674-9767-e55353b85205"
