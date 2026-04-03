from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

import httpx

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CrawlSourceResult, JobRecord
from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.scrapers.factory import create_scraper

DEFAULT_HTTP_TIMEOUT_SECONDS = 20.0

FetchHtmlCallable = Callable[[str], str]
StartedAtFactory = Callable[[], str]


class CrawlFetchError(Exception):
    """
    Raised when source HTML cannot be fetched successfully.
    """


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_html_with_httpx(url: str, timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS) -> str:
    """
    Fetch HTML content from a source URL using a simple httpx GET request.
    """
    try:
        response = httpx.get(
            url,
            timeout=timeout_seconds,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        message = f"Failed to fetch HTML from {url}: {exc}"
        raise CrawlFetchError(message) from exc

    return response.text


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
    2. fetch HTML
    3. create scraper
    4. parse HTML into JobRecord objects
    5. upsert jobs
    6. mark missing jobs inactive
    7. finish crawl run
    8. return CrawlSourceResult
    """
    crawl_run_id: int | None = None

    try:
        crawl_run_id = repository.start_crawl_run(
            source_name=source_config.source_name,
            started_at=started_at,
        )

        html = fetch_html(source_config.url)
        scraper = create_scraper(source_config)
        parsed_jobs = scraper.parse(html, scraped_at=started_at)
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