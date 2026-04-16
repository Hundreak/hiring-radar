from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database


def test_initialize_database_creates_notification_checkpoints_table(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test_notification_checkpoints.db"
    connection = initialize_database(str(db_path))

    try:
        table_row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'notification_checkpoints'
            """
        ).fetchone()

        assert table_row is not None

        columns = connection.execute("PRAGMA table_info(notification_checkpoints)").fetchall()
        column_names = [column[1] for column in columns]

        assert column_names == [
            "checkpoint_key",
            "last_processed_at",
            "updated_at",
        ]

    finally:
        connection.close()


def test_upsert_notification_checkpoint_inserts_and_updates(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test_notification_checkpoints_repo.db"
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)

    try:
        inserted = repository.upsert_notification_checkpoint(
            checkpoint_key="digest_email",
            last_processed_at="2026-04-03T18:00:00Z",
            updated_at="2026-04-03T18:00:00Z",
        )

        assert inserted.checkpoint_key == "digest_email"
        assert inserted.last_processed_at == "2026-04-03T18:00:00Z"
        assert inserted.updated_at == "2026-04-03T18:00:00Z"

        updated = repository.upsert_notification_checkpoint(
            checkpoint_key="digest_email",
            last_processed_at="2026-04-04T00:00:00Z",
            updated_at="2026-04-04T00:00:00Z",
        )

        assert updated.checkpoint_key == "digest_email"
        assert updated.last_processed_at == "2026-04-04T00:00:00Z"
        assert updated.updated_at == "2026-04-04T00:00:00Z"

        loaded = repository.get_notification_checkpoint("digest_email")
        assert loaded is not None
        assert loaded.checkpoint_key == "digest_email"
        assert loaded.last_processed_at == "2026-04-04T00:00:00Z"
        assert loaded.updated_at == "2026-04-04T00:00:00Z"

    finally:
        repository.close()


def test_get_notification_checkpoint_returns_none_for_missing_key(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test_notification_checkpoints_missing.db"
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)

    try:
        checkpoint = repository.get_notification_checkpoint("missing")
        assert checkpoint is None
    finally:
        repository.close()
