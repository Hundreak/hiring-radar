from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.user_auth import (
    UserAuthError,
    UserAuthSettings,
    consume_magic_link_token,
    create_user_session_token,
    decode_user_session_token,
    issue_magic_link_for_email,
)


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "user_auth_service.db"))
    return HiringRadarRepository(connection), connection


def _make_settings() -> UserAuthSettings:
    return UserAuthSettings(
        app_base_url="http://127.0.0.1:8000",
        session_secret="user-session-secret",
        session_ttl_seconds=3600,
        magic_link_ttl_seconds=900,
    )


def test_issue_magic_link_returns_login_url_for_active_subscriber(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice",
            updated_at="2026-04-04T10:00:00Z",
        )

        result = issue_magic_link_for_email(
            repository=repo,
            email="alice@example.com",
            settings=_make_settings(),
            now=datetime(2026, 4, 4, 10, 0, 0, tzinfo=UTC),
        )

        assert result is not None
        assert result.subscriber.email == "alice@example.com"
        assert result.login_url.startswith("http://127.0.0.1:8000/app/login?token=")
        assert result.expires_at == "2026-04-04T10:15:00Z"
    finally:
        close_connection(connection)


def test_issue_magic_link_returns_none_for_unknown_email(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        result = issue_magic_link_for_email(
            repository=repo,
            email="missing@example.com",
            settings=_make_settings(),
        )

        assert result is None
    finally:
        close_connection(connection)


def test_consume_magic_link_token_marks_token_as_used(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice",
            updated_at="2026-04-04T10:00:00Z",
        )
        issued = issue_magic_link_for_email(
            repository=repo,
            email="alice@example.com",
            settings=_make_settings(),
            now=datetime(2026, 4, 4, 10, 0, 0, tzinfo=UTC),
        )
        assert issued is not None

        subscriber = consume_magic_link_token(
            repository=repo,
            raw_token=issued.raw_token,
            now=datetime(2026, 4, 4, 10, 5, 0, tzinfo=UTC),
        )
        assert subscriber.email == "alice@example.com"

        with pytest.raises(UserAuthError) as exc_info:
            consume_magic_link_token(
                repository=repo,
                raw_token=issued.raw_token,
                now=datetime(2026, 4, 4, 10, 6, 0, tzinfo=UTC),
            )

        assert "already been used" in str(exc_info.value)
    finally:
        close_connection(connection)


def test_user_session_token_roundtrip() -> None:
    settings = _make_settings()
    now = datetime(2026, 4, 4, 12, 0, 0, tzinfo=UTC)

    token = create_user_session_token(
        subscriber_id=7,
        email="alice@example.com",
        settings=settings,
        now=now,
    )
    session = decode_user_session_token(
        token=token,
        settings=settings,
        now=now + timedelta(minutes=30),
    )

    assert session.subscriber_id == 7
    assert session.email == "alice@example.com"
    assert session.issued_at == "2026-04-04T12:00:00Z"