from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_release_environment.py"
SPEC = importlib.util.spec_from_file_location("check_release_environment", SCRIPT_PATH)
assert SPEC is not None
release_env = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = release_env
SPEC.loader.exec_module(release_env)


def _valid_prod_config() -> dict[str, str]:
    return {
        "HIRING_RADAR_ENV": "production",
        "HIRING_RADAR_AUTH_SECRET": "rA9vQ7mX2pL8nT4yB6cD1fG3hJ5kZ0wS9eU2iO4p",
        "HIRING_RADAR_ADMIN_SESSION_SECRET": "jK8sD2fH5qL9wP3zX6cV1bN4mA7tR0yE8uI2oG5h",
        "HIRING_RADAR_EMPLOYER_SESSION_SECRET": "pQ2wE4rT6yU8iO0aS3dF5gH7jK9lZ1xC2vB4nM6q",
        "HIRING_RADAR_ADMIN_EMAIL": "security@hiring-radar.test",
        "HIRING_RADAR_ADMIN_PASSWORD": "RotateThisAdminPassphrase2026!",
        "HIRING_RADAR_SESSION_COOKIE_SECURE": "true",
        "HIRING_RADAR_ADMIN_SESSION_COOKIE_SECURE": "true",
        "HIRING_RADAR_EMPLOYER_SESSION_COOKIE_SECURE": "true",
        "HIRING_RADAR_CSRF_COOKIE_SECURE": "true",
        "HIRING_RADAR_CSRF_ENABLED": "true",
        "HIRING_RADAR_RATE_LIMIT_ENABLED": "true",
        "HIRING_RADAR_OBSERVABILITY_ENABLED": "true",
        "HIRING_RADAR_EMPLOYER_DEMO_MODE": "false",
        "HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH": "false",
        "HIRING_RADAR_APP_BASE_URL": "https://app.hiring-radar.test",
        "BACKEND_URL": "https://api.hiring-radar.test",
        "GOOGLE_OAUTH_REDIRECT_URI": "https://api.hiring-radar.test/api/auth/google/callback",
        "HIRING_RADAR_DB_PATH": "/var/lib/hiring-radar/hiring_radar.sqlite3",
        "HIRING_RADAR_UPLOAD_DIR": "/var/lib/hiring-radar/uploads",
        "HIRING_RADAR_SMTP_HOST": "smtp.hiring-radar.test",
        "HIRING_RADAR_SMTP_PASSWORD": "SmtpPassphrase2026!rotated",
        "HIRING_RADAR_EMAIL_FROM": "Hiring Radar <noreply@hiring-radar.test>",
        "AI_ENABLED": "false",
    }


def test_release_environment_accepts_hardened_production_config() -> None:
    report = release_env.evaluate_environment(_valid_prod_config(), strict_production=True)

    assert report.ok
    assert not report.failures


def test_release_environment_rejects_placeholder_secrets() -> None:
    config = _valid_prod_config()
    config["HIRING_RADAR_AUTH_SECRET"] = "replace-with-a-long-random-secret"

    report = release_env.evaluate_environment(config, strict_production=True)

    assert not report.ok
    assert any("HIRING_RADAR_AUTH_SECRET" in item.message for item in report.failures)


def test_release_environment_rejects_insecure_production_flags() -> None:
    config = _valid_prod_config()
    config["HIRING_RADAR_CSRF_ENABLED"] = "false"
    config["HIRING_RADAR_EMPLOYER_DEMO_MODE"] = "true"
    config["HIRING_RADAR_APP_BASE_URL"] = "http://localhost:3000"

    report = release_env.evaluate_environment(config, strict_production=True)

    assert not report.ok
    failure_text = "\n".join(item.message for item in report.failures)
    assert "HIRING_RADAR_CSRF_ENABLED" in failure_text
    assert "HIRING_RADAR_EMPLOYER_DEMO_MODE" in failure_text
    assert "HIRING_RADAR_APP_BASE_URL" in failure_text


def test_env_file_parser_strips_quotes_and_inline_comments(tmp_path: Path) -> None:
    env_file = tmp_path / "release.env"
    env_file.write_text(
        """
        # comment
        export HIRING_RADAR_ENV='production'
        HIRING_RADAR_APP_BASE_URL="https://app.example.test" # inline comment
        """,
        encoding="utf-8",
    )

    values = release_env.parse_env_file(env_file)

    assert values["HIRING_RADAR_ENV"] == "production"
    assert values["HIRING_RADAR_APP_BASE_URL"] == "https://app.example.test"
