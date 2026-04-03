from __future__ import annotations

import typer

from hiring_radar.config import ConfigError, load_source_configs
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import CrawlSourceResult
from hiring_radar.services.crawl import run_multi_source_crawl
from hiring_radar.services.export import ExportResult, export_jobs_to_csv
from hiring_radar.services.summary import SummaryResult, build_summary

DEFAULT_COMPANIES_CONFIG_PATH = "config/companies.example.yml"
DEFAULT_DB_PATH = "data/hiring_radar.db"
DEFAULT_EXPORT_DIR = "data/exports"

app = typer.Typer(no_args_is_help=True, help="Hiring Radar CLI")


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