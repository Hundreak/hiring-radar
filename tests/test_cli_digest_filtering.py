from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.email_config import SMTPSettings
from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.models import CrawlSourceResult
from hiring_radar.services.digest import (
    DigestJobItem,
    DigestResult,
    DigestSourceSection,
)
from hiring_radar.settings import AppSettings

runner = CliRunner()


def make_settings(*, default_to: str | None) -> SMTPSettings:
    return SMTPSettings(
        host="smtp.example.com",
        port=587,
        username="smtp-user",
        password="smtp-pass",
        use_tls=True,
        email_from="alerts@example.com",
        default_to=default_to,
    )


def make_digest(*, titles: list[str], since: str = "2026-04-03T15:00:00Z") -> DigestResult:
    jobs = [
        DigestJobItem(
            company_name="Corelight",
            source_name="corelight-greenhouse",
            source_type="greenhouse",
            title=title,
            location="Remote",
            canonical_url=f"https://example.com/jobs/{index}",
            first_seen_at="2026-04-04T10:00:00Z",
        )
        for index, title in enumerate(titles, start=1)
    ]

    sections = []
    if jobs:
        sections = [
            DigestSourceSection(
                source_name="corelight-greenhouse",
                source_type="greenhouse",
                new_jobs_count=len(jobs),
                jobs=jobs,
            )
        ]

    return DigestResult(
        generated_at="2026-04-04T00:00:00Z",
        since=since,
        total_new_jobs=len(jobs),
        sections=sections,
    )


def make_app_settings() -> AppSettings:
    return AppSettings(
        keyword_filter=KeywordFilterSettings(
            include_keywords=("engineer",),
            exclude_keywords=("intern",),
            match_title=True,
            match_location=False,
            match_company_name=False,
        )
    )


def test_digest_preview_applies_keyword_filter_when_requested(monkeypatch) -> None:
    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: object())
    monkeypatch.setattr(cli, "load_app_settings", lambda path: make_app_settings())
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(
            titles=[
                "Security Engineer",
                "Security Intern",
            ],
            since=since,
        ),
    )

    result = runner.invoke(
        cli.app,
        [
            "digest-preview",
            "--since",
            "2026-04-03T15:00:00Z",
            "--apply-filter",
        ],
    )

    assert result.exit_code == 0
    assert "Digest Filter" in result.output
    assert "total_new_jobs_before_filter=2" in result.output
    assert "total_new_jobs_after_filter=1" in result.output
    assert "filtered_out_jobs=1" in result.output
    assert "Security Engineer" in result.output
    assert "Security Intern" not in result.output


def test_send_digest_applies_keyword_filter_when_requested(monkeypatch) -> None:
    notification_runs: list[tuple[str, str, str | None]] = []
    notification_finishes: list[tuple[int, str, int, int, str | None, str | None]] = []

    class FakeRepository:
        def list_digest_enabled_subscribers(self):
            raise AssertionError("subscriber list should not be used when --to is provided")

        def start_notification_run(
            self, *, notification_type: str, started_at: str, since: str | None
        ):
            notification_runs.append((notification_type, started_at, since))
            return 501

        def finish_notification_run(
            self,
            run_id: int,
            *,
            finished_at: str,
            status: str,
            recipient_count: int = 0,
            new_jobs_count: int = 0,
            subject: str | None = None,
            error_message: str | None = None,
        ):
            notification_finishes.append(
                (run_id, status, recipient_count, new_jobs_count, subject, error_message)
            )
            return True

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(cli, "load_app_settings", lambda path: make_app_settings())
    monkeypatch.setattr(
        cli,
        "load_smtp_settings",
        lambda env_path: make_settings(default_to="default@example.com"),
    )
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(
            titles=[
                "Security Engineer",
                "Security Intern",
            ],
            since=since,
        ),
    )

    captured_payloads: list[object] = []

    def fake_send_email_via_smtp(*, settings, payload, timeout_seconds: float = 20.0) -> None:
        captured_payloads.append(payload)

    monkeypatch.setattr(cli, "send_email_via_smtp", fake_send_email_via_smtp)

    result = runner.invoke(
        cli.app,
        [
            "send-digest",
            "--since",
            "2026-04-03T15:00:00Z",
            "--to",
            "recipient@example.com",
            "--apply-filter",
        ],
    )

    assert result.exit_code == 0
    assert "Digest Filter" in result.output
    assert "total_new_jobs_before_filter=2" in result.output
    assert "total_new_jobs_after_filter=1" in result.output
    assert "filtered_out_jobs=1" in result.output
    assert "Digest emails sent" in result.output
    assert "recipient_count=1" in result.output
    assert "new_jobs=1" in result.output

    assert notification_runs == [
        (
            cli.NOTIFICATION_TYPE_DIGEST_EMAIL,
            "2026-04-04T00:00:00Z",
            "2026-04-03T15:00:00Z",
        )
    ]
    assert notification_finishes == [
        (
            501,
            "sent",
            1,
            1,
            "Hiring Radar Digest: 1 new job since 2026-04-03T15:00:00Z",
            None,
        )
    ]

    assert len(captured_payloads) == 1
    payload = captured_payloads[0]
    assert payload.to == "recipient@example.com"
    assert payload.subject == "Hiring Radar Digest: 1 new job since 2026-04-03T15:00:00Z"
    assert "Security Engineer" in payload.body_text
    assert "Security Intern" not in payload.body_text


