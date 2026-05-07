from __future__ import annotations

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import JobSourceRecord
from hiring_radar.services.jobs.adapters.base import JobSourceAdapter
from hiring_radar.services.jobs.contracts import (
    JobSourceDefinition,
    JobSourcePayload,
    JobSourceSyncResult,
    ParsedSourceJob,
)
from hiring_radar.services.jobs.normalization import build_raw_payload_hash, serialize_raw_payload


def _deduplicate_parsed_jobs(records: list[ParsedSourceJob]) -> list[ParsedSourceJob]:
    deduplicated: dict[str, ParsedSourceJob] = {}
    order: list[str] = []
    for record in records:
        if record.external_job_id not in deduplicated:
            order.append(record.external_job_id)
        deduplicated[record.external_job_id] = record
    return [deduplicated[external_job_id] for external_job_id in order]


def _record_has_material_changes(existing: JobSourceRecord, candidate: JobSourceRecord) -> bool:
    comparable_fields = (
        existing.external_company_id != candidate.external_company_id,
        existing.raw_payload_hash != candidate.raw_payload_hash,
        existing.canonical_url != candidate.canonical_url,
        existing.title != candidate.title,
        existing.company_name != candidate.company_name,
        existing.location_text != candidate.location_text,
        existing.posted_at != candidate.posted_at,
        existing.apply_url != candidate.apply_url,
        existing.is_active != candidate.is_active,
    )
    return any(comparable_fields)


def sync_job_source(
    repository: HiringRadarRepository,
    *,
    adapter: JobSourceAdapter,
    definition: JobSourceDefinition,
    payload: JobSourcePayload,
) -> JobSourceSyncResult:
    source = repository.upsert_job_source(
        adapter.build_source(definition, fetched_at=payload.fetched_at)
    )

    parsed_jobs = _deduplicate_parsed_jobs(adapter.parse_jobs(definition, payload))
    inserted = 0
    updated = 0
    unchanged = 0
    reactivated = 0
    stored_records: list[JobSourceRecord] = []
    seen_external_job_ids: list[str] = []

    for parsed_job in parsed_jobs:
        raw_payload_json = serialize_raw_payload(parsed_job.raw_payload)
        candidate = JobSourceRecord(
            source_id=source.id or 0,
            external_job_id=parsed_job.external_job_id,
            external_company_id=parsed_job.external_company_id,
            raw_payload_json=raw_payload_json,
            raw_payload_hash=build_raw_payload_hash(parsed_job.raw_payload),
            canonical_url=parsed_job.canonical_url,
            title=parsed_job.title,
            company_name=parsed_job.company_name,
            location_text=parsed_job.location_text,
            posted_at=parsed_job.posted_at,
            apply_url=parsed_job.apply_url,
            fetched_at=payload.fetched_at,
            is_active=True,
        )
        existing = repository.get_job_source_record(
            source_id=source.id or 0,
            external_job_id=parsed_job.external_job_id,
        )
        if existing is None:
            inserted += 1
        elif _record_has_material_changes(existing, candidate):
            updated += 1
            if not existing.is_active:
                reactivated += 1
        else:
            unchanged += 1

        stored = repository.upsert_job_source_record(candidate)
        stored_records.append(stored)
        seen_external_job_ids.append(parsed_job.external_job_id)

    deactivated = repository.mark_missing_job_source_records_inactive(
        source_id=source.id or 0,
        seen_external_job_ids=seen_external_job_ids,
        updated_at=payload.fetched_at,
    )

    return JobSourceSyncResult(
        source=source,
        total_seen=len(parsed_jobs),
        inserted=inserted,
        updated=updated,
        unchanged=unchanged,
        deactivated=deactivated,
        reactivated=reactivated,
        records=tuple(stored_records),
    )
