from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True, frozen=True)
class JobRecord:
    id: int | None = None
    source_name: str = ""
    title: str = ""
    company_name: str = ""
    location: str | None = None
    canonical_url: str = ""
    source_type: str = ""
    source_job_id: str | None = None
    raw_posted_at: str | None = None
    posted_at: str | None = None
    fingerprint: str = ""
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    is_active: bool = True
    scraped_at: str = ""


@dataclass(slots=True, frozen=True)
class JobSource:
    id: int | None = None
    source_type: str = ""
    source_name: str = ""
    account_slug: str = ""
    base_url: str | None = None
    trust_score: float = 0.5
    country_scope: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class JobSourceRecord:
    id: int | None = None
    source_id: int = 0
    external_job_id: str = ""
    external_company_id: str | None = None
    raw_payload_json: str = "{}"
    raw_payload_hash: str = ""
    canonical_url: str | None = None
    title: str = ""
    company_name: str = ""
    location_text: str | None = None
    posted_at: str | None = None
    apply_url: str | None = None
    fetched_at: str | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    is_active: bool = True


@dataclass(slots=True, frozen=True)
class CanonicalJob:
    id: int | None = None
    canonical_key: str = ""
    normalized_title: str = ""
    normalized_company_name: str = ""
    display_title: str = ""
    display_company_name: str = ""
    location_city: str | None = None
    district: str | None = None
    country: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    seniority: str | None = None
    category: str | None = None
    department: str | None = None
    description_text: str | None = None
    description_html: str | None = None
    posted_at: str | None = None
    apply_url: str = ""
    trust_score: float = 0.5
    freshness_score: float = 0.5
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class CanonicalJobLink:
    canonical_job_id: int = 0
    source_job_id: int = 0
    merge_reason: str | None = None
    confidence: float = 1.0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class CanonicalJobFeature:
    id: int | None = None
    canonical_job_id: int = 0
    feature_version: str = "v1"
    role_family: str | None = None
    job_discipline: str | None = None
    department_family: str | None = None
    title_tokens: tuple[str, ...] = ()
    skill_terms: tuple[str, ...] = ()
    required_skill_terms: tuple[str, ...] = ()
    preferred_skill_terms: tuple[str, ...] = ()
    external_requirement_terms: tuple[str, ...] = ()
    external_technology_terms: tuple[str, ...] = ()
    external_responsibility_terms: tuple[str, ...] = ()
    location_tokens: tuple[str, ...] = ()
    language_requirements: tuple[str, ...] = ()
    education_level_hint: str | None = None
    years_experience_min: int | None = None
    management_track: bool = False
    individual_contributor: bool = True
    domain_signals: tuple[str, ...] = ()
    responsibility_scope: str | None = None
    external_context_status: str | None = None
    external_context_updated_at: str | None = None
    match_readiness_score: float = 0.0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberProfileFeature:
    id: int | None = None
    subscriber_id: int = 0
    feature_version: str = "v1"
    role_families: tuple[str, ...] = ()
    discipline_preferences: tuple[str, ...] = ()
    title_tokens: tuple[str, ...] = ()
    skill_terms: tuple[str, ...] = ()
    experience_evidence_terms: tuple[str, ...] = ()
    preferred_location_tokens: tuple[str, ...] = ()
    language_capabilities: tuple[str, ...] = ()
    education_level: str | None = None
    years_experience_total: int | None = None
    remote_preference: str | None = None
    management_preference: bool | None = None
    profile_strength_score: float = 0.0
    seniority_level: str | None = None
    domain_signals: tuple[str, ...] = ()
    responsibility_scope: str | None = None
    ownership_signals: tuple[str, ...] = ()
    impact_signals: tuple[str, ...] = ()
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberJobInteraction:
    id: int | None = None
    subscriber_id: int = 0
    api_job_id: int = 0
    job_kind: Literal["legacy", "canonical"] = "canonical"
    canonical_job_id: int | None = None
    legacy_job_id: int | None = None
    impression_count: int = 0
    open_count: int = 0
    save_count: int = 0
    apply_click_count: int = 0
    total_dwell_seconds: int = 0
    max_dwell_seconds: int = 0
    affinity_score: float = 0.0
    first_interacted_at: str | None = None
    last_interacted_at: str | None = None
    last_source_surface: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberJobInteractionEvent:
    id: int | None = None
    subscriber_id: int = 0
    api_job_id: int = 0
    job_kind: Literal["legacy", "canonical"] = "canonical"
    canonical_job_id: int | None = None
    legacy_job_id: int | None = None
    interaction_type: Literal["impression", "open", "dwell", "save", "apply_click"] = "open"
    source_surface: str | None = None
    dwell_seconds: int | None = None
    metadata_json: str = "{}"
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class CrawlRun:
    id: int | None = None
    source_name: str = ""
    started_at: str = ""
    finished_at: str | None = None
    success: bool | None = None
    notes: str | None = None


