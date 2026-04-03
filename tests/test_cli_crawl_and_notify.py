from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.email_config import SMTPSettings
from hiring_radar.models import CrawlSourceResult, NotificationCheckpoint, Subscriber
from hiring_radar.services.digest import DigestJobItem, DigestResult, DigestSourceSection

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


def make_digest(*, total_new_jobs: int, since: str) -> DigestResult:
    sections = []
    if total_new_jobs > 0:
        sections = [
            DigestSourceSection(
                source_name="threee-lever",
                source_type="lever",
                new_jobs_count=1,
                jobs=[
                    DigestJobItem(
                        company_name="3E",
                        source_name="threee-lever",
                        source_type="lever",
                        title="Growth Marketing Manager",
                        location="Bethesda, Maryland",
                        canonical_url="https://jobs.lever.co/3eco/1b69296f-f446-49e6-80d6-e73fe19f2ccc",
                        first_seen_at="2026-04-03T15:51:23Z",
                    )
                ],
            )
        ]

    return DigestResult(
        generated_at="2026-04-04T00:00:00Z",
        since=since,
        total_new_jobs=total_new_jobs,
        sections=sections,
    )


def test_crawl_and_notify_uses_fallback_window_when_checkpoint_is_missing(monkeypatch) -> None:
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
            return 201

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
    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "run_multi_source_crawl",
        lambda source_configs, repository: [
            CrawlSourceResult(
                source_name="threee-lever",
                source_type="lever",
                started_at="2026-04-04T00:00:00Z",
                finished_at="2026-04-04T00:01:00Z",
                success=True,
                total_parsed_jobs=14,
                new_jobs=14,
                updated_jobs=0,
                deactivated_jobs=0,
            )
        ],
    )

    captured_since: dict[str, str] = {}

    def fake_build_digest(repository, since, generated_at):
        captured_since["since"] = since
        return make_digest(total_new_jobs=1, since=since)

    monkeypatch.setattr(cli, "build_digest", fake_build_digest)
    monkeypatch.setattr(
        cli,
        "load_smtp_settings",
        lambda env_path: make_settings(default_to="default@example.com"),
    )

    captured_payloads: list[object] = []

    def fake_send_email_via_smtp(*, settings, payload, timeout_seconds: float = 20.0) -> None:
        captured_payloads.append(payload)

    monkeypatch.setattr(cli, "send_email_via_smtp", fake_send_email_via_smtp)

    result = runner.invoke(
        cli.app,
        [
            "crawl-and-notify",
            "--window-hours",
            "6",
        ],
    )

    assert result.exit_code == 0
    assert captured_since["since"] == "2026-04-03T18:00:00Z"
    assert len(captured_payloads) == 1
    assert notification_runs == [
        (
            cli.NOTIFICATION_TYPE_DIGEST_EMAIL,
            "2026-04-04T00:00:00Z",
            "2026-04-03T18:00:00Z",
        )
    ]
    assert notification_finishes == [
        (
            201,
            "sent",
            1,
            1,
            "Hiring Radar Digest: 1 new job since 2026-04-03T18:00:00Z",
            None,
        )
    ]
    assert checkpoint_updates == [
        (
            cli.DIGEST_EMAIL_CHECKPOINT_KEY,
            "2026-04-04T00:00:00Z",
            "2026-04-04T00:00:00Z",
        )
    ]


