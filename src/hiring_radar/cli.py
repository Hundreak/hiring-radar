from __future__ import annotations

from datetime import UTC, datetime

import typer

from hiring_radar.config import ConfigError, load_source_configs
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.email_config import EmailConfigError, load_smtp_settings
from hiring_radar.models import CrawlSourceResult, Subscriber
from hiring_radar.services.crawl import run_multi_source_crawl
from hiring_radar.services.digest import (
    DigestResult,
    build_digest,
    render_digest_subject,
    render_digest_text,
)
from hiring_radar.services.email import (
    EmailDeliveryError,
    EmailMessagePayload,
    send_email_via_smtp,
)
from hiring_radar.services.export import ExportResult, export_jobs_to_csv
from hiring_radar.services.summary import SummaryResult, build_summary

DEFAULT_COMPANIES_CONFIG_PATH = "config/companies.example.yml"
DEFAULT_DB_PATH = "data/hiring_radar.db"
DEFAULT_EXPORT_DIR = "data/exports"
DEFAULT_ENV_PATH = ".env"

app = typer.Typer(no_args_is_help=True, help="Hiring Radar CLI")


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


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


def _print_export_result(result: ExportResult) -> None:
    typer.secho("Export completed", fg="green", bold=True)
    typer.echo(f"  rows={result.row_count}")
    typer.echo(f"  output={result.output_path}")


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


@app.command()
def crawl(
    config_path: str = typer.Option(
        DEFAULT_COMPANIES_CONFIG_PATH,
        "--config-path",
        help="Path to the YAML source configuration file.",
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

        for result in results:
            _print_crawl_result(result)

        _print_crawl_summary(results)

    except Exception as exc:
        typer.secho(f"Unexpected crawl error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    finally:
        close_connection(connection)

    if any(not result.success for result in results):
        raise typer.Exit(code=1)


@app.command()
def export() -> None:
    """Export stored jobs to CSV."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        jobs = repository.list_jobs()
        result = export_jobs_to_csv(
            jobs=jobs,
            output_dir=DEFAULT_EXPORT_DIR,
        )

        _print_export_result(result)

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
) -> None:
    """Preview a digest of newly discovered jobs since a given timestamp."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        result = build_digest(
            repository,
            since=since,
            generated_at=_utc_now_iso(),
        )
        _print_digest_result(result)

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
) -> None:
    """Send a digest email for newly discovered jobs since a given timestamp."""
    connection = None

    try:
        connection = initialize_database(DEFAULT_DB_PATH)
        repository = HiringRadarRepository(connection)

        digest = build_digest(
            repository,
            since=since,
            generated_at=_utc_now_iso(),
        )

        if digest.total_new_jobs == 0 and not send_empty:
            typer.secho("Digest email skipped", fg="yellow", bold=True)
            typer.echo("  reason=no new jobs in this window")
            typer.echo(f"  since={digest.since}")
            return

        settings = load_smtp_settings(env_path)
        recipients = _resolve_digest_recipients(
            repository=repository,
            explicit_to=to,
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

        typer.secho("Digest emails sent", fg="green", bold=True)
        typer.echo(f"  recipient_count={len(recipients)}")
        typer.echo(f"  new_jobs={digest.total_new_jobs}")
        typer.echo(f"  subject={subject}")

    except EmailConfigError as exc:
        typer.secho(f"Email config error: {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    except EmailDeliveryError as exc:
        typer.secho(f"Email delivery error: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc

    except Exception as exc:
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