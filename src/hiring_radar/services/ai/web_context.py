from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any, Final
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import JobExternalContextSnapshot
from hiring_radar.services.matching.contracts import ExternalSourceInsights, ExternalSourceMetadata

_DEFAULT_TIMEOUT: Final[httpx.Timeout] = httpx.Timeout(8.0, connect=3.0, read=6.0, write=6.0, pool=3.0)
_ALLOWED_SCHEMES: Final[tuple[str, ...]] = ("http", "https")
_NOISE_SELECTORS: Final[tuple[str, ...]] = (
    "script",
    "style",
    "noscript",
    "svg",
    "form",
    "iframe",
    "header",
    "footer",
    "nav",
    "aside",
)
_CONTENT_ROOT_SELECTORS: Final[tuple[str, ...]] = (
    "div.posting-page",
    "div.posting",
    "main",
    "article",
    "body",
)
_TECH_TERMS: Final[tuple[str, ...]] = (
    "python",
    "fastapi",
    "django",
    "flask",
    "java",
    "kotlin",
    "spring",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "nextjs",
    "node.js",
    "nodejs",
    "golang",
    "go",
    "rust",
    "c#",
    ".net",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "postgresql",
    "mysql",
    "redis",
    "kafka",
    "spark",
    "airflow",
    "snowflake",
    "databricks",
    "cassandra",
    "couchbase",
    "mongodb",
    "elasticsearch",
    "prometheus",
    "grafana",
    "alertmanager",
    "ansible",
    "vmware",
    "openstack",
)
_SECTION_KEYWORDS: Final[dict[str, tuple[str, ...]]] = {
    "requirements": (
        "requirements",
        "qualifications",
        "must have",
        "what you bring",
        "what we're looking for",
        "what we are looking for",
        "preferred qualifications",
        "expected qualifications",
        "aranan nitelikler",
        "gereksinimler",
        "nitelikler",
    ),
    "responsibilities": (
        "responsibilities",
        "what you'll do",
        "what you will do",
        "your impact",
        "about the role",
        "day to day",
        "sorumluluklar",
        "görevler",
    ),
    "culture": (
        "why join",
        "what we offer",
        "our culture",
        "our values",
        "benefits",
        "perks",
        "culture",
        "about the team",
        "neden biz",
        "sunduğumuz imkanlar",
        "kültür",
        "değerlerimiz",
    ),
}
_BLOCK_SECTION_KEYWORDS: Final[dict[str, tuple[str, ...]]] = {
    "about_team": ("about the team", "team", "who we are"),
    "about_role": ("about the role", "about this role", "role overview"),
    "responsibilities": _SECTION_KEYWORDS["responsibilities"],
    "requirements": _SECTION_KEYWORDS["requirements"],
    "culture": _SECTION_KEYWORDS["culture"],
    "cta": ("take the next step", "apply", "apply for this job", "next step"),
}
_SENTENCE_SPLIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?])\s+|\n+")
_WHITESPACE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s+")
_BULLET_STRIP_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[\-•·◦▪▸►●*]+\s*")
_PROVIDER_LINE_SKIP: Final[tuple[str, ...]] = (
    "jobs powered by",
    "apply for this job",
    "home page",
)


@dataclass(slots=True, frozen=True)
class WebContextServiceConfig:
    timeout: httpx.Timeout = field(default_factory=lambda: _DEFAULT_TIMEOUT)
    max_html_chars: int = 250_000
    max_clean_text_chars: int = 16_000
    cache_ttl_minutes: int = 180
    user_agent: str = (
        "CoreSiftBot/1.0 (+https://coresift.local; respectful job-context fetcher)"
    )


@dataclass(slots=True, frozen=True)
class _FetchedPage:
    source_url: str
    final_url: str | None
    domain: str | None
    http_status: int | None
    html: str
    fetched_at: str
    warning: str | None = None


