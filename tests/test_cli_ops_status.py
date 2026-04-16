from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.models import CrawlRun, NotificationCheckpoint, NotificationRun

runner = CliRunner()


def test_ops_status_prints_expected_sections(monkeypatch) -> None:
    class FakeRepository:
        def get_latest_crawl_run(self):
            return CrawlRun(
                id=11,
                source_name="trendyol-lever",
                started_at="2026-04-04T09:00:00Z",
                finished_at="2026-04-04T09:00:05Z",
                success=True,
                notes=None,
            )

        def get_latest_notification_run(self, *, notification_type: str | None = None):
            assert notification_type == cli.NOTIFICATION_TYPE_DIGEST_EMAIL
            return NotificationRun(
                id=21,
                notification_type="digest_email",
                started_at="2026-04-04T09:00:06Z",
                finished_at="2026-04-04T09:00:08Z",
                status="sent",
                recipient_count=2,
                new_jobs_count=14,
                since="2026-04-04T03:00:00Z",
                subject="Hiring Radar Digest: 14 new jobs since 2026-04-04T03:00:00Z",
                error_message=None,
            )

        def get_notification_checkpoint(self, checkpoint_key: str):
            assert checkpoint_key == cli.DIGEST_EMAIL_CHECKPOINT_KEY
            return NotificationCheckpoint(
                checkpoint_key="digest_email",
                last_processed_at="2026-04-04T09:00:06Z",
                updated_at="2026-04-04T09:00:06Z",
            )

        def get_subscriber_counts(self):
            return {
                "total_subscribers": 3,
                "active_subscribers": 2,
                "digest_enabled_subscribers": 2,
            }

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())

    result = runner.invoke(
        cli.app,
        [
            "ops-status",
        ],
    )

    assert result.exit_code == 0
    assert "Operations Status" in result.output
    assert "Subscribers" in result.output
    assert "total=3" in result.output
    assert "active=2" in result.output
    assert "digest_enabled=2" in result.output
    assert "Digest Checkpoint" in result.output
    assert "last_processed_at=2026-04-04T09:00:06Z" in result.output
    assert "Latest Crawl Run" in result.output
    assert "source_name=trendyol-lever" in result.output
    assert "success=True" in result.output
    assert "Latest Notification Run" in result.output
    assert "status=sent" in result.output
    assert "recipient_count=2" in result.output


def test_ops_status_handles_empty_state(monkeypatch) -> None:
    class FakeRepository:
        def get_latest_crawl_run(self):
            return None

        def get_latest_notification_run(self, *, notification_type: str | None = None):
            return None

        def get_notification_checkpoint(self, checkpoint_key: str):
            return None

        def get_subscriber_counts(self):
            return {
                "total_subscribers": 0,
                "active_subscribers": 0,
                "digest_enabled_subscribers": 0,
            }

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())

    result = runner.invoke(
        cli.app,
        [
            "ops-status",
        ],
    )

    assert result.exit_code == 0
    assert "Operations Status" in result.output
    assert "total=0" in result.output
    assert "checkpoint=-" in result.output
    assert "no crawl runs" in result.output
    assert "no notification runs" in result.output
