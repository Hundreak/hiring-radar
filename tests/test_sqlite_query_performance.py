from __future__ import annotations

from pathlib import Path

from hiring_radar.db.performance import (
    PaginationBounds,
    explain_query_plan,
    list_query_performance_indexes,
    normalize_pagination,
)
from hiring_radar.db.sqlite import SQLITE_MIGRATIONS, close_connection, initialize_database

EXPECTED_PERFORMANCE_INDEXES = {
    "idx_jobs_active_first_seen_id",
    "idx_jobs_source_active_first_seen_id",
    "idx_jobs_company_active_first_seen_id",
    "idx_subscriber_saved_jobs_pipeline",
    "idx_subscriber_saved_jobs_created_id",
    "idx_subscriber_saved_job_notes_owner_lookup",
    "idx_subscriber_sessions_active_lookup",
    "idx_subscriber_login_history_owner_time",
    "idx_retrieval_embedding_jobs_status_attempt",
    "idx_job_external_context_snapshots_status_expiry",
    "idx_employer_jobs_company_status_updated_id",
    "idx_employer_candidates_company_score_updated_id",
    "idx_employer_candidate_matches_company_job_score",
    "idx_employer_candidate_matches_company_candidate",
    "idx_employer_outreach_campaigns_company_updated_id",
    "idx_employer_send_queue_candidate_status",
}


def test_query_performance_migration_is_registered() -> None:
    # Kayıtlı olması aranır, sonuncu olması değil: sıraya bağlanırsa her yeni
    # migration bu testi düşürür.
    registered = {migration.identifier for migration in SQLITE_MIGRATIONS}
    assert "2026_05_25_0016_query_performance_indexes" in registered


def test_initialize_database_creates_query_performance_indexes(tmp_path: Path) -> None:
    connection = initialize_database(str(tmp_path / "perf.db"))
    try:
        existing = list_query_performance_indexes(connection)
        migration_ids = {
            row["id"]
            for row in connection.execute("SELECT id FROM schema_migrations").fetchall()
        }
    finally:
        close_connection(connection)

    assert EXPECTED_PERFORMANCE_INDEXES.issubset(existing)
    assert "2026_05_25_0016_query_performance_indexes" in migration_ids


def test_sqlite_runtime_pragmas_are_applied(tmp_path: Path) -> None:
    connection = initialize_database(str(tmp_path / "runtime.db"))
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA cache_size").fetchone()[0] == -20000
        assert connection.execute("PRAGMA temp_store").fetchone()[0] >= 1
    finally:
        close_connection(connection)


def test_saved_jobs_pipeline_query_uses_additive_index(tmp_path: Path) -> None:
    connection = initialize_database(str(tmp_path / "plan.db"))
    try:
        details = explain_query_plan(
            connection,
            """
            SELECT id, subscriber_id, status, updated_at
            FROM subscriber_saved_jobs
            WHERE subscriber_id = ? AND status = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (123, "reviewing", 10),
        )
    finally:
        close_connection(connection)

    joined = "\n".join(details)
    assert "idx_subscriber_saved_jobs_pipeline" in joined


def test_normalize_pagination_clamps_untrusted_values() -> None:
    page, page_size, offset = normalize_pagination(
        page="-4",
        page_size="9000",
        bounds=PaginationBounds(default_page=1, default_page_size=25, max_page_size=80),
    )

    assert page == 1
    assert page_size == 80
    assert offset == 0

    page, page_size, offset = normalize_pagination(
        page="3",
        page_size="20",
        bounds=PaginationBounds(default_page=1, default_page_size=25, max_page_size=80),
    )
    assert (page, page_size, offset) == (3, 20, 40)