@dataclass(slots=True, frozen=True)
class Subscriber:
    id: int | None = None
    email: str = ""
    full_name: str | None = None
    password_hash: str | None = None
    password_updated_at: str | None = None
    is_active: bool = True
    digest_enabled: bool = True
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberMagicLinkToken:
    id: int | None = None
    subscriber_id: int = 0
    token_hash: str = ""
    expires_at: str = ""
    consumed_at: str | None = None
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberSignupVerification:
    id: int | None = None
    email: str = ""
    full_name: str = ""
    password_hash: str = ""
    verification_code_hash: str = ""
    expires_at: str = ""
    consumed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberPasswordResetToken:
    id: int | None = None
    subscriber_id: int = 0
    token_hash: str = ""
    expires_at: str = ""
    consumed_at: str | None = None
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberKeywordPreference:
    subscriber_id: int = 0
    include_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    match_title: bool = True
    match_location: bool = True
    match_company_name: bool = True
    updated_at: str | None = None

    def active_fields(self) -> tuple[str, ...]:
        fields: list[str] = []
        if self.match_title:
            fields.append("title")
        if self.match_location:
            fields.append("location")
        if self.match_company_name:
            fields.append("company_name")
        return tuple(fields)

    def is_enabled(self) -> bool:
        return bool(self.include_keywords or self.exclude_keywords)


@dataclass(slots=True, frozen=True)
class SubscriberProfile:
    subscriber_id: int = 0
    phone: str | None = None
    headline: str | None = None
    summary: str | None = None
    target_roles: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()
    preferred_locations: tuple[str, ...] = ()
    remote_preference: str | None = None
    cv_filename: str | None = None
    cv_uploaded_at: str | None = None
    avatar_asset_id: str | None = None
    avatar_storage_path: str | None = None
    avatar_content_type: str | None = None
    avatar_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberEducationEntry:
    id: int | None = None
    subscriber_id: int = 0
    school_name: str = ""
    degree_name: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    display_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberExperienceEntry:
    id: int | None = None
    subscriber_id: int = 0
    title: str = ""
    company_name: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    summary: str | None = None
    display_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberProfileCompleteness:
    score: int = 0
    completed_items: tuple[str, ...] = ()
    missing_items: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class SubscriberLanguageEntry:
    id: int | None = None
    subscriber_id: int = 0
    language_name: str = ""
    proficiency_level: str | None = None
    notes: str | None = None
    display_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberLanguageCertificate:
    id: int | None = None
    subscriber_id: int = 0
    language_entry_id: int | None = None
    certificate_name: str = ""
    issuer_name: str | None = None
    file_name: str | None = None
    storage_path: str | None = None
    uploaded_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberCertificationEntry:
    id: int | None = None
    subscriber_id: int = 0
    certificate_name: str = ""
    issuer_name: str | None = None
    issued_year: int | None = None
    file_name: str | None = None
    storage_path: str | None = None
    uploaded_at: str | None = None
    display_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberSkillDetail:
    id: int | None = None
    subscriber_id: int = 0
    skill_name: str = ""
    skill_name_normalized: str = ""
    category: str | None = None
    proficiency_hint: str | None = None
    years_hint: int | None = None
    evidence_note: str | None = None
    evidence_file_name: str | None = None
    evidence_storage_path: str | None = None
    uploaded_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None




