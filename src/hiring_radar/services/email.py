from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from hiring_radar.email_config import SMTPSettings


class EmailDeliveryError(RuntimeError):
    """Raised when an email cannot be delivered via SMTP."""


@dataclass(slots=True, frozen=True)
class EmailMessagePayload:
    to: str
    subject: str
    body_text: str


def build_email_message(
    *,
    payload: EmailMessagePayload,
    settings: SMTPSettings,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = payload.to
    message["Subject"] = payload.subject
    message.set_content(payload.body_text)

    return message


def send_email_via_smtp(
    *,
    settings: SMTPSettings,
    payload: EmailMessagePayload,
    timeout_seconds: float = 20.0,
) -> None:
    """
    Send a plain-text email using SMTP.

    Notes:
    - Uses SMTP with optional STARTTLS.
    - Authenticates using the configured username/password.
    - Raises EmailDeliveryError on connection, authentication, or send failures.
    """
    message = build_email_message(
        payload=payload,
        settings=settings,
    )

    try:
        with smtplib.SMTP(
            host=settings.host,
            port=settings.port,
            timeout=timeout_seconds,
        ) as server:
            server.ehlo()

            if settings.use_tls:
                server.starttls()
                server.ehlo()

            server.login(settings.username, settings.password)
            server.send_message(message)

    except (
        OSError,
        TimeoutError,
        smtplib.SMTPException,
    ) as exc:
        raise EmailDeliveryError(f"Failed to send email via SMTP: {exc}") from exc