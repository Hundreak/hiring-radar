from __future__ import annotations

import sqlite3

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS crawl_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        source_name TEXT NOT NULL,
        success INTEGER,
        notes TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_crawl_runs_source_name_started_at
    ON crawl_runs (source_name, started_at)
    """,
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
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_source_name_is_active
    ON jobs (source_name, is_active)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_company_name
    ON jobs (company_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_first_seen_at
    ON jobs (first_seen_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        full_name TEXT,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        digest_enabled INTEGER NOT NULL DEFAULT 1 CHECK (digest_enabled IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscribers_active_digest_enabled
    ON subscribers (is_active, digest_enabled)
    """,
    """
    CREATE TABLE IF NOT EXISTS notification_checkpoints (
        checkpoint_key TEXT PRIMARY KEY,
        last_processed_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notification_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notification_type TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT NOT NULL,
        recipient_count INTEGER NOT NULL DEFAULT 0,
        new_jobs_count INTEGER NOT NULL DEFAULT 0,
        since TEXT,
        subject TEXT,
        error_message TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_notification_runs_type_started_at
    ON notification_runs (notification_type, started_at)
    """,
)
 

def init_db_schema(connection: sqlite3.Connection) -> None:
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)