from __future__ import annotations

from typer.testing import CliRunner

from hiring_radar import cli
from hiring_radar.email_config import SMTPSettings
from hiring_radar.models import Subscriber
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


def make_digest(*, total_new_jobs: int) -> DigestResult:
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
        since="2026-04-03T15:00:00Z",
        total_new_jobs=total_new_jobs,
        sections=sections,
    )


def test_send_digest_sends_email_when_explicit_recipient_is_provided(monkeypatch) -> None:
    class FakeRepository:
        def list_digest_enabled_subscribers(self):
            raise AssertionError("subscriber list should not be used when --to is provided")

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "load_smtp_settings",
        lambda env_path: make_settings(default_to="default@example.com"),
    )
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(total_new_jobs=1),
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
        ],
    )

    assert result.exit_code == 0
    assert "Digest emails sent" in result.output
    assert "recipient_count=1" in result.output
    assert "new_jobs=1" in result.output

    assert len(captured_payloads) == 1
    payload = captured_payloads[0]
    assert payload.to == "recipient@example.com"
    assert payload.subject == "Hiring Radar Digest: 1 new job since 2026-04-03T15:00:00Z"
    assert "Growth Marketing Manager" in payload.body_text


def test_send_digest_uses_digest_enabled_subscribers_when_to_is_omitted(monkeypatch) -> None:
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

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "load_smtp_settings",
        lambda env_path: make_settings(default_to="default@example.com"),
    )
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(total_new_jobs=1),
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
        ],
    )

    assert result.exit_code == 0
    assert "Digest emails sent" in result.output
    assert "recipient_count=2" in result.output
    assert len(captured_payloads) == 2
    assert [payload.to for payload in captured_payloads] == [
        "alice@example.com",
        "bob@example.com",
    ]


def test_send_digest_falls_back_to_default_recipient_when_no_subscribers(monkeypatch) -> None:
    class FakeRepository:
        def list_digest_enabled_subscribers(self):
            return []

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "load_smtp_settings",
        lambda env_path: make_settings(default_to="default@example.com"),
    )
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(total_new_jobs=1),
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
        ],
    )

    assert result.exit_code == 0
    assert "recipient_count=1" in result.output
    assert len(captured_payloads) == 1
    assert captured_payloads[0].to == "default@example.com"


def test_send_digest_skips_empty_digest_when_send_empty_is_false(monkeypatch) -> None:
    class FakeRepository:
        def list_digest_enabled_subscribers(self):
            raise AssertionError("subscriber list should not be queried for skipped empty digest")

    monkeypatch.setattr(cli, "initialize_database", lambda _: object())
    monkeypatch.setattr(cli, "close_connection", lambda connection: None)
    monkeypatch.setattr(cli, "HiringRadarRepository", lambda connection: FakeRepository())
    monkeypatch.setattr(cli, "_utc_now_iso", lambda: "2026-04-04T00:00:00Z")
    monkeypatch.setattr(
        cli,
        "build_digest",
        lambda repository, since, generated_at: make_digest(total_new_jobs=0),
    )

    def fail_load_smtp_settings(env_path):
        raise AssertionError("SMTP settings should not be loaded for skipped empty digest")

    monkeypatch.setattr(cli, "load_smtp_settings", fail_load_smtp_settings)

    result = runner.invoke(
        cli.app,
        [
            "send-digest",
            "--since",
            "2026-04-03T15:00:00Z",
        ],
    )

    assert result.exit_code == 0
    assert "Digest email skipped" in result.output
    assert "reason=no new jobs in this window" in result.output