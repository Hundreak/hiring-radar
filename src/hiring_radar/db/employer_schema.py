from __future__ import annotations

import sqlite3

EMPLOYER_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS employer_companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        legal_name TEXT,
        website_url TEXT,
        industry TEXT,
        company_size TEXT,
        country TEXT,
        timezone TEXT NOT NULL DEFAULT 'Europe/Istanbul',
        default_locale TEXT NOT NULL DEFAULT 'tr',
        plan_tier TEXT NOT NULL DEFAULT 'starter',
        status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'archived')),
        brand_profile_json TEXT NOT NULL DEFAULT '{}',
        settings_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_companies_status
    ON employer_companies (status, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT,
        full_name TEXT NOT NULL,
        title TEXT,
        avatar_url TEXT,
        status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'disabled', 'deleted')),
        last_login_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_users_status
    ON employer_users (status, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        role_key TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        permissions_json TEXT NOT NULL DEFAULT '[]',
        is_system INTEGER NOT NULL DEFAULT 1 CHECK (is_system IN (0, 1)),
        risk_level TEXT NOT NULL DEFAULT 'medium' CHECK (risk_level IN ('low', 'medium', 'high')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        UNIQUE (company_id, role_key)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_roles_company
    ON employer_roles (company_id, role_key)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_team_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        user_id INTEGER,
        invited_email TEXT,
        role_key TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'disabled', 'removed')),
        invited_by_user_id INTEGER,
        invited_at TEXT,
        joined_at TEXT,
        last_active_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES employer_users(id) ON DELETE SET NULL,
        FOREIGN KEY (invited_by_user_id) REFERENCES employer_users(id) ON DELETE SET NULL,
        UNIQUE (company_id, user_id),
        UNIQUE (company_id, invited_email)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_team_members_company_status
    ON employer_team_members (company_id, status, role_key)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'paused', 'closed', 'archived')),
        location TEXT,
        work_model TEXT CHECK (work_model IN ('onsite', 'hybrid', 'remote')),
        employment_type TEXT,
        seniority TEXT,
        department TEXT,
        salary_min INTEGER,
        salary_max INTEGER,
        salary_currency TEXT NOT NULL DEFAULT 'TRY',
        description TEXT,
        required_skills_json TEXT NOT NULL DEFAULT '[]',
        preferred_skills_json TEXT NOT NULL DEFAULT '[]',
        quality_score INTEGER NOT NULL DEFAULT 0 CHECK (quality_score BETWEEN 0 AND 100),
        quality_factors_json TEXT NOT NULL DEFAULT '{}',
        risk_flags_json TEXT NOT NULL DEFAULT '[]',
        created_by_user_id INTEGER,
        published_at TEXT,
        closed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_user_id) REFERENCES employer_users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_jobs_company_status
    ON employer_jobs (company_id, status, updated_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_jobs_quality_score
    ON employer_jobs (company_id, quality_score DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        external_candidate_id TEXT,
        full_name TEXT NOT NULL,
        headline TEXT,
        email TEXT,
        phone TEXT,
        location TEXT,
        current_company TEXT,
        current_title TEXT,
        years_experience INTEGER,
        availability TEXT,
        source TEXT NOT NULL DEFAULT 'manual',
        salary_expectation_min INTEGER,
        salary_expectation_max INTEGER,
        salary_currency TEXT NOT NULL DEFAULT 'TRY',
        work_model_preference TEXT,
        match_score INTEGER NOT NULL DEFAULT 0 CHECK (match_score BETWEEN 0 AND 100),
        intent_score INTEGER NOT NULL DEFAULT 0 CHECK (intent_score BETWEEN 0 AND 100),
        profile_json TEXT NOT NULL DEFAULT '{}',
        skills_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        UNIQUE (company_id, external_candidate_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidates_company_scores
    ON employer_candidates (company_id, match_score DESC, intent_score DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidates_source
    ON employer_candidates (company_id, source, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_candidate_job_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        stage_key TEXT NOT NULL DEFAULT 'new',
        source TEXT NOT NULL DEFAULT 'radar',
        match_score INTEGER NOT NULL DEFAULT 0 CHECK (match_score BETWEEN 0 AND 100),
        intent_score INTEGER NOT NULL DEFAULT 0 CHECK (intent_score BETWEEN 0 AND 100),
        explanation_json TEXT NOT NULL DEFAULT '{}',
        is_archived INTEGER NOT NULL DEFAULT 0 CHECK (is_archived IN (0, 1)),
        last_activity_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES employer_jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES employer_candidates(id) ON DELETE CASCADE,
        UNIQUE (job_id, candidate_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidate_matches_stage
    ON employer_candidate_job_matches (company_id, stage_key, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_pipeline_stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        stage_key TEXT NOT NULL,
        name TEXT NOT NULL,
        position INTEGER NOT NULL,
        is_terminal INTEGER NOT NULL DEFAULT 0 CHECK (is_terminal IN (0, 1)),
        sla_days INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        UNIQUE (company_id, stage_key)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_pipeline_stages_position
    ON employer_pipeline_stages (company_id, position)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_candidate_stage_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        job_id INTEGER,
        from_stage_key TEXT,
        to_stage_key TEXT NOT NULL,
        changed_by_user_id INTEGER,
        note TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES employer_candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES employer_jobs(id) ON DELETE SET NULL,
        FOREIGN KEY (changed_by_user_id) REFERENCES employer_users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_stage_history_candidate
    ON employer_candidate_stage_history (company_id, candidate_id, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_candidate_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        author_user_id INTEGER,
        body TEXT NOT NULL,
        tone TEXT NOT NULL DEFAULT 'neutral',
        visibility TEXT NOT NULL DEFAULT 'team' CHECK (visibility IN ('private', 'team')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES employer_candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (author_user_id) REFERENCES employer_users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidate_notes_candidate
    ON employer_candidate_notes (company_id, candidate_id, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_candidate_tags (
        company_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        created_by_user_id INTEGER,
        created_at TEXT NOT NULL,
        PRIMARY KEY (company_id, candidate_id, tag),
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES employer_candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_user_id) REFERENCES employer_users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_candidate_tags_tag
    ON employer_candidate_tags (company_id, tag)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_outreach_campaigns (
        id TEXT PRIMARY KEY,
        company_id INTEGER NOT NULL,
        created_by_user_id INTEGER,
        name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'queued', 'sending', 'sent', 'paused', 'archived')),
        channel TEXT NOT NULL,
        tone TEXT,
        template_key TEXT,
        candidate_ids_json TEXT NOT NULL DEFAULT '[]',
        subject_preview TEXT,
        message_preview TEXT,
        response_rate INTEGER NOT NULL DEFAULT 0 CHECK (response_rate BETWEEN 0 AND 100),
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_user_id) REFERENCES employer_users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_outreach_campaigns_company_status
    ON employer_outreach_campaigns (company_id, status, updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_outreach_messages (
        id TEXT PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        candidate_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        response_score INTEGER NOT NULL DEFAULT 0 CHECK (response_score BETWEEN 0 AND 100),
        quality_score INTEGER NOT NULL DEFAULT 0 CHECK (quality_score BETWEEN 0 AND 100),
        status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'ready', 'review', 'blocked', 'sent')),
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES employer_outreach_campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES employer_candidates(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_outreach_messages_campaign
    ON employer_outreach_messages (campaign_id, status, response_score DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_send_queue_items (
        id TEXT PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        candidate_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        response_score INTEGER NOT NULL DEFAULT 0 CHECK (response_score BETWEEN 0 AND 100),
        status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('ready', 'review', 'blocked', 'sent', 'cancelled')),
        checks_json TEXT NOT NULL DEFAULT '[]',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        prepared_by_user_id INTEGER,
        prepared_at TEXT,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES employer_outreach_campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES employer_candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (prepared_by_user_id) REFERENCES employer_users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_send_queue_campaign_status
    ON employer_send_queue_items (campaign_id, status, response_score DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS employer_audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        actor_user_id INTEGER,
        event_type TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        before_json TEXT NOT NULL DEFAULT '{}',
        after_json TEXT NOT NULL DEFAULT '{}',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES employer_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (actor_user_id) REFERENCES employer_users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_employer_audit_events_company_created
    ON employer_audit_events (company_id, created_at DESC)
    """,
)


def init_employer_schema(connection: sqlite3.Connection) -> None:
    with connection:
        for statement in EMPLOYER_SCHEMA_STATEMENTS:
            connection.execute(statement)
