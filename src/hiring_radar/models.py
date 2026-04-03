from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class JobRecord:
    id: int | None = None
    source_name: str = ""
    title: str = ""
    company_name: str = ""
    location: str | None = None
    canonical_url: str = ""
    source_type: str = ""
    source_job_id: str | None = None
    raw_posted_at: str | None = None
    posted_at: str | None = None
    fingerprint: str = ""
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    is_active: bool = True
    scraped_at: str = ""


@dataclass(slots=True, frozen=True)
class CrawlRun:
    id: int | None = None
    source_name: str = ""
    started_at: str = ""
    finished_at: str | None = None
    success: bool | None = None
    notes: str | None = None


@dataclass(slots=True, frozen=True)
class Subscriber:
    id: int | None = None
    email: str = ""
    full_name: str | None = None
    is_active: bool = True
    digest_enabled: bool = True
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class NotificationCheckpoint:
    checkpoint_key: str = ""
    last_processed_at: str = ""
    updated_at: str = ""


@dataclass(slots=True, frozen=True)
class CrawlSourceResult:
    source_name: str = ""
    source_type: str = ""
    started_at: str = ""
    finished_at: str = ""
    success: bool = False
    total_parsed_jobs: int = 0
    new_jobs: int = 0
    updated_jobs: int = 0
    deactivated_jobs: int = 0
    crawl_run_id: int | None = None
    error_message: str | None = None