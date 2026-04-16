from __future__ import annotations

import smtplib
from email.message import EmailMessage

import pytest

from hiring_radar.email_config import SMTPSettings
from hiring_radar.services.email import (
    EmailDeliveryError,
    EmailMessagePayload,
    build_email_message,
    send_email_via_smtp,
)


class FakeSMTP:
    instances: list[FakeSMTP] = []

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.did_ehlo = 0
        self.did_starttls = False
        self.logged_in_with: tuple[str, str] | None = None
        self.sent_messages: list[EmailMessage] = []
        self.quit_called = False
        self.close_called = False
        FakeSMTP.instances.append(self)

    def ehlo(self) -> None:
        self.did_ehlo += 1

    def starttls(self) -> None:
        self.did_starttls = True

    def login(self, username: str, password: str) -> None:
        self.logged_in_with = (username, password)

    def send_message(self, message: EmailMessage) -> dict[str, tuple[int, bytes]]:
        self.sent_messages.append(message)
        return {}

    def quit(self) -> None:
        self.quit_called = True

    def close(self) -> None:
        self.close_called = True


class FailingAuthSMTP(FakeSMTP):
    def login(self, username: str, password: str) -> None:
        raise smtplib.SMTPAuthenticationError(535, b"Authentication failed")


class CleanupErrorSMTP(FakeSMTP):
    def quit(self) -> None:
        self.quit_called = True
        raise smtplib.SMTPResponseException(250, b"2.0.0 OK queued as abc123")


class RefusingRecipientSMTP(FakeSMTP):
    def send_message(self, message: EmailMessage) -> dict[str, tuple[int, bytes]]:
        self.sent_messages.append(message)
        return {
            "recipient@example.com": (550, b"User unknown"),
        }


@pytest.fixture(autouse=True)
def reset_fake_smtp_instances() -> None:
    FakeSMTP.instances.clear()


def make_settings(*, use_tls: bool) -> SMTPSettings:
    return SMTPSettings(
        host="smtp.example.com",
        port=587,
        username="smtp-user",
        password="smtp-pass",
        use_tls=use_tls,
        email_from="alerts@example.com",
        default_to="recipient@example.com",
    )


def test_build_email_message_creates_expected_plain_text_message() -> None:
    payload = EmailMessagePayload(
        to="recipient@example.com",
        subject="Hiring Radar Digest: 3 new jobs",
        body_text="Digest body here",
    )
    settings = make_settings(use_tls=True)

    message = build_email_message(
        payload=payload,
        settings=settings,
    )

    assert message["From"] == "alerts@example.com"
    assert message["To"] == "recipient@example.com"
    assert message["Subject"] == "Hiring Radar Digest: 3 new jobs"
    assert "Digest body here" in message.get_content()


def test_send_email_via_smtp_uses_starttls_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    payload = EmailMessagePayload(
        to="recipient@example.com",
        subject="Hiring Radar Digest: 3 new jobs",
        body_text="Digest body here",
    )
    settings = make_settings(use_tls=True)

    send_email_via_smtp(
        settings=settings,
        payload=payload,
        timeout_seconds=10.0,
    )

    assert len(FakeSMTP.instances) == 1
    smtp_client = FakeSMTP.instances[0]

    assert smtp_client.host == "smtp.example.com"
    assert smtp_client.port == 587
    assert smtp_client.timeout == 10.0
    assert smtp_client.did_ehlo == 2
    assert smtp_client.did_starttls is True
    assert smtp_client.logged_in_with == ("smtp-user", "smtp-pass")
    assert len(smtp_client.sent_messages) == 1
    assert smtp_client.sent_messages[0]["To"] == "recipient@example.com"
    assert smtp_client.quit_called is True


def test_send_email_via_smtp_skips_starttls_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    payload = EmailMessagePayload(
        to="recipient@example.com",
        subject="Hiring Radar Digest: 1 new job",
        body_text="Digest body here",
    )
    settings = make_settings(use_tls=False)

    send_email_via_smtp(
        settings=settings,
        payload=payload,
    )

    assert len(FakeSMTP.instances) == 1
    smtp_client = FakeSMTP.instances[0]

    assert smtp_client.did_ehlo == 1
    assert smtp_client.did_starttls is False
    assert smtp_client.logged_in_with == ("smtp-user", "smtp-pass")
    assert len(smtp_client.sent_messages) == 1
    assert smtp_client.quit_called is True


def test_send_email_via_smtp_wraps_authentication_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smtplib, "SMTP", FailingAuthSMTP)

    payload = EmailMessagePayload(
        to="recipient@example.com",
        subject="Hiring Radar Digest: 3 new jobs",
        body_text="Digest body here",
    )
    settings = make_settings(use_tls=True)

    with pytest.raises(EmailDeliveryError) as exc_info:
        send_email_via_smtp(
            settings=settings,
            payload=payload,
        )

    assert "SMTP authentication failed" in str(exc_info.value)


def test_send_email_via_smtp_raises_for_refused_recipients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smtplib, "SMTP", RefusingRecipientSMTP)

    payload = EmailMessagePayload(
        to="recipient@example.com",
        subject="Hiring Radar Digest: 2 new jobs",
        body_text="Digest body here",
    )
    settings = make_settings(use_tls=True)

    with pytest.raises(EmailDeliveryError) as exc_info:
        send_email_via_smtp(
            settings=settings,
            payload=payload,
        )

    assert "SMTP refused recipient(s): recipient@example.com" in str(exc_info.value)


def test_send_email_via_smtp_ignores_cleanup_error_after_successful_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smtplib, "SMTP", CleanupErrorSMTP)

    payload = EmailMessagePayload(
        to="recipient@example.com",
        subject="Hiring Radar Digest: 1 new job",
        body_text="Digest body here",
    )
    settings = make_settings(use_tls=True)

    send_email_via_smtp(
        settings=settings,
        payload=payload,
    )

    assert len(FakeSMTP.instances) == 1
    smtp_client = FakeSMTP.instances[0]
    assert len(smtp_client.sent_messages) == 1
    assert smtp_client.quit_called is True
    assert smtp_client.close_called is True
