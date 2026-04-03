from __future__ import annotations

import sqlite3

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        title TEXT NOT NULL,
        company_name TEXT NOT NULL,
        location TEXT,
        canonical_url TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_job_id TEXT,
        raw_posted_at TEXT,
        posted_at TEXT,
        fingerprint TEXT NOT NULL UNIQUE,
        first_seen_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        scraped_at TEXT NOT NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_source_name
    ON jobs (source_name);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_company_name
    ON jobs (company_name);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_is_active
    ON jobs (is_active);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_last_seen_at
    ON jobs (last_seen_at);
    """,
    """
    CREATE TABLE IF NOT EXISTS crawl_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        source_name TEXT NOT NULL,
        success INTEGER CHECK (success IN (0, 1)),
        notes TEXT
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_crawl_runs_source_name_started_at
    ON crawl_runs (source_name, started_at);
    """,
)


def init_db_schema(connection: sqlite3.Connection) -> None:
    """
    Create the SQLite schema required by the MVP.
    """
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)