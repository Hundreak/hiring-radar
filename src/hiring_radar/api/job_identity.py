from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CanonicalJob, JobRecord

CANONICAL_JOB_ID_OFFSET = 1_000_000_000
JobKind = Literal["legacy", "canonical"]


@dataclass(slots=True, frozen=True)
class ResolvedJobReference:
    api_job_id: int
    job_kind: JobKind
    legacy_job: JobRecord | None = None
    canonical_job: CanonicalJob | None = None

    @property
    def title(self) -> str:
        if self.legacy_job is not None:
            return self.legacy_job.title
        if self.canonical_job is not None:
            return self.canonical_job.display_title
        return ""

    @property
    def company_name(self) -> str:
        if self.legacy_job is not None:
            return self.legacy_job.company_name
        if self.canonical_job is not None:
            return self.canonical_job.display_company_name
        return ""

    @property
    def location(self) -> str | None:
        if self.legacy_job is not None:
            return self.legacy_job.location
        if self.canonical_job is not None:
            parts = [self.canonical_job.location_city, self.canonical_job.country]
            normalized = [part for part in parts if part]
            if normalized:
                return ", ".join(normalized)
        return None

    @property
    def canonical_url(self) -> str:
        if self.legacy_job is not None:
            return self.legacy_job.canonical_url
        if self.canonical_job is not None:
            return self.canonical_job.apply_url
        return ""

    @property
    def source_name(self) -> str:
        if self.legacy_job is not None:
            return self.legacy_job.source_name
        return "canonical-job-corpus"

    @property
    def is_active(self) -> bool:
        if self.legacy_job is not None:
            return self.legacy_job.is_active
        if self.canonical_job is not None:
            return self.canonical_job.is_active
        return False

    @property
    def first_seen_at(self) -> str | None:
        if self.legacy_job is not None:
            return self.legacy_job.first_seen_at
        if self.canonical_job is not None:
            return self.canonical_job.created_at
        return None

    @property
    def last_seen_at(self) -> str | None:
        if self.legacy_job is not None:
            return self.legacy_job.last_seen_at
        if self.canonical_job is not None:
            return self.canonical_job.updated_at
        return None


def encode_canonical_job_api_id(canonical_job_id: int) -> int:
    if canonical_job_id <= 0:
        raise ValueError("Canonical job id must be a positive integer.")
    return CANONICAL_JOB_ID_OFFSET + canonical_job_id


def is_canonical_job_api_id(api_job_id: int) -> bool:
    return api_job_id >= CANONICAL_JOB_ID_OFFSET


def decode_canonical_job_api_id(api_job_id: int) -> int | None:
    if not is_canonical_job_api_id(api_job_id):
        return None
    canonical_job_id = api_job_id - CANONICAL_JOB_ID_OFFSET
    if canonical_job_id <= 0:
        return None
    return canonical_job_id


def resolve_job_reference(
    repository: HiringRadarRepository,
    *,
    api_job_id: int,
) -> ResolvedJobReference | None:
    canonical_job_id = decode_canonical_job_api_id(api_job_id)
    if canonical_job_id is not None:
        canonical_job = repository.get_canonical_job_by_id(canonical_job_id)
        if canonical_job is None:
            return None
        return ResolvedJobReference(
            api_job_id=api_job_id,
            job_kind="canonical",
            canonical_job=canonical_job,
        )

    legacy_job = repository.get_job_by_id(api_job_id)
    if legacy_job is None:
        return None
    return ResolvedJobReference(
        api_job_id=api_job_id,
        job_kind="legacy",
        legacy_job=legacy_job,
    )