@dataclass(slots=True, frozen=True)
class SubscriberAiAuditLog:
    id: int | None = None
    subscriber_id: int = 0
    telemetry_ref: str | None = None
    target_field: str = ""
    target_entity_id: str | None = None
    action_type: str = "replace"
    source_panel: str | None = None
    before_snapshot_json: str = "null"
    after_snapshot_json: str = "null"
    persistence_status: str = "unsaved"
    evaluation_status: str | None = None
    evaluation_score: float | None = None
    manual_edit_distance: int | None = None
    request_ref: str | None = None
    metadata_json: str = "{}"
    created_at: str | None = None
    updated_at: str | None = None
    reverted_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberCvUpload:
    id: int | None = None
    subscriber_id: int = 0
    original_filename: str = ""
    storage_path: str = ""
    content_type: str | None = None
    file_size_bytes: int | None = None
    extracted_text: str | None = None
    parse_status: str = "pending"
    uploaded_at: str | None = None
    parsed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberCvParseRun:
    id: int | None = None
    subscriber_id: int = 0
    cv_upload_id: int = 0
    parser_version: str | None = None
    source_parse_status: str = "pending"
    snapshot_json: str = "{}"
    apply_status: str = "pending"
    applied_change_count: int = 0
    applied_at: str | None = None
    metadata_json: str = "{}"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberCvApplyAudit:
    id: int | None = None
    subscriber_id: int = 0
    parse_run_id: int = 0
    selected_operations_json: str = "{}"
    applied_operations_json: str = "{}"
    applied_change_count: int = 0
    resulting_apply_status: str = "pending"
    remaining_actionable_change_count: int = 0
    metadata_json: str = "{}"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class NotificationCheckpoint:
    checkpoint_key: str = ""
    last_processed_at: str = ""
    updated_at: str = ""


@dataclass(slots=True, frozen=True)
class NotificationRun:
    id: int | None = None
    notification_type: str = ""
    started_at: str = ""
    finished_at: str | None = None
    status: str = ""
    recipient_count: int = 0
    new_jobs_count: int = 0
    since: str | None = None
    subject: str | None = None
    error_message: str | None = None


@dataclass(slots=True, frozen=True)
class CrawlSourceResult:
    source_name: str = ""
    source_type: str = ""
    started_at: str = ""
    finished_at: str = ""
    success: bool = False
    total_parsed_jobs: int = 0
    new_jobs: int = 0
    updated_jobs: int = 0
    deactivated_jobs: int = 0
    crawl_run_id: int | None = None
    error_message: str | None = None


@dataclass(slots=True, frozen=True)
class RetrievalSource:
    id: int | None = None
    subscriber_id: int = 0
    source_type: str = ""
    source_ref: str = ""
    title: str | None = None
    locale: str | None = None
    status: str = "pending"
    checksum: str | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None
    last_ingested_at: str | None = None
    error_message: str | None = None


@dataclass(slots=True, frozen=True)
class RetrievalDocument:
    id: int | None = None
    source_id: int = 0
    document_kind: str = ""
    title: str | None = None
    body_text: str = ""
    metadata_json: dict[str, Any] = field(default_factory=dict)
    checksum: str | None = None
    status: str = "pending"
    version: int = 1
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class RetrievalChunk:
    id: int | None = None
    document_id: int = 0
    chunk_index: int = 0
    content: str = ""
    token_estimate: int | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)
    embedding_status: str = "pending"
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class RetrievalEmbedding:
    id: int | None = None
    chunk_id: int = 0
    provider: str = ""
    model: str = ""
    vector_ref: str | None = None
    vector_json: str | None = None
    dimensions: int | None = None
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class RetrievalSearchCandidate:
    chunk_id: int = 0
    document_id: int = 0
    source_id: int = 0
    subscriber_id: int = 0
    source_type: str = ""
    source_ref: str = ""
    source_title: str | None = None
    source_locale: str | None = None
    source_status: str = ""
    document_kind: str = ""
    document_title: str | None = None
    document_status: str = ""
    document_version: int = 1
    chunk_index: int = 0
    content: str = ""
    token_estimate: int | None = None
    chunk_metadata_json: dict[str, Any] = field(default_factory=dict)
    chunk_embedding_status: str = ""
    embedding_id: int | None = None
    embedding_provider: str = ""
    embedding_model: str = ""
    embedding_vector_json: str | None = None
    embedding_dimensions: int | None = None


