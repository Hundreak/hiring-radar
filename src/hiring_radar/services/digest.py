from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import JobRecord


@dataclass(slots=True, frozen=True)
class DigestJobItem:
    company_name: str
    source_name: str
    source_type: str
    title: str
    location: str | None
    canonical_url: str
    first_seen_at: str


@dataclass(slots=True, frozen=True)
class DigestSourceSection:
    source_name: str
    source_type: str
    new_jobs_count: int
    jobs: list[DigestJobItem]


@dataclass(slots=True, frozen=True)
class DigestResult:
    generated_at: str
    since: str
    total_new_jobs: int
    sections: list[DigestSourceSection]


def _to_digest_job_item(job: JobRecord) -> DigestJobItem:
    return DigestJobItem(
        company_name=job.company_name,
        source_name=job.source_name,
        source_type=job.source_type,
        title=job.title,
        location=job.location,
        canonical_url=job.canonical_url,
        first_seen_at=job.first_seen_at or "",
    )


def build_digest(
    repository: HiringRadarRepository,
    *,
    since: str,
    generated_at: str,
    source_name: str | None = None,
) -> DigestResult:
    """
    Build a digest result for jobs first seen since the provided timestamp.

    Notes:
    - The first digest iteration focuses only on newly discovered jobs.
    - Grouping is source-based because that is the most operationally useful
      view for notifications and later email sections.
    """
    jobs = repository.list_jobs_first_seen_since(
        since=since,
        source_name=source_name,
    )

    grouped: dict[tuple[str, str], list[DigestJobItem]] = {}

    for job in jobs:
        key = (job.source_name, job.source_type)
        grouped.setdefault(key, []).append(_to_digest_job_item(job))

    sections = [
        DigestSourceSection(
            source_name=group_source_name,
            source_type=group_source_type,
            new_jobs_count=len(group_jobs),
            jobs=group_jobs,
        )
        for (group_source_name, group_source_type), group_jobs in grouped.items()
    ]

    return DigestResult(
        generated_at=generated_at,
        since=since,
        total_new_jobs=len(jobs),
        sections=sections,
    )


def render_digest_subject(result: DigestResult) -> str:
    job_label = "job" if result.total_new_jobs == 1 else "jobs"
    return f"Hiring Radar Digest: {result.total_new_jobs} new {job_label} since {result.since}"


def render_digest_text(result: DigestResult) -> str:
    lines: list[str] = [
        "Hiring Radar Digest",
        "",
        "Window",
        f"  since={result.since}",
        f"  generated_at={result.generated_at}",
        "",
        "New jobs",
        f"  total={result.total_new_jobs}",
        "",
        "By source",
    ]

    if not result.sections:
        lines.append("  no new jobs in this window")
        return "\n".join(lines)

    for section in result.sections:
        lines.append(
            f"  {section.source_name} ({section.source_type}): {section.new_jobs_count}"
        )

        for job in section.jobs:
            location = job.location or "Unknown location"
            lines.append(f"    - {job.title} — {location}")
            lines.append(f"      {job.company_name} | first_seen_at={job.first_seen_at}")
            lines.append(f"      {job.canonical_url}")

    return "\n".join(lines)