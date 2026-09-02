from __future__ import annotations

from abc import ABC, abstractmethod

from hiring_radar.models import JobSource
from hiring_radar.services.jobs.contracts import (
    JobSourceDefinition,
    JobSourcePayload,
    ParsedSourceJob,
)


class JobSourceAdapter(ABC):
    source_type: str

    def build_source(self, definition: JobSourceDefinition, *, fetched_at: str) -> JobSource:
        if definition.source_type.strip().lower() != self.source_type:
            raise ValueError(
                f"Adapter {self.source_type} cannot build source for {definition.source_type}."
            )
        return JobSource(
            source_type=definition.source_type,
            source_name=definition.source_name,
            account_slug=definition.account_slug,
            base_url=definition.base_url,
            trust_score=definition.trust_score,
            country_scope=definition.country_scope,
            is_active=True,
            created_at=fetched_at,
            updated_at=fetched_at,
        )

    @abstractmethod
    def parse_jobs(
        self,
        definition: JobSourceDefinition,
        payload: JobSourcePayload,
    ) -> list[ParsedSourceJob]:
        raise NotImplementedError
