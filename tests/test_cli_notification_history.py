from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.models import NotificationRun

runner = CliRunner()


def test_notification_history_lists_recent_runs(monkeypatch) -> None:
    runs = [
        NotificationRun(
            id=2,
            notification_type="digest_email",
            started_at="2026-04-04T10:00:00Z",
            finished_at="2026-04-04T10:01:00Z",
            status="sent",
            recipient_count=2,
            new_jobs_count=14,
            since="2026-04-04T04:00:00Z",
            subject="Hiring Radar Digest: 14 new jobs since 2026-04-04T04:00:00Z",
            error_message=None,
        ),
        NotificationRun(
            id=1,
            notification_type="digest_email",
            started_at="2026-04-04T04:00:00Z",
            finished_at="2026-04-04T04:00:10Z",
            status="skipped",
            recipient_count=0,
            new_jobs_count=0,
            since="2026-04-03T22:00:00Z",
            subject=None,
            error_message="no new jobs in this window",
        ),
    ]

    class FakeRepository:
        def list_notification_runs(
            self,
            *,
            notification_type: str | None = None,
            limit: int = 50,
        ):
            assert notification_type is None
            assert limit == 20
            return runs

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(
        cli,
        "HiringRadarRepository",
        lambda connection: FakeRepository(),
    )

    result = runner.invoke(
        cli.app,
        [
            "notification-history",
        ],
    )

    assert result.exit_code == 0
    assert "Notification History" in result.output
    assert "id=2 type=digest_email status=sent" in result.output
    assert "recipient_count=2 new_jobs_count=14" in result.output
    assert "id=1 type=digest_email status=skipped" in result.output
    assert "detail=no new jobs in this window" in result.output


def test_notification_history_passes_filter_and_limit(monkeypatch) -> None:
    runs = [
        NotificationRun(
            id=7,
            notification_type="digest_email",
            started_at="2026-04-04T12:00:00Z",
            finished_at="2026-04-04T12:00:15Z",
            status="failed",
            recipient_count=0,
            new_jobs_count=3,
            since="2026-04-04T11:00:00Z",
            subject=None,
            error_message="SMTP authentication failed",
        )
    ]

    class FakeRepository:
        def list_notification_runs(
            self,
            *,
            notification_type: str | None = None,
            limit: int = 50,
        ):
            assert notification_type == "digest_email"
            assert limit == 5
            return runs

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(
        cli,
        "HiringRadarRepository",
        lambda connection: FakeRepository(),
    )

    result = runner.invoke(
        cli.app,
        [
            "notification-history",
            "--notification-type",
            "digest_email",
            "--limit",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "id=7 type=digest_email status=failed" in result.output
    assert "detail=SMTP authentication failed" in result.output


def test_notification_history_rejects_invalid_limit() -> None:
    result = runner.invoke(
        cli.app,
        [
            "notification-history",
            "--limit",
            "0",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid limit: must be >= 1" in result.output