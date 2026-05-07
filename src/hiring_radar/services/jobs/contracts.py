from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hiring_radar.models import CanonicalJob, CanonicalJobFeature, JobSource, JobSourceRecord


@dataclass(slots=True, frozen=True)
class JobSourceDefinition:
    source_type: str
    source_name: str
    account_slug: str
    company_name: str
    base_url: str
    trust_score: float = 0.95
    country_scope: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class JobSourcePayload:
    body: str
    fetched_at: str
    fetched_url: str | None = None
    content_type: str | None = None


@dataclass(slots=True, frozen=True)
class ParsedSourceJob:
    external_job_id: str
    title: str
    company_name: str
    location_text: str | None
    canonical_url: str | None
    apply_url: str | None
    posted_at: str | None
    raw_payload: Any
    external_company_id: str | None = None


@dataclass(slots=True, frozen=True)
class JobSourceSyncResult:
    source: JobSource
    total_seen: int
    inserted: int
    updated: int
    unchanged: int
    deactivated: int
    reactivated: int
    records: tuple[JobSourceRecord, ...]


@dataclass(slots=True, frozen=True)
class CanonicalRefreshResult:
    total_active_records: int
    grouped_jobs: int
    upserted_jobs: int
    deactivated_jobs: int
    links_upserted: int
    links_pruned: int
    canonical_jobs: tuple[CanonicalJob, ...]
    source_links_total: int = 0


@dataclass(slots=True, frozen=True)
class JobFeatureRefreshResult:
    total_jobs_considered: int
    refreshed_features: int
    pruned_features: int
    features: tuple[CanonicalJobFeature, ...]
