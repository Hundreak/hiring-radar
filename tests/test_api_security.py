from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hiring_radar.api.security import (
    AdminAuthError,
    AdminAuthSettings,
    create_admin_session_token,
    decode_admin_session_token,
    verify_admin_credentials,
)


def _make_auth_settings() -> AdminAuthSettings:
    return AdminAuthSettings(
        email="admin@example.com",
        password="super-secret",
        session_secret="test-session-secret",
        session_ttl_seconds=3600,
    )


def test_verify_admin_credentials_requires_exact_match() -> None:
    settings = _make_auth_settings()

    assert (
        verify_admin_credentials(
            email="admin@example.com",
            password="super-secret",
            settings=settings,
        )
        is True
    )
    assert (
        verify_admin_credentials(
            email="admin@example.com",
            password="wrong-password",
            settings=settings,
        )
        is False
    )


def test_create_and_decode_admin_session_token_roundtrip() -> None:
    settings = _make_auth_settings()
    now = datetime(2026, 4, 4, 12, 0, 0, tzinfo=UTC)

    token = create_admin_session_token(
        email="admin@example.com",
        settings=settings,
        now=now,
    )
    session = decode_admin_session_token(
        token=token,
        settings=settings,
        now=now + timedelta(minutes=5),
    )

    assert session.email == "admin@example.com"
    assert session.issued_at == "2026-04-04T12:00:00Z"
    assert session.expires_at == "2026-04-04T13:00:00Z"


def test_decode_admin_session_token_rejects_expired_token() -> None:
    settings = _make_auth_settings()
    issued_at = datetime(2026, 4, 4, 12, 0, 0, tzinfo=UTC)

    token = create_admin_session_token(
        email="admin@example.com",
        settings=settings,
        now=issued_at,
    )

    with pytest.raises(AdminAuthError) as exc_info:
        decode_admin_session_token(
            token=token,
            settings=settings,
            now=issued_at + timedelta(hours=2),
        )

    assert "expired" in str(exc_info.value).lower()
