from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

MigrationHandler = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True, slots=True)
class Migration:
    """Idempotent SQLite migration registered by a stable identifier.

    `run_always` is intended for legacy `_ensure_*` migrations that must keep
    self-healing older/drifted SQLite databases even after the migration has
    been recorded. New irreversible migrations should leave it as `False`.
    """

    identifier: str
    description: str
    handler: MigrationHandler
    run_always: bool = False

    @property
    def checksum(self) -> str:
        payload = f"{self.identifier}\n{self.description}".encode()
        return hashlib.sha256(payload).hexdigest()


def ensure_migration_registry(connection: sqlite3.Connection) -> None:
    """Create the schema migration registry if it does not exist yet."""
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at
            ON schema_migrations (applied_at DESC, id)
            """
        )


def get_applied_migration_ids(connection: sqlite3.Connection) -> set[str]:
    ensure_migration_registry(connection)
    rows = connection.execute("SELECT id FROM schema_migrations").fetchall()
    return {str(row[0]) for row in rows}


def run_migrations(
    connection: sqlite3.Connection,
    migrations: Sequence[Migration],
) -> list[str]:
    """Run pending migrations and record each successful application.

    Migration handlers must be idempotent. The runner records a migration only
    after the handler completes successfully, so a failing migration can be
    retried safely on the next application start.
    """
    ensure_migration_registry(connection)
    applied_ids = get_applied_migration_ids(connection)
    newly_applied: list[str] = []

    for migration in migrations:
        was_applied = migration.identifier in applied_ids
        if was_applied and not migration.run_always:
            continue

        migration.handler(connection)
        if was_applied:
            continue

        applied_at = datetime.now(UTC).isoformat(timespec="seconds")
        with connection:
            connection.execute(
                """
                INSERT INTO schema_migrations (id, description, checksum, applied_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    migration.identifier,
                    migration.description,
                    migration.checksum,
                    applied_at,
                ),
            )
        applied_ids.add(migration.identifier)
        newly_applied.append(migration.identifier)

    return newly_applied
