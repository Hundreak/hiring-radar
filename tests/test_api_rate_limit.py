from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_user_auth_settings
from hiring_radar.api.rate_limit import enforce_rate_limit, reset_rate_limiter_for_tests
from hiring_radar.services.user_auth import UserAuthSettings


def _make_request(ip: str = "127.0.0.1", headers: dict[str, str] | None = None):
    return SimpleNamespace(
        headers=headers or {},
        client=SimpleNamespace(host=ip),
    )


def _make_user_auth_settings() -> UserAuthSettings:
    return UserAuthSettings(
        secret_key="rate-limit-test-user-session-secret",
        session_ttl_seconds=3600,
        magic_link_ttl_seconds=900,
    )


def test_enforce_rate_limit_blocks_after_ip_threshold(monkeypatch) -> None:
    reset_rate_limiter_for_tests()
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_PROBE_IP_LIMIT", "2")
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_PROBE_IP_WINDOW_SECONDS", "60")

    request = _make_request(ip="198.51.100.10")

    enforce_rate_limit(request, action="probe", ip_limit=100, ip_window_seconds=900)
    enforce_rate_limit(request, action="probe", ip_limit=100, ip_window_seconds=900)

    with pytest.raises(HTTPException) as exc_info:
        enforce_rate_limit(request, action="probe", ip_limit=100, ip_window_seconds=900)

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"].isdigit()


def test_enforce_rate_limit_uses_hashed_identity_bucket_across_ips(monkeypatch) -> None:
    reset_rate_limiter_for_tests()
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_IDENTITY_PROBE_IDENTITY_LIMIT", "1")
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_IDENTITY_PROBE_IDENTITY_WINDOW_SECONDS", "60")

    enforce_rate_limit(
        _make_request(ip="198.51.100.11"),
        action="identity_probe",
        identity="Alice@Example.com",
        ip_limit=100,
        ip_window_seconds=900,
        identity_limit=100,
        identity_window_seconds=900,
    )

    with pytest.raises(HTTPException) as exc_info:
        enforce_rate_limit(
            _make_request(ip="198.51.100.12"),
            action="identity_probe",
            identity="alice@example.com",
            ip_limit=100,
            ip_window_seconds=900,
            identity_limit=100,
            identity_window_seconds=900,
        )

    assert exc_info.value.status_code == 429


def test_rate_limit_can_be_disabled_for_local_diagnostics(monkeypatch) -> None:
    reset_rate_limiter_for_tests()
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_DISABLED_PROBE_IP_LIMIT", "1")

    request = _make_request(ip="198.51.100.20")
    for _ in range(5):
        enforce_rate_limit(
            request,
            action="disabled_probe",
            ip_limit=1,
            ip_window_seconds=60,
        )


def test_public_signup_challenge_endpoint_is_rate_limited(monkeypatch) -> None:
    reset_rate_limiter_for_tests()
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_PUBLIC_SIGNUP_CHALLENGE_IP_LIMIT", "1")
    monkeypatch.setenv("HIRING_RADAR_RATE_LIMIT_PUBLIC_SIGNUP_CHALLENGE_IP_WINDOW_SECONDS", "60")

    app = create_app()
    app.dependency_overrides[get_user_auth_settings] = _make_user_auth_settings
    client = TestClient(app)

    first_response = client.get("/api/public/auth/signup-challenge")
    second_response = client.get("/api/public/auth/signup-challenge")

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.headers["retry-after"].isdigit()
