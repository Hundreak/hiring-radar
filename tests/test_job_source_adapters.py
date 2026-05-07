from __future__ import annotations

from pathlib import Path

from hiring_radar.services.jobs.contracts import JobSourceDefinition, JobSourcePayload
from hiring_radar.services.jobs.registry import create_job_source_adapter


def test_greenhouse_adapter_parses_public_jobs_api_payload() -> None:
    definition = JobSourceDefinition(
        source_type="greenhouse",
        source_name="acme-greenhouse",
        account_slug="acme",
        company_name="Acme",
        base_url="https://boards.greenhouse.io/acme",
    )
    payload = JobSourcePayload(
        body='''
        {
          "jobs": [
            {
              "id": 101,
              "title": "Backend Engineer",
              "absolute_url": "https://boards.greenhouse.io/acme/jobs/101",
              "location": {"name": "Remote - Turkey"}
            },
            {
              "id": 102,
              "title": "Data Engineer",
              "absolute_url": "https://boards.greenhouse.io/acme/jobs/102",
              "location": {"name": "Berlin, Germany"}
            }
          ]
        }
        ''',
        fetched_at="2026-04-18T11:00:00Z",
        content_type="application/json",
    )

    adapter = create_job_source_adapter("greenhouse")
    jobs = adapter.parse_jobs(definition, payload)

    assert len(jobs) == 2
    assert jobs[0].external_job_id == "101"
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].location_text == "Remote - Turkey"
    assert jobs[0].canonical_url == "https://boards.greenhouse.io/acme/jobs/101"
    assert jobs[0].apply_url == "https://boards.greenhouse.io/acme/jobs/101"
    assert jobs[1].external_job_id == "102"



def test_greenhouse_adapter_falls_back_to_html_parser() -> None:
    definition = JobSourceDefinition(
        source_type="greenhouse",
        source_name="demo-greenhouse",
        account_slug="demo-company",
        company_name="Demo Company",
        base_url="https://boards.greenhouse.io/demo-company",
    )
    html = Path("tests/fixtures/greenhouse_sample.html").read_text(encoding="utf-8")
    payload = JobSourcePayload(
        body=html,
        fetched_at="2026-04-18T11:05:00Z",
        fetched_url="https://boards.greenhouse.io/demo-company",
        content_type="text/html",
    )

    adapter = create_job_source_adapter("greenhouse")
    jobs = adapter.parse_jobs(definition, payload)

    assert len(jobs) == 2
    assert jobs[0].external_job_id == "123456"
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].location_text == "Remote - Turkey"



def test_lever_adapter_parses_postings_payload() -> None:
    definition = JobSourceDefinition(
        source_type="lever",
        source_name="acme-lever",
        account_slug="acme",
        company_name="Acme",
        base_url="https://jobs.lever.co/acme",
    )
    payload = JobSourcePayload(
        body='''
        [
          {
            "id": "lever-1",
            "text": "Product Designer",
            "hostedUrl": "https://jobs.lever.co/acme/lever-1",
            "applyUrl": "https://jobs.lever.co/acme/lever-1/apply",
            "createdAt": "2026-04-18T10:00:00Z",
            "categories": {
              "location": "Istanbul, Türkiye",
              "team": "Design"
            }
          },
          {
            "id": "lever-2",
            "text": "Field Sales Specialist",
            "hostedUrl": "https://jobs.lever.co/acme/lever-2",
            "applyUrl": "https://jobs.lever.co/acme/lever-2/apply",
            "createdAt": "2026-04-18T10:30:00Z",
            "categories": {
              "location": "Ankara, Türkiye",
              "team": "Sales"
            }
          }
        ]
        ''',
        fetched_at="2026-04-18T11:10:00Z",
        content_type="application/json",
    )

    adapter = create_job_source_adapter("lever")
    jobs = adapter.parse_jobs(definition, payload)

    assert len(jobs) == 2
    assert jobs[0].external_job_id == "lever-1"
    assert jobs[0].title == "Product Designer"
    assert jobs[0].location_text == "Istanbul, Türkiye"
    assert jobs[0].apply_url == "https://jobs.lever.co/acme/lever-1/apply"
    assert jobs[1].external_job_id == "lever-2"