def test_crawl_and_notify_uses_existing_checkpoint(monkeypatch) -> None:
    checkpoint_updates: list[tuple[str, str, str]] = []
    notification_runs: list[tuple[str, str, str | None]] = []
    notification_finishes: list[tuple[int, str, int, int, str | None, str | None]] = []

    class FakeRepository:
        def list_digest_enabled_subscribers(self):
            return [
                Subscriber(
                    id=1,
                    email="alice@example.com",
                    full_name="Alice Example",
                    is_active=True,
                    digest_enabled=True,
                    created_at="2026-04-04T10:00:00Z",
                    updated_at="2026-04-04T10:00:00Z",
                )
            ]

        def get_notification_checkpoint(self, checkpoint_key: str):
            assert checkpoint_key == cli.DIGEST_EMAIL_CHECKPOINT_KEY
            return NotificationCheckpoint(
                checkpoint_key=checkpoint_key,
                last_processed_at="2026-04-03T21:00:00Z",
                updated_at="2026-04-03T21:00:00Z",
            )

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
            return 202

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
    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "run_multi_source_crawl",
        lambda source_configs, repository: [
            CrawlSourceResult(
                source_name="threee-lever",
                source_type="lever",
                started_at="2026-04-04T00:00:00Z",
                finished_at="2026-04-04T00:01:00Z",
                success=True,
                total_parsed_jobs=14,
                new_jobs=14,
                updated_jobs=0,
                deactivated_jobs=0,
            )
        ],
    )

    captured_since: dict[str, str] = {}

    def fake_build_digest(repository, since, generated_at):
        captured_since["since"] = since
        return make_digest(total_new_jobs=1, since=since)

    monkeypatch.setattr(cli, "build_digest", fake_build_digest)
    monkeypatch.setattr(
        cli,
        "load_smtp_settings",
        lambda env_path: make_settings(default_to=None),
    )

    captured_payloads: list[object] = []

    def fake_send_email_via_smtp(*, settings, payload, timeout_seconds: float = 20.0) -> None:
        captured_payloads.append(payload)

    monkeypatch.setattr(cli, "send_email_via_smtp", fake_send_email_via_smtp)

    result = runner.invoke(
        cli.app,
        [
            "crawl-and-notify",
            "--window-hours",
            "6",
        ],
    )

    assert result.exit_code == 0
    assert captured_since["since"] == "2026-04-03T21:00:00Z"
    assert len(captured_payloads) == 1
    assert captured_payloads[0].to == "alice@example.com"
    assert notification_runs == [
        (
            cli.NOTIFICATION_TYPE_DIGEST_EMAIL,
            "2026-04-04T00:00:00Z",
            "2026-04-03T21:00:00Z",
        )
    ]
    assert notification_finishes == [
        (
            202,
            "sent",
            1,
            1,
            "Hiring Radar Digest: 1 new job since 2026-04-03T21:00:00Z",
            None,
        )
    ]
    assert checkpoint_updates == [
        (
            cli.DIGEST_EMAIL_CHECKPOINT_KEY,
            "2026-04-04T00:00:00Z",
            "2026-04-04T00:00:00Z",
        )
    ]


def test_crawl_and_notify_updates_checkpoint_when_empty_digest_is_skipped(monkeypatch) -> None:
    checkpoint_updates: list[tuple[str, str, str]] = []
    notification_runs: list[tuple[str, str, str | None]] = []
    notification_finishes: list[tuple[int, str, int, int, str | None, str | None]] = []

    class FakeRepository:
        def get_notification_checkpoint(self, checkpoint_key: str):
            return None

        def upsert_notification_checkpoint(
            self,
            *,
            checkpoint_key: str,
            last_processed_at: str,
            updated_at: str,
        ):
            checkpoint_updates.append((checkpoint_key, last_processed_at, updated_at))

        def list_digest_enabled_subscribers(self):
            raise AssertionError("subscriber list should not be used when empty digest is skipped")

        def start_notification_run(
            self, *, notification_type: str, started_at: str, since: str | None
        ):
            notification_runs.append((notification_type, started_at, since))
            return 203

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
    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "run_multi_source_crawl",
        lambda source_configs, repository: [
            CrawlSourceResult(
                source_name="threee-lever",
                source_type="lever",
                started_at="2026-04-04T00:00:00Z",
                finished_at="2026-04-04T00:01:00Z",
                success=True,
                total_parsed_jobs=14,
                new_jobs=0,
                updated_jobs=14,
                deactivated_jobs=0,
            )
        ],
    )
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(
            total_new_jobs=0,
            since=since,
        ),
    )

    def fail_load_smtp_settings(env_path):
        raise AssertionError("SMTP settings should not be loaded when empty digest is skipped")

    monkeypatch.setattr(cli, "load_smtp_settings", fail_load_smtp_settings)

    result = runner.invoke(
        cli.app,
        [
            "crawl-and-notify",
            "--window-hours",
            "6",
        ],
    )

    assert result.exit_code == 0
    assert "Digest email skipped" in result.output
    assert "reason=no new jobs in this window" in result.output
    assert notification_runs == [
        (
            cli.NOTIFICATION_TYPE_DIGEST_EMAIL,
            "2026-04-04T00:00:00Z",
            "2026-04-03T18:00:00Z",
        )
    ]
    assert notification_finishes == [
        (
            203,
            "skipped",
            0,
            0,
            None,
            "no new jobs in this window",
        )
    ]
    assert checkpoint_updates == [
        (
            cli.DIGEST_EMAIL_CHECKPOINT_KEY,
            "2026-04-04T00:00:00Z",
            "2026-04-04T00:00:00Z",
        )
    ]