def test_crawl_and_notify_skips_when_filter_removes_all_jobs(monkeypatch) -> None:
    checkpoint_updates: list[tuple[str, str, str]] = []
    notification_runs: list[tuple[str, str, str | None]] = []
    notification_finishes: list[tuple[int, str, int, int, str | None, str | None]] = []

    class FakeRepository:
        def list_digest_enabled_subscribers(self):
            return []

        def get_notification_checkpoint(self, checkpoint_key: str):
            assert checkpoint_key == cli.DIGEST_EMAIL_CHECKPOINT_KEY
            return None

        def upsert_notification_checkpoint(
            self,
            *,
            checkpoint_key: str,
            last_processed_at: str,
            updated_at: str,
        ):
            checkpoint_updates.append((checkpoint_key, last_processed_at, updated_at))

        def start_notification_run(
            self, *, notification_type: str, started_at: str, since: str | None
        ):
            notification_runs.append((notification_type, started_at, since))
            return 601

        def finish_notification_run(
            self,
            run_id: int,
            *,
            finished_at: str,
            status: str,
            recipient_count: int = 0,
            new_jobs_count: int = 0,
            subject: str | None = None,
            error_message: str | None = None,
        ):
            notification_finishes.append(
                (run_id, status, recipient_count, new_jobs_count, subject, error_message)
            )
            return True

    monkeypatch.setattr(cli, "load_source_configs", lambda config_path: ["fake-source"])
    monkeypatch.setattr(cli, "load_app_settings", lambda path: make_app_settings())
    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "run_multi_source_crawl",
        lambda source_configs, repository: [
            CrawlSourceResult(
                source_name="corelight-greenhouse",
                source_type="greenhouse",
                started_at="2026-04-04T00:00:00Z",
                finished_at="2026-04-04T00:01:00Z",
                success=True,
                total_parsed_jobs=1,
                new_jobs=1,
                updated_jobs=0,
                deactivated_jobs=0,
            )
        ],
    )
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(
            titles=["Growth Marketing Manager"],
            since=since,
        ),
    )

    def should_not_send_email(*, settings, payload, timeout_seconds: float = 20.0) -> None:
        raise AssertionError("email should not be sent when the filter removes all jobs")

    monkeypatch.setattr(cli, "send_email_via_smtp", should_not_send_email)

    result = runner.invoke(
        cli.app,
        [
            "crawl-and-notify",
            "--window-hours",
            "6",
            "--apply-filter",
        ],
    )

    assert result.exit_code == 0
    assert "Digest Filter" in result.output
    assert "total_new_jobs_before_filter=1" in result.output
    assert "total_new_jobs_after_filter=0" in result.output
    assert "filtered_out_jobs=1" in result.output
    assert "Digest email skipped" in result.output
    assert "reason=no jobs matched the active keyword filter" in result.output

    assert notification_runs == [
        (
            cli.NOTIFICATION_TYPE_DIGEST_EMAIL,
            "2026-04-04T00:00:00Z",
            "2026-04-03T18:00:00Z",
        )
    ]
    assert notification_finishes == [
        (
            601,
            "skipped",
            0,
            0,
            None,
            "no jobs matched the active keyword filter",
        )
    ]
    assert checkpoint_updates == [
        (
            cli.DIGEST_EMAIL_CHECKPOINT_KEY,
            "2026-04-04T00:00:00Z",
            "2026-04-04T00:00:00Z",
        )
    ]