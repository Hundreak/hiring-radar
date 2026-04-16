from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from hiring_radar.models import JobRecord
from hiring_radar.scrapers.base import BaseScraper, ScraperSourceConfig
from hiring_radar.utils.hashing import build_job_fingerprint, normalize_text

_NUMERIC_JOB_ID_PATTERN = re.compile(r"/jobs/(\d+)")
_LOCATION_CLASS_PATTERN = re.compile(r"(location|office|region|country|city)", re.IGNORECASE)

_OPENINGS_TEXT_HINTS: tuple[str, ...] = (
    "current openings",
    "open roles",
    "open positions",
    "view openings",
    "view open roles",
    "search jobs",
    "search roles",
)

_OPENINGS_URL_HINTS: tuple[str, ...] = (
    "open-jobs",
    "openings",
    "job-listing",
    "careers/open",
    "careers/jobs",
)

_GENERIC_TITLE_EXCLUSIONS: set[str] = {
    "apply",
    "apply now",
    "learn more",
    "read more",
    "current openings",
    "open roles",
    "open positions",
    "view openings",
    "view open roles",
    "search jobs",
    "search roles",
    "jobs",
    "careers",
    "benefits",
    "about us",
}

_GENERIC_PATH_EXCLUSIONS: set[str] = {
    "job",
    "jobs",
    "career",
    "careers",
    "opening",
    "openings",
    "open-jobs",
    "position",
    "positions",
    "role",
    "roles",
    "job-listing",
}


def extract_greenhouse_board_token(url: str) -> str | None:
    parsed = urlparse(url)
    hostname = (parsed.netloc or "").lower()

    if "greenhouse.io" not in hostname:
        return None

    path_parts = [part.strip() for part in parsed.path.split("/") if part.strip()]
    if not path_parts:
        return None

    return path_parts[0]


def build_greenhouse_jobs_api_url(board_token: str) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"


def _extract_source_job_id(canonical_url: str) -> str | None:
    numeric_match = _NUMERIC_JOB_ID_PATTERN.search(urlparse(canonical_url).path)
    if numeric_match is not None:
        return numeric_match.group(1)

    path = urlparse(canonical_url).path.strip("/")
    if not path:
        return None

    last_segment = path.split("/")[-1].strip()
    if not last_segment or last_segment.lower() in _GENERIC_PATH_EXCLUSIONS:
        return None

    return last_segment


def _build_job_record(
    *,
    source_name: str,
    company_name: str,
    source_type: str,
    base_url: str,
    title: str,
    href: str,
    location: str | None,
    scraped_at: str,
    source_job_id: str | None = None,
) -> JobRecord:
    canonical_url = urljoin(base_url, href)
    normalized_source_job_id = source_job_id or _extract_source_job_id(canonical_url)
    fingerprint = build_job_fingerprint(
        company_name=company_name,
        title=title,
        location=location,
        canonical_url=canonical_url,
    )

    return JobRecord(
        source_name=source_name,
        title=title,
        company_name=company_name,
        location=location,
        canonical_url=canonical_url,
        source_type=source_type,
        source_job_id=normalized_source_job_id,
        raw_posted_at=None,
        posted_at=None,
        fingerprint=fingerprint,
        scraped_at=scraped_at,
    )


def parse_greenhouse_jobs_api_payload(
    payload: str,
    *,
    source_config: ScraperSourceConfig,
    scraped_at: str,
) -> list[JobRecord]:
    try:
        payload_data = json.loads(payload)
    except json.JSONDecodeError:
        return []

    raw_jobs = payload_data.get("jobs")
    if not isinstance(raw_jobs, list):
        return []

    jobs: list[JobRecord] = []

    for item in raw_jobs:
        if not isinstance(item, dict):
            continue

        raw_title = item.get("title")
        raw_absolute_url = item.get("absolute_url")

        if not isinstance(raw_title, str) or not isinstance(raw_absolute_url, str):
            continue

        title = normalize_text(raw_title)
        absolute_url = raw_absolute_url.strip()

        if not title or not absolute_url:
            continue

        location = None
        raw_location = item.get("location")
        if isinstance(raw_location, dict):
            raw_location_name = raw_location.get("name")
            if isinstance(raw_location_name, str):
                location_name = normalize_text(raw_location_name)
                location = location_name or None

        source_job_id = None
        raw_job_id = item.get("id")
        if raw_job_id is not None:
            source_job_id = str(raw_job_id).strip() or None

        jobs.append(
            _build_job_record(
                source_name=source_config.source_name,
                company_name=source_config.company_name,
                source_type=source_config.source_type,
                base_url=absolute_url,
                title=title,
                href=absolute_url,
                location=location,
                scraped_at=scraped_at,
                source_job_id=source_job_id,
            )
        )

    return jobs


def _closest_container(anchor: Tag) -> Tag:
    for parent in anchor.parents:
        if getattr(parent, "name", None) in {"article", "li", "tr", "div", "section"}:
            return parent
    return anchor


