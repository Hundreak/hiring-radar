from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from hiring_radar.models import JobRecord

EXPORT_FIELDNAMES: Final[tuple[str, ...]] = (
    "id",
    "source_name",
    "company_name",
    "source_type",
    "title",
    "location",
    "canonical_url",
    "source_job_id",
    "raw_posted_at",
    "posted_at",
    "fingerprint",
    "first_seen_at",
    "last_seen_at",
    "is_active",
    "scraped_at",
)


@dataclass(slots=True, frozen=True)
class ExportResult:
    output_path: str
    row_count: int


def _utc_now_for_filename() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(":", "-").replace(
        "+00:00",
        "Z",
    )


def _serialize_job(job: JobRecord) -> dict[str, str]:
    return {
        "id": "" if job.id is None else str(job.id),
        "source_name": job.source_name,
        "company_name": job.company_name,
        "source_type": job.source_type,
        "title": job.title,
        "location": job.location or "",
        "canonical_url": job.canonical_url,
        "source_job_id": job.source_job_id or "",
        "raw_posted_at": job.raw_posted_at or "",
        "posted_at": job.posted_at or "",
        "fingerprint": job.fingerprint,
        "first_seen_at": job.first_seen_at or "",
        "last_seen_at": job.last_seen_at or "",
        "is_active": "true" if job.is_active else "false",
        "scraped_at": job.scraped_at,
    }


def export_jobs_to_csv(
    *,
    jobs: list[JobRecord],
    output_dir: str | Path,
    filename_prefix: str = "jobs_export",
    timestamp_factory: callable = _utc_now_for_filename,
) -> ExportResult:
    """
    Export normalized job records to a UTF-8 CSV file.

    Notes:
    - Creates the output directory automatically if needed.
    - Writes a header row even if the jobs list is empty.
    - Uses a timestamped filename for deterministic archive-style exports.
    """
    export_dir = Path(output_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = timestamp_factory()
    output_path = export_dir / f"{filename_prefix}_{timestamp}.csv"

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_FIELDNAMES)
        writer.writeheader()

        for job in jobs:
            writer.writerow(_serialize_job(job))

    return ExportResult(
        output_path=str(output_path),
        row_count=len(jobs),
    )