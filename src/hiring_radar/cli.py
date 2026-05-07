from __future__ import annotations

from datetime import UTC, datetime, timedelta
import asyncio
import json
from pathlib import Path

import typer

from hiring_radar.config import ConfigError, load_source_configs
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.email_config import EmailConfigError, load_smtp_settings
from hiring_radar.filtering import (
    JobFilterDecision,
    JobFilterResult,
    filter_jobs_by_keyword_settings,
)
from hiring_radar.models import CrawlSourceResult, NotificationRun, Subscriber
from hiring_radar.services.crawl import run_multi_source_crawl
from hiring_radar.services.ai.web_context import WebContextService
from hiring_radar.services.digest import (
    DigestFilterResult,
    DigestResult,
    build_digest,
    filter_digest_result_by_keyword_settings,
    render_digest_subject,
    render_digest_text,
)
from hiring_radar.services.cv_local_diagnostics import (
    LocalCvInspectionResult,
    inspect_local_cv_directory,
)
from hiring_radar.services.email import (
    EmailDeliveryError,
    EmailMessagePayload,
    send_email_via_smtp,
)
from hiring_radar.services.export import ExportResult, export_jobs_to_csv
from hiring_radar.services.retrieval.embedding_jobs import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    DeterministicEmbeddingProvider,
    PROCESS_ACTION_FAILED,
    PROCESS_ACTION_IDLE,
    PROCESS_ACTION_PROCESSED,
    run_embedding_job_batch,
)
from hiring_radar.services.summary import SummaryResult, build_summary
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.settings import AppSettings, load_app_settings

DEFAULT_COMPANIES_CONFIG_PATH = "config/companies.example.yml"
DEFAULT_SETTINGS_CONFIG_PATH = "config/settings.example.yml"
DEFAULT_DB_PATH = "data/hiring_radar.db"
DEFAULT_EXPORT_DIR = "data/exports"
DEFAULT_ENV_PATH = ".env"
DIGEST_EMAIL_CHECKPOINT_KEY = "digest_email"
NOTIFICATION_TYPE_DIGEST_EMAIL = "digest_email"

app = typer.Typer(no_args_is_help=True, help="Hiring Radar CLI")


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_iso_hours_ago(*, base_timestamp: str, hours: int) -> str:
    base_dt = datetime.fromisoformat(base_timestamp.replace("Z", "+00:00"))
    since_dt = base_dt - timedelta(hours=hours)
    return since_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


def _resolve_digest_since(
    *,
    repository: HiringRadarRepository,
    generated_at: str,
    window_hours: int,
) -> str:
    checkpoint = repository.get_notification_checkpoint(DIGEST_EMAIL_CHECKPOINT_KEY)
    if checkpoint is not None:
        return checkpoint.last_processed_at

    return _utc_iso_hours_ago(
        base_timestamp=generated_at,
        hours=window_hours,
    )


def _advance_digest_checkpoint(
    *,
    repository: HiringRadarRepository,
    processed_at: str,
) -> None:
    repository.upsert_notification_checkpoint(
        checkpoint_key=DIGEST_EMAIL_CHECKPOINT_KEY,
        last_processed_at=processed_at,
        updated_at=processed_at,
    )


def _finish_notification_run(
    *,
    repository: HiringRadarRepository | None,
    run_id: int | None,
    finished_at: str,
    status: str,
    recipient_count: int = 0,
    new_jobs_count: int = 0,
    subject: str | None = None,
    error_message: str | None = None,
) -> None:
    if repository is None or run_id is None:
        return

    repository.finish_notification_run(
        run_id,
        finished_at=finished_at,
        status=status,
        recipient_count=recipient_count,
        new_jobs_count=new_jobs_count,
        subject=subject,
        error_message=error_message,
    )


def _resolve_digest_recipients(
    *,
    repository: HiringRadarRepository,
    explicit_to: str | None,
    default_to: str | None,
) -> list[str]:
    if explicit_to:
        return [explicit_to]

    subscribers = repository.list_digest_enabled_subscribers()
    if subscribers:
        return [subscriber.email for subscriber in subscribers]

    if default_to:
        return [default_to]

    raise EmailConfigError(
        "No digest recipients configured. Use --to, add active digest-enabled subscribers, "
        "or set HIRING_RADAR_EMAIL_TO_DEFAULT."
    )


def _send_digest_emails(
    *,
    repository: HiringRadarRepository,
    digest: DigestResult,
    env_path: str,
    explicit_to: str | None,
) -> tuple[int, str]:
    settings = load_smtp_settings(env_path)
    recipients = _resolve_digest_recipients(
        repository=repository,
        explicit_to=explicit_to,
        default_to=settings.default_to,
    )

    subject = render_digest_subject(digest)
    body_text = render_digest_text(digest)

    for recipient in recipients:
        payload = EmailMessagePayload(
            to=recipient,
            subject=subject,
            body_text=body_text,
        )
        send_email_via_smtp(
            settings=settings,
            payload=payload,
        )

    return len(recipients), subject


def _print_crawl_result(result: CrawlSourceResult) -> None:
    status_label = "SUCCESS" if result.success else "FAILED"
    status_color = "green" if result.success else "red"

    typer.secho(f"[{status_label}] {result.source_name} ({result.source_type})", fg=status_color)
    typer.echo(
        f"  parsed={result.total_parsed_jobs} "
        f"new={result.new_jobs} "
        f"updated={result.updated_jobs} "
        f"deactivated={result.deactivated_jobs}"
    )

    if result.error_message:
        typer.secho(f"  error={result.error_message}", fg="red")


def _print_crawl_summary(results: list[CrawlSourceResult]) -> None:
    succeeded = sum(1 for result in results if result.success)
    failed = len(results) - succeeded

    total_new = sum(result.new_jobs for result in results)
    total_updated = sum(result.updated_jobs for result in results)
    total_deactivated = sum(result.deactivated_jobs for result in results)

    typer.echo("")
    typer.secho("Crawl summary", bold=True)
    typer.echo(f"  sources={len(results)} succeeded={succeeded} failed={failed}")
    typer.echo(
        f"  new_jobs={total_new} updated_jobs={total_updated} deactivated_jobs={total_deactivated}"
    )


def _build_partial_crawl_failure_detail(
    results: list[CrawlSourceResult],
) -> str | None:
    failed_source_names = [result.source_name for result in results if not result.success]
    successful_source_count = sum(1 for result in results if result.success)

    if not failed_source_names or successful_source_count == 0:
        return None

    noun = "source" if len(failed_source_names) == 1 else "sources"
    joined_names = ", ".join(failed_source_names)
    return f"partial crawl failure: {len(failed_source_names)} {noun} failed ({joined_names})"


def _print_crawl_warning(results: list[CrawlSourceResult]) -> None:
    detail = _build_partial_crawl_failure_detail(results)
    if detail is None:
        return

    typer.echo("")
    typer.secho("Crawl warning", fg="yellow", bold=True)
    typer.echo(f"  {detail}")


def _merge_notification_detail(
    primary_detail: str,
    secondary_detail: str | None,
) -> str:
    if secondary_detail is None:
        return primary_detail

    return f"{primary_detail}; {secondary_detail}"


