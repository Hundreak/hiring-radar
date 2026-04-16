from __future__ import annotations

from pathlib import Path

from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.greenhouse import (
    GreenhouseScraper,
    parse_greenhouse_jobs_api_payload,
)


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


def test_greenhouse_api_payload_parses_jobs() -> None:
    payload = """
    {
      "jobs": [
        {
          "id": 7751102,
          "title": "Critical Accounts Program (CAP) Director",
          "absolute_url": "https://boards.greenhouse.io/corelight/jobs/7751102",
          "location": {"name": "North America"}
        },
        {
          "id": 7751103,
          "title": "Senior Technical Account Manager",
          "absolute_url": "https://boards.greenhouse.io/corelight/jobs/7751103",
          "location": {"name": "North America"}
        }
      ]
    }
    """

    config = ScraperSourceConfig(
        source_name="corelight-greenhouse",
        company_name="Corelight",
        source_type="greenhouse",
        url="https://boards.greenhouse.io/corelight",
    )

    jobs = parse_greenhouse_jobs_api_payload(
        payload,
        source_config=config,
        scraped_at="2026-04-03T18:00:00Z",
    )

    assert len(jobs) == 2

    first_job = jobs[0]
    second_job = jobs[1]

    assert first_job.title == "Critical Accounts Program (CAP) Director"
    assert first_job.location == "North America"
    assert first_job.canonical_url == "https://boards.greenhouse.io/corelight/jobs/7751102"
    assert first_job.source_job_id == "7751102"

    assert second_job.title == "Senior Technical Account Manager"
    assert second_job.location == "North America"
    assert second_job.canonical_url == "https://boards.greenhouse.io/corelight/jobs/7751103"
    assert second_job.source_job_id == "7751103"


def test_greenhouse_scraper_parses_branded_jobs_page() -> None:
    html = """
    <html>
      <body>
        <main>
          <h2>31 jobs</h2>
          <section>
            <h3>Customer Success</h3>

            <div class="job-row">
              <a href="/company/careers/open-jobs/critical-accounts-program-cap-director">
                Critical Accounts Program (CAP) Director
              </a>
              <p>North America</p>
            </div>

            <div class="job-row">
              <a href="/company/careers/open-jobs/senior-technical-account-manager">
                Senior Technical Account Manager
              </a>
              <p>North America</p>
            </div>
          </section>
        </main>
      </body>
    </html>
    """

    config = ScraperSourceConfig(
        source_name="corelight-greenhouse",
        company_name="Corelight",
        source_type="greenhouse",
        url="https://www.corelight.com/company/careers/open-jobs",
    )
    scraper = GreenhouseScraper(config)

    jobs = scraper.parse(html, scraped_at="2026-04-03T18:05:00Z")

    assert len(jobs) == 2

    first_job = jobs[0]
    second_job = jobs[1]

    assert first_job.title == "Critical Accounts Program (CAP) Director"
    assert first_job.location == "North America"
    assert (
        first_job.canonical_url == "https://www.corelight.com/company/careers/open-jobs/"
        "critical-accounts-program-cap-director"
    )
    assert first_job.source_job_id == "critical-accounts-program-cap-director"

    assert second_job.title == "Senior Technical Account Manager"
    assert second_job.location == "North America"
    assert second_job.source_job_id == "senior-technical-account-manager"
