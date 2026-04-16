from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.settings import AppSettings

runner = CliRunner()


def test_keyword_filter_config_prints_loaded_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "load_app_settings",
        lambda path: AppSettings(
            keyword_filter=KeywordFilterSettings(
                include_keywords=("python", "security"),
                exclude_keywords=("intern",),
                match_title=True,
                match_location=False,
                match_company_name=True,
            )
        ),
    )

    result = runner.invoke(
        cli.app,
        [
            "keyword-filter-config",
            "--settings-path",
            "config/settings.example.yml",
        ],
    )

    assert result.exit_code == 0
    assert "Keyword Filter Config" in result.output
    assert "enabled=True" in result.output
    assert "include_keywords=['python', 'security']" in result.output
    assert "exclude_keywords=['intern']" in result.output
    assert "active_fields=['title', 'company_name']" in result.output


def test_keyword_filter_config_handles_disabled_filter(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "load_app_settings",
        lambda path: AppSettings(keyword_filter=KeywordFilterSettings()),
    )

    result = runner.invoke(
        cli.app,
        [
            "keyword-filter-config",
        ],
    )

    assert result.exit_code == 0
    assert "enabled=False" in result.output
    assert "include_keywords=[]" in result.output
    assert "exclude_keywords=[]" in result.output
    assert "active_fields=['title', 'location', 'company_name']" in result.output


def test_keyword_filter_config_returns_exit_code_2_on_config_error(monkeypatch) -> None:
    from hiring_radar.config import ConfigError

    def raise_config_error(path: str):
        raise ConfigError("bad settings file")

    monkeypatch.setattr(cli, "load_app_settings", raise_config_error)

    result = runner.invoke(
        cli.app,
        [
            "keyword-filter-config",
        ],
    )

    assert result.exit_code == 2
    assert "Config error" in result.output
    assert "bad settings file" in result.output