def test_crawl_and_notify_skips_digest_when_all_crawls_fail(monkeypatch) -> None:
    notification_runs: list[tuple[str, str, str | None]] = []
    notification_finishes: list[tuple[int, str, int, int, str | None, str | None]] = []

    class FakeRepository:
        def get_notification_checkpoint(self, checkpoint_key: str):
            raise AssertionError("checkpoint should not be read when all crawls fail")

        def upsert_notification_checkpoint(self, **kwargs):
            raise AssertionError("checkpoint should not be updated when all crawls fail")

        def list_digest_enabled_subscribers(self):
            raise AssertionError("subscriber list should not be used when all crawls fail")

        def start_notification_run(
            self, *, notification_type: str, started_at: str, since: str | None
        ):
            notification_runs.append((notification_type, started_at, since))
            return 204

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
    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "run_multi_source_crawl",
        lambda source_configs, repository: [
            CrawlSourceResult(
                source_name="threee-lever",
                source_type="lever",
                started_at="2026-04-04T00:00:00Z",
                finished_at="2026-04-04T00:01:00Z",
                success=False,
                total_parsed_jobs=0,
                new_jobs=0,
                updated_jobs=0,
                deactivated_jobs=0,
                error_message="network error",
            )
        ],
    )

    def fail_build_digest(*args, **kwargs):
        raise AssertionError("build_digest should not be called when all crawls fail")

    monkeypatch.setattr(cli, "build_digest", fail_build_digest)

    result = runner.invoke(
        cli.app,
        [
            "crawl-and-notify",
            "--window-hours",
            "6",
        ],
    )

    assert result.exit_code == 1
    assert "Digest email skipped" in result.output
    assert "reason=no successful crawl sources" in result.output
    assert notification_runs == [
        (
            cli.NOTIFICATION_TYPE_DIGEST_EMAIL,
            "2026-04-04T00:00:00Z",
            None,
        )
    ]
    assert notification_finishes == [
        (
            204,
            "skipped",
            0,
            0,
            None,
            "no successful crawl sources",
        )
    ]


def test_crawl_and_notify_sends_digest_on_partial_success_and_returns_nonzero(monkeypatch) -> None:
    checkpoint_updates: list[tuple[str, str, str]] = []
    notification_runs: list[tuple[str, str, str | None]] = []
    notification_finishes: list[tuple[int, str, int, int, str | None, str | None]] = []

    class FakeRepository:
        def list_digest_enabled_subscribers(self):
            return [
                Subscriber(
                    id=1,
                    email="alice@example.com",
                    full_name="Alice Example",
                    is_active=True,
                    digest_enabled=True,
                    created_at="2026-04-04T10:00:00Z",
                    updated_at="2026-04-04T10:00:00Z",
                ),
                Subscriber(
                    id=2,
                    email="bob@example.com",
                    full_name="Bob Example",
                    is_active=True,
                    digest_enabled=True,
                    created_at="2026-04-04T10:00:00Z",
                    updated_at="2026-04-04T10:00:00Z",
                ),
            ]

        def get_notification_checkpoint(self, checkpoint_key: str):
            return NotificationCheckpoint(
                checkpoint_key=checkpoint_key,
                last_processed_at="2026-04-03T21:00:00Z",
                updated_at="2026-04-03T21:00:00Z",
            )

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
            return 205

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
    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "run_multi_source_crawl",
        lambda source_configs, repository: [
            CrawlSourceResult(
                source_name="threee-lever",
                source_type="lever",
                started_at="2026-04-04T00:00:00Z",
                finished_at="2026-04-04T00:01:00Z",
                success=True,
                total_parsed_jobs=14,
                new_jobs=14,
                updated_jobs=0,
                deactivated_jobs=0,
            ),
            CrawlSourceResult(
                source_name="corelight-greenhouse",
                source_type="greenhouse",
                started_at="2026-04-04T00:00:00Z",
                finished_at="2026-04-04T00:01:00Z",
                success=False,
                total_parsed_jobs=0,
                new_jobs=0,
                updated_jobs=0,
                deactivated_jobs=0,
                error_message="429",
            ),
        ],
    )
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(
            total_new_jobs=1,
            since=since,
        ),
    )
    monkeypatch.setattr(
        cli,
        "load_smtp_settings",
        lambda env_path: make_settings(default_to=None),
    )

    captured_payloads: list[object] = []

    def fake_send_email_via_smtp(*, settings, payload, timeout_seconds: float = 20.0) -> None:
        captured_payloads.append(payload)

    monkeypatch.setattr(cli, "send_email_via_smtp", fake_send_email_via_smtp)

    result = runner.invoke(
        cli.app,
        [
            "crawl-and-notify",
            "--window-hours",
            "6",
        ],
    )

    assert result.exit_code == 1
    assert "Digest emails sent" in result.output
    assert "recipient_count=2" in result.output
    assert len(captured_payloads) == 2
    assert [payload.to for payload in captured_payloads] == [
        "alice@example.com",
        "bob@example.com",
    ]
    assert notification_runs == [
        (
            cli.NOTIFICATION_TYPE_DIGEST_EMAIL,
            "2026-04-04T00:00:00Z",
            "2026-04-03T21:00:00Z",
        )
    ]
    assert notification_finishes == [
        (
            205,
            "sent",
            2,
            1,
            "Hiring Radar Digest: 1 new job since 2026-04-03T21:00:00Z",
            None,
        )
    ]
    assert checkpoint_updates == [
        (
            cli.DIGEST_EMAIL_CHECKPOINT_KEY,
            "2026-04-04T00:00:00Z",
            "2026-04-04T00:00:00Z",
        )
    ]
