from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from hiring_radar.db.migration_registry import Migration, run_migrations
from hiring_radar.db.sqlite import SQLITE_MIGRATIONS, close_connection, initialize_database


def test_initialize_database_records_schema_migrations(tmp_path: Path) -> None:
    connection = initialize_database(str(tmp_path / "registry.db"))
    try:
        rows = connection.execute(
            """
            SELECT id, description, checksum, applied_at
            FROM schema_migrations
            ORDER BY id
            """
        ).fetchall()
    finally:
        close_connection(connection)

    assert [row["id"] for row in rows] == [migration.identifier for migration in SQLITE_MIGRATIONS]
    assert all(row["description"] for row in rows)
    assert all(len(row["checksum"]) == 64 for row in rows)
    assert all(row["applied_at"] for row in rows)


def test_initialize_database_migration_registry_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "registry_idempotent.db"

    first = initialize_database(str(db_path))
    first_rows = first.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    close_connection(first)

    second = initialize_database(str(db_path))
    try:
        second_rows = second.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        duplicate_ids = second.execute(
            """
            SELECT id, COUNT(*) AS count
            FROM schema_migrations
            GROUP BY id
            HAVING COUNT(*) > 1
            """
        ).fetchall()
    finally:
        close_connection(second)

    assert first_rows == len(SQLITE_MIGRATIONS)
    assert second_rows == first_rows
    assert duplicate_ids == []


def test_run_migrations_records_only_successful_migrations() -> None:
    connection = sqlite3.connect(":memory:")
    applied: list[str] = []

    def successful_handler(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS smoke (id INTEGER PRIMARY KEY)")
        applied.append("ok")

    def failing_handler(conn: sqlite3.Connection) -> None:
        applied.append("fail")
        raise RuntimeError("boom")

    migrations = (
        Migration("0001_success", "successful migration", successful_handler),
        Migration("0002_failure", "failing migration", failing_handler),
    )

    with pytest.raises(RuntimeError, match="boom"):
        run_migrations(connection, migrations)

    rows = connection.execute("SELECT id FROM schema_migrations ORDER BY id").fetchall()
    assert [row[0] for row in rows] == ["0001_success"]
    assert applied == ["ok", "fail"]

    retry = run_migrations(connection, migrations[:1])
    assert retry == []
    assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
