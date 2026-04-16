from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from hiring_radar.services.user_auth import (
    SessionDecodeError,
    UserAuthSettings,
    build_magic_link_expiration,
    build_magic_link_url,
    build_user_session,
    decode_user_session,
    generate_magic_link_token,
    hash_magic_link_token,
    sign_user_session,
)


def _make_settings() -> UserAuthSettings:
    return UserAuthSettings(
        secret_key="user-session-secret",
        session_ttl_seconds=3600,
        magic_link_ttl_seconds=900,
    )


def _far_future() -> datetime:
    return datetime(2099, 1, 1, 0, 0, 0, tzinfo=UTC)


def test_user_session_roundtrip() -> None:
    settings = _make_settings()
    now = _far_future()

    session = build_user_session(
        subscriber_id=7,
        email="alice@example.com",
        settings=settings,
        now=now,
    )
    assert session.subscriber_id == 7
    assert session.email == "alice@example.com"

    token = sign_user_session(session, settings=settings)

    with patch("hiring_radar.services.user_auth.utc_now", return_value=now + timedelta(minutes=5)):
        decoded = decode_user_session(token, settings=settings)

    assert decoded.subscriber_id == 7
    assert decoded.email == "alice@example.com"


def test_decode_user_session_rejects_expired_token() -> None:
    settings = UserAuthSettings(
        secret_key="user-session-secret",
        session_ttl_seconds=60,
        magic_link_ttl_seconds=900,
    )
    now = _far_future()

    session = build_user_session(
        subscriber_id=7,
        email="alice@example.com",
        settings=settings,
        now=now,
    )
    token = sign_user_session(session, settings=settings)

    with patch("hiring_radar.services.user_auth.utc_now", return_value=now + timedelta(hours=2)):
        with pytest.raises(SessionDecodeError, match="expired"):
            decode_user_session(token, settings=settings)


def test_decode_user_session_rejects_bad_signature() -> None:
    settings = _make_settings()

    with pytest.raises(SessionDecodeError, match="Invalid session signature"):
        decode_user_session("totally-bogus-token", settings=settings)


def test_generate_magic_link_token_is_unique() -> None:
    t1 = generate_magic_link_token()
    t2 = generate_magic_link_token()
    assert t1 != t2
    assert len(t1) > 20


def test_hash_magic_link_token_is_deterministic() -> None:
    token = "test-token-value"
    assert hash_magic_link_token(token) == hash_magic_link_token(token)


def test_build_magic_link_url() -> None:
    url = build_magic_link_url(
        base_url="http://127.0.0.1:8000/tr/login",
        token="abc123",
        email="Alice@Example.Com",
    )
    assert "token=abc123" in url
    assert "email=alice@example.com" in url


def test_build_magic_link_expiration() -> None:
    settings = _make_settings()
    now = datetime(2099, 4, 4, 10, 0, 0, tzinfo=UTC)
    expires = build_magic_link_expiration(settings=settings, now=now)
    assert expires == "2099-04-04T10:15:00Z"
