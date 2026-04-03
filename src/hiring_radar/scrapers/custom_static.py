from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from hiring_radar.models import JobRecord
from hiring_radar.scrapers.base import BaseScraper
from hiring_radar.utils.hashing import build_job_fingerprint, normalize_text


def _extract_source_job_id(canonical_url: str) -> str | None:
    path = urlparse(canonical_url).path.strip("/")
    if not path:
        return None

    last_segment = path.split("/")[-1].strip()
    return last_segment or None


class CustomStaticScraper(BaseScraper):
    def parse(self, html: str, scraped_at: str) -> list[JobRecord]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobRecord] = []

        for listing in soup.select(".job-listing"):
            link = listing.select_one(".job-link[href]")
            if link is None:
                continue

            title = normalize_text(link.get_text())
            if not title:
                continue

            href = link["href"].strip()
            canonical_url = urljoin(self.config.url, href)

            location_element = listing.select_one(".job-location")
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