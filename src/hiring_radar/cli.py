from __future__ import annotations

import typer

from hiring_radar.config import ConfigError, load_source_configs
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import CrawlSourceResult
from hiring_radar.services.crawl import run_multi_source_crawl

DEFAULT_COMPANIES_CONFIG_PATH = "config/companies.example.yml"
DEFAULT_DB_PATH = "data/hiring_radar.db"

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


@app.command()
def crawl() -> None:
    """Run configured job source crawls."""
    try:
        source_configs = load_source_configs(DEFAULT_COMPANIES_CONFIG_PATH)
    except ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg="red", err=True)
        raise typer.Exit(code=2) from exc

    connection = None

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
    typer.echo("TODO: export command will be implemented in a later step.")


@app.command()
def summary() -> None:
    """Show a short crawl / jobs summary."""
    typer.echo("TODO: summary command will be implemented in a later step.")


if __name__ == "__main__":
    app()