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
    body_html: str | None = None


def build_email_message(*, payload: EmailMessagePayload, settings: SMTPSettings) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = payload.to
    message["Subject"] = payload.subject
    message.set_content(payload.body_text)
    if payload.body_html:
        message.add_alternative(payload.body_html, subtype="html")
    return message


def _decode_smtp_error(value: bytes | str) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)


def _close_smtp_server(server: smtplib.SMTP | None) -> Exception | None:
    if server is None:
        return None
    try:
        server.quit()
    except (OSError, TimeoutError, smtplib.SMTPException) as exc:
        try:
            server.close()
        except Exception:
            pass
        return exc
    return None


def send_email_via_smtp(
    *,
    settings: SMTPSettings,
    payload: EmailMessagePayload,
    timeout_seconds: float = 20.0,
) -> None:
    message = build_email_message(payload=payload, settings=settings)

    server: smtplib.SMTP | None = None
    cleanup_error: Exception | None = None
    phase = "connect"
    message_sent = False

    try:
        server = smtplib.SMTP(
            host=settings.host,
            port=settings.port,
            timeout=timeout_seconds,
        )

        phase = "ehlo"
        server.ehlo()

        if settings.use_tls:
            phase = "starttls"
            server.starttls()
            phase = "ehlo_after_starttls"
            server.ehlo()

        phase = "login"
        server.login(settings.username, settings.password)

        phase = "send_message"
        refused_recipients = server.send_message(message)
        if refused_recipients:
            refused_summary = ", ".join(sorted(refused_recipients))
            raise EmailDeliveryError(f"SMTP refused recipient(s): {refused_summary}")

        message_sent = True

    except EmailDeliveryError:
        raise
    except smtplib.SMTPAuthenticationError as exc:
        raise EmailDeliveryError(
            "SMTP authentication failed "
            f"for {settings.username}: code={exc.smtp_code} "
            f"message={_decode_smtp_error(exc.smtp_error)}"
        ) from exc
    except smtplib.SMTPConnectError as exc:
        raise EmailDeliveryError(
            "SMTP connection failed "
            f"to {settings.host}:{settings.port}: code={exc.smtp_code} "
            f"message={_decode_smtp_error(exc.smtp_error)}"
        ) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        refused_summary = ", ".join(sorted(exc.recipients))
        raise EmailDeliveryError(f"SMTP refused recipient(s): {refused_summary}") from exc
    except smtplib.SMTPDataError as exc:
        raise EmailDeliveryError(
            "SMTP rejected message data: "
            f"code={exc.smtp_code} message={_decode_smtp_error(exc.smtp_error)}"
        ) from exc
    except (OSError, TimeoutError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError(f"SMTP {phase} failed: {exc}") from exc
    finally:
        cleanup_error = _close_smtp_server(server)

    if cleanup_error is not None and not message_sent:
        raise EmailDeliveryError(
            f"SMTP cleanup failed before delivery completed: {cleanup_error}"
        ) from cleanup_error
