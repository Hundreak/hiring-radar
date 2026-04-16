from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
class SubscriberSavedJob:
    id: int | None = None
    subscriber_id: int = 0
    job_id: int = 0
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
