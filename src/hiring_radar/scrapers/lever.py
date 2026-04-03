from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from hiring_radar.models import JobRecord
from hiring_radar.scrapers.base import BaseScraper
from hiring_radar.utils.hashing import build_job_fingerprint, normalize_text

_LOCATION_CLASS_PATTERN = re.compile(r"(location|office|region|country|city)", re.IGNORECASE)
_GENERIC_LINK_TEXTS: set[str] = {
    "apply",
    "apply now",
    "learn more",
    "read more",
    "details",
    "view details",
}
_TITLE_SELECTOR_PRIORITY: tuple[str, ...] = (
    '[data-qa="posting-name"]',
    ".posting-name",
    ".posting-title",
    ".posting-headline",
    "h5",
    "h4",
    "h3",
    "h2",
    "h1",
)
_CONTAINER_TAGS: set[str] = {"article", "li", "tr", "div", "section"}


def _extract_source_job_id(canonical_url: str) -> str | None:
    path = urlparse(canonical_url).path.strip("/")
    if not path:
        return None

    parts = [part.strip() for part in path.split("/") if part.strip()]
    if not parts:
        return None

    return parts[-1]


def _looks_like_generic_link_text(text: str) -> bool:
    return normalize_text(text).lower() in _GENERIC_LINK_TEXTS


def _looks_like_job_detail_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.netloc.lower()
    path_parts = [part.strip() for part in parsed.path.split("/") if part.strip()]

    if "lever.co" not in hostname:
        return False

    return len(path_parts) >= 2


def _closest_container(tag: Tag) -> Tag:
    for parent in tag.parents:
        if getattr(parent, "name", None) in _CONTAINER_TAGS:
            return parent
    return tag


def _extract_title(container: Tag, detail_anchors: list[Tag]) -> str | None:
    for selector in _TITLE_SELECTOR_PRIORITY:
        element = container.select_one(selector)
        if element is None:
            continue

        text = normalize_text(element.get_text(" ", strip=True))
        if text and not _looks_like_generic_link_text(text):
            return text

    for anchor in detail_anchors:
        text = normalize_text(anchor.get_text(" ", strip=True))
        if text and not _looks_like_generic_link_text(text):
            return text

    return None


def _extract_location(container: Tag, title: str) -> str | None:
    for element in container.find_all(attrs={"class": True}):
        class_names = " ".join(element.get("class", []))
        if _LOCATION_CLASS_PATTERN.search(class_names):
            text = normalize_text(element.get_text(" ", strip=True))
            if text and text != title and not _looks_like_generic_link_text(text):
                return text

    cleaned_strings: list[str] = []
    for value in container.stripped_strings:
        text = normalize_text(value)
        if not text or text == title or _looks_like_generic_link_text(text):
            continue
        cleaned_strings.append(text)

    if not cleaned_strings:
        return None

    return cleaned_strings[0]


def _select_detail_href(detail_anchors: list[Tag], base_url: str) -> str | None:
    for anchor in detail_anchors:
        text = normalize_text(anchor.get_text(" ", strip=True))
        href = anchor.get("href", "").strip()
        if not href:
            continue

        canonical_url = urljoin(base_url, href)
        if not _looks_like_job_detail_url(canonical_url):
            continue

        if text and not _looks_like_generic_link_text(text):
            return href

    for anchor in detail_anchors:
        href = anchor.get("href", "").strip()
        if not href:
            continue

        canonical_url = urljoin(base_url, href)
        if _looks_like_job_detail_url(canonical_url):
            return href

    return None


def _collect_candidate_containers(soup: BeautifulSoup, base_url: str) -> list[Tag]:
    containers: list[Tag] = []
    seen_ids: set[int] = set()

    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue

        canonical_url = urljoin(base_url, href)
        if not _looks_like_job_detail_url(canonical_url):
            continue

        container = _closest_container(anchor)
        container_id = id(container)
        if container_id in seen_ids:
            continue

        seen_ids.add(container_id)
        containers.append(container)

    return containers


class LeverScraper(BaseScraper):
    def parse(self, html: str, scraped_at: str) -> list[JobRecord]:
        soup = BeautifulSoup(html, "html.parser")
        base_url = self.config.url

        jobs: list[JobRecord] = []

        for container in _collect_candidate_containers(soup, base_url):
            detail_anchors = [
                anchor
                for anchor in container.select("a[href]")
                if _looks_like_job_detail_url(urljoin(base_url, anchor.get("href", "").strip()))
            ]
            if not detail_anchors:
                continue

            title = _extract_title(container, detail_anchors)
            if not title:
                continue

            href = _select_detail_href(detail_anchors, base_url)
            if not href:
                continue

            canonical_url = urljoin(base_url, href)
            source_job_id = _extract_source_job_id(canonical_url)
            location = _extract_location(container, title)
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