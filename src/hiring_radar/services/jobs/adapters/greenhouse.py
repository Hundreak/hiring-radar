from __future__ import annotations

import json
from typing import Any

from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.greenhouse import GreenhouseScraper
from hiring_radar.services.jobs.adapters.base import JobSourceAdapter
from hiring_radar.services.jobs.contracts import JobSourceDefinition, JobSourcePayload, ParsedSourceJob
from hiring_radar.services.jobs.normalization import normalize_location_text, normalize_text


class GreenhouseJobSourceAdapter(JobSourceAdapter):
    source_type = "greenhouse"

    def parse_jobs(
        self,
        definition: JobSourceDefinition,
        payload: JobSourcePayload,
    ) -> list[ParsedSourceJob]:
        try:
            payload_data = json.loads(payload.body)
        except json.JSONDecodeError:
            return self._parse_html_fallback(definition, payload)

        raw_jobs = payload_data.get("jobs")
        if not isinstance(raw_jobs, list):
            return self._parse_html_fallback(definition, payload)

        jobs: list[ParsedSourceJob] = []
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue
            job = self._build_parsed_job(definition, item)
            if job is not None:
                jobs.append(job)
        return jobs

    def _parse_html_fallback(
        self,
        definition: JobSourceDefinition,
        payload: JobSourcePayload,
    ) -> list[ParsedSourceJob]:
        scraper = GreenhouseScraper(
            ScraperSourceConfig(
                source_name=definition.source_name,
                company_name=definition.company_name,
                source_type=definition.source_type,
                url=payload.fetched_url or definition.base_url,
            )
        )
        parsed_records = scraper.parse(payload.body, scraped_at=payload.fetched_at)
        jobs: list[ParsedSourceJob] = []
        for record in parsed_records:
            raw_payload: dict[str, Any] = {
                "canonical_url": record.canonical_url,
                "title": record.title,
                "location": record.location,
                "source_job_id": record.source_job_id,
            }
            external_job_id = record.source_job_id or record.canonical_url
            jobs.append(
                ParsedSourceJob(
                    external_job_id=external_job_id,
                    title=record.title,
                    company_name=record.company_name,
                    location_text=normalize_location_text(record.location),
                    canonical_url=record.canonical_url,
                    apply_url=record.canonical_url,
                    posted_at=record.posted_at,
                    raw_payload=raw_payload,
                )
            )
        return jobs

    def _build_parsed_job(
        self,
        definition: JobSourceDefinition,
        item: dict[str, Any],
    ) -> ParsedSourceJob | None:
        raw_title = item.get("title")
        raw_absolute_url = item.get("absolute_url")
        raw_id = item.get("id")

        title = normalize_text(raw_title if isinstance(raw_title, str) else None)
        absolute_url = normalize_text(raw_absolute_url if isinstance(raw_absolute_url, str) else None)
        external_job_id = normalize_text(str(raw_id) if raw_id is not None else None)

        if not title or not absolute_url or not external_job_id:
            return None

        location_text: str | None = None
        raw_location = item.get("location")
        if isinstance(raw_location, dict):
            location_name = raw_location.get("name")
            if isinstance(location_name, str):
                location_text = normalize_location_text(location_name)

        return ParsedSourceJob(
            external_job_id=external_job_id,
            title=title,
            company_name=definition.company_name,
            location_text=location_text,
            canonical_url=absolute_url,
            apply_url=absolute_url,
            posted_at=None,
            raw_payload=item,
        )
