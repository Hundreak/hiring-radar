from __future__ import annotations

import pytest

from hiring_radar.api.employer_runtime import load_employer_runtime_settings
from hiring_radar.api.routers.employer_dashboard import _mock_employer_from_token
from hiring_radar.api.security import AdminAuthError, load_admin_auth_settings
from hiring_radar.services.employer_auth import EmployerAuthError, load_employer_auth_settings
from hiring_radar.services.user_auth import UserAuthError, load_user_auth_settings

_SECRET = "x" * 48


def _clear_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "HIRING_RADAR_AUTH_SECRET",
        "HIRING_RADAR_SECRET_KEY",
        "HIRING_RADAR_ADMIN_EMAIL",
        "HIRING_RADAR_ADMIN_PASSWORD",
        "HIRING_RADAR_ADMIN_SESSION_SECRET",
        "HIRING_RADAR_EMPLOYER_SESSION_SECRET",
        "HIRING_RADAR_USER_SESSION_SECRET",
        "HIRING_RADAR_SESSION_COOKIE_SECURE",
        "HIRING_RADAR_ADMIN_SESSION_COOKIE_SECURE",
        "HIRING_RADAR_EMPLOYER_SESSION_COOKIE_SECURE",
        "HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH",
        "HIRING_RADAR_EMPLOYER_DEMO_MODE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_user_auth_secret_is_required_in_production(monkeypatch, tmp_path) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")

    with pytest.raises(UserAuthError, match="HIRING_RADAR_AUTH_SECRET"):
        load_user_auth_settings(tmp_path / ".env")


def test_user_session_cookie_defaults_secure_in_production(monkeypatch, tmp_path) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")
    monkeypatch.setenv("HIRING_RADAR_AUTH_SECRET", _SECRET)

    settings = load_user_auth_settings(tmp_path / ".env")

    assert settings.secure_cookie is True
    assert settings.cookie_samesite == "lax"


def test_admin_session_secret_must_not_be_weak_in_production(monkeypatch, tmp_path) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")
    monkeypatch.setenv("HIRING_RADAR_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("HIRING_RADAR_ADMIN_PASSWORD", "Admin12345!")
    monkeypatch.setenv("HIRING_RADAR_ADMIN_SESSION_SECRET", "short")

    with pytest.raises(AdminAuthError, match="at least 32"):
        load_admin_auth_settings(tmp_path / ".env")


def test_admin_session_cookie_defaults_secure_in_production(monkeypatch, tmp_path) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")
    monkeypatch.setenv("HIRING_RADAR_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("HIRING_RADAR_ADMIN_PASSWORD", "Admin12345!")
    monkeypatch.setenv("HIRING_RADAR_ADMIN_SESSION_SECRET", _SECRET)

    settings = load_admin_auth_settings(tmp_path / ".env")

    assert settings.secure_cookie is True
    assert settings.cookie_samesite == "lax"


def test_employer_session_secret_is_required_in_production(monkeypatch) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")

    with pytest.raises(EmployerAuthError, match="HIRING_RADAR_EMPLOYER_SESSION_SECRET"):
        load_employer_auth_settings()


def test_employer_mock_token_is_disabled_by_default_in_production(monkeypatch) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")

    assert _mock_employer_from_token("mock_token_demo") is None


def test_employer_mock_token_cannot_be_enabled_in_production(monkeypatch) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "production")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_DEMO_MODE", "true")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH", "true")

    settings = load_employer_runtime_settings()

    assert settings.demo_mode_enabled is False
    assert settings.mock_auth_enabled is False
    assert _mock_employer_from_token("mock_token_demo") is None


def test_employer_mock_token_can_be_enabled_for_local_demo(monkeypatch) -> None:
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("HIRING_RADAR_ENV", "development")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_DEMO_MODE", "true")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH", "true")

    user = _mock_employer_from_token("mock_token_demo")

    assert user is not None
    assert user["auth_mode"] == "mock"
