from __future__ import annotations

from hiring_radar.services.jobs.adapters import (
    GreenhouseJobSourceAdapter,
    JobSourceAdapter,
    LeverJobSourceAdapter,
)


def create_job_source_adapter(source_type: str) -> JobSourceAdapter:
    normalized = source_type.strip().lower()
    if normalized == "greenhouse":
        return GreenhouseJobSourceAdapter()
    if normalized == "lever":
        return LeverJobSourceAdapter()
    raise ValueError(f"Unsupported job source adapter: {source_type}")
