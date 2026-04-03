from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from hiring_radar.models import JobRecord
from hiring_radar.scrapers.base import BaseScraper
from hiring_radar.utils.hashing import build_job_fingerprint, normalize_text

_GREENHOUSE_JOB_ID_PATTERN = re.compile(r"/jobs/(\d+)")


def _extract_source_job_id(canonical_url: str) -> str | None:
    match = _GREENHOUSE_JOB_ID_PATTERN.search(urlparse(canonical_url).path)
    if match is None:
        return None
    return match.group(1)


class GreenhouseScraper(BaseScraper):
    def parse(self, html: str, scraped_at: str) -> list[JobRecord]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobRecord] = []

        for opening in soup.select(".opening"):
            link = opening.find("a", href=True)
            if link is None:
                continue

            title = normalize_text(link.get_text())
            if not title:
                continue

            href = link["href"].strip()
            canonical_url = urljoin(self.config.url, href)

            location_element = opening.select_one(".location")
            location = None
            if location_element is not None:
                location_text = normalize_text(location_element.get_text())
                location = location_text or None

            source_job_id = _extract_source_job_id(canonical_url)
            fingerprint = build_job_fingerprint(
                company_name=self.config.company_name,
                title=title,
                location=location,
                canonical_url=canonical_url,
            )

            jobs.append(
                JobRecord(
                    source_name=self.config.source_name,
                    title=title,
                    company_name=self.config.company_name,
                    location=location,
                    canonical_url=canonical_url,
                    source_type=self.config.source_type,
                    source_job_id=source_job_id,
                    raw_posted_at=None,
                    posted_at=None,
                    fingerprint=fingerprint,
                    scraped_at=scraped_at,
                )
            )

        return jobs