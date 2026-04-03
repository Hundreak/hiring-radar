from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CrawlSourceResult, JobRecord
from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.factory import create_scraper
from hiring_radar.scrapers.greenhouse import (
    build_greenhouse_jobs_api_url,
    discover_greenhouse_openings_url,
    extract_greenhouse_board_token,
    parse_greenhouse_jobs_api_payload,
)

DEFAULT_HTTP_TIMEOUT_SECONDS = 20.0
DEFAULT_HTTP_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

StartedAtFactory = Callable[[], str]


@dataclass(slots=True, frozen=True)
class FetchResult:
    url: str
    html: str


FetchHtmlCallable = Callable[[str], FetchResult]


class CrawlFetchError(Exception):
    """
    Raised when source HTML cannot be fetched successfully.
    """


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_html_with_httpx(
    url: str,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> FetchResult:
    """
    Fetch HTML content from a source URL using a simple httpx GET request.

    Notes:
    - Uses browser-like default headers to reduce trivial bot blocking.
    - Follows redirects because some career pages redirect to branded domains.
    - Intentionally keeps the MVP fetch layer simple: no retries/backoff yet.
    """
    headers = dict(DEFAULT_HTTP_HEADERS)

    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=timeout_seconds,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        message = f"Failed to fetch HTML from {url}: {exc}"
        raise CrawlFetchError(message) from exc

    return FetchResult(
        url=str(response.url),
        html=response.text,
    )


def build_success_result(
    *,
    source_name: str,
    source_type: str,
    started_at: str,
    finished_at: str,
    total_parsed_jobs: int,
    new_jobs: int,
    updated_jobs: int,
    deactivated_jobs: int,
    crawl_run_id: int | None,
) -> CrawlSourceResult:
    return CrawlSourceResult(
        source_name=source_name,
        source_type=source_type,
        started_at=started_at,
        finished_at=finished_at,
        success=True,
        total_parsed_jobs=total_parsed_jobs,
        new_jobs=new_jobs,
        updated_jobs=updated_jobs,
        deactivated_jobs=deactivated_jobs,
        crawl_run_id=crawl_run_id,
        error_message=None,
    )


def build_failure_result(
    *,
    source_name: str,
    source_type: str,
    started_at: str,
    finished_at: str,
    error_message: str,
    crawl_run_id: int | None,
) -> CrawlSourceResult:
    return CrawlSourceResult(
        source_name=source_name,
        source_type=source_type,
        started_at=started_at,
        finished_at=finished_at,
        success=False,
        total_parsed_jobs=0,
        new_jobs=0,
        updated_jobs=0,
        deactivated_jobs=0,
        crawl_run_id=crawl_run_id,
        error_message=error_message,
    )


def _deduplicate_jobs_by_fingerprint(jobs: list[JobRecord]) -> list[JobRecord]:
    """
    Preserve first-seen order while removing duplicate fingerprints within a single crawl.
    """
    unique_jobs: list[JobRecord] = []
    seen_fingerprints: set[str] = set()

    for job in jobs:
        if job.fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(job.fingerprint)
        unique_jobs.append(job)

    return unique_jobs


def _try_parse_greenhouse_api_jobs(
    *,
    source_config: ScraperSourceConfig,
    fetch_html: FetchHtmlCallable,
    scraped_at: str,
) -> list[JobRecord]:
    board_token = extract_greenhouse_board_token(source_config.url)
    if board_token is None:
        return []

    api_url = build_greenhouse_jobs_api_url(board_token)

    try:
        api_fetch_result = fetch_html(api_url)
    except Exception:
        return []

    return parse_greenhouse_jobs_api_payload(
        api_fetch_result.html,
        source_config=source_config,
        scraped_at=scraped_at,
    )


def _parse_jobs_for_source(
    *,
    source_config: ScraperSourceConfig,
    fetch_html: FetchHtmlCallable,
    scraped_at: str,
) -> list[JobRecord]:
    if source_config.source_type == "greenhouse":
        api_jobs = _try_parse_greenhouse_api_jobs(
            source_config=source_config,
            fetch_html=fetch_html,
            scraped_at=scraped_at,
        )
        if api_jobs:
            return api_jobs

        fetch_result = fetch_html(source_config.url)
        scraper = create_scraper(source_config)
        parsed_jobs = scraper.parse(fetch_result.html, scraped_at=scraped_at)
        if parsed_jobs:
            return parsed_jobs

        fallback_url = discover_greenhouse_openings_url(
            fetch_result.html,
            base_url=fetch_result.url,
        )
        if fallback_url is None or fallback_url == fetch_result.url:
            return parsed_jobs

        fallback_fetch_result = fetch_html(fallback_url)
        fallback_source_config = ScraperSourceConfig(
            source_name=source_config.source_name,
            company_name=source_config.company_name,
            source_type=source_config.source_type,
            url=fallback_fetch_result.url,
        )
        fallback_scraper = create_scraper(fallback_source_config)

        return fallback_scraper.parse(
            fallback_fetch_result.html,
            scraped_at=scraped_at,
        )

    fetch_result = fetch_html(source_config.url)
    scraper = create_scraper(source_config)
    return scraper.parse(fetch_result.html, scraped_at=scraped_at)


def run_single_source_crawl(
    *,
    source_config: ScraperSourceConfig,
    repository: HiringRadarRepository,
    fetch_html: FetchHtmlCallable,
    started_at: str,
) -> CrawlSourceResult:
    """
    Run a full crawl flow for one configured source.

    Flow:
    1. start crawl run
    2. fetch source content
    3. parse source content into JobRecord objects
    4. upsert jobs
    5. mark missing jobs inactive
    6. finish crawl run
    7. return CrawlSourceResult
    """
    crawl_run_id: int | None = None

    try:
        crawl_run_id = repository.start_crawl_run(
            source_name=source_config.source_name,
            started_at=started_at,
        )

        parsed_jobs = _parse_jobs_for_source(
            source_config=source_config,
            fetch_html=fetch_html,
            scraped_at=started_at,
        )
        unique_jobs = _deduplicate_jobs_by_fingerprint(parsed_jobs)

        new_jobs = 0
        updated_jobs = 0
        seen_fingerprints: list[str] = []

        for job in unique_jobs:
            created = repository.upsert_job(job)
            if created:
                new_jobs += 1
            else:
                updated_jobs += 1

            seen_fingerprints.append(job.fingerprint)

        finished_at = _utc_now_iso()
        deactivated_jobs = repository.mark_missing_jobs_inactive(
            source_name=source_config.source_name,
            seen_fingerprints=seen_fingerprints,
            updated_at=finished_at,
        )

        repository.finish_crawl_run(
            run_id=crawl_run_id,
            finished_at=finished_at,
            success=True,
            notes=None,
        )

        return build_success_result(
            source_name=source_config.source_name,
            source_type=source_config.source_type,
            started_at=started_at,
            finished_at=finished_at,
            total_parsed_jobs=len(parsed_jobs),
            new_jobs=new_jobs,
            updated_jobs=updated_jobs,
            deactivated_jobs=deactivated_jobs,
            crawl_run_id=crawl_run_id,
        )

    except Exception as exc:
        finished_at = _utc_now_iso()
        error_message = str(exc)

        if crawl_run_id is not None:
            repository.finish_crawl_run(
                run_id=crawl_run_id,
                finished_at=finished_at,
                success=False,
                notes=error_message,
            )

        return build_failure_result(
            source_name=source_config.source_name,
            source_type=source_config.source_type,
            started_at=started_at,
            finished_at=finished_at,
            error_message=error_message,
            crawl_run_id=crawl_run_id,
        )


def run_multi_source_crawl(
    *,
    source_configs: Sequence[ScraperSourceConfig],
    repository: HiringRadarRepository,
    fetch_html: FetchHtmlCallable = fetch_html_with_httpx,
    started_at_factory: StartedAtFactory = _utc_now_iso,
) -> list[CrawlSourceResult]:
    """
    Run crawl orchestration sequentially for multiple configured sources.

    Design choices for the MVP:
    - sequential execution
    - no fail-fast behavior
    - one failing source must not prevent remaining sources from running
    """
    results: list[CrawlSourceResult] = []

    for source_config in source_configs:
        started_at = started_at_factory()
        result = run_single_source_crawl(
            source_config=source_config,
            repository=repository,
            fetch_html=fetch_html,
            started_at=started_at,
        )
        results.append(result)

    return results