from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.config import ConfigError
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.models import JobRecord
from hiring_radar.settings import AppSettings

runner = CliRunner()


class FakeRepository:
    def __init__(
        self,
        *,
        active_jobs: list[JobRecord],
        all_jobs: list[JobRecord] | None = None,
    ) -> None:
        self._active_jobs = active_jobs
        self._all_jobs = all_jobs if all_jobs is not None else active_jobs

    def list_active_jobs(self) -> list[JobRecord]:
        return self._active_jobs

    def list_jobs(self) -> list[JobRecord]:
        return self._all_jobs


def _job(
    *,
    title: str,
    company_name: str,
    location: str | None,
    canonical_url: str,
    is_active: bool = True,
) -> JobRecord:
    return JobRecord(
        source_name="example-source",
        title=title,
        company_name=company_name,
        location=location,
        canonical_url=canonical_url,
        source_type="lever",
        source_job_id=canonical_url.rsplit("/", maxsplit=1)[-1],
        raw_posted_at=None,
        posted_at=None,
        fingerprint=canonical_url,
        first_seen_at="2026-04-04T10:00:00Z",
        last_seen_at="2026-04-04T10:00:00Z",
        is_active=is_active,
        scraped_at="2026-04-04T10:00:00Z",
    )


def test_filter_preview_prints_summary_and_samples(monkeypatch) -> None:
    repository = FakeRepository(
        active_jobs=[
            _job(
                title="Senior Python Engineer",
                company_name="Trendyol",
                location="Istanbul",
                canonical_url="https://example.com/jobs/1",
            ),
            _job(
                title="Python Intern",
                company_name="ExampleCo",
                location="Remote",
                canonical_url="https://example.com/jobs/2",
            ),
        ]
    )

    monkeypatch.setattr(
        cli,
        "load_app_settings",
        lambda path: AppSettings(
            keyword_filter=KeywordFilterSettings(
                include_keywords=("python",),
                exclude_keywords=("intern",),
                match_title=True,
                match_location=False,
                match_company_name=False,
            )
        ),
    )
    monkeypatch.setattr(cli, "initialize_database", lambda path: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(
        cli,
        "HiringRadarRepository",
        lambda connection: repository,
    )

    result = runner.invoke(
        cli.app,
        [
            "filter-preview",
            "--sample-limit",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "Filter Preview" in result.output
    assert "jobs_scope=active_only" in result.output
    assert "total_jobs=2" in result.output
    assert "passed_jobs=1" in result.output
    assert "rejected_jobs=1" in result.output
    assert "include_matches=title:python" in result.output
    assert "exclude_matches=title:intern" in result.output


def test_filter_preview_uses_all_jobs_when_requested(monkeypatch) -> None:
    repository = FakeRepository(
        active_jobs=[
            _job(
                title="Senior Python Engineer",
                company_name="Trendyol",
                location="Istanbul",
                canonical_url="https://example.com/jobs/1",
                is_active=True,
            ),
        ],
        all_jobs=[
            _job(
                title="Senior Python Engineer",
                company_name="Trendyol",
                location="Istanbul",
                canonical_url="https://example.com/jobs/1",
                is_active=True,
            ),
            _job(
                title="Backend Engineer",
                company_name="ExampleCo",
                location="Ankara",
                canonical_url="https://example.com/jobs/2",
                is_active=False,
            ),
        ],
    )

    monkeypatch.setattr(
        cli,
        "load_app_settings",
        lambda path: AppSettings(
            keyword_filter=KeywordFilterSettings()
        ),
    )
    monkeypatch.setattr(cli, "initialize_database", lambda path: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(
        cli,
        "HiringRadarRepository",
        lambda connection: repository,
    )

    result = runner.invoke(
        cli.app,
        [
            "filter-preview",
            "--all-jobs",
        ],
    )

    assert result.exit_code == 0
    assert "jobs_scope=all_jobs" in result.output
    assert "total_jobs=2" in result.output
    assert "passed_jobs=2" in result.output
    assert "rejected_jobs=0" in result.output


def test_filter_preview_returns_exit_code_2_on_config_error(monkeypatch) -> None:
    def raise_config_error(path: str):
        raise ConfigError("bad settings file")

    monkeypatch.setattr(cli, "load_app_settings", raise_config_error)

    result = runner.invoke(
        cli.app,
        [
            "filter-preview",
        ],
    )

    assert result.exit_code == 2
    assert "Config error" in result.output
    assert "bad settings file" in result.output