@dataclass(slots=True, frozen=True)
class _ExtractedPageContext:
    clean_text: str
    meta_description: str | None
    section_blocks: dict[str, tuple[str, ...]]
    technology_terms: tuple[str, ...]
    provider_name: str | None
    acquisition_method: str
    provider_confidence: float
    raw_capture_metadata: dict[str, Any] = field(default_factory=dict)


class WebContextService:
    """Fetch and normalize external job pages for grounded analysis."""

    def __init__(
        self,
        *,
        repository: HiringRadarRepository,
        client: httpx.AsyncClient | None = None,
        config: WebContextServiceConfig | None = None,
    ) -> None:
        self._repository = repository
        self._client = client
        self._config = config or WebContextServiceConfig()

    async def get_external_source_insights(
        self,
        *,
        source_url: str,
        observed_at: str,
        force_refresh: bool = False,
    ) -> ExternalSourceInsights:
        normalized_url = self._normalize_source_url(source_url)
        if not normalized_url:
            return self._build_unavailable_insights(source_url=source_url, warning="Job source URL is missing or invalid.")

        cached_snapshot = self._repository.get_job_external_context_snapshot_by_url(normalized_url)
        if not force_refresh and self._is_snapshot_fresh(cached_snapshot, observed_at=observed_at):
            return self._snapshot_to_insights(cached_snapshot, enrichment_status="cached")

        try:
            fetched_page = await self._fetch_page(source_url=normalized_url, observed_at=observed_at)
            insights = await self._extract_insights_from_page(fetched_page)
        except Exception as exc:  # pragma: no cover - defensive fallback layer
            warning = f"External source enrichment could not be refreshed: {exc}"
            if cached_snapshot is not None:
                cached = self._snapshot_to_insights(cached_snapshot, enrichment_status="cached")
                return ExternalSourceInsights(
                    enrichment_status="cached",
                    site_specific_requirements=cached.site_specific_requirements,
                    company_culture_clues=cached.company_culture_clues,
                    responsibility_clues=cached.responsibility_clues,
                    technology_stack_terms=cached.technology_stack_terms,
                    original_source_metadata=cached.original_source_metadata,
                    clean_text=cached.clean_text,
                    meta_description=cached.meta_description,
                    section_lines=cached.section_lines,
                    section_blocks=cached.section_blocks,
                    raw_capture_metadata=cached.raw_capture_metadata,
                    warning=warning,
                )
            return self._build_error_insights(source_url=normalized_url, warning=warning)

        snapshot = self._insights_to_snapshot(insights=insights, observed_at=observed_at)
        self._repository.upsert_job_external_context_snapshot(snapshot)
        return insights

    async def _fetch_page(self, *, source_url: str, observed_at: str) -> _FetchedPage:
        parsed = urlparse(source_url)
        if parsed.scheme not in _ALLOWED_SCHEMES:
            raise ValueError("Only HTTP and HTTPS source URLs can be enriched.")

        response = await self._http_get(source_url)
        response.raise_for_status()
        html = response.text[: self._config.max_html_chars]
        final_url = str(response.url) if response.url else source_url
        domain = urlparse(final_url).netloc or parsed.netloc
        return _FetchedPage(
            source_url=source_url,
            final_url=final_url,
            domain=domain,
            http_status=response.status_code,
            html=html,
            fetched_at=observed_at,
        )

    async def _http_get(self, url: str) -> httpx.Response:
        headers = {
            "User-Agent": self._config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        }
        if self._client is None:
            async with httpx.AsyncClient(timeout=self._config.timeout, follow_redirects=True, headers=headers) as client:
                return await client.get(url)
        return await self._client.get(url, headers=headers, timeout=self._config.timeout, follow_redirects=True)

    async def _extract_insights_from_page(self, page: _FetchedPage) -> ExternalSourceInsights:
        provider_name = self._detect_provider(page.final_url or page.source_url)
        html_context = self._extract_html_context(page, provider_name=provider_name)
        api_context = await self._extract_provider_context(page, provider_name=provider_name)
        context = self._merge_contexts(html_context=html_context, provider_context=api_context)

        soup = BeautifulSoup(page.html, "html.parser")
        title = self._extract_title(soup)
        site_name = self._extract_site_name(soup)
        digest = hashlib.sha256(context.clean_text.encode("utf-8")).hexdigest() if context.clean_text else None

        metadata = ExternalSourceMetadata(
            source_url=page.source_url,
            final_url=page.final_url,
            source_domain=page.domain,
            fetch_status="live",
            http_status=page.http_status,
            page_title=title,
            site_name=site_name,
            fetched_at=page.fetched_at,
            content_digest=digest,
            text_char_count=len(context.clean_text),
            provider_name=context.provider_name,
            acquisition_method=context.acquisition_method,
            provider_confidence=context.provider_confidence,
        )
        section_lines = self._to_external_section_lines(context.section_blocks)
        return ExternalSourceInsights(
            enrichment_status="live",
            site_specific_requirements=section_lines.get("requirements", ()),
            company_culture_clues=section_lines.get("culture", ()),
            responsibility_clues=section_lines.get("responsibilities", ()),
            technology_stack_terms=context.technology_terms,
            original_source_metadata=metadata,
            clean_text=context.clean_text,
            meta_description=context.meta_description,
            section_lines=section_lines,
            section_blocks=context.section_blocks,
            raw_capture_metadata=context.raw_capture_metadata,
            warning=page.warning,
        )

    async def _extract_provider_context(
        self,
        page: _FetchedPage,
        *,
        provider_name: str | None,
    ) -> _ExtractedPageContext | None:
        if provider_name != "lever":
            return None
        return await self._extract_lever_context(page)

    async def _extract_lever_context(self, page: _FetchedPage) -> _ExtractedPageContext | None:
        company_slug, posting_id = self._extract_lever_identifiers(page.final_url or page.source_url)
        if not company_slug:
            return None
        api_url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
        try:
            response = await self._http_get(api_url)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return None

        posting = self._match_lever_posting(payload, target_url=page.final_url or page.source_url, posting_id=posting_id)
        if not posting:
            return None
        section_blocks = self._extract_lever_section_blocks(posting)
        clean_text = self._render_section_blocks(section_blocks)
        if len(clean_text) < 200:
            return None
        technology_terms = self._extract_technology_terms(clean_text)
        return _ExtractedPageContext(
            clean_text=clean_text,
            meta_description=self._extract_lever_meta_description(posting),
            section_blocks=section_blocks,
            technology_terms=technology_terms,
            provider_name="lever",
            acquisition_method="provider_api",
            provider_confidence=0.96,
            raw_capture_metadata={
                "provider_payload_excerpt": json.dumps(self._build_lever_payload_excerpt(posting), ensure_ascii=False),
            },
        )

    def _extract_html_context(self, page: _FetchedPage, *, provider_name: str | None) -> _ExtractedPageContext:
        soup = BeautifulSoup(page.html, "html.parser")
        for selector in _NOISE_SELECTORS:
            for tag in soup.select(selector):
                tag.decompose()
        root = self._select_content_root(soup)
        clean_text, ordered_lines = self._build_clean_text_and_lines(root)
        meta_description = self._extract_meta_description(soup)
        section_blocks = self._parse_section_blocks_from_lines(ordered_lines)
        if not section_blocks.get("about_role") and clean_text:
            summary = self._split_sentences(clean_text)[:3]
            if summary:
                section_blocks["about_role"] = summary
        technology_terms = self._extract_technology_terms(clean_text)
        return _ExtractedPageContext(
            clean_text=clean_text,
            meta_description=meta_description,
            section_blocks=section_blocks,
            technology_terms=technology_terms,
            provider_name=provider_name,
            acquisition_method="html_sections",
            provider_confidence=0.68 if section_blocks else 0.42,
            raw_capture_metadata={"raw_html": page.html},
        )


    def _merge_contexts(
        self,
        *,
        html_context: _ExtractedPageContext,
        provider_context: _ExtractedPageContext | None,
    ) -> _ExtractedPageContext:
        if provider_context is None:
            return html_context

        merged_blocks: dict[str, tuple[str, ...]] = {}
        html_contributed = False
        all_block_names = set(provider_context.section_blocks) | set(html_context.section_blocks)
        for name in all_block_names:
            provider_values = provider_context.section_blocks.get(name, ())
            html_values = html_context.section_blocks.get(name, ())
            if not provider_values:
                merged_values = html_values
                html_contributed = html_contributed or bool(html_values)
            elif name in {"culture", "cta", "about_team"} and len(html_values) > len(provider_values):
                merged_values = self._dedupe_keep_order((*provider_values, *html_values))
                html_contributed = True
            else:
                merged_values = self._dedupe_keep_order((*provider_values, *html_values))
                html_contributed = html_contributed or (len(merged_values) > len(provider_values))
            if merged_values:
                merged_blocks[name] = merged_values

        merged_clean_text = self._render_section_blocks(merged_blocks)
        merged_technology_terms = self._dedupe_keep_order((*provider_context.technology_terms, *html_context.technology_terms))
        acquisition_method = provider_context.acquisition_method
        provider_confidence = provider_context.provider_confidence
        if html_contributed:
            acquisition_method = f"{provider_context.acquisition_method}_plus_html"
            provider_confidence = min(0.99, max(provider_confidence, html_context.provider_confidence))

        raw_capture_metadata = dict(provider_context.raw_capture_metadata)
        if html_context.raw_capture_metadata.get("raw_html"):
            raw_capture_metadata.setdefault("raw_html", html_context.raw_capture_metadata.get("raw_html"))
        return _ExtractedPageContext(
            clean_text=merged_clean_text or provider_context.clean_text or html_context.clean_text,
            meta_description=provider_context.meta_description or html_context.meta_description,
            section_blocks=merged_blocks,
            technology_terms=merged_technology_terms,
            provider_name=provider_context.provider_name or html_context.provider_name,
            acquisition_method=acquisition_method,
            provider_confidence=provider_confidence,
            raw_capture_metadata=raw_capture_metadata,
        )

    def _context_score(self, context: _ExtractedPageContext) -> float:
        section_weight = sum(len(values) for values in context.section_blocks.values()) * 25
        char_weight = min(len(context.clean_text), 8_000) / 10.0
        return section_weight + char_weight + (context.provider_confidence * 100)

    @staticmethod
    def _detect_provider(url: str | None) -> str | None:
        parsed = urlparse(url or "")
        host = (parsed.netloc or "").casefold()
        if host.endswith("jobs.lever.co") or host == "jobs.lever.co":
            return "lever"
        return None

    @staticmethod
    def _extract_lever_identifiers(url: str) -> tuple[str | None, str | None]:
        parsed = urlparse(url)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2:
            return parts[0], parts[1]
        if len(parts) == 1:
            return parts[0], None
        return None, None

    def _match_lever_posting(self, payload: Any, *, target_url: str, posting_id: str | None) -> dict[str, Any] | None:
        if not isinstance(payload, list):
            return None
        normalized_target = self._normalize_url_for_match(target_url)
        for item in payload:
            if not isinstance(item, dict):
                continue
            hosted_url = self._normalize_url_for_match(str(item.get("hostedUrl") or item.get("hosted_url") or ""))
            if hosted_url and hosted_url == normalized_target:
                return item
            item_id = str(item.get("id") or "").strip()
            if posting_id and item_id and item_id == posting_id:
                return item
        return None

    @staticmethod
    def _normalize_url_for_match(url: str) -> str:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return url.strip().rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    def _extract_lever_section_blocks(self, posting: dict[str, Any]) -> dict[str, tuple[str, ...]]:
        section_blocks: dict[str, list[str]] = {
            "about_team": [],
            "about_role": [],
            "responsibilities": [],
            "requirements": [],
            "culture": [],
            "cta": [],
        }
        description_html = self._first_non_empty_string(
            posting.get("description"),
            posting.get("descriptionHtml"),
            self._nested_get(posting, "content", "description"),
        )
        description_plain = self._first_non_empty_string(
            posting.get("descriptionPlain"),
            self._nested_get(posting, "content", "descriptionPlain"),
        )
        if description_html:
            description_lines = self._html_fragment_to_lines(description_html)
        else:
            description_lines = self._plain_text_to_lines(description_plain)
        if description_lines:
            parsed_description_blocks = self._parse_section_blocks_from_lines(description_lines)
            if parsed_description_blocks:
                for key, values in parsed_description_blocks.items():
                    section_blocks.setdefault(key, []).extend(values)
            else:
                section_blocks["about_role"].extend(description_lines)

        for list_item in self._extract_lever_lists(posting):
            heading = self._normalize_line(str(list_item.get("heading") or ""))
            content = list_item.get("content")
            if isinstance(content, str):
                lines = self._html_fragment_to_lines(content)
            elif isinstance(content, (list, tuple)):
                lines = tuple(self._normalize_line(str(item)) for item in content if self._normalize_line(str(item)))
            else:
                lines = ()
            if not lines:
                continue
            section_name = self._classify_block_heading(heading)
            if section_name is None:
                continue
            section_blocks[section_name].extend(lines)

        closing_html = self._first_non_empty_string(
            posting.get("closing"),
            self._nested_get(posting, "content", "closing"),
        )
        closing_lines = self._html_fragment_to_lines(closing_html) if closing_html else ()
        if closing_lines:
            section_blocks["cta"].extend(closing_lines)

        return {key: self._dedupe_keep_order(values) for key, values in section_blocks.items() if values}

    def _extract_lever_lists(self, posting: dict[str, Any]) -> list[dict[str, Any]]:
        payload_lists = posting.get("lists") or self._nested_get(posting, "content", "lists") or []
        if not isinstance(payload_lists, list):
            return []
        normalized: list[dict[str, Any]] = []
        for item in payload_lists:
            if not isinstance(item, dict):
                continue
            normalized.append({
                "heading": item.get("text") or item.get("title") or item.get("name") or "",
                "content": item.get("content") or item.get("description") or item.get("body") or [],
            })
        return normalized

    def _extract_lever_meta_description(self, posting: dict[str, Any]) -> str | None:
        lines = []
        categories = posting.get("categories") if isinstance(posting.get("categories"), dict) else {}
        for value in categories.values():
            normalized = self._normalize_line(str(value))
            if normalized:
                lines.append(normalized)
        about_role = self._first_non_empty_string(
            posting.get("descriptionPlain"),
            self._nested_get(posting, "content", "descriptionPlain"),
        )
        if about_role:
            sentences = self._split_sentences(about_role)
            lines.extend(sentences[:2])
        if not lines:
            return None
        return " ".join(lines)[:500]

    @staticmethod
    def _build_lever_payload_excerpt(posting: dict[str, Any]) -> dict[str, Any]:
        excerpt: dict[str, Any] = {
            "id": posting.get("id"),
            "text": posting.get("text"),
            "hostedUrl": posting.get("hostedUrl") or posting.get("hosted_url"),
        }
        if isinstance(posting.get("categories"), dict):
            excerpt["categories"] = posting["categories"]
        lists = posting.get("lists") or (posting.get("content") or {}).get("lists") or []
        if isinstance(lists, list):
            excerpt["lists"] = [
                {
                    "heading": item.get("text") or item.get("title") or item.get("name"),
                    "content_length": len(str(item.get("content") or "")),
                }
                for item in lists
                if isinstance(item, dict)
            ]
        return excerpt

    def _select_content_root(self, soup: BeautifulSoup) -> Tag:
        for selector in _CONTENT_ROOT_SELECTORS:
            root = soup.select_one(selector)
            if root is not None:
                return root
        return soup

    def _build_clean_text_and_lines(self, root: Tag) -> tuple[str, tuple[str, ...]]:
        for tag in root.find_all(["br"]):
            tag.replace_with("\n")
        raw_text = root.get_text("\n", strip=True)
        raw_text = unescape(raw_text)
        ordered: list[str] = []
        seen: set[str] = set()
        for raw_line in raw_text.splitlines():
            normalized = self._normalize_line(raw_line)
            if not normalized or len(normalized) < 2:
                continue
            lowered = normalized.casefold()
            if lowered in seen:
                continue
            if any(skip in lowered for skip in _PROVIDER_LINE_SKIP):
                continue
            seen.add(lowered)
            ordered.append(normalized)
        clean_text = "\n".join(ordered)[: self._config.max_clean_text_chars]
        return clean_text, tuple(ordered)

    def _parse_section_blocks_from_lines(self, lines: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
        blocks: dict[str, list[str]] = {
            "about_team": [],
            "about_role": [],
            "responsibilities": [],
            "requirements": [],
            "culture": [],
            "cta": [],
        }
        current_block: str | None = None
        for line in lines:
            heading = self._classify_block_heading(line)
            if heading is not None and len(line) <= 80:
                current_block = heading
                continue
            if current_block is None:
                if line and not blocks["about_role"]:
                    blocks["about_role"].append(line)
                continue
            blocks[current_block].append(line)
        return {key: self._dedupe_keep_order(values) for key, values in blocks.items() if values}

    def _to_external_section_lines(self, section_blocks: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
        return {
            "requirements": tuple(section_blocks.get("requirements", ())),
            "responsibilities": tuple(section_blocks.get("responsibilities", ()) or section_blocks.get("about_role", ())[:5]),
            "culture": self._dedupe_keep_order((*section_blocks.get("culture", ()), *section_blocks.get("about_team", ())[:4])),
        }

    def _render_section_blocks(self, section_blocks: dict[str, tuple[str, ...]]) -> str:
        ordered_names = ("about_team", "about_role", "responsibilities", "requirements", "culture", "cta")
        heading_labels = {
            "about_team": "About the Team",
            "about_role": "About the Role",
            "responsibilities": "Responsibilities",
            "requirements": "Expected Qualifications",
            "culture": "What We Offer",
            "cta": "Take the Next Step",
        }
        parts: list[str] = []
        for name in ordered_names:
            values = section_blocks.get(name, ())
            if not values:
                continue
            parts.append(heading_labels.get(name, name.replace("_", " ").title()))
            parts.extend(values)
        return "\n".join(parts)[: self._config.max_clean_text_chars]

    def _html_fragment_to_lines(self, fragment: str | None) -> tuple[str, ...]:
        if not fragment:
            return ()
        soup = BeautifulSoup(fragment, "html.parser")
        for selector in _NOISE_SELECTORS:
            for tag in soup.select(selector):
                tag.decompose()
        text = soup.get_text("\n", strip=True)
        return tuple(self._plain_text_to_lines(text))

    def _plain_text_to_lines(self, text: str | None) -> tuple[str, ...]:
        if not text:
            return ()
        lines = []
        for raw_line in unescape(text).splitlines():
            normalized = self._normalize_line(raw_line)
            if normalized:
                lines.append(normalized)
        return self._dedupe_keep_order(lines)

    @staticmethod
    def _normalize_source_url(source_url: str | None) -> str:
        raw = (source_url or "").strip()
        if not raw:
            return ""
        parsed = urlparse(raw)
        if parsed.scheme not in _ALLOWED_SCHEMES or not parsed.netloc:
            return ""
        return raw

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str | None:
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        return title or None

    @staticmethod
    def _extract_site_name(soup: BeautifulSoup) -> str | None:
        tag = soup.find("meta", attrs={"property": "og:site_name"}) or soup.find("meta", attrs={"name": "application-name"})
        content = (tag.get("content") if tag else "") or ""
        content = content.strip()
        return content or None

    @staticmethod
    def _extract_meta_description(soup: BeautifulSoup) -> str | None:
        tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        content = (tag.get("content") if tag else "") or ""
        content = content.strip()
        return content or None

    @staticmethod
    def _normalize_line(value: str) -> str:
        cleaned = _BULLET_STRIP_PATTERN.sub("", value or "")
        cleaned = unescape(cleaned)
        cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip(" ·•-\t")
        return cleaned.strip()

    def _split_sentences(self, clean_text: str) -> tuple[str, ...]:
        parts = [self._normalize_line(part) for part in _SENTENCE_SPLIT_PATTERN.split(clean_text)]
        result = [part for part in parts if len(part) >= 20]
        return tuple(result[:150])

    def _extract_technology_terms(self, clean_text: str) -> tuple[str, ...]:
        lowered = clean_text.casefold()
        hits = [term for term in _TECH_TERMS if term in lowered]
        return self._dedupe_keep_order(hits)[:16]

    @staticmethod
    def _classify_block_heading(heading_text: str) -> str | None:
        lowered = heading_text.casefold()
        for section_name, keywords in _BLOCK_SECTION_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return section_name
        return None

    def _snapshot_to_insights(
        self,
        snapshot: JobExternalContextSnapshot,
        *,
        enrichment_status: str,
    ) -> ExternalSourceInsights:
        metadata_json = snapshot.source_metadata_json or {}
        metadata = ExternalSourceMetadata(
            source_url=snapshot.source_url,
            final_url=snapshot.final_url,
            source_domain=snapshot.source_domain,
            fetch_status=snapshot.fetch_status,
            http_status=snapshot.http_status,
            page_title=snapshot.page_title or metadata_json.get("page_title"),
            site_name=snapshot.site_name or metadata_json.get("site_name"),
            fetched_at=snapshot.fetched_at,
            content_digest=snapshot.content_digest,
            text_char_count=int(metadata_json.get("text_char_count") or len(snapshot.clean_text or "")),
            provider_name=metadata_json.get("provider_name"),
            acquisition_method=metadata_json.get("acquisition_method"),
            provider_confidence=(float(metadata_json["provider_confidence"]) if metadata_json.get("provider_confidence") is not None else None),
        )
        return ExternalSourceInsights(
            enrichment_status=enrichment_status,  # type: ignore[arg-type]
            site_specific_requirements=snapshot.site_specific_requirements,
            company_culture_clues=snapshot.company_culture_clues,
            responsibility_clues=snapshot.responsibility_clues,
            technology_stack_terms=snapshot.technology_stack_terms,
            original_source_metadata=metadata,
            clean_text=snapshot.clean_text or "",
            meta_description=snapshot.meta_description,
            section_lines=self._coerce_section_map(metadata_json.get("section_lines")),
            section_blocks=self._coerce_section_map(metadata_json.get("section_blocks")),
            raw_capture_metadata={
                "raw_html": metadata_json.get("raw_html"),
                "provider_payload_excerpt": metadata_json.get("provider_payload_excerpt"),
            },
            warning=snapshot.warning,
        )

    def _insights_to_snapshot(
        self,
        *,
        insights: ExternalSourceInsights,
        observed_at: str,
    ) -> JobExternalContextSnapshot:
        expires_at = self._add_minutes(observed_at, self._config.cache_ttl_minutes)
        metadata = insights.original_source_metadata
        return JobExternalContextSnapshot(
            source_url=metadata.source_url,
            final_url=metadata.final_url,
            source_domain=metadata.source_domain,
            fetch_status=metadata.fetch_status,
            http_status=metadata.http_status,
            page_title=metadata.page_title,
            site_name=metadata.site_name,
            meta_description=insights.meta_description,
            clean_text=insights.clean_text,
            content_digest=metadata.content_digest,
            site_specific_requirements=insights.site_specific_requirements,
            company_culture_clues=insights.company_culture_clues,
            responsibility_clues=insights.responsibility_clues,
            technology_stack_terms=insights.technology_stack_terms,
            source_metadata_json={
                "final_url": metadata.final_url,
                "source_domain": metadata.source_domain,
                "fetch_status": metadata.fetch_status,
                "http_status": metadata.http_status,
                "page_title": metadata.page_title,
                "site_name": metadata.site_name,
                "fetched_at": metadata.fetched_at,
                "content_digest": metadata.content_digest,
                "text_char_count": metadata.text_char_count,
                "provider_name": metadata.provider_name,
                "acquisition_method": metadata.acquisition_method,
                "provider_confidence": metadata.provider_confidence,
                "section_lines": self._serialize_section_map(insights.section_lines),
                "section_blocks": self._serialize_section_map(insights.section_blocks),
                "raw_html": insights.raw_capture_metadata.get("raw_html"),
                "provider_payload_excerpt": insights.raw_capture_metadata.get("provider_payload_excerpt"),
            },
            warning=insights.warning,
            fetched_at=metadata.fetched_at,
            expires_at=expires_at,
            updated_at=observed_at,
        )

    def _is_snapshot_fresh(
        self,
        snapshot: JobExternalContextSnapshot | None,
        *,
        observed_at: str,
    ) -> bool:
        if snapshot is None or not snapshot.expires_at:
            return False
        try:
            return self._parse_iso(snapshot.expires_at) >= self._parse_iso(observed_at)
        except ValueError:
            return False

    @staticmethod
    def _serialize_section_map(payload: dict[str, tuple[str, ...]]) -> dict[str, list[str]]:
        return {key: list(values) for key, values in payload.items() if values}

    @staticmethod
    def _coerce_section_map(payload: Any) -> dict[str, tuple[str, ...]]:
        if not isinstance(payload, dict):
            return {}
        normalized: dict[str, tuple[str, ...]] = {}
        for key, value in payload.items():
            if isinstance(value, str):
                normalized[str(key)] = (value,)
                continue
            if isinstance(value, (list, tuple)):
                cleaned = tuple(str(item).strip() for item in value if str(item).strip())
                if cleaned:
                    normalized[str(key)] = cleaned
        return normalized

    @staticmethod
    def _nested_get(payload: dict[str, Any], *path: str) -> Any:
        current: Any = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _first_non_empty_string(self, *values: Any) -> str | None:
        for value in values:
            if not isinstance(value, str):
                continue
            normalized = value.strip()
            if normalized:
                return normalized
        return None

    def _dedupe_keep_order(self, values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            normalized = self._normalize_line(value)
            if len(normalized) < 2:
                continue
            key = normalized.casefold()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(normalized)
        return tuple(ordered)

    @staticmethod
    def _build_unavailable_insights(*, source_url: str, warning: str) -> ExternalSourceInsights:
        return ExternalSourceInsights(
            enrichment_status="unavailable",
            original_source_metadata=ExternalSourceMetadata(source_url=source_url, fetch_status="unavailable"),
            warning=warning,
        )

    @staticmethod
    def _build_error_insights(*, source_url: str, warning: str) -> ExternalSourceInsights:
        return ExternalSourceInsights(
            enrichment_status="error",
            original_source_metadata=ExternalSourceMetadata(source_url=source_url, fetch_status="error"),
            warning=warning,
        )

    @staticmethod
    def _parse_iso(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _add_minutes(value: str, minutes: int) -> str:
        return (WebContextService._parse_iso(value) + timedelta(minutes=minutes)).astimezone(timezone.utc).isoformat()


__all__ = ["WebContextService", "WebContextServiceConfig"]
