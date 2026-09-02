from __future__ import annotations

import json
from typing import Any

from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.lever import LeverScraper
from hiring_radar.services.jobs.adapters.base import JobSourceAdapter
from hiring_radar.services.jobs.contracts import (
    JobSourceDefinition,
    JobSourcePayload,
    ParsedSourceJob,
)
from hiring_radar.services.jobs.normalization import normalize_location_text, normalize_text


class LeverJobSourceAdapter(JobSourceAdapter):
    source_type = "lever"

    def parse_jobs(
        self,
        definition: JobSourceDefinition,
        payload: JobSourcePayload,
    ) -> list[ParsedSourceJob]:
        try:
            payload_data = json.loads(payload.body)
        except json.JSONDecodeError:
            return self._parse_html_fallback(definition, payload)

        if not isinstance(payload_data, list):
            return self._parse_html_fallback(definition, payload)

        jobs: list[ParsedSourceJob] = []
        for item in payload_data:
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
        scraper = LeverScraper(
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
        raw_id = item.get("id")
        raw_title = item.get("text") or item.get("title")
        raw_canonical_url = item.get("hostedUrl") or item.get("absolute_url") or item.get("applyUrl")
        raw_apply_url = item.get("applyUrl") or item.get("hostedUrl") or item.get("absolute_url")
        raw_posted_at = item.get("createdAt") or item.get("updatedAt")

        external_job_id = normalize_text(str(raw_id) if raw_id is not None else None)
        title = normalize_text(raw_title if isinstance(raw_title, str) else None)
        canonical_url = normalize_text(raw_canonical_url if isinstance(raw_canonical_url, str) else None)
        apply_url = normalize_text(raw_apply_url if isinstance(raw_apply_url, str) else None)
        posted_at = normalize_text(raw_posted_at if isinstance(raw_posted_at, str) else None) or None

        if not external_job_id or not title or not canonical_url:
            return None

        categories = item.get("categories")
        location_text: str | None = None
        if isinstance(categories, dict):
            raw_location = categories.get("location")
            if isinstance(raw_location, str):
                location_text = normalize_location_text(raw_location)

        company_name = definition.company_name
        raw_categories_commitment = categories.get("team") if isinstance(categories, dict) else None
        raw_company_name = item.get("company")
        if isinstance(raw_company_name, str) and normalize_text(raw_company_name):
            company_name = normalize_text(raw_company_name)
        elif isinstance(raw_categories_commitment, str) and normalize_text(raw_categories_commitment) == company_name:
            company_name = normalize_text(raw_categories_commitment)

        return ParsedSourceJob(
            external_job_id=external_job_id,
            title=title,
            company_name=company_name,
            location_text=location_text,
            canonical_url=canonical_url,
            apply_url=apply_url or canonical_url,
            posted_at=posted_at,
            raw_payload=item,
        )