def _extract_location_from_container(container: Tag, title: str) -> str | None:
    for element in container.find_all(attrs={"class": True}):
        class_names = " ".join(element.get("class", []))
        if _LOCATION_CLASS_PATTERN.search(class_names):
            text = normalize_text(element.get_text(" ", strip=True))
            if text and text != title:
                return text

    cleaned_strings: list[str] = []
    for value in container.stripped_strings:
        text = normalize_text(value)
        if not text or text == title:
            continue
        cleaned_strings.append(text)

    if not cleaned_strings:
        return None

    return cleaned_strings[0]


def _looks_like_job_title(title: str) -> bool:
    normalized = normalize_text(title)
    lowered = normalized.lower()

    if not normalized:
        return False

    if lowered in _GENERIC_TITLE_EXCLUSIONS:
        return False

    if len(normalized) < 4 or len(normalized) > 140:
        return False

    return any(char.isalpha() for char in normalized)


def _looks_like_job_detail_url(canonical_url: str) -> bool:
    parsed = urlparse(canonical_url)
    path = parsed.path.strip("/").lower()

    if not path:
        return False

    last_segment = path.split("/")[-1]
    if last_segment in _GENERIC_PATH_EXCLUSIONS:
        return False

    if any(keyword in path for keyword in ("job", "career", "position", "opening", "role")):
        return True

    return "gh_jid=" in canonical_url.lower()


def _parse_standard_openings(
    *,
    soup: BeautifulSoup,
    source_name: str,
    company_name: str,
    source_type: str,
    base_url: str,
    scraped_at: str,
) -> list[JobRecord]:
    jobs: list[JobRecord] = []

    for opening in soup.select(".opening"):
        link = opening.find("a", href=True)
        if link is None:
            continue

        title = normalize_text(link.get_text())
        if not title:
            continue

        href = link["href"].strip()

        location_element = opening.select_one(".location")
        location = None
        if location_element is not None:
            location_text = normalize_text(location_element.get_text())
            location = location_text or None

        jobs.append(
            _build_job_record(
                source_name=source_name,
                company_name=company_name,
                source_type=source_type,
                base_url=base_url,
                title=title,
                href=href,
                location=location,
                scraped_at=scraped_at,
            )
        )

    return jobs


def _parse_generic_job_links(
    *,
    soup: BeautifulSoup,
    source_name: str,
    company_name: str,
    source_type: str,
    base_url: str,
    scraped_at: str,
) -> list[JobRecord]:
    jobs: list[JobRecord] = []
    seen_urls: set[str] = set()

    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue

        title = normalize_text(anchor.get_text(" ", strip=True))
        if not _looks_like_job_title(title):
            continue

        canonical_url = urljoin(base_url, href)
        if not _looks_like_job_detail_url(canonical_url):
            continue

        if canonical_url in seen_urls:
            continue

        container = _closest_container(anchor)
        location = _extract_location_from_container(container, title)

        jobs.append(
            _build_job_record(
                source_name=source_name,
                company_name=company_name,
                source_type=source_type,
                base_url=base_url,
                title=title,
                href=href,
                location=location,
                scraped_at=scraped_at,
            )
        )
        seen_urls.add(canonical_url)

    return jobs


def discover_greenhouse_openings_url(html: str, base_url: str) -> str | None:
    """
    Discover a likely second-step openings page from a branded Greenhouse landing page.
    """
    soup = BeautifulSoup(html, "html.parser")
    best_url: str | None = None
    best_score = 0

    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue

        text = normalize_text(anchor.get_text(" ", strip=True)).lower()
        candidate_url = urljoin(base_url, href)
        parsed = urlparse(candidate_url)
        path = parsed.path.lower()

        score = 0
        if any(hint in text for hint in _OPENINGS_TEXT_HINTS):
            score += 3
        if any(hint in path or hint in candidate_url.lower() for hint in _OPENINGS_URL_HINTS):
            score += 2
        if "career" in path or "job" in path or "opening" in path or "role" in path:
            score += 1

        if score > best_score:
            best_score = score
            best_url = candidate_url

    if best_score < 3:
        return None

    return best_url


class GreenhouseScraper(BaseScraper):
    def parse(self, html: str, scraped_at: str) -> list[JobRecord]:
        soup = BeautifulSoup(html, "html.parser")
        base_url = self.config.url

        standard_jobs = _parse_standard_openings(
            soup=soup,
            source_name=self.config.source_name,
            company_name=self.config.company_name,
            source_type=self.config.source_type,
            base_url=base_url,
            scraped_at=scraped_at,
        )
        if standard_jobs:
            return standard_jobs

        return _parse_generic_job_links(
            soup=soup,
            source_name=self.config.source_name,
            company_name=self.config.company_name,
            source_type=self.config.source_type,
            base_url=base_url,
            scraped_at=scraped_at,
        )
