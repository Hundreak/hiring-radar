#!/usr/bin/env python3
"""Run a disposable SQLite migration/bootstrap check for release validation."""
from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hiring_radar.db.performance import list_query_performance_indexes
from hiring_radar.db.sqlite import SQLITE_MIGRATIONS, initialize_database

REQUIRED_TABLES = {
    "jobs",
    "subscribers",
    "subscriber_sessions",
    "subscriber_saved_jobs",
    "subscriber_notification_preferences",
    "employer_companies",
    "employer_users",
    "employer_audit_events",
    "employer_outreach_campaigns",
    "employer_send_queue_items",
    "schema_migrations",
}
REQUIRED_INDEXES = {
    "idx_subscriber_saved_jobs_pipeline",
    "idx_employer_jobs_company_status_updated_id",
    "idx_employer_candidates_company_score_updated_id",
    "idx_employer_outreach_campaigns_company_updated_id",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Keep the temporary database and print its path for debugging.",
    )
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="hiring-radar-release-db-") as tmp_dir:
        db_path = Path(tmp_dir) / "release_dry_run.sqlite3"
        connection = initialize_database(str(db_path))
        try:
            _assert_runtime_pragmas(connection)
            _assert_tables(connection)
            _assert_migrations(connection)
            _assert_indexes(connection)
        finally:
            connection.close()

        if args.keep_db:
            kept_path = Path.cwd() / "release_dry_run.sqlite3"
            kept_path.write_bytes(db_path.read_bytes())
            print(f"Release migration dry-run database copied to {kept_path}")

    print("Release migration dry-run passed.")
    return 0


def _assert_runtime_pragmas(connection: sqlite3.Connection) -> None:
    foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
    busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
    if int(foreign_keys) != 1:
        raise RuntimeError("SQLite foreign_keys pragma must be enabled.")
    if int(busy_timeout) < 1000:
        raise RuntimeError("SQLite busy_timeout is unexpectedly low.")


def _assert_tables(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    names = {str(row[0]) for row in rows}
    missing = sorted(REQUIRED_TABLES - names)
    if missing:
        raise RuntimeError(f"Missing release-critical tables: {', '.join(missing)}")


def _assert_migrations(connection: sqlite3.Connection) -> None:
    rows = connection.execute("SELECT id FROM schema_migrations").fetchall()
    applied = {str(row[0]) for row in rows}
    expected = {migration.identifier for migration in SQLITE_MIGRATIONS}
    missing = sorted(expected - applied)
    if missing:
        raise RuntimeError(f"Missing migration registry entries: {', '.join(missing)}")


def _assert_indexes(connection: sqlite3.Connection) -> None:
    indexes = list_query_performance_indexes(connection)
    missing = sorted(REQUIRED_INDEXES - indexes)
    if missing:
        raise RuntimeError(f"Missing release-critical indexes: {', '.join(missing)}")


if __name__ == "__main__":
    raise SystemExit(main())