def _resolve_digest_filter_policy(
    *,
    settings_path: str,
    apply_filter: bool,
    no_apply_filter: bool,
) -> tuple[bool, AppSettings | None, str]:
    if apply_filter and no_apply_filter:
        raise ConfigError("Use only one of --apply-filter or --no-apply-filter.")

    if no_apply_filter:
        return False, None, "cli_override"

    settings = load_app_settings(settings_path)

    if apply_filter:
        return True, settings, "cli_override"

    return (
        settings.notifications.apply_keyword_filter_to_digest,
        settings,
        "settings.notifications.apply_keyword_filter_to_digest",
    )


def _print_digest_filter_policy(
    *,
    resolved_apply_filter: bool,
    policy_source: str,
    settings: AppSettings | None,
) -> None:
    typer.echo("")
    typer.secho("Digest Filter Policy", bold=True)
    typer.echo(f"  resolved_apply_filter={resolved_apply_filter}")
    typer.echo(f"  policy_source={policy_source}")

    if settings is None:
        typer.echo("  settings_apply_keyword_filter_to_digest=-")
        return

    typer.echo(
        "  settings_apply_keyword_filter_to_digest="
        f"{settings.notifications.apply_keyword_filter_to_digest}"
    )


def _filter_digest_result_if_requested(
    *,
    digest: DigestResult,
    apply_filter: bool,
    settings: AppSettings | None,
) -> DigestFilterResult:
    if not apply_filter:
        return DigestFilterResult(
            original_total_new_jobs=digest.total_new_jobs,
            filtered_total_new_jobs=digest.total_new_jobs,
            filtered_out_jobs=0,
            digest=digest,
        )

    if settings is None:
        raise RuntimeError("Digest filter settings are required when apply_filter=True.")

    return filter_digest_result_by_keyword_settings(
        digest,
        settings=settings.keyword_filter,
    )


def _print_digest_filter_summary(
    *,
    filter_result: DigestFilterResult,
    settings: AppSettings,
) -> None:
    keyword_filter = settings.keyword_filter

    typer.echo("")
    typer.secho("Digest Filter", bold=True)
    typer.echo(f"  total_new_jobs_before_filter={filter_result.original_total_new_jobs}")
    typer.echo(f"  total_new_jobs_after_filter={filter_result.filtered_total_new_jobs}")
    typer.echo(f"  filtered_out_jobs={filter_result.filtered_out_jobs}")
    typer.echo(f"  include_keywords={list(keyword_filter.include_keywords)}")
    typer.echo(f"  exclude_keywords={list(keyword_filter.exclude_keywords)}")
    typer.echo(f"  active_fields={list(keyword_filter.active_fields())}")


def _build_digest_skip_reason(
    *,
    filter_applied: bool,
    filter_result: DigestFilterResult,
) -> str:
    if (
        filter_applied
        and filter_result.original_total_new_jobs > 0
        and filter_result.filtered_total_new_jobs == 0
    ):
        return "no jobs matched the active keyword filter"

    return "no new jobs in this window"


def _print_export_result(result: ExportResult) -> None:
    typer.secho("Export completed", fg="green", bold=True)
    typer.echo(f"  rows={result.row_count}")
    typer.echo(f"  output={result.output_path}")


def _print_export_scope_summary(
    *,
    total_selected_jobs: int,
    exported_jobs: int,
    filter_applied: bool,
    active_only: bool,
    settings: AppSettings | None,
) -> None:
    typer.secho("Export Scope", bold=True)
    typer.echo(f"  jobs_scope={'active_only' if active_only else 'all_jobs'}")
    typer.echo(f"  filter_applied={filter_applied}")
    typer.echo(f"  total_selected_jobs={total_selected_jobs}")

    if filter_applied:
        filtered_out_jobs = total_selected_jobs - exported_jobs
        typer.echo(f"  exported_jobs={exported_jobs}")
        typer.echo(f"  filtered_out_jobs={filtered_out_jobs}")

        keyword_filter = settings.keyword_filter if settings is not None else None
        if keyword_filter is not None:
            typer.echo(f"  include_keywords={list(keyword_filter.include_keywords)}")
            typer.echo(f"  exclude_keywords={list(keyword_filter.exclude_keywords)}")
            typer.echo(f"  active_fields={list(keyword_filter.active_fields())}")




def _print_retrieval_embedding_batch_results(results) -> None:
    processed = sum(1 for result in results if result.action == PROCESS_ACTION_PROCESSED)
    failed = sum(1 for result in results if result.action == PROCESS_ACTION_FAILED)
    idle = sum(1 for result in results if result.action == PROCESS_ACTION_IDLE)

    typer.secho("Retrieval embedding batch", bold=True)
    typer.echo(
        f"  processed={processed} failed={failed} idle={idle} total={len(results)}"
    )

    for result in results:
        if result.action == PROCESS_ACTION_PROCESSED and result.job is not None:
            typer.secho(
                f"  [processed] job_id={result.job.id} chunk_id={result.job.chunk_id}",
                fg="green",
            )
            continue

        if result.action == PROCESS_ACTION_FAILED:
            job_label = "-"
            chunk_label = "-"
            if result.job is not None:
                job_label = str(result.job.id)
                chunk_label = str(result.job.chunk_id)
            typer.secho(
                f"  [failed] job_id={job_label} chunk_id={chunk_label} error={result.error_message or '-'}",
                fg="red",
                err=True,
            )
            continue

        typer.echo(f"  [idle] reason={result.reason or '-'}")


def _print_summary_result(result: SummaryResult) -> None:
    typer.secho("Summary", bold=True)
    typer.echo("")
    typer.secho("Overall", bold=True)
    typer.echo(f"  total_jobs={result.overall.total_jobs}")
    typer.echo(f"  active_jobs={result.overall.active_jobs}")
    typer.echo(f"  inactive_jobs={result.overall.inactive_jobs}")

    typer.echo("")
    typer.secho("By source", bold=True)
    if result.by_source:
        for row in result.by_source:
            typer.echo(
                f"  {row.source_name} ({row.source_type}): "
                f"total={row.total_jobs} active={row.active_jobs} inactive={row.inactive_jobs}"
            )
    else:
        typer.echo("  no source data")

    typer.echo("")
    typer.secho("By company", bold=True)
    if result.by_company:
        for row in result.by_company:
            typer.echo(
                f"  {row.company_name}: "
                f"total={row.total_jobs} active={row.active_jobs} inactive={row.inactive_jobs}"
            )
    else:
        typer.echo("  no company data")


def _print_digest_result(result: DigestResult) -> None:
    typer.secho("Digest Preview", bold=True)
    typer.echo("")
    typer.secho("Window", bold=True)
    typer.echo(f"  since={result.since}")
    typer.echo(f"  generated_at={result.generated_at}")

    typer.echo("")
    typer.secho("New jobs", bold=True)
    typer.echo(f"  total={result.total_new_jobs}")

    typer.echo("")
    typer.secho("By source", bold=True)

    if not result.sections:
        typer.echo("  no new jobs in this window")
        return

    for section in result.sections:
        typer.echo(f"  {section.source_name} ({section.source_type}): {section.new_jobs_count}")
        for job in section.jobs:
            location = job.location or "Unknown location"
            typer.echo(f"    - {job.title} — {location}")
            typer.echo(f"      {job.company_name} | first_seen_at={job.first_seen_at}")
            typer.echo(f"      {job.canonical_url}")


