from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.api.job_identity import encode_canonical_job_api_id
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import CanonicalJob, CanonicalJobLink, JobSource, JobSourceRecord


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / "job_interactions.db"))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()



def _seed_canonical_job(repository: HiringRadarRepository) -> int:
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-18T10:00:00Z",
    )
    source = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme",
            trust_score=0.97,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )
    source_record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="backend-1",
            raw_payload_json='{"title":"Senior Backend Engineer"}',
            raw_payload_hash="hash-backend-1",
            canonical_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            title="Senior Backend Engineer",
            company_name="Acme",
            location_text="Remote, Turkey",
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            fetched_at="2026-04-18T09:10:00Z",
            is_active=True,
        )
    )
    canonical_job = repository.upsert_canonical_job(
        CanonicalJob(
            canonical_key="acme|senior backend engineer|remote|backend-1",
            normalized_title="senior backend engineer",
            normalized_company_name="acme",
            display_title="Senior Backend Engineer",
            display_company_name="Acme",
            location_city="Remote",
            country="Turkey",
            workplace_type="remote",
            employment_type="full_time",
            seniority="senior",
            category="software_engineering",
            department="engineering",
            description_text="Python FastAPI Docker required.",
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            trust_score=0.97,
            freshness_score=0.92,
            is_active=True,
            created_at="2026-04-18T09:12:00Z",
            updated_at="2026-04-18T09:12:00Z",
        )
    )
    repository.upsert_canonical_job_link(
        CanonicalJobLink(
            canonical_job_id=canonical_job.id or 0,
            source_job_id=source_record.id or 0,
            merge_reason="unit_test_link",
            confidence=0.99,
            created_at="2026-04-18T09:13:00Z",
            updated_at="2026-04-18T09:13:00Z",
        )
    )
    return encode_canonical_job_api_id(canonical_job.id or 0), subscriber.id or 0, canonical_job.id or 0



def test_repository_aggregates_job_interactions_and_exposes_affinity_scores(
    repository: HiringRadarRepository,
) -> None:
    api_job_id, subscriber_id, canonical_job_id = _seed_canonical_job(repository)

    repository.record_subscriber_job_interaction(
        subscriber_id=subscriber_id,
        api_job_id=api_job_id,
        job_kind="canonical",
        canonical_job_id=canonical_job_id,
        legacy_job_id=None,
        interaction_type="impression",
        interacted_at="2026-04-18T10:00:00Z",
        source_surface="jobs",
    )
    repository.record_subscriber_job_interaction(
        subscriber_id=subscriber_id,
        api_job_id=api_job_id,
        job_kind="canonical",
        canonical_job_id=canonical_job_id,
        legacy_job_id=None,
        interaction_type="open",
        interacted_at="2026-04-18T10:01:00Z",
        source_surface="jobs",
    )
    interaction = repository.record_subscriber_job_interaction(
        subscriber_id=subscriber_id,
        api_job_id=api_job_id,
        job_kind="canonical",
        canonical_job_id=canonical_job_id,
        legacy_job_id=None,
        interaction_type="dwell",
        interacted_at="2026-04-18T10:02:00Z",
        source_surface="jobs",
        dwell_seconds=240,
    )

    assert interaction.impression_count == 1
    assert interaction.open_count == 1
    assert interaction.total_dwell_seconds == 240
    assert interaction.max_dwell_seconds == 240
    assert interaction.affinity_score > 0.0

    events = repository.list_subscriber_job_interaction_events(
        subscriber_id=subscriber_id,
        api_job_id=api_job_id,
    )
    assert [event.interaction_type for event in events] == ["dwell", "open", "impression"]

    affinity = repository.list_subscriber_job_behavioral_affinity_scores(
        subscriber_id=subscriber_id,
        canonical_job_ids=[canonical_job_id],
    )
    assert affinity[canonical_job_id] == pytest.approx(interaction.affinity_score)
