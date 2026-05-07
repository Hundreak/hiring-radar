"""Generic JSON job source adapter.

This adapter can consume any JSON-based job board or ATS API that exposes a
list of job objects with standard fields (id, title, location, apply_url,
posted_at, description, etc.). It is designed as a fallback / catch-all for
new sources before writing a dedicated adapter.

Expected JSON shape (flexible):
  {
    "jobs": [
      {
        "id": "12345",
        "title": "Senior Backend Engineer",
        "location": "Remote / Berlin",
        "apply_url": "https://example.com/jobs/12345",
        "posted_at": "2026-04-15",
        "description": "..."
      }
    ]
  }

Or a top-level list:
  [
    {"id": "...", "title": "...", ...},
    ...
  ]
"""
from __future__ import annotations

import json
from typing import Any

from hiring_radar.services.jobs.adapters.base import JobSourceAdapter
from hiring_radar.services.jobs.contracts import JobSourceDefinition, JobSourcePayload, ParsedSourceJob
from hiring_radar.services.jobs.normalization import normalize_location_text, normalize_text


class GenericJsonJobSourceAdapter(JobSourceAdapter):
    """Parse generic JSON job feeds into normalized ParsedSourceJob records."""

    source_type = "generic_json"

    # Configurable field mappings so callers can adapt unusual JSON shapes
    # without writing a new adapter class.
    DEFAULT_FIELD_MAP: dict[str, str] = {
        "id": "id",
        "title": "title",
        "location": "location",
        "company_name": "company_name",
        "apply_url": "apply_url",
        "canonical_url": "canonical_url",
        "posted_at": "posted_at",
        "description": "description",
    }

    def parse_jobs(
        self,
        definition: JobSourceDefinition,
        payload: JobSourcePayload,
    ) -> list[ParsedSourceJob]:
        field_map = self._resolve_field_map(definition)

        try:
            payload_data = json.loads(payload.body)
        except json.JSONDecodeError:
            return []

        raw_jobs: list[dict[str, Any]] = []
        if isinstance(payload_data, list):
            raw_jobs = payload_data
        elif isinstance(payload_data, dict):
            # Try common list keys
            for key in ("jobs", "data", "results", "items", "postings"):
                candidate = payload_data.get(key)
                if isinstance(candidate, list):
                    raw_jobs = candidate
                    break

        jobs: list[ParsedSourceJob] = []
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue
            job = self._build_parsed_job(definition, item, field_map)
            if job is not None:
                jobs.append(job)
        return jobs

    def _resolve_field_map(self, definition: JobSourceDefinition) -> dict[str, str]:
        """Allow per-definition field overrides via metadata."""
        base = dict(self.DEFAULT_FIELD_MAP)
        overrides = definition.metadata or {}
        if isinstance(overrides, dict):
            field_map = overrides.get("field_map")
            if isinstance(field_map, dict):
                for key, value in field_map.items():
                    if key in base and isinstance(value, str):
                        base[key] = value
        return base

    def _build_parsed_job(
        self,
        definition: JobSourceDefinition,
        item: dict[str, Any],
        field_map: dict[str, str],
    ) -> ParsedSourceJob | None:
        raw_id = item.get(field_map.get("id", "id"))
        if raw_id is None:
            return None

        external_job_id = str(raw_id).strip()
        if not external_job_id:
            return None

        title = normalize_text(
            item.get(field_map.get("title", "title"), ""),
        )
        if not title:
            return None

        location_text = normalize_location_text(
            item.get(field_map.get("location", "location"), "")
        )

        company_name = normalize_text(
            item.get(field_map.get("company_name", "company_name"), ""),
        ) or (definition.company_name or definition.source_name)

        apply_url = self._extract_url(item, field_map, "apply_url")
        canonical_url = self._extract_url(item, field_map, "canonical_url") or apply_url
        posted_at = self._extract_string(item, field_map, "posted_at")
        description = self._extract_string(item, field_map, "description")

        raw_payload: dict[str, Any] = dict(item)
        raw_payload["_adapter_type"] = self.source_type
        raw_payload["_field_map"] = field_map

        return ParsedSourceJob(
            external_job_id=external_job_id,
            title=title,
            company_name=company_name or definition.source_name,
            location_text=location_text,
            canonical_url=canonical_url,
            apply_url=apply_url or canonical_url,
            posted_at=posted_at,
            raw_payload=raw_payload,
        )

    @staticmethod
    def _extract_string(item: dict[str, Any], field_map: dict[str, str], key: str) -> str | None:
        value = item.get(field_map.get(key, key))
        if value is None:
            return None
        result = str(value).strip()
        return result or None

    @staticmethod
    def _extract_url(item: dict[str, Any], field_map: dict[str, str], key: str) -> str | None:
        value = item.get(field_map.get(key, key))
        if value is None:
            return None
        result = str(value).strip()
        if result.startswith("http://") or result.startswith("https://"):
            return result
        return None
