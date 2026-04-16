from __future__ import annotations

import sqlite3
from pathlib import Path

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
        password_hash TEXT,
        password_updated_at TEXT,
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
    CREATE TABLE IF NOT EXISTS subscriber_magic_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        expires_at TEXT NOT NULL,
        consumed_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_magic_links_subscriber_id
    ON subscriber_magic_links(subscriber_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_magic_links_expires_at
    ON subscriber_magic_links(expires_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_signup_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        verification_code_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        consumed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_signup_verifications_expires_at
    ON subscriber_signup_verifications(expires_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        expires_at TEXT NOT NULL,
        consumed_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_password_reset_tokens_subscriber_id
    ON subscriber_password_reset_tokens(subscriber_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_password_reset_tokens_expires_at
    ON subscriber_password_reset_tokens(expires_at)
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
    """
    CREATE TABLE IF NOT EXISTS subscriber_keyword_preferences (
        subscriber_id INTEGER PRIMARY KEY,
        include_keywords_json TEXT NOT NULL DEFAULT '[]',
        exclude_keywords_json TEXT NOT NULL DEFAULT '[]',
        match_title INTEGER NOT NULL DEFAULT 1 CHECK (match_title IN (0, 1)),
        match_location INTEGER NOT NULL DEFAULT 1 CHECK (match_location IN (0, 1)),
        match_company_name INTEGER NOT NULL DEFAULT 1 CHECK (match_company_name IN (0, 1)),
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_keyword_preferences_updated_at
    ON subscriber_keyword_preferences (updated_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_profiles (
        subscriber_id INTEGER PRIMARY KEY,
        phone TEXT,
        headline TEXT,
        summary TEXT,
        target_roles_json TEXT NOT NULL DEFAULT '[]',
        skills_json TEXT NOT NULL DEFAULT '[]',
        preferred_locations_json TEXT NOT NULL DEFAULT '[]',
        remote_preference TEXT,
        cv_filename TEXT,
        cv_uploaded_at TEXT,
        avatar_asset_id TEXT,
        avatar_storage_path TEXT,
        avatar_content_type TEXT,
        avatar_url TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_profiles_updated_at
    ON subscriber_profiles (updated_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_education_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        school_name TEXT NOT NULL,
        degree_name TEXT,
        field_of_study TEXT,
        start_year INTEGER,
        end_year INTEGER,
        display_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_education_entries_subscriber_id
    ON subscriber_education_entries (subscriber_id, display_order, id)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_experience_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        company_name TEXT,
        start_year INTEGER,
        end_year INTEGER,
        summary TEXT,
        display_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_experience_entries_subscriber_id
    ON subscriber_experience_entries (subscriber_id, display_order, id)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_language_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        language_name TEXT NOT NULL,
        proficiency_level TEXT,
        notes TEXT,
        display_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_language_entries_subscriber_id
    ON subscriber_language_entries (subscriber_id, display_order, id)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_language_certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        language_entry_id INTEGER,
        certificate_name TEXT NOT NULL,
        issuer_name TEXT,
        file_name TEXT,
        storage_path TEXT,
        uploaded_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id),
        FOREIGN KEY (language_entry_id) REFERENCES subscriber_language_entries(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_language_certificates_subscriber_id
    ON subscriber_language_certificates (subscriber_id, id)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_skill_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        skill_name_normalized TEXT NOT NULL,
        category TEXT,
        proficiency_hint TEXT,
        years_hint INTEGER,
        evidence_note TEXT,
        evidence_file_name TEXT,
        evidence_storage_path TEXT,
        uploaded_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(subscriber_id, skill_name_normalized),
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_skill_details_subscriber_id
    ON subscriber_skill_details (subscriber_id, skill_name_normalized)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_ai_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        telemetry_ref TEXT,
        target_field TEXT NOT NULL,
        target_entity_id TEXT,
        action_type TEXT NOT NULL,
        source_panel TEXT,
        before_snapshot_json TEXT NOT NULL,
        after_snapshot_json TEXT NOT NULL,
        persistence_status TEXT NOT NULL DEFAULT 'unsaved',
        evaluation_status TEXT,
        evaluation_score REAL,
        manual_edit_distance INTEGER,
        request_ref TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        reverted_at TEXT,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_ai_audit_logs_subscriber_id
    ON subscriber_ai_audit_logs (subscriber_id, created_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_cv_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        original_filename TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        content_type TEXT,
        file_size_bytes INTEGER,
        extracted_text TEXT,
        parse_status TEXT NOT NULL DEFAULT 'pending',
        uploaded_at TEXT NOT NULL,
        parsed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_cv_uploads_subscriber_id
    ON subscriber_cv_uploads (subscriber_id, uploaded_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_cv_parse_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        cv_upload_id INTEGER NOT NULL,
        parser_version TEXT,
        source_parse_status TEXT NOT NULL,
        snapshot_json TEXT NOT NULL,
        apply_status TEXT NOT NULL DEFAULT 'pending',
        applied_change_count INTEGER NOT NULL DEFAULT 0,
        applied_at TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id),
        FOREIGN KEY (cv_upload_id) REFERENCES subscriber_cv_uploads(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_cv_parse_runs_upload_id
    ON subscriber_cv_parse_runs (cv_upload_id, created_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_cv_parse_runs_subscriber_id
    ON subscriber_cv_parse_runs (subscriber_id, created_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_cv_apply_audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        parse_run_id INTEGER NOT NULL,
        selected_operations_json TEXT NOT NULL,
        applied_operations_json TEXT NOT NULL,
        applied_change_count INTEGER NOT NULL,
        resulting_apply_status TEXT NOT NULL,
        remaining_actionable_change_count INTEGER NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id),
        FOREIGN KEY (parse_run_id) REFERENCES subscriber_cv_parse_runs(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_cv_apply_audits_parse_run_id
    ON subscriber_cv_apply_audits (parse_run_id, created_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_cv_apply_audits_subscriber_id
    ON subscriber_cv_apply_audits (subscriber_id, created_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS retrieval_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        source_type TEXT NOT NULL,
        source_ref TEXT NOT NULL,
        title TEXT,
        locale TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        checksum TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_ingested_at TEXT,
        error_message TEXT,
        UNIQUE(subscriber_id, source_type, source_ref),
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_retrieval_sources_subscriber_id
    ON retrieval_sources (subscriber_id, source_type, updated_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS retrieval_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        document_kind TEXT NOT NULL,
        title TEXT,
        body_text TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        checksum TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (source_id) REFERENCES retrieval_sources(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_retrieval_documents_source_id
    ON retrieval_documents (source_id, updated_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS retrieval_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        token_estimate INTEGER,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        embedding_status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        UNIQUE(document_id, chunk_index),
        FOREIGN KEY (document_id) REFERENCES retrieval_documents(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_retrieval_chunks_document_id
    ON retrieval_chunks (document_id, chunk_index, id)
    """,
    """
    CREATE TABLE IF NOT EXISTS retrieval_embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chunk_id INTEGER NOT NULL,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        vector_ref TEXT,
        vector_json TEXT,
        dimensions INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY (chunk_id) REFERENCES retrieval_chunks(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_retrieval_embeddings_chunk_id
    ON retrieval_embeddings (chunk_id, created_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_ai_copilot_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        locale TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_message_at TEXT,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_ai_copilot_conversations_subscriber_id
    ON subscriber_ai_copilot_conversations (subscriber_id, updated_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_ai_copilot_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        subscriber_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES subscriber_ai_copilot_conversations(id),
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_ai_copilot_messages_conversation_id
    ON subscriber_ai_copilot_messages (conversation_id, created_at ASC, id ASC)
    """,
    """
    CREATE TABLE IF NOT EXISTS career_knowledge_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        locale TEXT,
        source_name TEXT,
        source_url TEXT,
        trust_level TEXT NOT NULL DEFAULT 'curated',
        freshness_label TEXT NOT NULL DEFAULT 'foundation',
        body_text TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        checksum TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_career_knowledge_documents_category_locale
    ON career_knowledge_documents (category, locale, updated_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_ai_learned_memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        memory_key TEXT NOT NULL,
        memory_note TEXT NOT NULL,
        source_type TEXT NOT NULL DEFAULT 'conversation',
        confidence REAL NOT NULL DEFAULT 0.5,
        times_reinforced INTEGER NOT NULL DEFAULT 1,
        last_observed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(subscriber_id, memory_key),
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_ai_learned_memories_subscriber_id
    ON subscriber_ai_learned_memories (subscriber_id, updated_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_saved_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'reviewing',
        match_score INTEGER,
        deadline_at TEXT,
        interview_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(subscriber_id, job_id),
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_saved_jobs_subscriber_id
    ON subscriber_saved_jobs (subscriber_id, status, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_saved_job_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        saved_job_id INTEGER NOT NULL,
        subscriber_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (saved_job_id) REFERENCES subscriber_saved_jobs(id),
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_saved_job_notes_saved_job_id
    ON subscriber_saved_job_notes (saved_job_id, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        session_token_hash TEXT NOT NULL UNIQUE,
        device_label TEXT NOT NULL DEFAULT '',
        ip_address TEXT NOT NULL DEFAULT '',
        user_agent TEXT NOT NULL DEFAULT '',
        is_current INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        last_active_at TEXT NOT NULL,
        expired_at TEXT,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_sessions_subscriber_id
    ON subscriber_sessions (subscriber_id, last_active_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_login_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        ip_address TEXT NOT NULL DEFAULT '',
        user_agent TEXT NOT NULL DEFAULT '',
        detail TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_login_history_subscriber_id
    ON subscriber_login_history (subscriber_id, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_email_change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        new_email TEXT NOT NULL,
        verification_code_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        consumed_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_totp_secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL UNIQUE,
        secret_encrypted TEXT NOT NULL,
        is_verified INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        verified_at TEXT,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_account_deletions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        email TEXT NOT NULL,
        reason TEXT,
        deleted_at TEXT NOT NULL
    )
    """,
)


def _ensure_column(
    connection: sqlite3.Connection,
    *,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    existing_columns = {
        row["name"]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }
    if column_name in existing_columns:
        return

    with connection:
        connection.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {column_definition}"
        )


def _ensure_subscriber_auth_migrations(connection: sqlite3.Connection) -> None:
    _ensure_column(
        connection,
        table_name="subscribers",
        column_name="password_hash",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscribers",
        column_name="password_updated_at",
        column_definition="TEXT",
    )


def _ensure_profile_asset_migrations(connection: sqlite3.Connection) -> None:
    _ensure_column(
        connection,
        table_name="subscriber_profiles",
        column_name="avatar_asset_id",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_profiles",
        column_name="avatar_storage_path",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_profiles",
        column_name="avatar_content_type",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_profiles",
        column_name="avatar_url",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_cv_parse_runs",
        column_name="apply_status",
        column_definition="TEXT NOT NULL DEFAULT 'pending'",
    )
    _ensure_column(
        connection,
        table_name="subscriber_cv_parse_runs",
        column_name="applied_change_count",
        column_definition="INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        connection,
        table_name="subscriber_cv_parse_runs",
        column_name="applied_at",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_cv_parse_runs",
        column_name="metadata_json",
        column_definition="TEXT NOT NULL DEFAULT '{}'",
    )
    _ensure_column(
        connection,
        table_name="subscriber_cv_apply_audits",
        column_name="metadata_json",
        column_definition="TEXT NOT NULL DEFAULT '{}'",
    )




def _ensure_copilot_ai_migrations(connection: sqlite3.Connection) -> None:
    _ensure_column(
        connection,
        table_name="subscriber_ai_copilot_conversations",
        column_name="locale",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_ai_copilot_conversations",
        column_name="status",
        column_definition="TEXT NOT NULL DEFAULT 'active'",
    )
    _ensure_column(
        connection,
        table_name="subscriber_ai_copilot_conversations",
        column_name="last_message_at",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_ai_copilot_messages",
        column_name="metadata_json",
        column_definition="TEXT NOT NULL DEFAULT '{}'",
    )
    _ensure_column(
        connection,
        table_name="career_knowledge_documents",
        column_name="trust_level",
        column_definition="TEXT NOT NULL DEFAULT 'curated'",
    )
    _ensure_column(
        connection,
        table_name="career_knowledge_documents",
        column_name="freshness_label",
        column_definition="TEXT NOT NULL DEFAULT 'foundation'",
    )
    _ensure_column(
        connection,
        table_name="career_knowledge_documents",
        column_name="metadata_json",
        column_definition="TEXT NOT NULL DEFAULT '{}'",
    )
    _ensure_column(
        connection,
        table_name="subscriber_ai_learned_memories",
        column_name="confidence",
        column_definition="REAL NOT NULL DEFAULT 0.5",
    )
    _ensure_column(
        connection,
        table_name="subscriber_ai_learned_memories",
        column_name="times_reinforced",
        column_definition="INTEGER NOT NULL DEFAULT 1",
    )
    _ensure_column(
        connection,
        table_name="subscriber_ai_learned_memories",
        column_name="last_observed_at",
        column_definition="TEXT",
    )

def _ensure_retrieval_migrations(connection: sqlite3.Connection) -> None:
    _ensure_column(
        connection,
        table_name="retrieval_sources",
        column_name="last_ingested_at",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="retrieval_sources",
        column_name="error_message",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="retrieval_documents",
        column_name="checksum",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="retrieval_documents",
        column_name="status",
        column_definition="TEXT NOT NULL DEFAULT 'pending'",
    )


def init_db_schema(connection: sqlite3.Connection) -> None:
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)


def initialize_database(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(path),
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    init_db_schema(connection)
    _ensure_subscriber_auth_migrations(connection)
    _ensure_profile_asset_migrations(connection)
    _ensure_retrieval_migrations(connection)
    _ensure_copilot_ai_migrations(connection)

    return connection


def close_connection(connection: sqlite3.Connection | None) -> None:
    if connection is None:
        return

    connection.close()
