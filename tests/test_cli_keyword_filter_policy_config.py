from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.settings import AppSettings, NotificationsSettings

runner = CliRunner()


def test_keyword_filter_config_prints_notification_policy(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "load_app_settings",
        lambda path: AppSettings(
            keyword_filter=KeywordFilterSettings(
                include_keywords=("python",),
                exclude_keywords=("intern",),
                match_title=True,
                match_location=False,
                match_company_name=True,
            ),
            notifications=NotificationsSettings(apply_keyword_filter_to_digest=True),
        ),
    )

    result = runner.invoke(
        cli.app,
        [
            "keyword-filter-config",
        ],
    )

    assert result.exit_code == 0
    assert "Keyword Filter Config" in result.output
    assert "Notification Policy" in result.output
    assert "apply_keyword_filter_to_digest=True" in result.output