@dataclass(slots=True, frozen=True)
class RetrievalEmbeddingJob:
    id: int | None = None
    chunk_id: int = 0
    provider: str = ""
    model: str = ""
    status: str = "queued"
    attempt_count: int = 0
    last_error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    claimed_at: str | None = None
    completed_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberAiCopilotConversation:
    id: int | None = None
    subscriber_id: int = 0
    title: str = ""
    locale: str | None = None
    status: str = "active"
    created_at: str | None = None
    updated_at: str | None = None
    last_message_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberAiCopilotMessage:
    id: int | None = None
    conversation_id: int = 0
    subscriber_id: int = 0
    role: str = "user"
    content: str = ""
    metadata_json: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class CareerKnowledgeDocument:
    id: int | None = None
    slug: str = ""
    title: str = ""
    category: str = "career"
    locale: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    trust_level: str = "curated"
    freshness_label: str = "foundation"
    body_text: str = ""
    metadata_json: dict[str, Any] = field(default_factory=dict)
    checksum: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberAiLearnedMemory:
    id: int | None = None
    subscriber_id: int = 0
    memory_key: str = ""
    memory_note: str = ""
    source_type: str = "conversation"
    confidence: float = 0.5
    times_reinforced: int = 1
    last_observed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class JobExternalContextSnapshot:
    id: int | None = None
    source_url: str = ""
    final_url: str | None = None
    source_domain: str | None = None
    fetch_status: str = "unavailable"
    http_status: int | None = None
    page_title: str | None = None
    site_name: str | None = None
    meta_description: str | None = None
    clean_text: str = ""
    content_digest: str | None = None
    site_specific_requirements: tuple[str, ...] = ()
    company_culture_clues: tuple[str, ...] = ()
    responsibility_clues: tuple[str, ...] = ()
    technology_stack_terms: tuple[str, ...] = ()
    source_metadata_json: dict[str, Any] = field(default_factory=dict)
    warning: str | None = None
    fetched_at: str | None = None
    expires_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberSavedJob:
    id: int | None = None
    subscriber_id: int = 0
    job_id: int = 0
    api_job_id: int | None = None
    status: str = "reviewing"
    match_score: int | None = None
    deadline_at: str | None = None
    interview_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberSavedJobNote:
    id: int | None = None
    saved_job_id: int = 0
    subscriber_id: int = 0
    content: str = ""
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberSession:
    id: int | None = None
    subscriber_id: int = 0
    session_token_hash: str = ""
    device_label: str = ""
    ip_address: str = ""
    user_agent: str = ""
    is_current: bool = False
    created_at: str | None = None
    last_active_at: str | None = None
    expired_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberLoginHistoryEntry:
    id: int | None = None
    subscriber_id: int = 0
    event_type: str = ""
    ip_address: str = ""
    user_agent: str = ""
    detail: str | None = None
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberEmailChangeRequest:
    id: int | None = None
    subscriber_id: int = 0
    new_email: str = ""
    verification_code_hash: str = ""
    expires_at: str = ""
    consumed_at: str | None = None
    created_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberTotpSecret:
    id: int | None = None
    subscriber_id: int = 0
    secret_encrypted: str = ""
    is_verified: bool = False
    created_at: str | None = None
    verified_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberOAuthProvider:
    id: int | None = None
    subscriber_id: int = 0
    provider: str = ""
    provider_user_id: str = ""
    email_at_provider: str = ""
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class SubscriberOAuthState:
    id: int | None = None
    state_token_hash: str = ""
    redirect_path: str = ""
    nonce: str = ""
    expires_at: str = ""
    created_at: str | None = None
