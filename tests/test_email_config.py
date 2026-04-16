from __future__ import annotations

import os
from pathlib import Path

import pytest

from hiring_radar.email_config import (
    EmailConfigError,
    load_env_file,
    load_smtp_settings,
)

SMTP_KEYS = (
    "HIRING_RADAR_SMTP_HOST",
    "HIRING_RADAR_SMTP_PORT",
    "HIRING_RADAR_SMTP_USERNAME",
    "HIRING_RADAR_SMTP_PASSWORD",
    "HIRING_RADAR_SMTP_USE_TLS",
    "HIRING_RADAR_EMAIL_FROM",
    "HIRING_RADAR_EMAIL_TO_DEFAULT",
)


@pytest.fixture(autouse=True)
def clear_smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in SMTP_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_load_env_file_reads_key_value_pairs_without_overwriting_existing_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "HIRING_RADAR_SMTP_HOST=smtp.example.com",
                "HIRING_RADAR_SMTP_PORT=587",
                'HIRING_RADAR_EMAIL_FROM="alerts@example.com"',
                "export HIRING_RADAR_SMTP_USE_TLS=true",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("HIRING_RADAR_SMTP_PORT", "2525")

    load_env_file(env_file)

    assert os.environ["HIRING_RADAR_SMTP_HOST"] == "smtp.example.com"
    assert os.environ["HIRING_RADAR_SMTP_PORT"] == "2525"
    assert os.environ["HIRING_RADAR_EMAIL_FROM"] == "alerts@example.com"
    assert os.environ["HIRING_RADAR_SMTP_USE_TLS"] == "true"


def test_load_smtp_settings_reads_and_parses_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "HIRING_RADAR_SMTP_HOST=smtp.example.com",
                "HIRING_RADAR_SMTP_PORT=587",
                "HIRING_RADAR_SMTP_USERNAME=test-user",
                "HIRING_RADAR_SMTP_PASSWORD=super-secret",
                "HIRING_RADAR_SMTP_USE_TLS=true",
                "HIRING_RADAR_EMAIL_FROM=alerts@example.com",
                "HIRING_RADAR_EMAIL_TO_DEFAULT=recipient@example.com",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_smtp_settings(env_file)

    assert settings.host == "smtp.example.com"
    assert settings.port == 587
    assert settings.username == "test-user"
    assert settings.password == "super-secret"
    assert settings.use_tls is True
    assert settings.email_from == "alerts@example.com"
    assert settings.default_to == "recipient@example.com"


def test_load_smtp_settings_raises_for_missing_required_settings(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "HIRING_RADAR_SMTP_HOST=smtp.example.com",
                "HIRING_RADAR_SMTP_PORT=587",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(EmailConfigError) as exc_info:
        load_smtp_settings(env_file)

    assert "Missing required SMTP settings" in str(exc_info.value)


def test_load_smtp_settings_raises_for_invalid_port(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "HIRING_RADAR_SMTP_HOST=smtp.example.com",
                "HIRING_RADAR_SMTP_PORT=not-a-number",
                "HIRING_RADAR_SMTP_USERNAME=test-user",
                "HIRING_RADAR_SMTP_PASSWORD=super-secret",
                "HIRING_RADAR_SMTP_USE_TLS=true",
                "HIRING_RADAR_EMAIL_FROM=alerts@example.com",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(EmailConfigError) as exc_info:
        load_smtp_settings(env_file)

    assert "HIRING_RADAR_SMTP_PORT must be an integer" in str(exc_info.value)


def test_load_smtp_settings_raises_for_invalid_boolean(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "HIRING_RADAR_SMTP_HOST=smtp.example.com",
                "HIRING_RADAR_SMTP_PORT=587",
                "HIRING_RADAR_SMTP_USERNAME=test-user",
                "HIRING_RADAR_SMTP_PASSWORD=super-secret",
                "HIRING_RADAR_SMTP_USE_TLS=maybe",
                "HIRING_RADAR_EMAIL_FROM=alerts@example.com",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(EmailConfigError) as exc_info:
        load_smtp_settings(env_file)

    assert "Invalid boolean value for SMTP config" in str(exc_info.value)
