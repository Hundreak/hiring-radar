from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class EmailConfigError(ValueError):
    """Raised when SMTP/email configuration is missing or invalid."""


@dataclass(slots=True, frozen=True)
class SMTPSettings:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    email_from: str
    default_to: str | None = None


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise EmailConfigError(
        f"Invalid boolean value for SMTP config: {value!r}. "
        "Use one of: true/false, yes/no, 1/0."
    )


def load_env_file(path: str | Path = ".env") -> None:
    """
    Load key=value pairs from a .env-style file into os.environ.

    Notes:
    - Existing environment variables are preserved.
    - Empty lines and comments are ignored.
    - Optional `export KEY=value` lines are supported.
    - Missing .env file is not treated as an error.
    """
    env_path = Path(path)

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def load_smtp_settings(env_path: str | Path = ".env") -> SMTPSettings:
    """
    Load SMTP settings from environment variables, optionally hydrating them
    from a local .env file first.
    """
    load_env_file(env_path)

    required_keys = (
        "HIRING_RADAR_SMTP_HOST",
        "HIRING_RADAR_SMTP_PORT",
        "HIRING_RADAR_SMTP_USERNAME",
        "HIRING_RADAR_SMTP_PASSWORD",
        "HIRING_RADAR_SMTP_USE_TLS",
        "HIRING_RADAR_EMAIL_FROM",
    )

    missing = [key for key in required_keys if not os.environ.get(key)]
    if missing:
        joined = ", ".join(missing)
        raise EmailConfigError(f"Missing required SMTP settings: {joined}")

    raw_port = os.environ["HIRING_RADAR_SMTP_PORT"]
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise EmailConfigError(
            f"HIRING_RADAR_SMTP_PORT must be an integer, got: {raw_port!r}"
        ) from exc

    use_tls = _parse_bool(os.environ["HIRING_RADAR_SMTP_USE_TLS"])

    default_to = os.environ.get("HIRING_RADAR_EMAIL_TO_DEFAULT") or None

    return SMTPSettings(
        host=os.environ["HIRING_RADAR_SMTP_HOST"],
        port=port,
        username=os.environ["HIRING_RADAR_SMTP_USERNAME"],
        password=os.environ["HIRING_RADAR_SMTP_PASSWORD"],
        use_tls=use_tls,
        email_from=os.environ["HIRING_RADAR_EMAIL_FROM"],
        default_to=default_to,
    )