def _print_subscribers(subscribers: list[Subscriber]) -> None:
    typer.secho("Subscribers", bold=True)

    if not subscribers:
        typer.echo("  no subscribers")
        return

    for subscriber in subscribers:
        name = subscriber.full_name or "-"
        typer.echo(
            f"  {subscriber.email} | "
            f"active={_format_bool(subscriber.is_active)} "
            f"digest_enabled={_format_bool(subscriber.digest_enabled)} "
            f"name={name}"
        )


def _print_notification_runs(runs: list[NotificationRun]) -> None:
    typer.secho("Notification History", bold=True)

    if not runs:
        typer.echo("  no notification runs")
        return

    for run in runs:
        typer.echo(f"  id={run.id} type={run.notification_type} status={run.status}")
        typer.echo(f"    started_at={run.started_at}")
        typer.echo(f"    finished_at={run.finished_at or '-'}")
        typer.echo(f"    recipient_count={run.recipient_count} new_jobs_count={run.new_jobs_count}")
        typer.echo(f"    since={run.since or '-'}")
        typer.echo(f"    subject={run.subject or '-'}")
        if run.error_message:
            typer.echo(f"    detail={run.error_message}")


def _print_ops_status(
    *,
    latest_crawl_run,
    latest_notification_run,
    digest_checkpoint,
    subscriber_counts: dict[str, int],
) -> None:
    typer.secho("Operations Status", bold=True)

    typer.echo("")
    typer.secho("Subscribers", bold=True)
    typer.echo(f"  total={subscriber_counts['total_subscribers']}")
    typer.echo(f"  active={subscriber_counts['active_subscribers']}")
    typer.echo(f"  digest_enabled={subscriber_counts['digest_enabled_subscribers']}")

    typer.echo("")
    typer.secho("Digest Checkpoint", bold=True)
    if digest_checkpoint is None:
        typer.echo("  checkpoint=-")
    else:
        typer.echo(f"  checkpoint_key={digest_checkpoint.checkpoint_key}")
        typer.echo(f"  last_processed_at={digest_checkpoint.last_processed_at}")
        typer.echo(f"  updated_at={digest_checkpoint.updated_at}")

    typer.echo("")
    typer.secho("Latest Crawl Run", bold=True)
    if latest_crawl_run is None:
        typer.echo("  no crawl runs")
    else:
        typer.echo(f"  id={latest_crawl_run.id}")
        typer.echo(f"  source_name={latest_crawl_run.source_name}")
        typer.echo(f"  started_at={latest_crawl_run.started_at}")
        typer.echo(f"  finished_at={latest_crawl_run.finished_at or '-'}")
        typer.echo(f"  success={latest_crawl_run.success}")
        typer.echo(f"  notes={latest_crawl_run.notes or '-'}")

    typer.echo("")
    typer.secho("Latest Notification Run", bold=True)
    if latest_notification_run is None:
        typer.echo("  no notification runs")
    else:
        typer.echo(f"  id={latest_notification_run.id}")
        typer.echo(f"  type={latest_notification_run.notification_type}")
        typer.echo(f"  status={latest_notification_run.status}")
        typer.echo(f"  started_at={latest_notification_run.started_at}")
        typer.echo(f"  finished_at={latest_notification_run.finished_at or '-'}")
        typer.echo(f"  recipient_count={latest_notification_run.recipient_count}")
        typer.echo(f"  new_jobs_count={latest_notification_run.new_jobs_count}")
        typer.echo(f"  since={latest_notification_run.since or '-'}")
        typer.echo(f"  subject={latest_notification_run.subject or '-'}")
        if latest_notification_run.error_message:
            typer.echo(f"  detail={latest_notification_run.error_message}")


def _print_keyword_filter_config(settings: AppSettings) -> None:
    keyword_filter = settings.keyword_filter

    typer.secho("Keyword Filter Config", bold=True)
    typer.echo(f"  enabled={keyword_filter.is_enabled()}")
    typer.echo(f"  include_keywords={list(keyword_filter.include_keywords)}")
    typer.echo(f"  exclude_keywords={list(keyword_filter.exclude_keywords)}")
    typer.echo(f"  active_fields={list(keyword_filter.active_fields())}")

    typer.echo("")
    typer.secho("Notification Policy", bold=True)
    typer.echo(
        f"  apply_keyword_filter_to_digest={settings.notifications.apply_keyword_filter_to_digest}"
    )


def _format_keyword_field_matches(decisions) -> str:
    if not decisions:
        return "-"

    return ", ".join(f"{match.field_name}:{match.keyword}" for match in decisions)


def _print_filter_decision_samples(
    *,
    heading: str,
    decisions: tuple[JobFilterDecision, ...],
    sample_limit: int,
) -> None:
    typer.echo("")
    typer.secho(heading, bold=True)

    if not decisions:
        typer.echo("  none")
        return

    for decision in decisions[:sample_limit]:
        job = decision.job
        location = job.location or "Unknown location"

        typer.echo(f"  - {job.title} | {job.company_name} | {location}")
        typer.echo(
            "    "
            f"include_matches="
            f"{_format_keyword_field_matches(decision.evaluation.include_matches)}"
        )
        typer.echo(
            "    "
            f"exclude_matches="
            f"{_format_keyword_field_matches(decision.evaluation.exclude_matches)}"
        )
        typer.echo(f"    canonical_url={job.canonical_url}")

    remaining = len(decisions) - sample_limit
    if remaining > 0:
        typer.echo(f"  ... {remaining} more")


def _print_filter_preview_result(
    *,
    result: JobFilterResult,
    settings: AppSettings,
    all_jobs: bool,
    sample_limit: int,
) -> None:
    keyword_filter = settings.keyword_filter

    typer.secho("Filter Preview", bold=True)

    typer.echo("")
    typer.secho("Scope", bold=True)
    typer.echo(f"  jobs_scope={'all_jobs' if all_jobs else 'active_only'}")
    typer.echo(f"  total_jobs={result.total_jobs}")

    typer.echo("")
    typer.secho("Filter", bold=True)
    typer.echo(f"  enabled={keyword_filter.is_enabled()}")
    typer.echo(f"  include_keywords={list(keyword_filter.include_keywords)}")
    typer.echo(f"  exclude_keywords={list(keyword_filter.exclude_keywords)}")
    typer.echo(f"  active_fields={list(keyword_filter.active_fields())}")

    typer.echo("")
    typer.secho("Summary", bold=True)
    typer.echo(f"  passed_jobs={result.passed_count}")
    typer.echo(f"  rejected_jobs={result.rejected_count}")

    _print_filter_decision_samples(
        heading="Passed Samples",
        decisions=result.passed_decisions,
        sample_limit=sample_limit,
    )
    _print_filter_decision_samples(
        heading="Rejected Samples",
        decisions=result.rejected_decisions,
        sample_limit=sample_limit,
    )




def _find_canonical_job_ids_for_url(
    repository: HiringRadarRepository,
    *,
    source_url: str,
) -> list[int]:
    normalized = source_url.strip()
    if not normalized:
        return []
    return [
        job.id for job in repository.list_canonical_jobs(active_only=False)
        if job.id is not None and (job.apply_url or '').strip() == normalized
    ]


