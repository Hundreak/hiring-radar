from __future__ import annotations

import sqlite3
from pathlib import Path

from hiring_radar.db.employer_schema import init_employer_schema
from hiring_radar.db.migration_registry import Migration, run_migrations
from hiring_radar.db.performance import (
    configure_sqlite_runtime,
    ensure_query_performance_indexes,
)

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
    CREATE TABLE IF NOT EXISTS job_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT NOT NULL,
        source_name TEXT NOT NULL,
        account_slug TEXT NOT NULL DEFAULT '',
        base_url TEXT,
        trust_score REAL NOT NULL DEFAULT 0.5,
        country_scope TEXT,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (source_type, source_name, account_slug)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_sources_type_active
    ON job_sources (source_type, is_active, source_name)
    """,
    """
    CREATE TABLE IF NOT EXISTS job_source_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        external_job_id TEXT NOT NULL,
        external_company_id TEXT,
        raw_payload_json TEXT NOT NULL,
        raw_payload_hash TEXT NOT NULL,
        canonical_url TEXT,
        title TEXT NOT NULL,
        company_name TEXT NOT NULL,
        location_text TEXT,
        posted_at TEXT,
        apply_url TEXT,
        fetched_at TEXT NOT NULL,
        first_seen_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        FOREIGN KEY (source_id) REFERENCES job_sources(id) ON DELETE CASCADE,
        UNIQUE (source_id, external_job_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_source_records_source_active
    ON job_source_records (source_id, is_active, last_seen_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_source_records_payload_hash
    ON job_source_records (raw_payload_hash)
    """,
    """
    CREATE TABLE IF NOT EXISTS canonical_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_key TEXT NOT NULL UNIQUE,
        normalized_title TEXT NOT NULL,
        normalized_company_name TEXT NOT NULL,
        display_title TEXT NOT NULL,
        display_company_name TEXT NOT NULL,
        location_city TEXT,
        district TEXT,
        country TEXT,
        workplace_type TEXT,
        employment_type TEXT,
        seniority TEXT,
        category TEXT,
        department TEXT,
        description_text TEXT,
        description_html TEXT,
        posted_at TEXT,
        apply_url TEXT NOT NULL,
        trust_score REAL NOT NULL DEFAULT 0.5,
        freshness_score REAL NOT NULL DEFAULT 0.5,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_canonical_jobs_active_updated_at
    ON canonical_jobs (is_active, updated_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_canonical_jobs_company_title
    ON canonical_jobs (normalized_company_name, normalized_title)
    """,
    """
    CREATE TABLE IF NOT EXISTS canonical_job_links (
        canonical_job_id INTEGER NOT NULL,
        source_job_id INTEGER NOT NULL UNIQUE,
        merge_reason TEXT,
        confidence REAL NOT NULL DEFAULT 1.0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (canonical_job_id, source_job_id),
        FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (source_job_id) REFERENCES job_source_records(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_canonical_job_links_canonical_job_id
    ON canonical_job_links (canonical_job_id, confidence DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS canonical_job_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_job_id INTEGER NOT NULL UNIQUE,
        feature_version TEXT NOT NULL,
        role_family TEXT,
        job_discipline TEXT,
        department_family TEXT,
        title_tokens_json TEXT NOT NULL DEFAULT '[]',
        skill_terms_json TEXT NOT NULL DEFAULT '[]',
        location_tokens_json TEXT NOT NULL DEFAULT '[]',
        language_requirements_json TEXT NOT NULL DEFAULT '[]',
        education_level_hint TEXT,
        years_experience_min INTEGER,
        management_track INTEGER NOT NULL DEFAULT 0 CHECK (management_track IN (0, 1)),
        individual_contributor INTEGER NOT NULL DEFAULT 1 CHECK (individual_contributor IN (0, 1)),
        match_readiness_score REAL NOT NULL DEFAULT 0.0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_canonical_job_features_role_family
    ON canonical_job_features (role_family, job_discipline)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_canonical_job_features_match_readiness
    ON canonical_job_features (match_readiness_score DESC, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_profile_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL UNIQUE,
        feature_version TEXT NOT NULL,
        role_families_json TEXT NOT NULL DEFAULT '[]',
        discipline_preferences_json TEXT NOT NULL DEFAULT '[]',
        title_tokens_json TEXT NOT NULL DEFAULT '[]',
        skill_terms_json TEXT NOT NULL DEFAULT '[]',
        experience_evidence_terms_json TEXT NOT NULL DEFAULT '[]',
        preferred_location_tokens_json TEXT NOT NULL DEFAULT '[]',
        language_capabilities_json TEXT NOT NULL DEFAULT '[]',
        education_level TEXT,
        years_experience_total INTEGER,
        remote_preference TEXT,
        management_preference INTEGER CHECK (management_preference IN (0, 1)),
        profile_strength_score REAL NOT NULL DEFAULT 0.0,
        seniority_level TEXT,
        domain_signals_json TEXT NOT NULL DEFAULT '[]',
        responsibility_scope TEXT,
        ownership_signals_json TEXT NOT NULL DEFAULT '[]',
        impact_signals_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_profile_features_strength
    ON subscriber_profile_features (profile_strength_score DESC, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_job_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        api_job_id INTEGER NOT NULL,
        job_kind TEXT NOT NULL CHECK (job_kind IN ('legacy', 'canonical')),
        canonical_job_id INTEGER,
        legacy_job_id INTEGER,
        impression_count INTEGER NOT NULL DEFAULT 0,
        open_count INTEGER NOT NULL DEFAULT 0,
        save_count INTEGER NOT NULL DEFAULT 0,
        apply_click_count INTEGER NOT NULL DEFAULT 0,
        total_dwell_seconds INTEGER NOT NULL DEFAULT 0,
        max_dwell_seconds INTEGER NOT NULL DEFAULT 0,
        affinity_score REAL NOT NULL DEFAULT 0.0,
        first_interacted_at TEXT NOT NULL,
        last_interacted_at TEXT NOT NULL,
        last_source_surface TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
        FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (legacy_job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        UNIQUE (subscriber_id, api_job_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_job_interactions_affinity
    ON subscriber_job_interactions (subscriber_id, affinity_score DESC, last_interacted_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_job_interactions_canonical
    ON subscriber_job_interactions (subscriber_id, canonical_job_id, affinity_score DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_job_interaction_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        api_job_id INTEGER NOT NULL,
        job_kind TEXT NOT NULL CHECK (job_kind IN ('legacy', 'canonical')),
        canonical_job_id INTEGER,
        legacy_job_id INTEGER,
        interaction_type TEXT NOT NULL CHECK (interaction_type IN ('impression', 'open', 'dwell', 'save', 'apply_click')),
        source_surface TEXT,
        dwell_seconds INTEGER,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
        FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (legacy_job_id) REFERENCES jobs(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_job_interaction_events_subscriber_time
    ON subscriber_job_interaction_events (subscriber_id, created_at DESC, id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_job_interaction_events_canonical
    ON subscriber_job_interaction_events (subscriber_id, canonical_job_id, created_at DESC)
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
    CREATE TABLE IF NOT EXISTS subscriber_certification_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        certificate_name TEXT NOT NULL,
        issuer_name TEXT,
        issued_year INTEGER,
        file_name TEXT,
        storage_path TEXT,
        uploaded_at TEXT,
        display_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_subscriber_certification_entries_subscriber_id
    ON subscriber_certification_entries (subscriber_id, display_order, id)
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
    CREATE TABLE IF NOT EXISTS retrieval_embedding_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chunk_id INTEGER NOT NULL,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued',
        attempt_count INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        claimed_at TEXT,
        completed_at TEXT,
        FOREIGN KEY (chunk_id) REFERENCES retrieval_chunks(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_retrieval_embedding_jobs_chunk_id
    ON retrieval_embedding_jobs (chunk_id, status, created_at, id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_retrieval_embedding_jobs_queue
    ON retrieval_embedding_jobs (provider, model, status, created_at, id)
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
    CREATE TABLE IF NOT EXISTS job_external_context_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_url TEXT NOT NULL UNIQUE,
        final_url TEXT,
        source_domain TEXT,
        fetch_status TEXT NOT NULL DEFAULT 'unavailable',
        http_status INTEGER,
        page_title TEXT,
        site_name TEXT,
        meta_description TEXT,
        clean_text TEXT NOT NULL DEFAULT '',
        content_digest TEXT,
        site_specific_requirements_json TEXT NOT NULL DEFAULT '[]',
        company_culture_clues_json TEXT NOT NULL DEFAULT '[]',
        responsibility_clues_json TEXT NOT NULL DEFAULT '[]',
        technology_stack_terms_json TEXT NOT NULL DEFAULT '[]',
        source_metadata_json TEXT NOT NULL DEFAULT '{}',
        warning TEXT,
        fetched_at TEXT,
        expires_at TEXT,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_external_context_snapshots_expires_at
    ON job_external_context_snapshots (expires_at, updated_at DESC, id DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriber_saved_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        api_job_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'reviewing',
        match_score INTEGER,
        deadline_at TEXT,
        interview_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(subscriber_id, api_job_id),
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


def _ensure_saved_jobs_api_reference_migration(connection: sqlite3.Connection) -> None:
    _ensure_column(
        connection,
        table_name="subscriber_saved_jobs",
        column_name="api_job_id",
        column_definition="INTEGER",
    )
    with connection:
        connection.execute(
            """
            UPDATE subscriber_saved_jobs
            SET api_job_id = job_id
            WHERE api_job_id IS NULL
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriber_saved_jobs_api_job_id
            ON subscriber_saved_jobs (subscriber_id, api_job_id)
            """
        )


def _ensure_matching_engine_migrations(connection: sqlite3.Connection) -> None:
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_profile_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL UNIQUE,
                feature_version TEXT NOT NULL,
                role_families_json TEXT NOT NULL DEFAULT '[]',
                discipline_preferences_json TEXT NOT NULL DEFAULT '[]',
                title_tokens_json TEXT NOT NULL DEFAULT '[]',
                skill_terms_json TEXT NOT NULL DEFAULT '[]',
                experience_evidence_terms_json TEXT NOT NULL DEFAULT '[]',
                preferred_location_tokens_json TEXT NOT NULL DEFAULT '[]',
                language_capabilities_json TEXT NOT NULL DEFAULT '[]',
                education_level TEXT,
                years_experience_total INTEGER,
                remote_preference TEXT,
                management_preference INTEGER CHECK (management_preference IN (0, 1)),
                profile_strength_score REAL NOT NULL DEFAULT 0.0,
                seniority_level TEXT,
                domain_signals_json TEXT NOT NULL DEFAULT '[]',
                responsibility_scope TEXT,
                ownership_signals_json TEXT NOT NULL DEFAULT '[]',
                impact_signals_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_profile_features_strength
            ON subscriber_profile_features (profile_strength_score DESC, updated_at DESC)
            """
        )


def _ensure_job_interaction_memory_migrations(connection: sqlite3.Connection) -> None:
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_job_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL,
                api_job_id INTEGER NOT NULL,
                job_kind TEXT NOT NULL CHECK (job_kind IN ('legacy', 'canonical')),
                canonical_job_id INTEGER,
                legacy_job_id INTEGER,
                impression_count INTEGER NOT NULL DEFAULT 0,
                open_count INTEGER NOT NULL DEFAULT 0,
                save_count INTEGER NOT NULL DEFAULT 0,
                apply_click_count INTEGER NOT NULL DEFAULT 0,
                total_dwell_seconds INTEGER NOT NULL DEFAULT 0,
                max_dwell_seconds INTEGER NOT NULL DEFAULT 0,
                affinity_score REAL NOT NULL DEFAULT 0.0,
                first_interacted_at TEXT NOT NULL,
                last_interacted_at TEXT NOT NULL,
                last_source_surface TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
                FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE,
                FOREIGN KEY (legacy_job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                UNIQUE (subscriber_id, api_job_id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_job_interactions_affinity
            ON subscriber_job_interactions (subscriber_id, affinity_score DESC, last_interacted_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_job_interactions_canonical
            ON subscriber_job_interactions (subscriber_id, canonical_job_id, affinity_score DESC)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_job_interaction_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL,
                api_job_id INTEGER NOT NULL,
                job_kind TEXT NOT NULL CHECK (job_kind IN ('legacy', 'canonical')),
                canonical_job_id INTEGER,
                legacy_job_id INTEGER,
                interaction_type TEXT NOT NULL CHECK (interaction_type IN ('impression', 'open', 'dwell', 'save', 'apply_click')),
                source_surface TEXT,
                dwell_seconds INTEGER,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
                FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE,
                FOREIGN KEY (legacy_job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_job_interaction_events_subscriber_time
            ON subscriber_job_interaction_events (subscriber_id, created_at DESC, id DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_job_interaction_events_canonical
            ON subscriber_job_interaction_events (subscriber_id, canonical_job_id, created_at DESC)
            """
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

def _ensure_job_corpus_expansion_migrations(connection: sqlite3.Connection) -> None:
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS job_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_name TEXT NOT NULL,
                account_slug TEXT NOT NULL DEFAULT '',
                base_url TEXT,
                trust_score REAL NOT NULL DEFAULT 0.5,
                country_scope TEXT,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (source_type, source_name, account_slug)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_sources_type_active
            ON job_sources (source_type, is_active, source_name)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS job_source_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                external_job_id TEXT NOT NULL,
                external_company_id TEXT,
                raw_payload_json TEXT NOT NULL,
                raw_payload_hash TEXT NOT NULL,
                canonical_url TEXT,
                title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                location_text TEXT,
                posted_at TEXT,
                apply_url TEXT,
                fetched_at TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                FOREIGN KEY (source_id) REFERENCES job_sources(id) ON DELETE CASCADE,
                UNIQUE (source_id, external_job_id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_source_records_source_active
            ON job_source_records (source_id, is_active, last_seen_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_source_records_payload_hash
            ON job_source_records (raw_payload_hash)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS canonical_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_key TEXT NOT NULL UNIQUE,
                normalized_title TEXT NOT NULL,
                normalized_company_name TEXT NOT NULL,
                display_title TEXT NOT NULL,
                display_company_name TEXT NOT NULL,
                location_city TEXT,
                district TEXT,
                country TEXT,
                workplace_type TEXT,
                employment_type TEXT,
                seniority TEXT,
                category TEXT,
                department TEXT,
                description_text TEXT,
                description_html TEXT,
                posted_at TEXT,
                apply_url TEXT NOT NULL,
                trust_score REAL NOT NULL DEFAULT 0.5,
                freshness_score REAL NOT NULL DEFAULT 0.5,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_jobs_active_updated_at
            ON canonical_jobs (is_active, updated_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_jobs_company_title
            ON canonical_jobs (normalized_company_name, normalized_title)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS canonical_job_links (
                canonical_job_id INTEGER NOT NULL,
                source_job_id INTEGER NOT NULL UNIQUE,
                merge_reason TEXT,
                confidence REAL NOT NULL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (canonical_job_id, source_job_id),
                FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE,
                FOREIGN KEY (source_job_id) REFERENCES job_source_records(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_job_links_canonical_job_id
            ON canonical_job_links (canonical_job_id, confidence DESC)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS canonical_job_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_job_id INTEGER NOT NULL UNIQUE,
                feature_version TEXT NOT NULL,
                role_family TEXT,
                job_discipline TEXT,
                department_family TEXT,
                title_tokens_json TEXT NOT NULL DEFAULT '[]',
                skill_terms_json TEXT NOT NULL DEFAULT '[]',
                location_tokens_json TEXT NOT NULL DEFAULT '[]',
                language_requirements_json TEXT NOT NULL DEFAULT '[]',
                education_level_hint TEXT,
                years_experience_min INTEGER,
                management_track INTEGER NOT NULL DEFAULT 0 CHECK (management_track IN (0, 1)),
                individual_contributor INTEGER NOT NULL DEFAULT 1 CHECK (individual_contributor IN (0, 1)),
                match_readiness_score REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (canonical_job_id) REFERENCES canonical_jobs(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_job_features_role_family
            ON canonical_job_features (role_family, job_discipline)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_job_features_match_readiness
            ON canonical_job_features (match_readiness_score DESC, updated_at DESC)
            """
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
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS retrieval_embedding_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                attempt_count INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                claimed_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (chunk_id) REFERENCES retrieval_chunks(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_retrieval_embedding_jobs_chunk_id
            ON retrieval_embedding_jobs (chunk_id, status, created_at, id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_retrieval_embedding_jobs_queue
            ON retrieval_embedding_jobs (provider, model, status, created_at, id)
            """
        )


def _ensure_job_external_context_migrations(connection: sqlite3.Connection) -> None:
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS job_external_context_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL UNIQUE,
                final_url TEXT,
                source_domain TEXT,
                fetch_status TEXT NOT NULL DEFAULT 'unavailable',
                http_status INTEGER,
                page_title TEXT,
                site_name TEXT,
                meta_description TEXT,
                clean_text TEXT NOT NULL DEFAULT '',
                content_digest TEXT,
                site_specific_requirements_json TEXT NOT NULL DEFAULT '[]',
                company_culture_clues_json TEXT NOT NULL DEFAULT '[]',
                responsibility_clues_json TEXT NOT NULL DEFAULT '[]',
                technology_stack_terms_json TEXT NOT NULL DEFAULT '[]',
                source_metadata_json TEXT NOT NULL DEFAULT '{}',
                warning TEXT,
                fetched_at TEXT,
                expires_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_external_context_snapshots_expires_at
            ON job_external_context_snapshots (expires_at, updated_at DESC, id DESC)
            """
        )


def init_db_schema(connection: sqlite3.Connection) -> None:
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)


def _ensure_google_oauth_migrations(connection: sqlite3.Connection) -> None:
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_oauth_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                email_at_provider TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
                UNIQUE (provider, provider_user_id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_oauth_providers_subscriber
            ON subscriber_oauth_providers (subscriber_id, provider)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_oauth_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_token_hash TEXT NOT NULL UNIQUE,
                redirect_path TEXT NOT NULL DEFAULT '',
                nonce TEXT NOT NULL DEFAULT '',
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_oauth_states_expires_at
            ON subscriber_oauth_states (expires_at)
            """
        )


def _ensure_matching_engine_v2_migrations(connection: sqlite3.Connection) -> None:
    """Add seniority and experience-evidence columns introduced in matching engine v2."""
    _ensure_column(
        connection,
        table_name="subscriber_profile_features",
        column_name="seniority_level",
        column_definition="TEXT",
    )


def _ensure_matching_engine_v3_migrations(connection: sqlite3.Connection) -> None:
    """Add required/preferred skill split, domain signals, and responsibility scope (v3)."""
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="required_skill_terms_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="preferred_skill_terms_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="domain_signals_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="responsibility_scope",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_profile_features",
        column_name="domain_signals_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )


def _ensure_matching_engine_v4_migrations(connection: sqlite3.Connection) -> None:
    """Add external job-intelligence columns to canonical job features (v4)."""
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="external_requirement_terms_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="external_technology_terms_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="external_responsibility_terms_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="external_context_status",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="canonical_job_features",
        column_name="external_context_updated_at",
        column_definition="TEXT",
    )




def _ensure_profile_certification_migrations(connection: sqlite3.Connection) -> None:
    """Create the generic subscriber certification table for CV-derived awards."""
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_certification_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL,
                certificate_name TEXT NOT NULL,
                issuer_name TEXT,
                issued_year INTEGER,
                file_name TEXT,
                storage_path TEXT,
                uploaded_at TEXT,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
                    ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_certification_entries_subscriber_id
            ON subscriber_certification_entries (subscriber_id, display_order, id)
            """
        )


def _ensure_matching_engine_v5_migrations(connection: sqlite3.Connection) -> None:
    """Add persisted profile-evidence columns introduced in matching engine v5."""
    _ensure_column(
        connection,
        table_name="subscriber_profile_features",
        column_name="experience_evidence_terms_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="subscriber_profile_features",
        column_name="responsibility_scope",
        column_definition="TEXT",
    )
    _ensure_column(
        connection,
        table_name="subscriber_profile_features",
        column_name="ownership_signals_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )
    _ensure_column(
        connection,
        table_name="subscriber_profile_features",
        column_name="impact_signals_json",
        column_definition="TEXT NOT NULL DEFAULT '[]'",
    )


def _ensure_query_performance_migrations(connection: sqlite3.Connection) -> None:
    """Create additive indexes for dashboard/list/queue read paths."""
    ensure_query_performance_indexes(connection)

def _ensure_user_notification_preferences_migrations(connection: sqlite3.Connection) -> None:
    """Create per-user communication preference table."""
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriber_notification_preferences (
                subscriber_id INTEGER PRIMARY KEY,
                product_updates_enabled INTEGER NOT NULL DEFAULT 0 CHECK (product_updates_enabled IN (0, 1)),
                employer_messages_enabled INTEGER NOT NULL DEFAULT 1 CHECK (employer_messages_enabled IN (0, 1)),
                security_alerts_enabled INTEGER NOT NULL DEFAULT 1 CHECK (security_alerts_enabled IN (0, 1)),
                quiet_hours_enabled INTEGER NOT NULL DEFAULT 0 CHECK (quiet_hours_enabled IN (0, 1)),
                quiet_hours_start TEXT NOT NULL DEFAULT '22:00',
                quiet_hours_end TEXT NOT NULL DEFAULT '08:00',
                timezone TEXT NOT NULL DEFAULT 'Europe/Istanbul',
                updated_at TEXT,
                FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_subscriber_notification_preferences_updated_at
            ON subscriber_notification_preferences (updated_at DESC, subscriber_id)
            """
        )

SQLITE_MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        identifier="2026_05_25_0001_subscriber_auth",
        description="Create and backfill subscriber authentication/session tables and columns.",
        run_always=True,
        handler=_ensure_subscriber_auth_migrations,
    ),
    Migration(
        identifier="2026_05_25_0002_profile_assets",
        description="Create profile asset tables and subscriber profile media columns.",
        run_always=True,
        handler=_ensure_profile_asset_migrations,
    ),
    Migration(
        identifier="2026_05_25_0003_retrieval",
        description="Create retrieval documents, chunks, embeddings, jobs, and health tables.",
        run_always=True,
        handler=_ensure_retrieval_migrations,
    ),
    Migration(
        identifier="2026_05_25_0004_copilot_ai",
        description="Create AI copilot conversation, audit, and recommendation tables.",
        run_always=True,
        handler=_ensure_copilot_ai_migrations,
    ),
    Migration(
        identifier="2026_05_25_0005_job_corpus_expansion",
        description="Create expanded canonical job corpus and source ingestion tables.",
        run_always=True,
        handler=_ensure_job_corpus_expansion_migrations,
    ),
    Migration(
        identifier="2026_05_25_0006_matching_engine_v1",
        description="Create persisted profile/job features and first matching engine support tables.",
        run_always=True,
        handler=_ensure_matching_engine_migrations,
    ),
    Migration(
        identifier="2026_05_25_0007_job_interaction_memory",
        description="Create subscriber job interaction memory and event tables.",
        run_always=True,
        handler=_ensure_job_interaction_memory_migrations,
    ),
    Migration(
        identifier="2026_05_25_0008_saved_jobs_api_reference",
        description="Migrate saved jobs to stable API job references and canonical/legacy metadata.",
        run_always=True,
        handler=_ensure_saved_jobs_api_reference_migration,
    ),
    Migration(
        identifier="2026_05_25_0009_job_external_context",
        description="Create external job context snapshot cache and feature context columns.",
        run_always=True,
        handler=_ensure_job_external_context_migrations,
    ),
    Migration(
        identifier="2026_05_25_0010_google_oauth",
        description="Create Google OAuth provider linking and OAuth state tables.",
        run_always=True,
        handler=_ensure_google_oauth_migrations,
    ),
    Migration(
        identifier="2026_05_25_0011_matching_engine_v2",
        description="Add seniority and experience evidence fields to subscriber features.",
        run_always=True,
        handler=_ensure_matching_engine_v2_migrations,
    ),
    Migration(
        identifier="2026_05_25_0012_matching_engine_v3",
        description="Add required/preferred skill split and domain signal columns.",
        run_always=True,
        handler=_ensure_matching_engine_v3_migrations,
    ),
    Migration(
        identifier="2026_05_25_0013_matching_engine_v4",
        description="Add external job intelligence fields to canonical job features.",
        run_always=True,
        handler=_ensure_matching_engine_v4_migrations,
    ),
    Migration(
        identifier="2026_05_25_0014_matching_engine_v5",
        description="Add persisted profile evidence, ownership, and impact signal columns.",
        run_always=True,
        handler=_ensure_matching_engine_v5_migrations,
    ),
    Migration(
        identifier="2026_05_25_0015_profile_certifications",
        description="Create generic subscriber certification entries for CV-derived awards.",
        run_always=True,
        handler=_ensure_profile_certification_migrations,
    ),
    Migration(
        identifier="2026_05_25_0016_query_performance_indexes",
        description="Create additive indexes for dashboard, saved-job, session, retrieval, and queue reads.",
        run_always=True,
        handler=_ensure_query_performance_migrations,
    ),
    Migration(
        identifier="2026_05_25_0017_user_notification_preferences",
        description="Create per-user notification and communication preference table.",
        run_always=True,
        handler=_ensure_user_notification_preferences_migrations,
    ),
)


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    configure_sqlite_runtime(connection)


def initialize_database(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(path),
        check_same_thread=False,
    )
    _configure_connection(connection)

    init_db_schema(connection)
    init_employer_schema(connection)
    run_migrations(connection, SQLITE_MIGRATIONS)

    return connection


def close_connection(connection: sqlite3.Connection | None) -> None:
    if connection is None:
        return

    connection.close()
