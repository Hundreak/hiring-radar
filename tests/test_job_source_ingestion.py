from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.services.jobs.contracts import JobSourceDefinition, JobSourcePayload
from hiring_radar.services.jobs.ingestion import sync_job_source
from hiring_radar.services.jobs.registry import create_job_source_adapter


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "job_source_sync.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()



def test_sync_job_source_inserts_updates_and_deactivates_records(
    repository: HiringRadarRepository,
) -> None:
    adapter = create_job_source_adapter("greenhouse")
    definition = JobSourceDefinition(
        source_type="greenhouse",
        source_name="acme-greenhouse",
        account_slug="acme",
        company_name="Acme",
        base_url="https://boards.greenhouse.io/acme",
        trust_score=0.95,
        country_scope="global",
    )

    first_payload = JobSourcePayload(
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
        fetched_at="2026-04-18T11:30:00Z",
        content_type="application/json",
    )

    first_result = sync_job_source(
        repository,
        adapter=adapter,
        definition=definition,
        payload=first_payload,
    )

    assert first_result.total_seen == 2
    assert first_result.inserted == 2
    assert first_result.updated == 0
    assert first_result.unchanged == 0
    assert first_result.deactivated == 0
    assert first_result.reactivated == 0

    source_id = first_result.source.id or 0
    first_records = repository.list_job_source_records(source_id=source_id)
    assert len(first_records) == 2
    assert all(record.is_active for record in first_records)

    second_payload = JobSourcePayload(
        body='''
        {
          "jobs": [
            {
              "id": 101,
              "title": "Senior Backend Engineer",
              "absolute_url": "https://boards.greenhouse.io/acme/jobs/101",
              "location": {"name": "Remote - Europe"}
            },
            {
              "id": 103,
              "title": "Solutions Architect",
              "absolute_url": "https://boards.greenhouse.io/acme/jobs/103",
              "location": {"name": "Istanbul, Türkiye"}
            }
          ]
        }
        ''',
        fetched_at="2026-04-18T12:00:00Z",
        content_type="application/json",
    )

    second_result = sync_job_source(
        repository,
        adapter=adapter,
        definition=definition,
        payload=second_payload,
    )

    assert second_result.total_seen == 2
    assert second_result.inserted == 1
    assert second_result.updated == 1
    assert second_result.unchanged == 0
    assert second_result.deactivated == 1
    assert second_result.reactivated == 0

    all_records = repository.list_job_source_records(source_id=source_id)
    assert len(all_records) == 3

    active_records = repository.list_job_source_records(source_id=source_id, active_only=True)
    assert {record.external_job_id for record in active_records} == {"101", "103"}

    inactive_record = repository.get_job_source_record(source_id=source_id, external_job_id="102")
    assert inactive_record is not None
    assert inactive_record.is_active is False

    updated_record = repository.get_job_source_record(source_id=source_id, external_job_id="101")
    assert updated_record is not None
    assert updated_record.title == "Senior Backend Engineer"
    assert updated_record.location_text == "Remote - Europe"
