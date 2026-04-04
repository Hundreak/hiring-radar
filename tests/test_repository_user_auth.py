from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "test_user_auth.db"))
    return HiringRadarRepository(connection), connection


def test_repository_can_create_and_consume_magic_link(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice",
            updated_at="2026-04-04T10:00:00Z",
        )

        link = repo.create_subscriber_magic_link(
            subscriber_id=subscriber.id or 0,
            token_hash="hash-123",
            expires_at="2026-04-04T10:15:00Z",
            created_at="2026-04-04T10:00:00Z",
        )

        fetched = repo.get_subscriber_magic_link_by_hash("hash-123")
        assert fetched is not None
        assert fetched.id == link.id
        assert fetched.subscriber_id == subscriber.id

        consumed = repo.consume_subscriber_magic_link(
            link.id or 0,
            consumed_at="2026-04-04T10:05:00Z",
        )
        assert consumed is True

        fetched_after = repo.get_subscriber_magic_link_by_hash("hash-123")
        assert fetched_after is not None
        assert fetched_after.consumed_at == "2026-04-04T10:05:00Z"
    finally:
        close_connection(connection)