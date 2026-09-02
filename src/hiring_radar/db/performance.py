from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PaginationBounds:
    """Safe defaults for page/limit based API and repository calls."""

    default_page: int = 1
    default_page_size: int = 25
    max_page_size: int = 100
    max_page: int = 1_000


def clamp_int(
    value: Any,
    *,
    default: int,
    minimum: int = 1,
    maximum: int = 100,
) -> int:
    """Return an integer clamped to a safe inclusive range.

    The helper is intentionally permissive for call sites that receive values
    from HTTP query params, JSON payloads or internal task configuration. Invalid
    or missing values fall back to `default` instead of leaking ValueError into
    request handlers.
    """

    try:
        candidate = int(value)
    except (TypeError, ValueError):
        candidate = default

    if candidate < minimum:
        return minimum
    if candidate > maximum:
        return maximum
    return candidate


def normalize_pagination(
    *,
    page: Any,
    page_size: Any,
    bounds: PaginationBounds | None = None,
) -> tuple[int, int, int]:
    """Normalize page/page_size and return `(page, page_size, offset)`."""

    limits = bounds or PaginationBounds()
    normalized_page = clamp_int(
        page,
        default=limits.default_page,
        minimum=1,
        maximum=limits.max_page,
    )
    normalized_page_size = clamp_int(
        page_size,
        default=limits.default_page_size,
        minimum=1,
        maximum=limits.max_page_size,
    )
    return (
        normalized_page,
        normalized_page_size,
        (normalized_page - 1) * normalized_page_size,
    )


QUERY_PERFORMANCE_INDEX_STATEMENTS: tuple[str, ...] = (
    # Legacy job listing and admin filtering.
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_active_first_seen_id
    ON jobs (is_active, first_seen_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_source_active_first_seen_id
    ON jobs (source_name, is_active, first_seen_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_jobs_company_active_first_seen_id
    ON jobs (company_name, is_active, first_seen_at DESC, id DESC)
    """,
    # Candidate saved-job pipeline and note lookups.
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_saved_jobs_pipeline
    ON subscriber_saved_jobs (subscriber_id, status, updated_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_saved_jobs_created_id
    ON subscriber_saved_jobs (subscriber_id, created_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_saved_job_notes_owner_lookup
    ON subscriber_saved_job_notes (subscriber_id, saved_job_id, created_at DESC, id DESC)
    """,
    # Session/security screens: active session lists and history surfaces.
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_sessions_active_lookup
    ON subscriber_sessions (subscriber_id, expired_at, last_active_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_login_history_owner_time
    ON subscriber_login_history (subscriber_id, created_at DESC, id DESC)
    """,
    # Retrieval and AI queues.
    """
    CREATE INDEX IF NOT EXISTS idx_retrieval_embedding_jobs_status_attempt
    ON retrieval_embedding_jobs (status, attempt_count ASC, created_at ASC, id ASC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_external_context_snapshots_status_expiry
    ON job_external_context_snapshots (fetch_status, expires_at, updated_at DESC)
    """,
    # Employer dashboard and talent workflow joins.
    """
    CREATE INDEX IF NOT EXISTS idx_employer_jobs_company_status_updated_id
    ON employer_jobs (company_id, status, updated_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidates_company_score_updated_id
    ON employer_candidates (company_id, match_score DESC, intent_score DESC, updated_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidate_matches_company_job_score
    ON employer_candidate_job_matches (company_id, job_id, is_archived, match_score DESC, updated_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidate_matches_company_candidate
    ON employer_candidate_job_matches (company_id, candidate_id, updated_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_outreach_campaigns_company_updated_id
    ON employer_outreach_campaigns (company_id, updated_at DESC, id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_send_queue_candidate_status
    ON employer_send_queue_items (candidate_id, status, response_score DESC)
    """,
)


def configure_sqlite_runtime(connection: sqlite3.Connection) -> None:
    """Apply conservative SQLite runtime pragmas for API workloads.

    These pragmas keep local/dev SQLite responsive under concurrent read-heavy
    FastAPI requests without changing schema semantics. WAL is applied only when
    the main database is file-backed; in-memory databases keep SQLite defaults.
    """

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA cache_size = -20000")  # ~20 MiB, negative means KiB.

    main_db_file = _main_database_file(connection)
    if main_db_file:
        try:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
        except sqlite3.DatabaseError:
            # Some managed/read-only SQLite deployments disallow journal changes.
            # The application should still start with the rest of the runtime guards.
            pass


def ensure_query_performance_indexes(connection: sqlite3.Connection) -> None:
    """Create additive indexes used by list, dashboard and queue surfaces."""

    with connection:
        for statement in QUERY_PERFORMANCE_INDEX_STATEMENTS:
            connection.execute(statement)


def list_query_performance_indexes(connection: sqlite3.Connection) -> set[str]:
    """Return the additive performance indexes currently present in SQLite."""

    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
          AND name LIKE 'idx_%'
        """
    ).fetchall()
    return {str(row[0]) for row in rows}


def explain_query_plan(
    connection: sqlite3.Connection,
    sql: str,
    params: Iterable[Any] = (),
) -> list[str]:
    """Return SQLite query-plan details for lightweight regression tests."""

    rows = connection.execute(f"EXPLAIN QUERY PLAN {sql}", tuple(params)).fetchall()
    details: list[str] = []
    for row in rows:
        try:
            details.append(str(row["detail"]))
        except (KeyError, TypeError, IndexError):
            details.append(str(row[-1]))
    return details


def _main_database_file(connection: sqlite3.Connection) -> str | None:
    rows = connection.execute("PRAGMA database_list").fetchall()
    for row in rows:
        name = row[1] if not isinstance(row, sqlite3.Row) else row["name"]
        if name != "main":
            continue
        file_path = row[2] if not isinstance(row, sqlite3.Row) else row["file"]
        cleaned = str(file_path or "").strip()
        return cleaned or None
    return None
