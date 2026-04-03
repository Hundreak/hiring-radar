from __future__ import annotations

from pathlib import Path

from hiring_radar.db.sqlite import initialize_database


def test_initialize_database_creates_subscribers_table_with_expected_columns(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test_subscribers.db"
    connection = initialize_database(str(db_path))

    try:
        table_row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'subscribers'
            """
        ).fetchone()

        assert table_row is not None

        columns = connection.execute("PRAGMA table_info(subscribers)").fetchall()
        column_names = [column[1] for column in columns]

        assert column_names == [
            "id",
            "email",
            "full_name",
            "is_active",
            "digest_enabled",
            "created_at",
            "updated_at",
        ]

        indexes = connection.execute("PRAGMA index_list(subscribers)").fetchall()
        index_names = [index[1] for index in indexes]

        assert "idx_subscribers_active_digest_enabled" in index_names

    finally:
        connection.close()