def _hydrate_single_job_url(
    repository: HiringRadarRepository,
    *,
    source_url: str,
    force_refresh: bool,
    verbose: bool,
) -> None:
    observed_at = _utc_now_iso()
    service = WebContextService(repository=repository)
    insights = asyncio.run(
        service.get_external_source_insights(
            source_url=source_url,
            observed_at=observed_at,
            force_refresh=force_refresh,
        )
    )

    canonical_job_ids = _find_canonical_job_ids_for_url(repository, source_url=source_url)
    refreshed_feature_count = 0
    if canonical_job_ids:
        refresh_result = refresh_matching_readiness_features(
            repository,
            refreshed_at=observed_at,
            canonical_job_ids=canonical_job_ids,
        )
        refreshed_feature_count = refresh_result.refreshed_features

    metadata = insights.original_source_metadata
    typer.secho("Hydrated job URL", bold=True)
    typer.echo(f"  source_url={metadata.source_url}")
    typer.echo(f"  hydration_status={insights.enrichment_status}")
    typer.echo(f"  fetch_status={metadata.fetch_status}")
    typer.echo(f"  http_status={metadata.http_status}")
    typer.echo(f"  final_url={metadata.final_url}")
    typer.echo(f"  page_title={metadata.page_title or '-'}")
    typer.echo(f"  site_name={metadata.site_name or '-'}")
    typer.echo(f"  text_char_count={metadata.text_char_count}")
    typer.echo(f"  clean_text_chars={len(insights.clean_text)}")
    typer.echo(f"  content_digest={metadata.content_digest or '-'}")
    typer.echo(f"  matched_canonical_jobs={len(canonical_job_ids)}")
    typer.echo(f"  refreshed_feature_count={refreshed_feature_count}")
    typer.echo(
        "  requirements="
        f"{len(insights.site_specific_requirements)} "
        "responsibilities="
        f"{len(insights.responsibility_clues)} "
        "culture="
        f"{len(insights.company_culture_clues)} "
        "tech_terms="
        f"{len(insights.technology_stack_terms)}"
    )

    if not verbose:
        return

    def _print_block(title: str, values: tuple[str, ...]) -> None:
        typer.echo("")
        typer.secho(title, bold=True)
        if not values:
            typer.echo("  -")
            return
        for item in values:
            typer.echo(f"  - {item}")

    _print_block("Technology terms", insights.technology_stack_terms)
    _print_block("Requirements", insights.site_specific_requirements)
    _print_block("Responsibilities", insights.responsibility_clues)
    _print_block("Culture / benefits", insights.company_culture_clues)

    typer.echo("")
    typer.secho("Section lines", bold=True)
    section_lines = insights.section_lines or {}
    printed_any = False
    for section_name in ("requirements", "responsibilities", "culture"):
        values = tuple(section_lines.get(section_name, ()))
        if not values:
            continue
        printed_any = True
        typer.echo(f"  [{section_name}]")
        for item in values[:8]:
            typer.echo(f"    - {item}")
    if not printed_any:
        typer.echo("  -")

    typer.echo("")
    typer.secho("Clean text preview", bold=True)
    preview = insights.clean_text[:1200].strip()
    typer.echo(f"  {preview or '-'}")


def _hydrate_active_canonical_job_pages(
    repository: HiringRadarRepository,
    *,
    force_refresh: bool,
) -> tuple[int, int]:
    hydrated_urls = 0
    refreshed_features = 0
    processed_urls: set[str] = set()
    observed_at = _utc_now_iso()
    service = WebContextService(repository=repository)

    for job in repository.list_canonical_jobs(active_only=True):
        source_url = (job.apply_url or '').strip()
        if not source_url or source_url in processed_urls:
            continue
        processed_urls.add(source_url)
        asyncio.run(
            service.get_external_source_insights(
                source_url=source_url,
                observed_at=observed_at,
                force_refresh=force_refresh,
            )
        )
        hydrated_urls += 1

    if processed_urls:
        refresh_result = refresh_matching_readiness_features(
            repository,
            refreshed_at=observed_at,
            canonical_job_ids=[job.id for job in repository.list_canonical_jobs(active_only=True) if job.id is not None],
        )
        refreshed_features = refresh_result.refreshed_features

    return hydrated_urls, refreshed_features


