from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class JobRecord:
    """
    Normalized and persisted job representation.

    All internal timestamps are stored as UTC ISO-8601 strings in the DB layer.
    """

    source_name: str
    title: str
    company_name: str
    canonical_url: str
    source_type: str
    fingerprint: str
    scraped_at: str

    location: str | None = None
    source_job_id: str | None = None
    raw_posted_at: str | None = None
    posted_at: str | None = None

    first_seen_at: str | None = None
    last_seen_at: str | None = None
    is_active: bool = True

    id: int | None = None


@dataclass(slots=True, kw_only=True)
class CrawlRun:
    """
    Represents one crawl execution for a single configured source.
    """

    source_name: str
    started_at: str

    finished_at: str | None = None
    success: bool | None = None
    notes: str | None = None

    id: int | None = None


@dataclass(slots=True, kw_only=True)
class CrawlSourceResult:
    """
    Result summary for one source crawl execution.

    This is the service-layer output that higher layers (CLI, later dashboard,
    email digest, etc.) can consume without knowing repository details.
    """

    source_name: str
    source_type: str
    started_at: str
    finished_at: str
    success: bool

    total_parsed_jobs: int = 0
    new_jobs: int = 0
    updated_jobs: int = 0
    deactivated_jobs: int = 0

    crawl_run_id: int | None = None
    error_message: str | None = None