@app.command(name="hydrate-job-url")
def hydrate_job_url(
    url: str = typer.Option(..., "--url", help="Exact external job page URL to hydrate."),
    force_refresh: bool = typer.Option(False, "--force-refresh", help="Ignore cache and refetch the page."),
    verbose: bool = typer.Option(False, "--verbose", help="Print extracted sections and clean text preview."),
) -> None:
    connection = None
    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)
        _hydrate_single_job_url(
            repository,
            source_url=url,
            force_refresh=force_refresh,
            verbose=verbose,
        )
    except Exception as exc:
        typer.secho(f"Unexpected hydration error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    finally:
        close_connection(connection)


@app.command(name="hydrate-job-pages")
def hydrate_job_pages(
    force_refresh: bool = typer.Option(False, "--force-refresh", help="Ignore cache and refetch all active canonical job pages."),
) -> None:
    connection = None
    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)
        hydrated, refreshed = _hydrate_active_canonical_job_pages(
            repository,
            force_refresh=force_refresh,
        )
        typer.secho("Job page hydration", bold=True)
        typer.echo(f"  hydrated_urls={hydrated}")
        typer.echo(f"  refreshed_features={refreshed}")
    except Exception as exc:
        typer.secho(f"Unexpected hydration error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    finally:
        close_connection(connection)


@app.command()
def crawl(
    config_path: str = typer.Option(
        DEFAULT_COMPANIES_CONFIG_PATH,
        "--config-path",
        help="Path to the YAML source configuration file.",
    ),
    hydrate_job_pages: bool = typer.Option(
        False,
        "--hydrate-job-pages",
        help="Refresh external job-page snapshots after crawl for active canonical jobs.",
    ),
) -> None:
    """Run configured job source crawls."""
    try:
        source_configs = load_source_configs(config_path)
    except ConfigError as exc:
        typer.secho(f"Config error ({config_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    connection = None
    results: list[CrawlSourceResult] = []

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        results = run_multi_source_crawl(
            source_configs=source_configs,
            repository=repository,
        )

        if hydrate_job_pages:
            hydrated, refreshed = _hydrate_active_canonical_job_pages(repository=repository, force_refresh=False)
            typer.echo("")
            typer.secho("Job page hydration", bold=True)
            typer.echo(f"  hydrated_urls={hydrated} refreshed_features={refreshed}")

        for result in results:
            _print_crawl_result(result)

        _print_crawl_summary(results)
        _print_crawl_warning(results)

    except Exception as exc:
        typer.secho(f"Unexpected crawl error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)

    if any(not result.success for result in results):
        raise typer.Exit(code=1)


@app.command(name="crawl-and-notify")
def crawl_and_notify(
    config_path: str = typer.Option(
        DEFAULT_COMPANIES_CONFIG_PATH,
        "--config-path",
        help="Path to the YAML source configuration file.",
    ),
    window_hours: int = typer.Option(
        6,
        "--window-hours",
        help="Fallback digest window size in hours when no notification checkpoint exists yet.",
    ),
    env_path: str = typer.Option(
        DEFAULT_ENV_PATH,
        "--env-path",
        help="Path to the .env file that contains SMTP settings.",
    ),
    to: str | None = typer.Option(
        None,
        "--to",
        help="Send only to this recipient instead of the subscriber list.",
    ),
    send_empty: bool = typer.Option(
        False,
        "--send-empty",
        help="Send the digest even when there are no new jobs in the selected window.",
    ),
    settings_path: str = typer.Option(
        DEFAULT_SETTINGS_CONFIG_PATH,
        "--settings-path",
        help="Path to the application settings YAML file.",
    ),
    apply_filter: bool = typer.Option(
        False,
        "--apply-filter",
        help="Force-apply the keyword filter before sending the digest.",
    ),
    no_apply_filter: bool = typer.Option(
        False,
        "--no-apply-filter",
        help="Force-disable the keyword filter before sending the digest.",
    ),
    hydrate_job_pages: bool = typer.Option(
        False,
        "--hydrate-job-pages",
        help="Refresh external job-page snapshots after crawl for active canonical jobs.",
    ),
) -> None:
    """Run crawl and then send a digest using the notification checkpoint."""
    if window_hours < 1:
        typer.secho("Invalid window-hours: must be >= 1", fg="red", err=True)
        raise typer.Exit(code=2)

    try:
        source_configs = load_source_configs(config_path)
    except ConfigError as exc:
        typer.secho(f"Config error ({config_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    connection = None
    repository: HiringRadarRepository | None = None
    results: list[CrawlSourceResult] = []
    notification_run_id: int | None = None
    settings: AppSettings | None = None

    try:
        resolved_apply_filter, settings, policy_source = _resolve_digest_filter_policy(
            settings_path=settings_path,
            apply_filter=apply_filter,
            no_apply_filter=no_apply_filter,
        )

        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        results = run_multi_source_crawl(
            source_configs=source_configs,
            repository=repository,
        )

        if hydrate_job_pages:
            hydrated, refreshed = _hydrate_active_canonical_job_pages(repository=repository, force_refresh=False)
            typer.echo("")
            typer.secho("Job page hydration", bold=True)
            typer.echo(f"  hydrated_urls={hydrated} refreshed_features={refreshed}")

        for result in results:
            _print_crawl_result(result)

        _print_crawl_summary(results)
        partial_crawl_failure_detail = _build_partial_crawl_failure_detail(results)
        _print_crawl_warning(results)

        successful_results = [result for result in results if result.success]
        generated_at = _utc_now_iso()

        if not successful_results:
            notification_run_id = repository.start_notification_run(
                notification_type=NOTIFICATION_TYPE_DIGEST_EMAIL,
                started_at=generated_at,
                since=None,
            )
            _finish_notification_run(
                repository=repository,
                run_id=notification_run_id,
                finished_at=_utc_now_iso(),
                status="skipped",
                error_message="no successful crawl sources",
            )
            typer.secho("Digest email skipped", fg="yellow", bold=True)
            typer.echo("  reason=no successful crawl sources")
        else:
            since = _resolve_digest_since(
                repository=repository,
                generated_at=generated_at,
                window_hours=window_hours,
            )

            notification_run_id = repository.start_notification_run(
                notification_type=NOTIFICATION_TYPE_DIGEST_EMAIL,
                started_at=generated_at,
                since=since,
            )

            digest = build_digest(
                repository,
                since=since,
                generated_at=generated_at,
            )
            filter_result = _filter_digest_result_if_requested(
                digest=digest,
                apply_filter=resolved_apply_filter,
                settings=settings,
            )
            digest_to_send = filter_result.digest

            _print_digest_filter_policy(
                resolved_apply_filter=resolved_apply_filter,
                policy_source=policy_source,
                settings=settings,
            )

            if resolved_apply_filter and settings is not None:
                _print_digest_filter_summary(
                    filter_result=filter_result,
                    settings=settings,
                )

            if digest_to_send.total_new_jobs == 0 and not send_empty:
                skip_reason = _build_digest_skip_reason(
                    filter_applied=resolved_apply_filter,
                    filter_result=filter_result,
                )
                _finish_notification_run(
                    repository=repository,
                    run_id=notification_run_id,
                    finished_at=_utc_now_iso(),
                    status="skipped",
                    recipient_count=0,
                    new_jobs_count=0,
                    error_message=_merge_notification_detail(
                        skip_reason,
                        partial_crawl_failure_detail,
                    ),
                )

                typer.secho("Digest email skipped", fg="yellow", bold=True)
                typer.echo(f"  reason={skip_reason}")
                typer.echo(f"  since={digest_to_send.since}")
                _advance_digest_checkpoint(
                    repository=repository,
                    processed_at=generated_at,
                )
            else:
                recipient_count, subject = _send_digest_emails(
                    repository=repository,
                    digest=digest_to_send,
                    env_path=env_path,
                    explicit_to=to,
                )
                _finish_notification_run(
                    repository=repository,
                    run_id=notification_run_id,
                    finished_at=_utc_now_iso(),
                    status="sent",
                    recipient_count=recipient_count,
                    new_jobs_count=digest_to_send.total_new_jobs,
                    subject=subject,
                    error_message=partial_crawl_failure_detail,
                )
                typer.secho("Digest emails sent", fg="green", bold=True)
                typer.echo(f"  recipient_count={recipient_count}")
                typer.echo(f"  new_jobs={digest_to_send.total_new_jobs}")
                typer.echo(f"  subject={subject}")
                _advance_digest_checkpoint(
                    repository=repository,
                    processed_at=generated_at,
                )

    except ConfigError as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Config error ({settings_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except EmailConfigError as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Email config error: {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except EmailDeliveryError as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Email delivery error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    except Exception as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Unexpected crawl-and-notify error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)

    if any(not result.success for result in results):
        raise typer.Exit(code=1)


@app.command()
def export(
    output_dir: str = typer.Option(
        DEFAULT_EXPORT_DIR,
        "--output-dir",
        help="Directory where the CSV export file will be written.",
    ),
    settings_path: str = typer.Option(
        DEFAULT_SETTINGS_CONFIG_PATH,
        "--settings-path",
        help="Path to the application settings YAML file.",
    ),
    apply_filter: bool = typer.Option(
        False,
        "--apply-filter",
        help="Apply the keyword filter settings before exporting jobs.",
    ),
    active_only: bool = typer.Option(
        False,
        "--active-only",
        help="Export only active jobs.",
    ),
) -> None:
    """Export stored jobs to CSV."""
    connection = None
    settings: AppSettings | None = None

    try:
        if apply_filter:
            settings = load_app_settings(settings_path)

        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        selected_jobs = repository.list_active_jobs() if active_only else repository.list_jobs()

        jobs_to_export = selected_jobs
        if apply_filter:
            filter_result = filter_jobs_by_keyword_settings(
                jobs=selected_jobs,
                settings=settings.keyword_filter,
            )
            jobs_to_export = list(filter_result.passed_jobs)

        result = export_jobs_to_csv(
            jobs=jobs_to_export,
            output_dir=output_dir,
        )

        _print_export_scope_summary(
            total_selected_jobs=len(selected_jobs),
            exported_jobs=len(jobs_to_export),
            filter_applied=apply_filter,
            active_only=active_only,
            settings=settings,
        )
        typer.echo("")
        _print_export_result(result)

    except ConfigError as exc:
        typer.secho(f"Config error ({settings_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except Exception as exc:
        typer.secho(f"Unexpected export error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="digest-preview")
def digest_preview(
    since: str = typer.Option(
        ...,
        "--since",
        help="Include jobs whose first_seen_at is greater than or equal to this UTC timestamp.",
    ),
    settings_path: str = typer.Option(
        DEFAULT_SETTINGS_CONFIG_PATH,
        "--settings-path",
        help="Path to the application settings YAML file.",
    ),
    apply_filter: bool = typer.Option(
        False,
        "--apply-filter",
        help="Force-apply the keyword filter to the digest preview.",
    ),
    no_apply_filter: bool = typer.Option(
        False,
        "--no-apply-filter",
        help="Force-disable the keyword filter for the digest preview.",
    ),
) -> None:
    """Preview a digest of newly discovered jobs since a given timestamp."""
    connection = None
    settings: AppSettings | None = None

    try:
        resolved_apply_filter, settings, policy_source = _resolve_digest_filter_policy(
            settings_path=settings_path,
            apply_filter=apply_filter,
            no_apply_filter=no_apply_filter,
        )

        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        digest = build_digest(
            repository,
            since=since,
            generated_at=_utc_now_iso(),
        )
        filter_result = _filter_digest_result_if_requested(
            digest=digest,
            apply_filter=resolved_apply_filter,
            settings=settings,
        )

        _print_digest_filter_policy(
            resolved_apply_filter=resolved_apply_filter,
            policy_source=policy_source,
            settings=settings,
        )

        if resolved_apply_filter and settings is not None:
            _print_digest_filter_summary(
                filter_result=filter_result,
                settings=settings,
            )

        _print_digest_result(filter_result.digest)

    except ConfigError as exc:
        typer.secho(f"Config error ({settings_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except Exception as exc:
        typer.secho(f"Unexpected digest error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="send-digest")
def send_digest(
    since: str = typer.Option(
        ...,
        "--since",
        help="Include jobs whose first_seen_at is greater than or equal to this UTC timestamp.",
    ),
    to: str | None = typer.Option(
        None,
        "--to",
        help="Send only to this recipient instead of the subscriber list.",
    ),
    env_path: str = typer.Option(
        DEFAULT_ENV_PATH,
        "--env-path",
        help="Path to the .env file that contains SMTP settings.",
    ),
    send_empty: bool = typer.Option(
        False,
        "--send-empty",
        help="Send the digest even when there are no new jobs in the selected window.",
    ),
    settings_path: str = typer.Option(
        DEFAULT_SETTINGS_CONFIG_PATH,
        "--settings-path",
        help="Path to the application settings YAML file.",
    ),
    apply_filter: bool = typer.Option(
        False,
        "--apply-filter",
        help="Force-apply the keyword filter before sending the digest.",
    ),
    no_apply_filter: bool = typer.Option(
        False,
        "--no-apply-filter",
        help="Force-disable the keyword filter before sending the digest.",
    ),
) -> None:
    """Send a digest email for newly discovered jobs since a given timestamp."""
    connection = None
    repository: HiringRadarRepository | None = None
    notification_run_id: int | None = None
    settings: AppSettings | None = None

    try:
        resolved_apply_filter, settings, policy_source = _resolve_digest_filter_policy(
            settings_path=settings_path,
            apply_filter=apply_filter,
            no_apply_filter=no_apply_filter,
        )

        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        started_at = _utc_now_iso()
        notification_run_id = repository.start_notification_run(
            notification_type=NOTIFICATION_TYPE_DIGEST_EMAIL,
            started_at=started_at,
            since=since,
        )

        digest = build_digest(
            repository,
            since=since,
            generated_at=started_at,
        )
        filter_result = _filter_digest_result_if_requested(
            digest=digest,
            apply_filter=resolved_apply_filter,
            settings=settings,
        )
        digest_to_send = filter_result.digest

        _print_digest_filter_policy(
            resolved_apply_filter=resolved_apply_filter,
            policy_source=policy_source,
            settings=settings,
        )

        if resolved_apply_filter and settings is not None:
            _print_digest_filter_summary(
                filter_result=filter_result,
                settings=settings,
            )

        if digest_to_send.total_new_jobs == 0 and not send_empty:
            skip_reason = _build_digest_skip_reason(
                filter_applied=resolved_apply_filter,
                filter_result=filter_result,
            )
            _finish_notification_run(
                repository=repository,
                run_id=notification_run_id,
                finished_at=_utc_now_iso(),
                status="skipped",
                recipient_count=0,
                new_jobs_count=0,
                error_message=skip_reason,
            )
            typer.secho("Digest email skipped", fg="yellow", bold=True)
            typer.echo(f"  reason={skip_reason}")
            typer.echo(f"  since={digest_to_send.since}")
            return

        recipient_count, subject = _send_digest_emails(
            repository=repository,
            digest=digest_to_send,
            env_path=env_path,
            explicit_to=to,
        )

        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="sent",
            recipient_count=recipient_count,
            new_jobs_count=digest_to_send.total_new_jobs,
            subject=subject,
        )

        typer.secho("Digest emails sent", fg="green", bold=True)
        typer.echo(f"  recipient_count={recipient_count}")
        typer.echo(f"  new_jobs={digest_to_send.total_new_jobs}")
        typer.echo(f"  subject={subject}")

    except ConfigError as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Config error ({settings_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except EmailConfigError as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Email config error: {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except EmailDeliveryError as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Email delivery error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    except Exception as exc:
        _finish_notification_run(
            repository=repository,
            run_id=notification_run_id,
            finished_at=_utc_now_iso(),
            status="failed",
            error_message=str(exc),
        )
        typer.secho(f"Unexpected send-digest error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="add-subscriber")
def add_subscriber(
    email: str = typer.Option(
        ...,
        "--email",
        help="Subscriber email address.",
    ),
    full_name: str | None = typer.Option(
        None,
        "--full-name",
        help="Optional subscriber full name.",
    ),
) -> None:
    """Add or reactivate a subscriber."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        subscriber, created = repository.upsert_subscriber(
            email=email,
            full_name=full_name,
            updated_at=_utc_now_iso(),
        )

        typer.secho("Subscriber added" if created else "Subscriber updated", fg="green", bold=True)
        typer.echo(f"  email={subscriber.email}")
        typer.echo(f"  full_name={subscriber.full_name or '-'}")
        typer.echo(f"  is_active={_format_bool(subscriber.is_active)}")
        typer.echo(f"  digest_enabled={_format_bool(subscriber.digest_enabled)}")

    except Exception as exc:
        typer.secho(f"Unexpected add-subscriber error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="list-subscribers")
def list_subscribers(
    digest_only: bool = typer.Option(
        False,
        "--digest-only",
        help="Only show subscribers with is_active=true and digest_enabled=true.",
    ),
) -> None:
    """List subscribers."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        subscribers = (
            repository.list_digest_enabled_subscribers()
            if digest_only
            else repository.list_subscribers()
        )
        _print_subscribers(subscribers)

    except Exception as exc:
        typer.secho(f"Unexpected list-subscribers error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="disable-subscriber")
def disable_subscriber(
    email: str = typer.Option(
        ...,
        "--email",
        help="Subscriber email address.",
    ),
) -> None:
    """Disable a subscriber without deleting the record."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        updated = repository.set_subscriber_active(
            email=email,
            is_active=False,
            updated_at=_utc_now_iso(),
        )

        if not updated:
            typer.secho("Subscriber not found", fg="red", err=True)
            typer.echo(f"  email={email}")
            raise typer.Exit(code=1)

        typer.secho("Subscriber disabled", fg="green", bold=True)
        typer.echo(f"  email={email}")
        typer.echo("  is_active=false")

    except typer.Exit:
        raise

    except Exception as exc:
        typer.secho(f"Unexpected disable-subscriber error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="enable-subscriber")
def enable_subscriber(
    email: str = typer.Option(
        ...,
        "--email",
        help="Subscriber email address.",
    ),
) -> None:
    """Enable a subscriber."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        updated = repository.set_subscriber_active(
            email=email,
            is_active=True,
            updated_at=_utc_now_iso(),
        )

        if not updated:
            typer.secho("Subscriber not found", fg="red", err=True)
            typer.echo(f"  email={email}")
            raise typer.Exit(code=1)

        typer.secho("Subscriber enabled", fg="green", bold=True)
        typer.echo(f"  email={email}")
        typer.echo("  is_active=true")

    except typer.Exit:
        raise

    except Exception as exc:
        typer.secho(f"Unexpected enable-subscriber error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="disable-digest")
def disable_digest(
    email: str = typer.Option(
        ...,
        "--email",
        help="Subscriber email address.",
    ),
) -> None:
    """Disable digest delivery for a subscriber."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        updated = repository.set_subscriber_digest_enabled(
            email=email,
            digest_enabled=False,
            updated_at=_utc_now_iso(),
        )

        if not updated:
            typer.secho("Subscriber not found", fg="red", err=True)
            typer.echo(f"  email={email}")
            raise typer.Exit(code=1)

        typer.secho("Subscriber digest disabled", fg="green", bold=True)
        typer.echo(f"  email={email}")
        typer.echo("  digest_enabled=false")

    except typer.Exit:
        raise

    except Exception as exc:
        typer.secho(f"Unexpected disable-digest error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="enable-digest")
def enable_digest(
    email: str = typer.Option(
        ...,
        "--email",
        help="Subscriber email address.",
    ),
) -> None:
    """Enable digest delivery for a subscriber."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        updated = repository.set_subscriber_digest_enabled(
            email=email,
            digest_enabled=True,
            updated_at=_utc_now_iso(),
        )

        if not updated:
            typer.secho("Subscriber not found", fg="red", err=True)
            typer.echo(f"  email={email}")
            raise typer.Exit(code=1)

        typer.secho("Subscriber digest enabled", fg="green", bold=True)
        typer.echo(f"  email={email}")
        typer.echo("  digest_enabled=true")

    except typer.Exit:
        raise

    except Exception as exc:
        typer.secho(f"Unexpected enable-digest error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="notification-history")
def notification_history(
    notification_type: str | None = typer.Option(
        None,
        "--notification-type",
        help="Optional notification type filter, for example digest_email.",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        help="Maximum number of notification runs to display.",
    ),
) -> None:
    """Show recent notification run history."""
    if limit < 1:
        typer.secho("Invalid limit: must be >= 1", fg="red", err=True)
        raise typer.Exit(code=2)

    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        runs = repository.list_notification_runs(
            notification_type=notification_type,
            limit=limit,
        )
        _print_notification_runs(runs)

    except Exception as exc:
        typer.secho(
            f"Unexpected notification-history error: {exc}",
            fg="red",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="ops-status")
def ops_status() -> None:
    """Show a compact operational status view."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        latest_crawl_run = repository.get_latest_crawl_run()
        latest_notification_run = repository.get_latest_notification_run(
            notification_type=NOTIFICATION_TYPE_DIGEST_EMAIL,
        )
        digest_checkpoint = repository.get_notification_checkpoint(
            DIGEST_EMAIL_CHECKPOINT_KEY,
        )
        subscriber_counts = repository.get_subscriber_counts()

        _print_ops_status(
            latest_crawl_run=latest_crawl_run,
            latest_notification_run=latest_notification_run,
            digest_checkpoint=digest_checkpoint,
            subscriber_counts=subscriber_counts,
        )

    except Exception as exc:
        typer.secho(
            f"Unexpected ops-status error: {exc}",
            fg="red",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="keyword-filter-config")
def keyword_filter_config(
    settings_path: str = typer.Option(
        DEFAULT_SETTINGS_CONFIG_PATH,
        "--settings-path",
        help="Path to the application settings YAML file.",
    ),
) -> None:
    """Show the currently loaded keyword filter settings."""
    try:
        settings = load_app_settings(settings_path)
        _print_keyword_filter_config(settings)

    except ConfigError as exc:
        typer.secho(f"Config error ({settings_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except Exception as exc:
        typer.secho(
            f"Unexpected keyword-filter-config error: {exc}",
            fg="red",
            err=True,
        )
        raise typer.Exit(code=1) from exc


@app.command(name="filter-preview")
def filter_preview(
    settings_path: str = typer.Option(
        DEFAULT_SETTINGS_CONFIG_PATH,
        "--settings-path",
        help="Path to the application settings YAML file.",
    ),
    all_jobs: bool = typer.Option(
        False,
        "--all-jobs",
        help="Include inactive jobs in the preview.",
    ),
    sample_limit: int = typer.Option(
        5,
        "--sample-limit",
        help="Maximum number of passed/rejected sample jobs to display.",
    ),
) -> None:
    """Preview how the current keyword filter affects stored jobs."""
    if sample_limit < 1:
        typer.secho("Invalid sample-limit: must be >= 1", fg="red", err=True)
        raise typer.Exit(code=2)

    try:
        settings = load_app_settings(settings_path)
    except ConfigError as exc:
        typer.secho(f"Config error ({settings_path}): {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        jobs = repository.list_jobs() if all_jobs else repository.list_active_jobs()
        result = filter_jobs_by_keyword_settings(
            jobs=jobs,
            settings=settings.keyword_filter,
        )

        _print_filter_preview_result(
            result=result,
            settings=settings,
            all_jobs=all_jobs,
            sample_limit=sample_limit,
        )

    except Exception as exc:
        typer.secho(
            f"Unexpected filter-preview error: {exc}",
            fg="red",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


@app.command(name="process-retrieval-embeddings")
def process_retrieval_embeddings(
    limit: int = typer.Option(
        10,
        "--limit",
        min=1,
        help="Maximum number of retrieval embedding jobs to process.",
    ),
    stop_on_error: bool = typer.Option(
        False,
        "--stop-on-error",
        help="Stop the batch after the first failed retrieval embedding job.",
    ),
) -> None:
    """Process queued retrieval embedding jobs."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)
        provider = DeterministicEmbeddingProvider(
            provider=DEFAULT_EMBEDDING_PROVIDER,
            model=DEFAULT_EMBEDDING_MODEL,
        )
        results = run_embedding_job_batch(
            repository,
            embedding_provider=provider,
            provider=DEFAULT_EMBEDDING_PROVIDER,
            model=DEFAULT_EMBEDDING_MODEL,
            limit=limit,
            stop_on_error=stop_on_error,
        )
        _print_retrieval_embedding_batch_results(results)

        if any(result.action == PROCESS_ACTION_FAILED for result in results):
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as exc:
        typer.secho(
            f"Unexpected process-retrieval-embeddings error: {exc}",
            fg="red",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)




def _truncate_cli_text(value: str | None, max_chars: int = 180) -> str:
    if not value:
        return "-"
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars].rstrip()}…"


def _format_year_span(start_year: object, end_year: object) -> str:
    start = str(start_year) if start_year else "-"
    end = str(end_year) if end_year else "present"
    if start == "-" and end == "present":
        return "-"
    return f"{start}-{end}"


def _format_education_years(start_year: object, end_year: object) -> str:
    if start_year and end_year and start_year != end_year:
        return f"{start_year}-{end_year}"
    if end_year:
        return str(end_year)
    if start_year:
        return str(start_year)
    return "-"


def _print_mapping_entries(
    *,
    title: str,
    entries: list[dict] | tuple[dict, ...],
    formatter,
) -> None:
    if not entries:
        return
    typer.echo(f"    {title}:")
    for entry in entries:
        typer.echo(f"      - {formatter(entry)}")


def _print_cv_inspection_result(result: LocalCvInspectionResult) -> None:
    status_label = "OK" if result.success else "FAILED"
    status_color = "green" if result.success else "red"
    typer.secho(f"[{status_label}] {result.filename}", fg=status_color, bold=True)
    typer.echo(
        "  "
        f"format={result.file_format} "
        f"content_type={result.content_type or '-'} "
        f"size={result.file_size_bytes} "
        f"status={result.parse_status}"
    )
    if result.extraction_method is not None:
        quality_band = "-"
        quality_score = "-"
        if result.quality:
            quality_band = str(result.quality.get("band", "-"))
            quality_score = str(result.quality.get("score", "-"))
        typer.echo(
            "  "
            f"method={result.extraction_method} "
            f"used_ocr={_format_bool(result.used_ocr)} "
            f"pages={result.page_count} "
            f"chars={result.extracted_character_count} "
            f"quality={quality_band}/{quality_score}"
        )
    if result.error:
        typer.secho(f"  error={result.error}", fg="red")
        return

    snapshot_payload = result.to_dict().get("snapshot") or {}
    draft = snapshot_payload.get("draft") or {}
    profile_after = (result.profile_after_apply or {}).get("profile") or {}
    applied = (result.profile_after_apply or {}).get("applied") or {}

    typer.echo("  Draft")
    typer.echo(f"    full_name={draft.get('full_name') or '-'}")
    typer.echo(
        "    "
        f"email={draft.get('email') or '-'} "
        f"phone={draft.get('phone') or '-'} "
        f"linkedin={draft.get('linkedin_url') or '-'} "
        f"github={draft.get('github_url') or '-'}"
    )
    typer.echo(f"    headline={draft.get('headline') or '-'}")
    typer.echo(f"    summary={_truncate_cli_text(draft.get('summary'))}")
    typer.echo(f"    skills={', '.join(draft.get('skills') or []) or '-'}")
    typer.echo(f"    target_roles={', '.join(draft.get('target_roles') or []) or '-'}")
    typer.echo(f"    preferred_locations={', '.join(draft.get('preferred_locations') or []) or '-'}")
    typer.echo(
        "    "
        f"education={len(draft.get('education_entries') or [])} "
        f"experience={len(draft.get('experience_entries') or [])} "
        f"languages={len(draft.get('language_entries') or [])} "
        f"certifications={len(draft.get('certification_entries') or [])}"
    )
    _print_mapping_entries(
        title="education_entries",
        entries=draft.get('education_entries') or [],
        formatter=lambda item: (
            f"{_format_education_years(item.get('start_year'), item.get('end_year'))} | "
            f"{item.get('degree_name') or '-'} | "
            f"{item.get('field_of_study') or '-'} | "
            f"{item.get('school_name') or '-'}"
        ),
    )
    _print_mapping_entries(
        title="experience_entries",
        entries=draft.get('experience_entries') or [],
        formatter=lambda item: (
            f"{_format_year_span(item.get('start_year'), item.get('end_year'))} | "
            f"{item.get('title') or '-'} | "
            f"{item.get('company_name') or '-'} | "
            f"{_truncate_cli_text(item.get('summary'), max_chars=120)}"
        ),
    )
    _print_mapping_entries(
        title="certification_entries",
        entries=draft.get('certification_entries') or [],
        formatter=lambda item: (
            f"{item.get('issued_year') or '-'} | "
            f"{item.get('certificate_name') or '-'} | "
            f"{item.get('issuer_name') or '-'}"
        ),
    )
    typer.echo("  Profile placement simulation")
    typer.echo(f"    headline={profile_after.get('headline') or '-'}")
    typer.echo(f"    skills={', '.join(profile_after.get('skills') or []) or '-'}")
    typer.echo(
        "    "
        f"applied_total={applied.get('total_applied_changes', 0)} "
        f"scalars={','.join(applied.get('scalar_fields') or []) or '-'} "
        f"lists={','.join(applied.get('list_fields') or []) or '-'} "
        f"contacts={','.join(applied.get('contact_fields') or []) or '-'} "
        f"edu={applied.get('added_education_entry_count', 0)} "
        f"exp={applied.get('added_experience_entry_count', 0)} "
        f"lang={applied.get('added_language_entry_count', 0)} "
        f"cert={applied.get('added_certification_entry_count', 0)}"
    )
    certification_after = (result.profile_after_apply or {}).get('certification_entries') or []
    if certification_after:
        typer.echo(f"    certification_entries={len(certification_after)}")
    if result.text_preview:
        typer.echo("  Text preview")
        for line in result.text_preview.splitlines():
            typer.echo(f"    {line}")


@app.command(name="cv-inspect-folder")
def cv_inspect_folder(
    directory: str = typer.Option(
        "/home/remzi/Desktop/CV",
        "--directory",
        "-d",
        help="Folder containing CV files to extract and parse.",
    ),
    ai_structuring: str = typer.Option(
        "ocr",
        "--ai-structuring",
        help="Ollama structuring mode: off, ocr, auto, or all.",
    ),
    json_output: str | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write full inspection results as JSON.",
    ),
    text_preview_chars: int = typer.Option(
        0,
        "--text-preview-chars",
        min=0,
        help="Print this many extracted-text characters per CV (0 disables preview).",
    ),
    include_unsupported: bool = typer.Option(
        False,
        "--include-unsupported",
        help="Also report files outside supported CV extensions instead of skipping them.",
    ),
) -> None:
    """Inspect local CV files and show extraction + profile-placement results."""
    try:
        results = inspect_local_cv_directory(
            directory,
            ai_structuring_mode=ai_structuring,
            text_preview_chars=text_preview_chars,
            include_unsupported=include_unsupported,
        )
    except Exception as exc:
        typer.secho(f"CV inspection error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    typer.secho("CV inspection", bold=True)
    typer.echo(f"  directory={directory}")
    typer.echo(f"  files={len(results)} ai_structuring={ai_structuring}")
    if not include_unsupported:
        typer.echo("  unsupported_files=skipped (use --include-unsupported to show them)")
    typer.echo("")

    for index, result in enumerate(results):
        if index:
            typer.echo("")
        _print_cv_inspection_result(result)

    if json_output:
        output_path = Path(json_output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                [result.to_dict() for result in results],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        typer.echo("")
        typer.secho(f"Wrote JSON report: {output_path}", fg="green")

    if any(not result.success for result in results):
        raise typer.Exit(code=1)


@app.command()
def summary() -> None:
    """Show a short jobs summary."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        result = build_summary(repository)
        _print_summary_result(result)

    except Exception as exc:
        typer.secho(f"Unexpected summary error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)


if __name__ == "__main__":
    app()
