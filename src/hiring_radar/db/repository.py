from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Iterable
from typing import Any

from hiring_radar.models import (
    CanonicalJob,
    CanonicalJobFeature,
    CanonicalJobLink,
    CrawlRun,
    JobRecord,
    JobSource,
    JobSourceRecord,
    JobExternalContextSnapshot,
    NotificationCheckpoint,
    NotificationRun,
    Subscriber,
    SubscriberAiAuditLog,
    SubscriberAiCopilotConversation,
    SubscriberAiCopilotMessage,
    SubscriberAiLearnedMemory,
    SubscriberCvApplyAudit,
    SubscriberCvParseRun,
    SubscriberCvUpload,
    SubscriberCertificationEntry,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberKeywordPreference,
    SubscriberLanguageCertificate,
    SubscriberLanguageEntry,
    SubscriberMagicLinkToken,
    SubscriberPasswordResetToken,
    SubscriberSavedJob,
    SubscriberSavedJobNote,
    SubscriberSession,
    SubscriberLoginHistoryEntry,
    SubscriberEmailChangeRequest,
    SubscriberTotpSecret,
    SubscriberSignupVerification,
    SubscriberOAuthProvider,
    SubscriberOAuthState,
    SubscriberProfile,
    SubscriberProfileFeature,
    SubscriberJobInteraction,
    SubscriberJobInteractionEvent,
    SubscriberSkillDetail,
    CareerKnowledgeDocument,
    RetrievalChunk,
    RetrievalDocument,
    RetrievalEmbedding,
    RetrievalEmbeddingJob,
    RetrievalSearchCandidate,
    RetrievalSource,
)


def _row_to_job_record(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        id=row["id"],
        source_name=row["source_name"],
        title=row["title"],
        company_name=row["company_name"],
        location=row["location"],
        canonical_url=row["canonical_url"],
        source_type=row["source_type"],
        source_job_id=row["source_job_id"],
        raw_posted_at=row["raw_posted_at"],
        posted_at=row["posted_at"],
        fingerprint=row["fingerprint"],
        first_seen_at=row["first_seen_at"],
        last_seen_at=row["last_seen_at"],
        is_active=bool(row["is_active"]),
        scraped_at=row["scraped_at"],
    )


def _row_to_job_source(row: sqlite3.Row) -> JobSource:
    return JobSource(
        id=row["id"],
        source_type=row["source_type"],
        source_name=row["source_name"],
        account_slug=row["account_slug"],
        base_url=row["base_url"],
        trust_score=float(row["trust_score"]),
        country_scope=row["country_scope"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_job_source_record(row: sqlite3.Row) -> JobSourceRecord:
    return JobSourceRecord(
        id=row["id"],
        source_id=row["source_id"],
        external_job_id=row["external_job_id"],
        external_company_id=row["external_company_id"],
        raw_payload_json=row["raw_payload_json"],
        raw_payload_hash=row["raw_payload_hash"],
        canonical_url=row["canonical_url"],
        title=row["title"],
        company_name=row["company_name"],
        location_text=row["location_text"],
        posted_at=row["posted_at"],
        apply_url=row["apply_url"],
        fetched_at=row["fetched_at"],
        first_seen_at=row["first_seen_at"],
        last_seen_at=row["last_seen_at"],
        is_active=bool(row["is_active"]),
    )


def _row_to_canonical_job(row: sqlite3.Row) -> CanonicalJob:
    return CanonicalJob(
        id=row["id"],
        canonical_key=row["canonical_key"],
        normalized_title=row["normalized_title"],
        normalized_company_name=row["normalized_company_name"],
        display_title=row["display_title"],
        display_company_name=row["display_company_name"],
        location_city=row["location_city"],
        district=row["district"],
        country=row["country"],
        workplace_type=row["workplace_type"],
        employment_type=row["employment_type"],
        seniority=row["seniority"],
        category=row["category"],
        department=row["department"],
        description_text=row["description_text"],
        description_html=row["description_html"],
        posted_at=row["posted_at"],
        apply_url=row["apply_url"],
        trust_score=float(row["trust_score"]),
        freshness_score=float(row["freshness_score"]),
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_job_link(row: sqlite3.Row) -> CanonicalJobLink:
    return CanonicalJobLink(
        canonical_job_id=row["canonical_job_id"],
        source_job_id=row["source_job_id"],
        merge_reason=row["merge_reason"],
        confidence=float(row["confidence"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_job_feature(row: sqlite3.Row) -> CanonicalJobFeature:
    keys = row.keys()
    return CanonicalJobFeature(
        id=row["id"],
        canonical_job_id=row["canonical_job_id"],
        feature_version=row["feature_version"],
        role_family=row["role_family"],
        job_discipline=row["job_discipline"],
        department_family=row["department_family"],
        title_tokens=tuple(json.loads(row["title_tokens_json"] or "[]")),
        skill_terms=tuple(json.loads(row["skill_terms_json"] or "[]")),
        required_skill_terms=tuple(json.loads(row["required_skill_terms_json"] or "[]")) if "required_skill_terms_json" in keys else (),
        preferred_skill_terms=tuple(json.loads(row["preferred_skill_terms_json"] or "[]")) if "preferred_skill_terms_json" in keys else (),
        external_requirement_terms=tuple(json.loads(row["external_requirement_terms_json"] or "[]")) if "external_requirement_terms_json" in keys else (),
        external_technology_terms=tuple(json.loads(row["external_technology_terms_json"] or "[]")) if "external_technology_terms_json" in keys else (),
        external_responsibility_terms=tuple(json.loads(row["external_responsibility_terms_json"] or "[]")) if "external_responsibility_terms_json" in keys else (),
        location_tokens=tuple(json.loads(row["location_tokens_json"] or "[]")),
        language_requirements=tuple(json.loads(row["language_requirements_json"] or "[]")),
        education_level_hint=row["education_level_hint"],
        years_experience_min=row["years_experience_min"],
        management_track=bool(row["management_track"]),
        individual_contributor=bool(row["individual_contributor"]),
        domain_signals=tuple(json.loads(row["domain_signals_json"] or "[]")) if "domain_signals_json" in keys else (),
        responsibility_scope=row["responsibility_scope"] if "responsibility_scope" in keys else None,
        external_context_status=row["external_context_status"] if "external_context_status" in keys else None,
        external_context_updated_at=row["external_context_updated_at"] if "external_context_updated_at" in keys else None,
        match_readiness_score=float(row["match_readiness_score"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_profile_feature(row: sqlite3.Row) -> SubscriberProfileFeature:
    management_preference_value = row["management_preference"]
    keys = row.keys()
    return SubscriberProfileFeature(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        feature_version=row["feature_version"],
        role_families=tuple(json.loads(row["role_families_json"] or "[]")),
        discipline_preferences=tuple(json.loads(row["discipline_preferences_json"] or "[]")),
        title_tokens=tuple(json.loads(row["title_tokens_json"] or "[]")),
        skill_terms=tuple(json.loads(row["skill_terms_json"] or "[]")),
        experience_evidence_terms=(
            tuple(json.loads(row["experience_evidence_terms_json"] or "[]"))
            if "experience_evidence_terms_json" in keys else ()
        ),
        preferred_location_tokens=tuple(json.loads(row["preferred_location_tokens_json"] or "[]")),
        language_capabilities=tuple(json.loads(row["language_capabilities_json"] or "[]")),
        education_level=row["education_level"],
        years_experience_total=row["years_experience_total"],
        remote_preference=row["remote_preference"],
        management_preference=(
            None if management_preference_value is None else bool(management_preference_value)
        ),
        profile_strength_score=float(row["profile_strength_score"]),
        seniority_level=row["seniority_level"] if "seniority_level" in keys else None,
        domain_signals=tuple(json.loads(row["domain_signals_json"] or "[]")) if "domain_signals_json" in keys else (),
        responsibility_scope=row["responsibility_scope"] if "responsibility_scope" in keys else None,
        ownership_signals=(
            tuple(json.loads(row["ownership_signals_json"] or "[]"))
            if "ownership_signals_json" in keys else ()
        ),
        impact_signals=(
            tuple(json.loads(row["impact_signals_json"] or "[]"))
            if "impact_signals_json" in keys else ()
        ),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_job_interaction(row: sqlite3.Row) -> SubscriberJobInteraction:
    return SubscriberJobInteraction(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        api_job_id=row["api_job_id"],
        job_kind=row["job_kind"],
        canonical_job_id=row["canonical_job_id"],
        legacy_job_id=row["legacy_job_id"],
        impression_count=row["impression_count"],
        open_count=row["open_count"],
        save_count=row["save_count"],
        apply_click_count=row["apply_click_count"],
        total_dwell_seconds=row["total_dwell_seconds"],
        max_dwell_seconds=row["max_dwell_seconds"],
        affinity_score=float(row["affinity_score"]),
        first_interacted_at=row["first_interacted_at"],
        last_interacted_at=row["last_interacted_at"],
        last_source_surface=row["last_source_surface"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_job_interaction_event(
    row: sqlite3.Row,
) -> SubscriberJobInteractionEvent:
    return SubscriberJobInteractionEvent(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        api_job_id=row["api_job_id"],
        job_kind=row["job_kind"],
        canonical_job_id=row["canonical_job_id"],
        legacy_job_id=row["legacy_job_id"],
        interaction_type=row["interaction_type"],
        source_surface=row["source_surface"],
        dwell_seconds=row["dwell_seconds"],
        metadata_json=row["metadata_json"],
        created_at=row["created_at"],
    )


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def _compute_behavioral_affinity_score(
    *,
    impression_count: int,
    open_count: int,
    save_count: int,
    apply_click_count: int,
    total_dwell_seconds: int,
) -> float:
    impression_signal = min(0.06, math.log1p(max(0, impression_count)) * 0.016)
    open_signal = min(0.40, math.log1p(max(0, open_count)) * 0.18)
    save_signal = min(0.24, math.log1p(max(0, save_count)) * 0.16)
    apply_signal = min(0.18, math.log1p(max(0, apply_click_count)) * 0.13)
    dwell_units = max(0, total_dwell_seconds) / 30.0
    dwell_signal = min(0.22, math.log1p(dwell_units) * 0.085)
    return round(
        _clamp_score(
            impression_signal
            + open_signal
            + save_signal
            + apply_signal
            + dwell_signal
        ),
        4,
    )


def _row_to_crawl_run(row: sqlite3.Row) -> CrawlRun:
    success_value = row["success"]
    success = None if success_value is None else bool(success_value)

    return CrawlRun(
        id=row["id"],
        source_name=row["source_name"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        success=success,
        notes=row["notes"],
    )


def _row_to_subscriber(row: sqlite3.Row) -> Subscriber:
    return Subscriber(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        password_hash=row["password_hash"],
        password_updated_at=row["password_updated_at"],
        is_active=bool(row["is_active"]),
        digest_enabled=bool(row["digest_enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )



def _row_to_subscriber_signup_verification(
    row: sqlite3.Row,
) -> SubscriberSignupVerification:
    return SubscriberSignupVerification(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        password_hash=row["password_hash"],
        verification_code_hash=row["verification_code_hash"],
        expires_at=row["expires_at"],
        consumed_at=row["consumed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_password_reset_token(
    row: sqlite3.Row,
) -> SubscriberPasswordResetToken:
    return SubscriberPasswordResetToken(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        token_hash=row["token_hash"],
        expires_at=row["expires_at"],
        consumed_at=row["consumed_at"],
        created_at=row["created_at"],
    )


def _row_to_subscriber_keyword_preference(
    row: sqlite3.Row,
) -> SubscriberKeywordPreference:
    include_keywords_raw = row["include_keywords_json"] or "[]"
    exclude_keywords_raw = row["exclude_keywords_json"] or "[]"

    include_keywords = tuple(json.loads(include_keywords_raw))
    exclude_keywords = tuple(json.loads(exclude_keywords_raw))

    return SubscriberKeywordPreference(
        subscriber_id=row["subscriber_id"],
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        match_title=bool(row["match_title"]),
        match_location=bool(row["match_location"]),
        match_company_name=bool(row["match_company_name"]),
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_profile(row: sqlite3.Row) -> SubscriberProfile:
    target_roles_raw = row["target_roles_json"] or "[]"
    skills_raw = row["skills_json"] or "[]"
    preferred_locations_raw = row["preferred_locations_json"] or "[]"

    return SubscriberProfile(
        subscriber_id=row["subscriber_id"],
        phone=row["phone"],
        headline=row["headline"],
        summary=row["summary"],
        target_roles=tuple(json.loads(target_roles_raw)),
        skills=tuple(json.loads(skills_raw)),
        preferred_locations=tuple(json.loads(preferred_locations_raw)),
        remote_preference=row["remote_preference"],
        cv_filename=row["cv_filename"],
        cv_uploaded_at=row["cv_uploaded_at"],
        avatar_asset_id=row["avatar_asset_id"],
        avatar_storage_path=row["avatar_storage_path"],
        avatar_content_type=row["avatar_content_type"],
        avatar_url=row["avatar_url"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_education_entry(
    row: sqlite3.Row,
) -> SubscriberEducationEntry:
    return SubscriberEducationEntry(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        school_name=row["school_name"],
        degree_name=row["degree_name"],
        field_of_study=row["field_of_study"],
        start_year=row["start_year"],
        end_year=row["end_year"],
        display_order=row["display_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_experience_entry(
    row: sqlite3.Row,
) -> SubscriberExperienceEntry:
    return SubscriberExperienceEntry(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        title=row["title"],
        company_name=row["company_name"],
        start_year=row["start_year"],
        end_year=row["end_year"],
        summary=row["summary"],
        display_order=row["display_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_language_entry(
    row: sqlite3.Row,
) -> SubscriberLanguageEntry:
    return SubscriberLanguageEntry(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        language_name=row["language_name"],
        proficiency_level=row["proficiency_level"],
        notes=row["notes"],
        display_order=row["display_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_language_certificate(
    row: sqlite3.Row,
) -> SubscriberLanguageCertificate:
    return SubscriberLanguageCertificate(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        language_entry_id=row["language_entry_id"],
        certificate_name=row["certificate_name"],
        issuer_name=row["issuer_name"],
        file_name=row["file_name"],
        storage_path=row["storage_path"],
        uploaded_at=row["uploaded_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_certification_entry(
    row: sqlite3.Row,
) -> SubscriberCertificationEntry:
    return SubscriberCertificationEntry(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        certificate_name=row["certificate_name"],
        issuer_name=row["issuer_name"],
        issued_year=row["issued_year"],
        file_name=row["file_name"],
        storage_path=row["storage_path"],
        uploaded_at=row["uploaded_at"],
        display_order=row["display_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_skill_detail(
    row: sqlite3.Row,
) -> SubscriberSkillDetail:
    return SubscriberSkillDetail(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        skill_name=row["skill_name"],
        skill_name_normalized=row["skill_name_normalized"],
        category=row["category"],
        proficiency_hint=row["proficiency_hint"],
        years_hint=row["years_hint"],
        evidence_note=row["evidence_note"],
        evidence_file_name=row["evidence_file_name"],
        evidence_storage_path=row["evidence_storage_path"],
        uploaded_at=row["uploaded_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

def _row_to_subscriber_ai_audit_log(
    row: sqlite3.Row,
) -> SubscriberAiAuditLog:
    return SubscriberAiAuditLog(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        telemetry_ref=row["telemetry_ref"],
        target_field=row["target_field"],
        target_entity_id=row["target_entity_id"],
        action_type=row["action_type"],
        source_panel=row["source_panel"],
        before_snapshot_json=row["before_snapshot_json"],
        after_snapshot_json=row["after_snapshot_json"],
        persistence_status=row["persistence_status"],
        evaluation_status=row["evaluation_status"],
        evaluation_score=row["evaluation_score"],
        manual_edit_distance=row["manual_edit_distance"],
        request_ref=row["request_ref"],
        metadata_json=row["metadata_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        reverted_at=row["reverted_at"],
    )


def _row_to_subscriber_cv_upload(row: sqlite3.Row) -> SubscriberCvUpload:
    return SubscriberCvUpload(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        original_filename=row["original_filename"],
        storage_path=row["storage_path"],
        content_type=row["content_type"],
        file_size_bytes=row["file_size_bytes"],
        extracted_text=row["extracted_text"],
        parse_status=row["parse_status"],
        uploaded_at=row["uploaded_at"],
        parsed_at=row["parsed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_cv_parse_run(row: sqlite3.Row) -> SubscriberCvParseRun:
    """Map a SQLite row to a subscriber CV parse run entity.

    Args:
        row: SQLite row returned from the subscriber_cv_parse_runs table.

    Returns:
        The mapped parse run entity.
    """
    return SubscriberCvParseRun(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        cv_upload_id=row["cv_upload_id"],
        parser_version=row["parser_version"],
        source_parse_status=row["source_parse_status"],
        snapshot_json=row["snapshot_json"],
        metadata_json=row["metadata_json"],
        apply_status=row["apply_status"],
        applied_change_count=row["applied_change_count"],
        applied_at=row["applied_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

def _row_to_subscriber_cv_apply_audit(row: sqlite3.Row) -> SubscriberCvApplyAudit:
    """Map a SQLite row to a subscriber CV apply audit entity.

    Args:
        row: SQLite row returned from the subscriber_cv_apply_audits table.

    Returns:
        The mapped apply audit entity.
    """
    return SubscriberCvApplyAudit(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        parse_run_id=row["parse_run_id"],
        selected_operations_json=row["selected_operations_json"],
        applied_operations_json=row["applied_operations_json"],
        metadata_json=row["metadata_json"],
        applied_change_count=row["applied_change_count"],
        resulting_apply_status=row["resulting_apply_status"],
        remaining_actionable_change_count=row["remaining_actionable_change_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

def _row_to_retrieval_source(row: sqlite3.Row) -> RetrievalSource:
    metadata_raw = row["metadata_json"] or "{}"

    return RetrievalSource(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        source_type=row["source_type"],
        source_ref=row["source_ref"],
        title=row["title"],
        locale=row["locale"],
        status=row["status"],
        checksum=row["checksum"],
        metadata_json=json.loads(metadata_raw),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_ingested_at=row["last_ingested_at"],
        error_message=row["error_message"],
    )


def _row_to_retrieval_document(row: sqlite3.Row) -> RetrievalDocument:
    metadata_raw = row["metadata_json"] or "{}"

    return RetrievalDocument(
        id=row["id"],
        source_id=row["source_id"],
        document_kind=row["document_kind"],
        title=row["title"],
        body_text=row["body_text"],
        metadata_json=json.loads(metadata_raw),
        checksum=row["checksum"],
        status=row["status"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_retrieval_chunk(row: sqlite3.Row) -> RetrievalChunk:
    metadata_raw = row["metadata_json"] or "{}"

    return RetrievalChunk(
        id=row["id"],
        document_id=row["document_id"],
        chunk_index=row["chunk_index"],
        content=row["content"],
        token_estimate=row["token_estimate"],
        metadata_json=json.loads(metadata_raw),
        embedding_status=row["embedding_status"],
        created_at=row["created_at"],
    )


def _row_to_retrieval_embedding(row: sqlite3.Row) -> RetrievalEmbedding:
    return RetrievalEmbedding(
        id=row["id"],
        chunk_id=row["chunk_id"],
        provider=row["provider"],
        model=row["model"],
        vector_ref=row["vector_ref"],
        vector_json=row["vector_json"],
        dimensions=row["dimensions"],
        created_at=row["created_at"],
    )


def _row_to_subscriber_ai_copilot_conversation(
    row: sqlite3.Row,
) -> SubscriberAiCopilotConversation:
    return SubscriberAiCopilotConversation(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        title=row["title"],
        locale=row["locale"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_message_at=row["last_message_at"],
    )


def _row_to_subscriber_ai_copilot_message(
    row: sqlite3.Row,
) -> SubscriberAiCopilotMessage:
    metadata_json = row["metadata_json"]
    return SubscriberAiCopilotMessage(
        id=row["id"],
        conversation_id=row["conversation_id"],
        subscriber_id=row["subscriber_id"],
        role=row["role"],
        content=row["content"],
        metadata_json=json.loads(metadata_json) if metadata_json else {},
        created_at=row["created_at"],
    )


def _row_to_career_knowledge_document(row: sqlite3.Row) -> CareerKnowledgeDocument:
    metadata_json = row["metadata_json"]
    return CareerKnowledgeDocument(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        category=row["category"],
        locale=row["locale"],
        source_name=row["source_name"],
        source_url=row["source_url"],
        trust_level=row["trust_level"],
        freshness_label=row["freshness_label"],
        body_text=row["body_text"],
        metadata_json=json.loads(metadata_json) if metadata_json else {},
        checksum=row["checksum"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_subscriber_ai_learned_memory(row: sqlite3.Row) -> SubscriberAiLearnedMemory:
    return SubscriberAiLearnedMemory(
        id=row["id"],
        subscriber_id=row["subscriber_id"],
        memory_key=row["memory_key"],
        memory_note=row["memory_note"],
        source_type=row["source_type"],
        confidence=float(row["confidence"]),
        times_reinforced=int(row["times_reinforced"]),
        last_observed_at=row["last_observed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_job_external_context_snapshot(row: sqlite3.Row) -> JobExternalContextSnapshot:
    metadata_raw = row["source_metadata_json"] or "{}"
    return JobExternalContextSnapshot(
        id=row["id"],
        source_url=row["source_url"],
        final_url=row["final_url"],
        source_domain=row["source_domain"],
        fetch_status=row["fetch_status"],
        http_status=row["http_status"],
        page_title=row["page_title"],
        site_name=row["site_name"],
        meta_description=row["meta_description"],
        clean_text=row["clean_text"] or "",
        content_digest=row["content_digest"],
        site_specific_requirements=tuple(json.loads(row["site_specific_requirements_json"] or "[]")),
        company_culture_clues=tuple(json.loads(row["company_culture_clues_json"] or "[]")),
        responsibility_clues=tuple(json.loads(row["responsibility_clues_json"] or "[]")),
        technology_stack_terms=tuple(json.loads(row["technology_stack_terms_json"] or "[]")),
        source_metadata_json=json.loads(metadata_raw),
        warning=row["warning"],
        fetched_at=row["fetched_at"],
        expires_at=row["expires_at"],
        updated_at=row["updated_at"],
    )


def _row_to_notification_checkpoint(row: sqlite3.Row) -> NotificationCheckpoint:
    return NotificationCheckpoint(
        checkpoint_key=row["checkpoint_key"],
        last_processed_at=row["last_processed_at"],
        updated_at=row["updated_at"],
    )


def _row_to_notification_run(row: sqlite3.Row) -> NotificationRun:
    return NotificationRun(
        id=row["id"],
        notification_type=row["notification_type"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        status=row["status"],
        recipient_count=int(row["recipient_count"]),
        new_jobs_count=int(row["new_jobs_count"]),
        since=row["since"],
        subject=row["subject"],
        error_message=row["error_message"],
    )


def _row_to_retrieval_embedding_job(row: sqlite3.Row) -> RetrievalEmbeddingJob:
    return RetrievalEmbeddingJob(
        id=row["id"],
        chunk_id=row["chunk_id"],
        provider=row["provider"],
        model=row["model"],
        status=row["status"],
        attempt_count=row["attempt_count"],
        last_error=row["last_error"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        claimed_at=row["claimed_at"],
        completed_at=row["completed_at"],
    )




def _row_to_retrieval_search_candidate(row: sqlite3.Row) -> RetrievalSearchCandidate:
    chunk_metadata_raw = row["chunk_metadata_json"] or "{}"

    return RetrievalSearchCandidate(
        chunk_id=row["chunk_id"],
        document_id=row["document_id"],
        source_id=row["source_id"],
        subscriber_id=row["subscriber_id"],
        source_type=row["source_type"],
        source_ref=row["source_ref"],
        source_title=row["source_title"],
        source_locale=row["source_locale"],
        source_status=row["source_status"],
        document_kind=row["document_kind"],
        document_title=row["document_title"],
        document_status=row["document_status"],
        document_version=row["document_version"],
        chunk_index=row["chunk_index"],
        content=row["chunk_content"],
        token_estimate=row["token_estimate"],
        chunk_metadata_json=json.loads(chunk_metadata_raw),
        chunk_embedding_status=row["chunk_embedding_status"],
        embedding_id=row["embedding_id"],
        embedding_provider=row["embedding_provider"],
        embedding_model=row["embedding_model"],
        embedding_vector_json=row["embedding_vector_json"],
        embedding_dimensions=row["embedding_dimensions"],
    )




class HiringRadarRepository:
    """
    Persistence layer for crawl runs, normalized jobs, and subscribers.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def start_crawl_run(self, source_name: str, started_at: str) -> int:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO crawl_runs (started_at, source_name)
                VALUES (?, ?)
                """,
                (started_at, source_name),
            )

        return int(cursor.lastrowid)

    def finish_crawl_run(
        self,
        run_id: int,
        finished_at: str,
        success: bool,
        notes: str | None = None,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE crawl_runs
                SET finished_at = ?, success = ?, notes = ?
                WHERE id = ?
                """,
                (finished_at, int(success), notes, run_id),
            )

    def get_crawl_run(self, run_id: int) -> CrawlRun | None:
        cursor = self.connection.execute(
            """
            SELECT id, started_at, finished_at, source_name, success, notes
            FROM crawl_runs
            WHERE id = ?
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_crawl_run(row)

    def get_job_by_id(self, job_id: int) -> JobRecord | None:
        cursor = self.connection.execute(
            """
            SELECT
                id, source_name, title, company_name, location,
                canonical_url, source_type, source_job_id,
                raw_posted_at, posted_at, fingerprint,
                first_seen_at, last_seen_at, is_active, scraped_at
            FROM jobs
            WHERE id = ?
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_job_record(row)

    def get_job_by_fingerprint(self, fingerprint: str) -> JobRecord | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                source_name,
                title,
                company_name,
                location,
                canonical_url,
                source_type,
                source_job_id,
                raw_posted_at,
                posted_at,
                fingerprint,
                first_seen_at,
                last_seen_at,
                is_active,
                scraped_at
            FROM jobs
            WHERE fingerprint = ?
            """,
            (fingerprint,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_job_record(row)

    def list_jobs(self, source_name: str | None = None) -> list[JobRecord]:
        """
        List all stored jobs, including inactive records.

        This method is intended for export and reporting flows, so it returns
        the full dataset rather than only active jobs.
        """
        if source_name is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                ORDER BY company_name, source_name, title, canonical_url
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE source_name = ?
                ORDER BY company_name, source_name, title, canonical_url
                """,
                (source_name,),
            )

        rows = cursor.fetchall()
        return [_row_to_job_record(row) for row in rows]

    def get_job_counts(self) -> dict[str, int]:
        """
        Return overall job counts for summary/reporting flows.
        """
        cursor = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_jobs,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_jobs,
                COALESCE(SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END), 0) AS inactive_jobs
            FROM jobs
            """
        )
        row = cursor.fetchone()

        if row is None:
            return {
                "total_jobs": 0,
                "active_jobs": 0,
                "inactive_jobs": 0,
            }

        return {
            "total_jobs": int(row["total_jobs"]),
            "active_jobs": int(row["active_jobs"]),
            "inactive_jobs": int(row["inactive_jobs"]),
        }

    def get_source_summary_rows(self) -> list[dict[str, Any]]:
        """
        Return aggregated summary rows grouped by source.
        """
        cursor = self.connection.execute(
            """
            SELECT
                source_name,
                source_type,
                COUNT(*) AS total_jobs,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_jobs,
                COALESCE(SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END), 0) AS inactive_jobs
            FROM jobs
            GROUP BY source_name, source_type
            ORDER BY source_name, source_type
            """
        )
        rows = cursor.fetchall()

        return [
            {
                "source_name": row["source_name"],
                "source_type": row["source_type"],
                "total_jobs": int(row["total_jobs"]),
                "active_jobs": int(row["active_jobs"]),
                "inactive_jobs": int(row["inactive_jobs"]),
            }
            for row in rows
        ]

    def get_company_summary_rows(self) -> list[dict[str, Any]]:
        """
        Return aggregated summary rows grouped by company.
        """
        cursor = self.connection.execute(
            """
            SELECT
                company_name,
                COUNT(*) AS total_jobs,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_jobs,
                COALESCE(SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END), 0) AS inactive_jobs
            FROM jobs
            GROUP BY company_name
            ORDER BY company_name
            """
        )
        rows = cursor.fetchall()

        return [
            {
                "company_name": row["company_name"],
                "total_jobs": int(row["total_jobs"]),
                "active_jobs": int(row["active_jobs"]),
                "inactive_jobs": int(row["inactive_jobs"]),
            }
            for row in rows
        ]

    def list_jobs_first_seen_since(
        self,
        since: str,
        source_name: str | None = None,
    ) -> list[JobRecord]:
        """
        List jobs whose first_seen_at is greater than or equal to `since`.

        Notes:
        - This is intended for digest/notification flows.
        - It returns jobs regardless of active/inactive status because the
          first digest iteration focuses on "newly discovered" postings.
        """
        if source_name is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE first_seen_at >= ?
                ORDER BY first_seen_at, company_name, source_name, title, canonical_url
                """,
                (since,),
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE first_seen_at >= ? AND source_name = ?
                ORDER BY first_seen_at, company_name, source_name, title, canonical_url
                """,
                (since, source_name),
            )

        rows = cursor.fetchall()
        return [_row_to_job_record(row) for row in rows]

    def get_notification_checkpoint(
        self,
        checkpoint_key: str,
    ) -> NotificationCheckpoint | None:
        cursor = self.connection.execute(
            """
            SELECT
                checkpoint_key,
                last_processed_at,
                updated_at
            FROM notification_checkpoints
            WHERE checkpoint_key = ?
            """,
            (checkpoint_key,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_notification_checkpoint(row)

    def start_notification_run(
        self,
        *,
        notification_type: str,
        started_at: str,
        since: str | None,
    ) -> int:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO notification_runs (
                    notification_type,
                    started_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_type,
                    started_at,
                    "running",
                    0,
                    0,
                    since,
                ),
            )

        return int(cursor.lastrowid)

    def finish_notification_run(
        self,
        run_id: int,
        *,
        finished_at: str,
        status: str,
        recipient_count: int = 0,
        new_jobs_count: int = 0,
        subject: str | None = None,
        error_message: str | None = None,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE notification_runs
                SET
                    finished_at = ?,
                    status = ?,
                    recipient_count = ?,
                    new_jobs_count = ?,
                    subject = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    subject,
                    error_message,
                    run_id,
                ),
            )

        return cursor.rowcount > 0

    def get_notification_run(self, run_id: int) -> NotificationRun | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                notification_type,
                started_at,
                finished_at,
                status,
                recipient_count,
                new_jobs_count,
                since,
                subject,
                error_message
            FROM notification_runs
            WHERE id = ?
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_notification_run(row)

    def list_notification_runs(
        self,
        *,
        notification_type: str | None = None,
        limit: int = 50,
    ) -> list[NotificationRun]:
        if notification_type is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                WHERE notification_type = ?
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (notification_type, limit),
            )

        rows = cursor.fetchall()
        return [_row_to_notification_run(row) for row in rows]

    def get_latest_crawl_run(self) -> CrawlRun | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                started_at,
                finished_at,
                source_name,
                success,
                notes
            FROM crawl_runs
            ORDER BY started_at DESC, id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_crawl_run(row)

    def get_latest_notification_run(
        self,
        *,
        notification_type: str | None = None,
    ) -> NotificationRun | None:
        if notification_type is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    notification_type,
                    started_at,
                    finished_at,
                    status,
                    recipient_count,
                    new_jobs_count,
                    since,
                    subject,
                    error_message
                FROM notification_runs
                WHERE notification_type = ?
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """,
                (notification_type,),
            )

        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_notification_run(row)

    def get_subscriber_counts(self) -> dict[str, int]:
        cursor = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total_subscribers,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_subscribers,
                COALESCE(
                    SUM(CASE WHEN is_active = 1 AND digest_enabled = 1 THEN 1 ELSE 0 END),
                    0
                ) AS digest_enabled_subscribers
            FROM subscribers
            """
        )
        row = cursor.fetchone()

        if row is None:
            return {
                "total_subscribers": 0,
                "active_subscribers": 0,
                "digest_enabled_subscribers": 0,
            }

        return {
            "total_subscribers": int(row["total_subscribers"]),
            "active_subscribers": int(row["active_subscribers"]),
            "digest_enabled_subscribers": int(row["digest_enabled_subscribers"]),
        }

    def upsert_notification_checkpoint(
        self,
        *,
        checkpoint_key: str,
        last_processed_at: str,
        updated_at: str,
    ) -> NotificationCheckpoint:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO notification_checkpoints (
                    checkpoint_key,
                    last_processed_at,
                    updated_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(checkpoint_key) DO UPDATE SET
                    last_processed_at = excluded.last_processed_at,
                    updated_at = excluded.updated_at
                """,
                (
                    checkpoint_key,
                    last_processed_at,
                    updated_at,
                ),
            )

        checkpoint = self.get_notification_checkpoint(checkpoint_key)
        if checkpoint is None:
            raise RuntimeError(
                "Notification checkpoint upsert succeeded but record could not be reloaded."
            )

        return checkpoint

    def get_subscriber_by_email(self, email: str) -> Subscriber | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                password_hash,
                password_updated_at,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            WHERE email = ?
            """,
            (email,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_subscriber(row)

    def get_subscriber_keyword_preference(
        self,
        subscriber_id: int,
    ) -> SubscriberKeywordPreference:
        cursor = self.connection.execute(
            """
            SELECT
                subscriber_id,
                include_keywords_json,
                exclude_keywords_json,
                match_title,
                match_location,
                match_company_name,
                updated_at
            FROM subscriber_keyword_preferences
            WHERE subscriber_id = ?
            """,
            (subscriber_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return SubscriberKeywordPreference(
                subscriber_id=subscriber_id,
                include_keywords=(),
                exclude_keywords=(),
                match_title=True,
                match_location=True,
                match_company_name=True,
                updated_at=None,
            )

        return _row_to_subscriber_keyword_preference(row)

    def upsert_subscriber_keyword_preference(
        self,
        subscriber_id: int,
        *,
        include_keywords: tuple[str, ...],
        exclude_keywords: tuple[str, ...],
        match_title: bool,
        match_location: bool,
        match_company_name: bool,
        updated_at: str,
    ) -> SubscriberKeywordPreference:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_keyword_preferences (
                    subscriber_id,
                    include_keywords_json,
                    exclude_keywords_json,
                    match_title,
                    match_location,
                    match_company_name,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(subscriber_id) DO UPDATE SET
                    include_keywords_json = excluded.include_keywords_json,
                    exclude_keywords_json = excluded.exclude_keywords_json,
                    match_title = excluded.match_title,
                    match_location = excluded.match_location,
                    match_company_name = excluded.match_company_name,
                    updated_at = excluded.updated_at
                """,
                (
                    subscriber_id,
                    json.dumps(list(include_keywords)),
                    json.dumps(list(exclude_keywords)),
                    int(match_title),
                    int(match_location),
                    int(match_company_name),
                    updated_at,
                ),
            )

        return self.get_subscriber_keyword_preference(subscriber_id)

    def get_subscriber_profile(
        self,
        subscriber_id: int,
    ) -> SubscriberProfile:
        cursor = self.connection.execute(
            """
            SELECT
                subscriber_id,
                phone,
                headline,
                summary,
                target_roles_json,
                skills_json,
                preferred_locations_json,
                remote_preference,
                cv_filename,
                cv_uploaded_at,
                avatar_asset_id,
                avatar_storage_path,
                avatar_content_type,
                avatar_url,
                created_at,
                updated_at
            FROM subscriber_profiles
            WHERE subscriber_id = ?
            """,
            (subscriber_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return SubscriberProfile(subscriber_id=subscriber_id)

        return _row_to_subscriber_profile(row)

    def upsert_subscriber_profile(
        self,
        subscriber_id: int,
        *,
        phone: str | None,
        headline: str | None,
        summary: str | None,
        target_roles: tuple[str, ...],
        skills: tuple[str, ...],
        preferred_locations: tuple[str, ...],
        remote_preference: str | None,
        cv_filename: str | None,
        cv_uploaded_at: str | None,
        updated_at: str,
        avatar_asset_id: str | None = None,
        avatar_storage_path: str | None = None,
        avatar_content_type: str | None = None,
        avatar_url: str | None = None,
    ) -> SubscriberProfile:
        existing = self.get_subscriber_profile(subscriber_id)
        created_at = existing.created_at or updated_at
        resolved_avatar_asset_id = (
            avatar_asset_id if avatar_asset_id is not None else existing.avatar_asset_id
        )
        resolved_avatar_storage_path = (
            avatar_storage_path
            if avatar_storage_path is not None
            else existing.avatar_storage_path
        )
        resolved_avatar_content_type = (
            avatar_content_type
            if avatar_content_type is not None
            else existing.avatar_content_type
        )
        resolved_avatar_url = avatar_url if avatar_url is not None else existing.avatar_url

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_profiles (
                    subscriber_id,
                    phone,
                    headline,
                    summary,
                    target_roles_json,
                    skills_json,
                    preferred_locations_json,
                    remote_preference,
                    cv_filename,
                    cv_uploaded_at,
                    avatar_asset_id,
                    avatar_storage_path,
                    avatar_content_type,
                    avatar_url,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(subscriber_id) DO UPDATE SET
                    phone = excluded.phone,
                    headline = excluded.headline,
                    summary = excluded.summary,
                    target_roles_json = excluded.target_roles_json,
                    skills_json = excluded.skills_json,
                    preferred_locations_json = excluded.preferred_locations_json,
                    remote_preference = excluded.remote_preference,
                    cv_filename = excluded.cv_filename,
                    cv_uploaded_at = excluded.cv_uploaded_at,
                    avatar_asset_id = excluded.avatar_asset_id,
                    avatar_storage_path = excluded.avatar_storage_path,
                    avatar_content_type = excluded.avatar_content_type,
                    avatar_url = excluded.avatar_url,
                    updated_at = excluded.updated_at
                """,
                (
                    subscriber_id,
                    phone,
                    headline,
                    summary,
                    json.dumps(list(target_roles)),
                    json.dumps(list(skills)),
                    json.dumps(list(preferred_locations)),
                    remote_preference,
                    cv_filename,
                    cv_uploaded_at,
                    resolved_avatar_asset_id,
                    resolved_avatar_storage_path,
                    resolved_avatar_content_type,
                    resolved_avatar_url,
                    created_at,
                    updated_at,
                ),
            )

        return self.get_subscriber_profile(subscriber_id)

    def list_subscriber_education_entries(
        self,
        subscriber_id: int,
    ) -> list[SubscriberEducationEntry]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                school_name,
                degree_name,
                field_of_study,
                start_year,
                end_year,
                display_order,
                created_at,
                updated_at
            FROM subscriber_education_entries
            WHERE subscriber_id = ?
            ORDER BY display_order ASC, id ASC
            """,
            (subscriber_id,),
        )
        return [_row_to_subscriber_education_entry(row) for row in cursor.fetchall()]

    def replace_subscriber_education_entries(
        self,
        subscriber_id: int,
        *,
        entries: list[SubscriberEducationEntry],
        updated_at: str,
    ) -> list[SubscriberEducationEntry]:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM subscriber_education_entries
                WHERE subscriber_id = ?
                """,
                (subscriber_id,),
            )

            for index, entry in enumerate(entries):
                self.connection.execute(
                    """
                    INSERT INTO subscriber_education_entries (
                        subscriber_id,
                        school_name,
                        degree_name,
                        field_of_study,
                        start_year,
                        end_year,
                        display_order,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        entry.school_name,
                        entry.degree_name,
                        entry.field_of_study,
                        entry.start_year,
                        entry.end_year,
                        index,
                        updated_at,
                        updated_at,
                    ),
                )

        return self.list_subscriber_education_entries(subscriber_id)

    def list_subscriber_experience_entries(
        self,
        subscriber_id: int,
    ) -> list[SubscriberExperienceEntry]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                title,
                company_name,
                start_year,
                end_year,
                summary,
                display_order,
                created_at,
                updated_at
            FROM subscriber_experience_entries
            WHERE subscriber_id = ?
            ORDER BY display_order ASC, id ASC
            """,
            (subscriber_id,),
        )
        return [_row_to_subscriber_experience_entry(row) for row in cursor.fetchall()]

    def replace_subscriber_experience_entries(
        self,
        subscriber_id: int,
        *,
        entries: list[SubscriberExperienceEntry],
        updated_at: str,
    ) -> list[SubscriberExperienceEntry]:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM subscriber_experience_entries
                WHERE subscriber_id = ?
                """,
                (subscriber_id,),
            )

            for index, entry in enumerate(entries):
                self.connection.execute(
                    """
                    INSERT INTO subscriber_experience_entries (
                        subscriber_id,
                        title,
                        company_name,
                        start_year,
                        end_year,
                        summary,
                        display_order,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        entry.title,
                        entry.company_name,
                        entry.start_year,
                        entry.end_year,
                        entry.summary,
                        index,
                        updated_at,
                        updated_at,
                    ),
                )

        return self.list_subscriber_experience_entries(subscriber_id)

    def list_subscriber_language_entries(
        self,
        subscriber_id: int,
    ) -> list[SubscriberLanguageEntry]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                language_name,
                proficiency_level,
                notes,
                display_order,
                created_at,
                updated_at
            FROM subscriber_language_entries
            WHERE subscriber_id = ?
            ORDER BY display_order ASC, id ASC
            """,
            (subscriber_id,),
        )
        return [_row_to_subscriber_language_entry(row) for row in cursor.fetchall()]

    def replace_subscriber_language_entries(
        self,
        subscriber_id: int,
        *,
        entries: list[SubscriberLanguageEntry],
        updated_at: str,
    ) -> list[SubscriberLanguageEntry]:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM subscriber_language_entries
                WHERE subscriber_id = ?
                """,
                (subscriber_id,),
            )

            for index, entry in enumerate(entries):
                self.connection.execute(
                    """
                    INSERT INTO subscriber_language_entries (
                        subscriber_id,
                        language_name,
                        proficiency_level,
                        notes,
                        display_order,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        entry.language_name,
                        entry.proficiency_level,
                        entry.notes,
                        index,
                        updated_at,
                        updated_at,
                    ),
                )

        return self.list_subscriber_language_entries(subscriber_id)

    def list_subscriber_language_certificates(
        self,
        subscriber_id: int,
    ) -> list[SubscriberLanguageCertificate]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                language_entry_id,
                certificate_name,
                issuer_name,
                file_name,
                storage_path,
                uploaded_at,
                created_at,
                updated_at
            FROM subscriber_language_certificates
            WHERE subscriber_id = ?
            ORDER BY id ASC
            """,
            (subscriber_id,),
        )
        return [
            _row_to_subscriber_language_certificate(row)
            for row in cursor.fetchall()
        ]

    def replace_subscriber_language_certificates(
        self,
        subscriber_id: int,
        *,
        certificates: list[SubscriberLanguageCertificate],
        updated_at: str,
    ) -> list[SubscriberLanguageCertificate]:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM subscriber_language_certificates
                WHERE subscriber_id = ?
                """,
                (subscriber_id,),
            )

            for certificate in certificates:
                self.connection.execute(
                    """
                    INSERT INTO subscriber_language_certificates (
                        subscriber_id,
                        language_entry_id,
                        certificate_name,
                        issuer_name,
                        file_name,
                        storage_path,
                        uploaded_at,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        certificate.language_entry_id,
                        certificate.certificate_name,
                        certificate.issuer_name,
                        certificate.file_name,
                        certificate.storage_path,
                        certificate.uploaded_at or updated_at,
                        updated_at,
                        updated_at,
                    ),
                )

        return self.list_subscriber_language_certificates(subscriber_id)

    def list_subscriber_certification_entries(
        self,
        subscriber_id: int,
    ) -> list[SubscriberCertificationEntry]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                certificate_name,
                issuer_name,
                issued_year,
                file_name,
                storage_path,
                uploaded_at,
                display_order,
                created_at,
                updated_at
            FROM subscriber_certification_entries
            WHERE subscriber_id = ?
            ORDER BY display_order ASC, id ASC
            """,
            (subscriber_id,),
        )
        return [
            _row_to_subscriber_certification_entry(row)
            for row in cursor.fetchall()
        ]

    def replace_subscriber_certification_entries(
        self,
        subscriber_id: int,
        *,
        entries: list[SubscriberCertificationEntry],
        updated_at: str,
    ) -> list[SubscriberCertificationEntry]:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM subscriber_certification_entries
                WHERE subscriber_id = ?
                """,
                (subscriber_id,),
            )

            for index, entry in enumerate(entries):
                self.connection.execute(
                    """
                    INSERT INTO subscriber_certification_entries (
                        subscriber_id,
                        certificate_name,
                        issuer_name,
                        issued_year,
                        file_name,
                        storage_path,
                        uploaded_at,
                        display_order,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        entry.certificate_name,
                        entry.issuer_name,
                        entry.issued_year,
                        entry.file_name,
                        entry.storage_path,
                        entry.uploaded_at,
                        index,
                        updated_at,
                        updated_at,
                    ),
                )

        return self.list_subscriber_certification_entries(subscriber_id)

    def list_subscriber_skill_details(
        self,
        subscriber_id: int,
    ) -> list[SubscriberSkillDetail]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                skill_name,
                skill_name_normalized,
                category,
                proficiency_hint,
                years_hint,
                evidence_note,
                evidence_file_name,
                evidence_storage_path,
                uploaded_at,
                created_at,
                updated_at
            FROM subscriber_skill_details
            WHERE subscriber_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (subscriber_id,),
        )
        return [_row_to_subscriber_skill_detail(row) for row in cursor.fetchall()]

    def get_subscriber_skill_detail_by_name(
        self,
        subscriber_id: int,
        skill_name: str,
    ) -> SubscriberSkillDetail | None:
        skill_name_normalized = skill_name.strip().lower()
        if not skill_name_normalized:
            return None

        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                skill_name,
                skill_name_normalized,
                category,
                proficiency_hint,
                years_hint,
                evidence_note,
                evidence_file_name,
                evidence_storage_path,
                uploaded_at,
                created_at,
                updated_at
            FROM subscriber_skill_details
            WHERE subscriber_id = ? AND skill_name_normalized = ?
            """,
            (subscriber_id, skill_name_normalized),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber_skill_detail(row)

    def upsert_subscriber_skill_detail(
        self,
        subscriber_id: int,
        *,
        skill_name: str,
        category: str | None,
        proficiency_hint: str | None,
        years_hint: int | None,
        evidence_note: str | None,
        updated_at: str,
        evidence_file_name: str | None = None,
        evidence_storage_path: str | None = None,
        uploaded_at: str | None = None,
    ) -> SubscriberSkillDetail:
        normalized = skill_name.strip().lower()
        existing = self.get_subscriber_skill_detail_by_name(subscriber_id, skill_name)
        created_at = existing.created_at if existing is not None else updated_at
        resolved_file_name = evidence_file_name if evidence_file_name is not None else (existing.evidence_file_name if existing is not None else None)
        resolved_storage_path = evidence_storage_path if evidence_storage_path is not None else (existing.evidence_storage_path if existing is not None else None)
        resolved_uploaded_at = uploaded_at if uploaded_at is not None else (existing.uploaded_at if existing is not None else None)

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_skill_details (
                    subscriber_id,
                    skill_name,
                    skill_name_normalized,
                    category,
                    proficiency_hint,
                    years_hint,
                    evidence_note,
                    evidence_file_name,
                    evidence_storage_path,
                    uploaded_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(subscriber_id, skill_name_normalized) DO UPDATE SET
                    skill_name = excluded.skill_name,
                    category = excluded.category,
                    proficiency_hint = excluded.proficiency_hint,
                    years_hint = excluded.years_hint,
                    evidence_note = excluded.evidence_note,
                    evidence_file_name = excluded.evidence_file_name,
                    evidence_storage_path = excluded.evidence_storage_path,
                    uploaded_at = excluded.uploaded_at,
                    updated_at = excluded.updated_at
                """,
                (
                    subscriber_id,
                    skill_name,
                    normalized,
                    category,
                    proficiency_hint,
                    years_hint,
                    evidence_note,
                    resolved_file_name,
                    resolved_storage_path,
                    resolved_uploaded_at,
                    created_at,
                    updated_at,
                ),
            )

        return self.get_subscriber_skill_detail_by_name(subscriber_id, skill_name) or SubscriberSkillDetail(
            subscriber_id=subscriber_id,
            skill_name=skill_name,
            skill_name_normalized=normalized,
            category=category,
            proficiency_hint=proficiency_hint,
            years_hint=years_hint,
            evidence_note=evidence_note,
            evidence_file_name=resolved_file_name,
            evidence_storage_path=resolved_storage_path,
            uploaded_at=resolved_uploaded_at,
            created_at=created_at,
            updated_at=updated_at,
        )

    def rename_subscriber_skill_detail(
        self,
        subscriber_id: int,
        *,
        old_skill_name: str,
        new_skill_name: str,
        updated_at: str,
    ) -> SubscriberSkillDetail | None:
        existing = self.get_subscriber_skill_detail_by_name(subscriber_id, old_skill_name)
        if existing is None:
            return None

        with self.connection:
            self.connection.execute(
                """
                UPDATE subscriber_skill_details
                SET skill_name = ?,
                    skill_name_normalized = ?,
                    updated_at = ?
                WHERE subscriber_id = ? AND skill_name_normalized = ?
                """,
                (
                    new_skill_name,
                    new_skill_name.strip().lower(),
                    updated_at,
                    subscriber_id,
                    old_skill_name.strip().lower(),
                ),
            )

        return self.get_subscriber_skill_detail_by_name(subscriber_id, new_skill_name)

    def delete_subscriber_skill_detail(
        self,
        subscriber_id: int,
        *,
        skill_name: str,
    ) -> None:
        normalized = skill_name.strip().lower()
        if not normalized:
            return

        with self.connection:
            self.connection.execute(
                """
                DELETE FROM subscriber_skill_details
                WHERE subscriber_id = ? AND skill_name_normalized = ?
                """,
                (subscriber_id, normalized),
            )

    def create_subscriber_ai_audit_log(
        self,
        subscriber_id: int,
        *,
        telemetry_ref: str | None,
        target_field: str,
        target_entity_id: str | None,
        action_type: str,
        source_panel: str | None,
        before_snapshot_json: str,
        after_snapshot_json: str,
        persistence_status: str,
        evaluation_status: str | None,
        evaluation_score: float | None,
        manual_edit_distance: int | None,
        request_ref: str | None,
        metadata_json: str,
        created_at: str,
    ) -> SubscriberAiAuditLog:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_ai_audit_logs (
                    subscriber_id,
                    telemetry_ref,
                    target_field,
                    target_entity_id,
                    action_type,
                    source_panel,
                    before_snapshot_json,
                    after_snapshot_json,
                    persistence_status,
                    evaluation_status,
                    evaluation_score,
                    manual_edit_distance,
                    request_ref,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscriber_id,
                    telemetry_ref,
                    target_field,
                    target_entity_id,
                    action_type,
                    source_panel,
                    before_snapshot_json,
                    after_snapshot_json,
                    persistence_status,
                    evaluation_status,
                    evaluation_score,
                    manual_edit_distance,
                    request_ref,
                    metadata_json,
                    created_at,
                    created_at,
                ),
            )
        item = self.get_subscriber_ai_audit_log_by_id(subscriber_id, int(cursor.lastrowid))
        if item is None:
            raise RuntimeError("Failed to load created AI audit log.")
        return item

    def get_subscriber_ai_audit_log_by_id(
        self,
        subscriber_id: int,
        audit_log_id: int,
    ) -> SubscriberAiAuditLog | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                telemetry_ref,
                target_field,
                target_entity_id,
                action_type,
                source_panel,
                before_snapshot_json,
                after_snapshot_json,
                persistence_status,
                evaluation_status,
                evaluation_score,
                manual_edit_distance,
                request_ref,
                metadata_json,
                created_at,
                updated_at,
                reverted_at
            FROM subscriber_ai_audit_logs
            WHERE subscriber_id = ? AND id = ?
            """,
            (subscriber_id, audit_log_id),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber_ai_audit_log(row)

    def list_subscriber_ai_audit_logs(
        self,
        subscriber_id: int,
        *,
        limit: int = 100,
    ) -> list[SubscriberAiAuditLog]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                telemetry_ref,
                target_field,
                target_entity_id,
                action_type,
                source_panel,
                before_snapshot_json,
                after_snapshot_json,
                persistence_status,
                evaluation_status,
                evaluation_score,
                manual_edit_distance,
                request_ref,
                metadata_json,
                created_at,
                updated_at,
                reverted_at
            FROM subscriber_ai_audit_logs
            WHERE subscriber_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (subscriber_id, limit),
        )
        return [_row_to_subscriber_ai_audit_log(row) for row in cursor.fetchall()]

    def update_subscriber_ai_audit_log(
        self,
        subscriber_id: int,
        audit_log_id: int,
        *,
        after_snapshot_json: str | None = None,
        persistence_status: str | None = None,
        evaluation_status: str | None = None,
        evaluation_score: float | None = None,
        manual_edit_distance: int | None = None,
        metadata_json: str | None = None,
        request_ref: str | None = None,
        reverted_at: str | None = None,
        updated_at: str,
    ) -> SubscriberAiAuditLog | None:
        existing = self.get_subscriber_ai_audit_log_by_id(subscriber_id, audit_log_id)
        if existing is None:
            return None
        with self.connection:
            self.connection.execute(
                """
                UPDATE subscriber_ai_audit_logs
                SET after_snapshot_json = ?,
                    persistence_status = ?,
                    evaluation_status = ?,
                    evaluation_score = ?,
                    manual_edit_distance = ?,
                    metadata_json = ?,
                    request_ref = ?,
                    reverted_at = ?,
                    updated_at = ?
                WHERE subscriber_id = ? AND id = ?
                """,
                (
                    after_snapshot_json if after_snapshot_json is not None else existing.after_snapshot_json,
                    persistence_status if persistence_status is not None else existing.persistence_status,
                    evaluation_status if evaluation_status is not None else existing.evaluation_status,
                    evaluation_score if evaluation_score is not None else existing.evaluation_score,
                    manual_edit_distance if manual_edit_distance is not None else existing.manual_edit_distance,
                    metadata_json if metadata_json is not None else existing.metadata_json,
                    request_ref if request_ref is not None else existing.request_ref,
                    reverted_at if reverted_at is not None else existing.reverted_at,
                    updated_at,
                    subscriber_id,
                    audit_log_id,
                ),
            )
        return self.get_subscriber_ai_audit_log_by_id(subscriber_id, audit_log_id)

    def get_subscriber_cv_upload_by_id(
        self,
        upload_id: int,
    ) -> SubscriberCvUpload | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                original_filename,
                storage_path,
                content_type,
                file_size_bytes,
                extracted_text,
                parse_status,
                uploaded_at,
                parsed_at,
                created_at,
                updated_at
            FROM subscriber_cv_uploads
            WHERE id = ?
            """,
            (upload_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return _row_to_subscriber_cv_upload(row)

    def list_subscriber_cv_uploads(
        self,
        subscriber_id: int,
    ) -> list[SubscriberCvUpload]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                original_filename,
                storage_path,
                content_type,
                file_size_bytes,
                extracted_text,
                parse_status,
                uploaded_at,
                parsed_at,
                created_at,
                updated_at
            FROM subscriber_cv_uploads
            WHERE subscriber_id = ?
            ORDER BY uploaded_at DESC, id DESC
            """,
            (subscriber_id,),
        )
        return [_row_to_subscriber_cv_upload(row) for row in cursor.fetchall()]

    def get_latest_subscriber_cv_upload(
        self,
        subscriber_id: int,
    ) -> SubscriberCvUpload | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                original_filename,
                storage_path,
                content_type,
                file_size_bytes,
                extracted_text,
                parse_status,
                uploaded_at,
                parsed_at,
                created_at,
                updated_at
            FROM subscriber_cv_uploads
            WHERE subscriber_id = ?
            ORDER BY uploaded_at DESC, id DESC
            LIMIT 1
            """,
            (subscriber_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return _row_to_subscriber_cv_upload(row)

    def create_subscriber_cv_upload(
        self,
        subscriber_id: int,
        *,
        original_filename: str,
        storage_path: str,
        content_type: str | None,
        file_size_bytes: int | None,
        extracted_text: str | None,
        parse_status: str,
        uploaded_at: str,
        parsed_at: str | None,
    ) -> SubscriberCvUpload:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_cv_uploads (
                    subscriber_id,
                    original_filename,
                    storage_path,
                    content_type,
                    file_size_bytes,
                    extracted_text,
                    parse_status,
                    uploaded_at,
                    parsed_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscriber_id,
                    original_filename,
                    storage_path,
                    content_type,
                    file_size_bytes,
                    extracted_text,
                    parse_status,
                    uploaded_at,
                    parsed_at,
                    uploaded_at,
                    uploaded_at,
                ),
            )

        upload_id = cursor.lastrowid
        if upload_id is None:
            raise RuntimeError("Failed to create subscriber CV upload record.")

        upload = self.get_subscriber_cv_upload_by_id(int(upload_id))
        if upload is None:
            raise RuntimeError("Failed to reload subscriber CV upload record.")

        return upload



    def update_subscriber_cv_upload_parse_result(
        self,
        upload_id: int,
        *,
        extracted_text: str | None,
        parse_status: str,
        parsed_at: str | None,
        updated_at: str,
    ) -> SubscriberCvUpload | None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscriber_cv_uploads
                SET
                    extracted_text = ?,
                    parse_status = ?,
                    parsed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    extracted_text,
                    parse_status,
                    parsed_at,
                    updated_at,
                    upload_id,
                ),
            )
    
        if cursor.rowcount == 0:
            return None
    
        return self.get_subscriber_cv_upload_by_id(upload_id)
    

    def create_subscriber_cv_parse_run(
        self,
        subscriber_id: int,
        *,
        cv_upload_id: int,
        parser_version: str | None,
        source_parse_status: str,
        snapshot_json: str,
        created_at: str,
        metadata_json: str | None = None,
    ) -> SubscriberCvParseRun:
        """Persist a versioned CV parse snapshot for a specific upload.

        Args:
            subscriber_id: Owner of the CV upload.
            cv_upload_id: Source CV upload identifier.
            parser_version: Parser version used to generate the snapshot.
            source_parse_status: Final extraction status of the source upload.
            snapshot_json: Serialized snapshot payload.
            created_at: ISO 8601 timestamp for the parse run.

        Returns:
            The persisted parse run, reloaded from SQLite.

        Raises:
            RuntimeError: If the row cannot be inserted or reloaded.
        """
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_cv_parse_runs (
                    subscriber_id,
                    cv_upload_id,
                    parser_version,
                    source_parse_status,
                    snapshot_json,
                    metadata_json,
                    apply_status,
                    applied_change_count,
                    applied_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscriber_id,
                    cv_upload_id,
                    parser_version,
                    source_parse_status,
                    snapshot_json,
                    metadata_json or "{}",
                    "pending",
                    0,
                    None,
                    created_at,
                    created_at,
                ),
            )

        parse_run_id = cursor.lastrowid
        if parse_run_id is None:
            raise RuntimeError("Failed to create subscriber CV parse run record.")

        parse_run = self.get_subscriber_cv_parse_run_by_id(int(parse_run_id))
        if parse_run is None:
            raise RuntimeError("Failed to reload subscriber CV parse run record.")

        return parse_run

    def get_subscriber_cv_parse_run_by_id(
        self,
        parse_run_id: int,
    ) -> SubscriberCvParseRun | None:
        """Fetch a CV parse run by primary key.

        Args:
            parse_run_id: Parse run identifier.

        Returns:
            The parse run if found, otherwise None.
        """
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                cv_upload_id,
                parser_version,
                source_parse_status,
                snapshot_json,
                metadata_json,
                apply_status,
                applied_change_count,
                applied_at,
                created_at,
                updated_at
            FROM subscriber_cv_parse_runs
            WHERE id = ?
            """,
            (parse_run_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return _row_to_subscriber_cv_parse_run(row)

    def list_subscriber_cv_parse_runs_for_upload(
        self,
        cv_upload_id: int,
    ) -> list[SubscriberCvParseRun]:
        """List all persisted parse runs for a given CV upload.

        Args:
            cv_upload_id: Source CV upload identifier.

        Returns:
            Parse runs ordered from newest to oldest.
        """
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                cv_upload_id,
                parser_version,
                source_parse_status,
                snapshot_json,
                metadata_json,
                apply_status,
                applied_change_count,
                applied_at,
                created_at,
                updated_at
            FROM subscriber_cv_parse_runs
            WHERE cv_upload_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (cv_upload_id,),
        )
        rows = cursor.fetchall()
        return [_row_to_subscriber_cv_parse_run(row) for row in rows]

    def get_latest_subscriber_cv_parse_run_for_upload(
        self,
        cv_upload_id: int,
    ) -> SubscriberCvParseRun | None:
        """Fetch the latest persisted parse run for a given CV upload.

        Args:
            cv_upload_id: Source CV upload identifier.

        Returns:
            The newest parse run if one exists, otherwise None.
        """
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                cv_upload_id,
                parser_version,
                source_parse_status,
                snapshot_json,
                metadata_json,
                apply_status,
                applied_change_count,
                applied_at,
                created_at,
                updated_at
            FROM subscriber_cv_parse_runs
            WHERE cv_upload_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (cv_upload_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return _row_to_subscriber_cv_parse_run(row)


    def update_subscriber_cv_parse_run_apply_state(
        self,
        parse_run_id: int,
        *,
        apply_status: str,
        applied_change_count: int,
        applied_at: str,
        updated_at: str,
    ) -> SubscriberCvParseRun | None:
        """Update the aggregated apply state for a CV parse run.

        Args:
            parse_run_id: Parse run identifier.
            apply_status: Aggregated apply status.
            applied_change_count: Total applied operation count so far.
            applied_at: Timestamp of the latest successful apply.
            updated_at: Update timestamp.

        Returns:
            The updated parse run if found, otherwise None.
        """
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscriber_cv_parse_runs
                SET
                    apply_status = ?,
                    applied_change_count = ?,
                    applied_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    apply_status,
                    applied_change_count,
                    applied_at,
                    updated_at,
                    parse_run_id,
                ),
            )

        if cursor.rowcount == 0:
            return None

        return self.get_subscriber_cv_parse_run_by_id(parse_run_id)

    def create_subscriber_cv_apply_audit(
        self,
        subscriber_id: int,
        *,
        parse_run_id: int,
        selected_operations_json: str,
        applied_operations_json: str,
        applied_change_count: int,
        resulting_apply_status: str,
        remaining_actionable_change_count: int,
        created_at: str,
        metadata_json: str | None = None,
    ) -> SubscriberCvApplyAudit:
        """Persist an immutable audit record for a CV apply execution.

        Args:
            subscriber_id: Owner subscriber identifier.
            parse_run_id: Source parse run identifier.
            selected_operations_json: Serialized selected-operation payload.
            applied_operations_json: Serialized applied-operation payload.
            applied_change_count: Count of operations applied in this execution.
            resulting_apply_status: Resulting parse run apply status.
            remaining_actionable_change_count: Remaining actionable item count.
            created_at: Creation timestamp.

        Returns:
            The persisted apply audit entity.

        Raises:
            RuntimeError: If the row cannot be inserted or reloaded.
        """
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_cv_apply_audits (
                    subscriber_id,
                    parse_run_id,
                    selected_operations_json,
                    applied_operations_json,
                    metadata_json,
                    applied_change_count,
                    resulting_apply_status,
                    remaining_actionable_change_count,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscriber_id,
                    parse_run_id,
                    selected_operations_json,
                    applied_operations_json,
                    metadata_json or "{}",
                    applied_change_count,
                    resulting_apply_status,
                    remaining_actionable_change_count,
                    created_at,
                    created_at,
                ),
            )

        audit_id = cursor.lastrowid
        if audit_id is None:
            raise RuntimeError("Failed to create subscriber CV apply audit record.")

        audit = self.get_subscriber_cv_apply_audit_by_id(int(audit_id))
        if audit is None:
            raise RuntimeError("Failed to reload subscriber CV apply audit record.")

        return audit

    def get_subscriber_cv_apply_audit_by_id(
        self,
        audit_id: int,
    ) -> SubscriberCvApplyAudit | None:
        """Fetch a CV apply audit by primary key.

        Args:
            audit_id: Audit identifier.

        Returns:
            The audit entity if found, otherwise None.
        """
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                parse_run_id,
                selected_operations_json,
                applied_operations_json,
                metadata_json,
                applied_change_count,
                resulting_apply_status,
                remaining_actionable_change_count,
                created_at,
                updated_at
            FROM subscriber_cv_apply_audits
            WHERE id = ?
            """,
            (audit_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return _row_to_subscriber_cv_apply_audit(row)

    def list_subscriber_cv_apply_audits_for_parse_run(
        self,
        parse_run_id: int,
    ) -> list[SubscriberCvApplyAudit]:
        """List all apply audit records for a parse run.

        Args:
            parse_run_id: Source parse run identifier.

        Returns:
            Apply audit rows ordered from newest to oldest.
        """
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                parse_run_id,
                selected_operations_json,
                applied_operations_json,
                metadata_json,
                applied_change_count,
                resulting_apply_status,
                remaining_actionable_change_count,
                created_at,
                updated_at
            FROM subscriber_cv_apply_audits
            WHERE parse_run_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (parse_run_id,),
        )
        rows = cursor.fetchall()
        return [_row_to_subscriber_cv_apply_audit(row) for row in rows]


    def get_latest_subscriber_cv_parse_run(
        self,
        subscriber_id: int,
    ) -> SubscriberCvParseRun | None:
        """Fetch the latest persisted CV parse run for a subscriber.
    
        Args:
            subscriber_id: Subscriber identifier.
    
        Returns:
            The newest parse run if one exists, otherwise None.
        """
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                cv_upload_id,
                parser_version,
                source_parse_status,
                snapshot_json,
                metadata_json,
                apply_status,
                applied_change_count,
                applied_at,
                created_at,
                updated_at
            FROM subscriber_cv_parse_runs
            WHERE subscriber_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (subscriber_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
    
        return _row_to_subscriber_cv_parse_run(row)
    
    def upsert_subscriber(
        self,
        *,
        email: str,
        full_name: str | None,
        updated_at: str,
        password_hash: str | None = None,
        password_updated_at: str | None = None,
    ) -> tuple[Subscriber, bool]:
        """Insert a new subscriber or reactivate/update an existing one.

        Returns:
            (subscriber, created)
        """
        existing = self.get_subscriber_by_email(email)

        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO subscribers (
                        email,
                        full_name,
                        password_hash,
                        password_updated_at,
                        is_active,
                        digest_enabled,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email,
                        full_name,
                        password_hash,
                        password_updated_at,
                        1,
                        1,
                        updated_at,
                        updated_at,
                    ),
                )

            subscriber = self.get_subscriber_by_email(email)
            if subscriber is None:
                raise RuntimeError(
                    "Subscriber insert succeeded but record could not be reloaded."
                )

            return subscriber, True

        effective_full_name = full_name if full_name is not None else existing.full_name
        effective_password_hash = (
            password_hash if password_hash is not None else existing.password_hash
        )
        effective_password_updated_at = (
            password_updated_at
            if password_updated_at is not None
            else existing.password_updated_at
        )

        with self.connection:
            self.connection.execute(
                """
                UPDATE subscribers
                SET
                    full_name = ?,
                    password_hash = ?,
                    password_updated_at = ?,
                    is_active = 1,
                    digest_enabled = 1,
                    updated_at = ?
                WHERE email = ?
                """,
                (
                    effective_full_name,
                    effective_password_hash,
                    effective_password_updated_at,
                    updated_at,
                    email,
                ),
            )

        subscriber = self.get_subscriber_by_email(email)
        if subscriber is None:
            raise RuntimeError(
                "Subscriber update succeeded but record could not be reloaded."
            )

        return subscriber, False

    def set_subscriber_password(
        self,
        *,
        subscriber_id: int,
        password_hash: str,
        password_updated_at: str,
        updated_at: str,
    ) -> Subscriber | None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscribers
                SET
                    password_hash = ?,
                    password_updated_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    password_hash,
                    password_updated_at,
                    updated_at,
                    subscriber_id,
                ),
            )

        if cursor.rowcount == 0:
            return None

        return self.get_subscriber_by_id(subscriber_id)


    def list_subscribers(self) -> list[Subscriber]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                password_hash,
                password_updated_at,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            ORDER BY email
            """
        )
        rows = cursor.fetchall()
        return [_row_to_subscriber(row) for row in rows]

    def list_digest_enabled_subscribers(self) -> list[Subscriber]:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                password_hash,
                password_updated_at,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            WHERE is_active = 1 AND digest_enabled = 1
            ORDER BY email
            """
        )
        rows = cursor.fetchall()
        return [_row_to_subscriber(row) for row in rows]

    def set_subscriber_active(
        self,
        *,
        email: str,
        is_active: bool,
        updated_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscribers
                SET
                    is_active = ?,
                    updated_at = ?
                WHERE email = ?
                """,
                (
                    int(is_active),
                    updated_at,
                    email,
                ),
            )

        return cursor.rowcount > 0

    def set_subscriber_digest_enabled(
        self,
        *,
        email: str,
        digest_enabled: bool,
        updated_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscribers
                SET
                    digest_enabled = ?,
                    updated_at = ?
                WHERE email = ?
                """,
                (
                    int(digest_enabled),
                    updated_at,
                    email,
                ),
            )

        return cursor.rowcount > 0

    def list_active_jobs(self, source_name: str | None = None) -> list[JobRecord]:
        if source_name is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE is_active = 1
                ORDER BY company_name, title, canonical_url
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_name,
                    title,
                    company_name,
                    location,
                    canonical_url,
                    source_type,
                    source_job_id,
                    raw_posted_at,
                    posted_at,
                    fingerprint,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    scraped_at
                FROM jobs
                WHERE is_active = 1 AND source_name = ?
                ORDER BY company_name, title, canonical_url
                """,
                (source_name,),
            )

        rows = cursor.fetchall()
        return [_row_to_job_record(row) for row in rows]

    def upsert_job(self, job: JobRecord) -> bool:
        """
        Insert a new job if the fingerprint is unseen.

        Returns:
            True if a new row was inserted, False if an existing row was updated.
        """
        existing = self.get_job_by_fingerprint(job.fingerprint)

        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO jobs (
                        source_name,
                        title,
                        company_name,
                        location,
                        canonical_url,
                        source_type,
                        source_job_id,
                        raw_posted_at,
                        posted_at,
                        fingerprint,
                        first_seen_at,
                        last_seen_at,
                        is_active,
                        scraped_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.source_name,
                        job.title,
                        job.company_name,
                        job.location,
                        job.canonical_url,
                        job.source_type,
                        job.source_job_id,
                        job.raw_posted_at,
                        job.posted_at,
                        job.fingerprint,
                        job.scraped_at,
                        job.scraped_at,
                        1,
                        job.scraped_at,
                    ),
                )
            return True

        with self.connection:
            self.connection.execute(
                """
                UPDATE jobs
                SET
                    source_name = ?,
                    title = ?,
                    company_name = ?,
                    location = ?,
                    canonical_url = ?,
                    source_type = ?,
                    source_job_id = ?,
                    raw_posted_at = ?,
                    posted_at = ?,
                    last_seen_at = ?,
                    is_active = 1,
                    scraped_at = ?
                WHERE fingerprint = ?
                """,
                (
                    job.source_name,
                    job.title,
                    job.company_name,
                    job.location,
                    job.canonical_url,
                    job.source_type,
                    job.source_job_id,
                    job.raw_posted_at,
                    job.posted_at,
                    job.scraped_at,
                    job.scraped_at,
                    job.fingerprint,
                ),
            )

        return False

    def mark_missing_jobs_inactive(
        self,
        source_name: str,
        seen_fingerprints: Iterable[str],
        updated_at: str,
    ) -> int:
        """
        Mark active jobs as inactive when they were not seen in the current run.

        Note:
            `updated_at` is accepted for API clarity and future evolution.
            In the MVP we intentionally do not overwrite `last_seen_at` when
            a job becomes inactive.
        """
        _ = updated_at
        fingerprints = tuple(seen_fingerprints)

        if fingerprints:
            placeholders = ", ".join(["?"] * len(fingerprints))
            query = f"""
                UPDATE jobs
                SET is_active = 0
                WHERE source_name = ?
                  AND is_active = 1
                  AND fingerprint NOT IN ({placeholders})
            """
            params: tuple[str | int, ...] = (source_name, *fingerprints)
        else:
            query = """
                UPDATE jobs
                SET is_active = 0
                WHERE source_name = ?
                  AND is_active = 1
            """
            params = (source_name,)

        with self.connection:
            cursor = self.connection.execute(query, params)

        return cursor.rowcount

    def get_job_source_by_id(self, source_id: int) -> JobSource | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                source_type,
                source_name,
                account_slug,
                base_url,
                trust_score,
                country_scope,
                is_active,
                created_at,
                updated_at
            FROM job_sources
            WHERE id = ?
            """,
            (source_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_job_source(row)

    def list_job_sources(self, *, active_only: bool = False) -> list[JobSource]:
        if active_only:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_type,
                    source_name,
                    account_slug,
                    base_url,
                    trust_score,
                    country_scope,
                    is_active,
                    created_at,
                    updated_at
                FROM job_sources
                WHERE is_active = 1
                ORDER BY source_type ASC, source_name ASC, id ASC
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_type,
                    source_name,
                    account_slug,
                    base_url,
                    trust_score,
                    country_scope,
                    is_active,
                    created_at,
                    updated_at
                FROM job_sources
                ORDER BY source_type ASC, source_name ASC, id ASC
                """
            )
        return [_row_to_job_source(row) for row in cursor.fetchall()]

    def get_job_source(
        self,
        *,
        source_type: str,
        source_name: str,
        account_slug: str = "",
    ) -> JobSource | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                source_type,
                source_name,
                account_slug,
                base_url,
                trust_score,
                country_scope,
                is_active,
                created_at,
                updated_at
            FROM job_sources
            WHERE source_type = ?
              AND source_name = ?
              AND account_slug = ?
            """,
            (source_type, source_name, account_slug),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_job_source(row)

    def upsert_job_source(self, source: JobSource) -> JobSource:
        existing = self.get_job_source(
            source_type=source.source_type,
            source_name=source.source_name,
            account_slug=source.account_slug,
        )
        if existing is None:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    INSERT INTO job_sources (
                        source_type,
                        source_name,
                        account_slug,
                        base_url,
                        trust_score,
                        country_scope,
                        is_active,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source.source_type,
                        source.source_name,
                        source.account_slug,
                        source.base_url,
                        source.trust_score,
                        source.country_scope,
                        int(source.is_active),
                        source.created_at,
                        source.updated_at,
                    ),
                )
            created_id = int(cursor.lastrowid)
            created = self.get_job_source(
                source_type=source.source_type,
                source_name=source.source_name,
                account_slug=source.account_slug,
            )
            if created is None:
                raise RuntimeError(f"Failed to load created job source {created_id}.")
            return created

        with self.connection:
            self.connection.execute(
                """
                UPDATE job_sources
                SET
                    base_url = ?,
                    trust_score = ?,
                    country_scope = ?,
                    is_active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    source.base_url,
                    source.trust_score,
                    source.country_scope,
                    int(source.is_active),
                    source.updated_at,
                    existing.id,
                ),
            )

        refreshed = self.get_job_source(
            source_type=source.source_type,
            source_name=source.source_name,
            account_slug=source.account_slug,
        )
        if refreshed is None:
            raise RuntimeError("Failed to reload updated job source.")
        return refreshed

    def get_job_source_record(
        self,
        *,
        source_id: int,
        external_job_id: str,
    ) -> JobSourceRecord | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                source_id,
                external_job_id,
                external_company_id,
                raw_payload_json,
                raw_payload_hash,
                canonical_url,
                title,
                company_name,
                location_text,
                posted_at,
                apply_url,
                fetched_at,
                first_seen_at,
                last_seen_at,
                is_active
            FROM job_source_records
            WHERE source_id = ?
              AND external_job_id = ?
            """,
            (source_id, external_job_id),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_job_source_record(row)

    def upsert_job_source_record(self, record: JobSourceRecord) -> JobSourceRecord:
        existing = self.get_job_source_record(
            source_id=record.source_id,
            external_job_id=record.external_job_id,
        )
        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO job_source_records (
                        source_id,
                        external_job_id,
                        external_company_id,
                        raw_payload_json,
                        raw_payload_hash,
                        canonical_url,
                        title,
                        company_name,
                        location_text,
                        posted_at,
                        apply_url,
                        fetched_at,
                        first_seen_at,
                        last_seen_at,
                        is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.source_id,
                        record.external_job_id,
                        record.external_company_id,
                        record.raw_payload_json,
                        record.raw_payload_hash,
                        record.canonical_url,
                        record.title,
                        record.company_name,
                        record.location_text,
                        record.posted_at,
                        record.apply_url,
                        record.fetched_at,
                        record.fetched_at,
                        record.fetched_at,
                        int(record.is_active),
                    ),
                )
        else:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE job_source_records
                    SET
                        external_company_id = ?,
                        raw_payload_json = ?,
                        raw_payload_hash = ?,
                        canonical_url = ?,
                        title = ?,
                        company_name = ?,
                        location_text = ?,
                        posted_at = ?,
                        apply_url = ?,
                        fetched_at = ?,
                        last_seen_at = ?,
                        is_active = ?
                    WHERE id = ?
                    """,
                    (
                        record.external_company_id,
                        record.raw_payload_json,
                        record.raw_payload_hash,
                        record.canonical_url,
                        record.title,
                        record.company_name,
                        record.location_text,
                        record.posted_at,
                        record.apply_url,
                        record.fetched_at,
                        record.fetched_at,
                        int(record.is_active),
                        existing.id,
                    ),
                )

        refreshed = self.get_job_source_record(
            source_id=record.source_id,
            external_job_id=record.external_job_id,
        )
        if refreshed is None:
            raise RuntimeError("Failed to reload job source record.")
        return refreshed

    def list_job_source_records(
        self,
        *,
        source_id: int,
        active_only: bool = False,
    ) -> list[JobSourceRecord]:
        if active_only:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    external_job_id,
                    external_company_id,
                    raw_payload_json,
                    raw_payload_hash,
                    canonical_url,
                    title,
                    company_name,
                    location_text,
                    posted_at,
                    apply_url,
                    fetched_at,
                    first_seen_at,
                    last_seen_at,
                    is_active
                FROM job_source_records
                WHERE source_id = ?
                  AND is_active = 1
                ORDER BY last_seen_at DESC, id DESC
                """,
                (source_id,),
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    external_job_id,
                    external_company_id,
                    raw_payload_json,
                    raw_payload_hash,
                    canonical_url,
                    title,
                    company_name,
                    location_text,
                    posted_at,
                    apply_url,
                    fetched_at,
                    first_seen_at,
                    last_seen_at,
                    is_active
                FROM job_source_records
                WHERE source_id = ?
                ORDER BY last_seen_at DESC, id DESC
                """,
                (source_id,),
            )
        return [_row_to_job_source_record(row) for row in cursor.fetchall()]

    def mark_missing_job_source_records_inactive(
        self,
        *,
        source_id: int,
        seen_external_job_ids: Iterable[str],
        updated_at: str,
    ) -> int:
        _ = updated_at
        external_job_ids = tuple(seen_external_job_ids)

        if external_job_ids:
            placeholders = ", ".join(["?"] * len(external_job_ids))
            query = f"""
                UPDATE job_source_records
                SET is_active = 0
                WHERE source_id = ?
                  AND is_active = 1
                  AND external_job_id NOT IN ({placeholders})
            """
            params: tuple[str | int, ...] = (source_id, *external_job_ids)
        else:
            query = """
                UPDATE job_source_records
                SET is_active = 0
                WHERE source_id = ?
                  AND is_active = 1
            """
            params = (source_id,)

        with self.connection:
            cursor = self.connection.execute(query, params)

        return cursor.rowcount

    def get_canonical_job_by_id(self, canonical_job_id: int) -> CanonicalJob | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                canonical_key,
                normalized_title,
                normalized_company_name,
                display_title,
                display_company_name,
                location_city,
                district,
                country,
                workplace_type,
                employment_type,
                seniority,
                category,
                department,
                description_text,
                description_html,
                posted_at,
                apply_url,
                trust_score,
                freshness_score,
                is_active,
                created_at,
                updated_at
            FROM canonical_jobs
            WHERE id = ?
            """,
            (canonical_job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_canonical_job(row)

    def get_canonical_job(self, *, canonical_key: str) -> CanonicalJob | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                canonical_key,
                normalized_title,
                normalized_company_name,
                display_title,
                display_company_name,
                location_city,
                district,
                country,
                workplace_type,
                employment_type,
                seniority,
                category,
                department,
                description_text,
                description_html,
                posted_at,
                apply_url,
                trust_score,
                freshness_score,
                is_active,
                created_at,
                updated_at
            FROM canonical_jobs
            WHERE canonical_key = ?
            """,
            (canonical_key,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_canonical_job(row)

    def upsert_canonical_job(self, job: CanonicalJob) -> CanonicalJob:
        existing = self.get_canonical_job(canonical_key=job.canonical_key)
        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO canonical_jobs (
                        canonical_key,
                        normalized_title,
                        normalized_company_name,
                        display_title,
                        display_company_name,
                        location_city,
                        district,
                        country,
                        workplace_type,
                        employment_type,
                        seniority,
                        category,
                        department,
                        description_text,
                        description_html,
                        posted_at,
                        apply_url,
                        trust_score,
                        freshness_score,
                        is_active,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.canonical_key,
                        job.normalized_title,
                        job.normalized_company_name,
                        job.display_title,
                        job.display_company_name,
                        job.location_city,
                        job.district,
                        job.country,
                        job.workplace_type,
                        job.employment_type,
                        job.seniority,
                        job.category,
                        job.department,
                        job.description_text,
                        job.description_html,
                        job.posted_at,
                        job.apply_url,
                        job.trust_score,
                        job.freshness_score,
                        int(job.is_active),
                        job.created_at,
                        job.updated_at,
                    ),
                )
        else:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE canonical_jobs
                    SET
                        normalized_title = ?,
                        normalized_company_name = ?,
                        display_title = ?,
                        display_company_name = ?,
                        location_city = ?,
                        district = ?,
                        country = ?,
                        workplace_type = ?,
                        employment_type = ?,
                        seniority = ?,
                        category = ?,
                        department = ?,
                        description_text = ?,
                        description_html = ?,
                        posted_at = ?,
                        apply_url = ?,
                        trust_score = ?,
                        freshness_score = ?,
                        is_active = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        job.normalized_title,
                        job.normalized_company_name,
                        job.display_title,
                        job.display_company_name,
                        job.location_city,
                        job.district,
                        job.country,
                        job.workplace_type,
                        job.employment_type,
                        job.seniority,
                        job.category,
                        job.department,
                        job.description_text,
                        job.description_html,
                        job.posted_at,
                        job.apply_url,
                        job.trust_score,
                        job.freshness_score,
                        int(job.is_active),
                        job.updated_at,
                        existing.id,
                    ),
                )

        refreshed = self.get_canonical_job(canonical_key=job.canonical_key)
        if refreshed is None:
            raise RuntimeError("Failed to reload canonical job.")
        return refreshed

    def list_canonical_jobs(self, *, active_only: bool = False) -> list[CanonicalJob]:
        if active_only:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    canonical_key,
                    normalized_title,
                    normalized_company_name,
                    display_title,
                    display_company_name,
                    location_city,
                    district,
                    country,
                    workplace_type,
                    employment_type,
                    seniority,
                    category,
                    department,
                    description_text,
                    description_html,
                    posted_at,
                    apply_url,
                    trust_score,
                    freshness_score,
                    is_active,
                    created_at,
                    updated_at
                FROM canonical_jobs
                WHERE is_active = 1
                ORDER BY updated_at DESC, id DESC
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    canonical_key,
                    normalized_title,
                    normalized_company_name,
                    display_title,
                    display_company_name,
                    location_city,
                    district,
                    country,
                    workplace_type,
                    employment_type,
                    seniority,
                    category,
                    department,
                    description_text,
                    description_html,
                    posted_at,
                    apply_url,
                    trust_score,
                    freshness_score,
                    is_active,
                    created_at,
                    updated_at
                FROM canonical_jobs
                ORDER BY updated_at DESC, id DESC
                """
            )
        return [_row_to_canonical_job(row) for row in cursor.fetchall()]

    def list_ranked_canonical_jobs(
        self,
        *,
        active_only: bool = True,
        limit: int | None = None,
    ) -> list[CanonicalJob]:
        where_clause = "WHERE is_active = 1" if active_only else ""
        query = f"""
            SELECT
                id,
                canonical_key,
                normalized_title,
                normalized_company_name,
                display_title,
                display_company_name,
                location_city,
                district,
                country,
                workplace_type,
                employment_type,
                seniority,
                category,
                department,
                description_text,
                description_html,
                posted_at,
                apply_url,
                trust_score,
                freshness_score,
                is_active,
                created_at,
                updated_at
            FROM canonical_jobs
            {where_clause}
            ORDER BY ((trust_score * 0.65) + (freshness_score * 0.35)) DESC,
                     trust_score DESC,
                     freshness_score DESC,
                     updated_at DESC,
                     id DESC
        """
        params: tuple[int, ...] = ()
        if limit is not None:
            query += "\n LIMIT ?"
            params = (limit,)
        cursor = self.connection.execute(query, params)
        return [_row_to_canonical_job(row) for row in cursor.fetchall()]

    def get_canonical_job_feature(
        self,
        *,
        canonical_job_id: int,
    ) -> CanonicalJobFeature | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                canonical_job_id,
                feature_version,
                role_family,
                job_discipline,
                department_family,
                title_tokens_json,
                skill_terms_json,
                required_skill_terms_json,
                preferred_skill_terms_json,
                external_requirement_terms_json,
                external_technology_terms_json,
                external_responsibility_terms_json,
                location_tokens_json,
                language_requirements_json,
                education_level_hint,
                years_experience_min,
                management_track,
                individual_contributor,
                domain_signals_json,
                responsibility_scope,
                external_context_status,
                external_context_updated_at,
                match_readiness_score,
                created_at,
                updated_at
            FROM canonical_job_features
            WHERE canonical_job_id = ?
            """,
            (canonical_job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_canonical_job_feature(row)

    def upsert_canonical_job_feature(
        self,
        feature: CanonicalJobFeature,
    ) -> CanonicalJobFeature:
        existing = self.get_canonical_job_feature(canonical_job_id=feature.canonical_job_id)
        serialized_title_tokens = json.dumps(list(feature.title_tokens), ensure_ascii=False)
        serialized_skill_terms = json.dumps(list(feature.skill_terms), ensure_ascii=False)
        serialized_required_skill_terms = json.dumps(list(feature.required_skill_terms), ensure_ascii=False)
        serialized_preferred_skill_terms = json.dumps(list(feature.preferred_skill_terms), ensure_ascii=False)
        serialized_external_requirement_terms = json.dumps(list(feature.external_requirement_terms), ensure_ascii=False)
        serialized_external_technology_terms = json.dumps(list(feature.external_technology_terms), ensure_ascii=False)
        serialized_external_responsibility_terms = json.dumps(list(feature.external_responsibility_terms), ensure_ascii=False)
        serialized_location_tokens = json.dumps(list(feature.location_tokens), ensure_ascii=False)
        serialized_language_requirements = json.dumps(list(feature.language_requirements), ensure_ascii=False)
        serialized_domain_signals = json.dumps(list(feature.domain_signals), ensure_ascii=False)

        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO canonical_job_features (
                        canonical_job_id,
                        feature_version,
                        role_family,
                        job_discipline,
                        department_family,
                        title_tokens_json,
                        skill_terms_json,
                        required_skill_terms_json,
                        preferred_skill_terms_json,
                        external_requirement_terms_json,
                        external_technology_terms_json,
                        external_responsibility_terms_json,
                        location_tokens_json,
                        language_requirements_json,
                        education_level_hint,
                        years_experience_min,
                        management_track,
                        individual_contributor,
                        domain_signals_json,
                        responsibility_scope,
                        external_context_status,
                        external_context_updated_at,
                        match_readiness_score,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feature.canonical_job_id,
                        feature.feature_version,
                        feature.role_family,
                        feature.job_discipline,
                        feature.department_family,
                        serialized_title_tokens,
                        serialized_skill_terms,
                        serialized_required_skill_terms,
                        serialized_preferred_skill_terms,
                        serialized_external_requirement_terms,
                        serialized_external_technology_terms,
                        serialized_external_responsibility_terms,
                        serialized_location_tokens,
                        serialized_language_requirements,
                        feature.education_level_hint,
                        feature.years_experience_min,
                        int(feature.management_track),
                        int(feature.individual_contributor),
                        serialized_domain_signals,
                        feature.responsibility_scope,
                        feature.external_context_status,
                        feature.external_context_updated_at,
                        feature.match_readiness_score,
                        feature.created_at,
                        feature.updated_at,
                    ),
                )
        else:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE canonical_job_features
                    SET
                        feature_version = ?,
                        role_family = ?,
                        job_discipline = ?,
                        department_family = ?,
                        title_tokens_json = ?,
                        skill_terms_json = ?,
                        required_skill_terms_json = ?,
                        preferred_skill_terms_json = ?,
                        external_requirement_terms_json = ?,
                        external_technology_terms_json = ?,
                        external_responsibility_terms_json = ?,
                        location_tokens_json = ?,
                        language_requirements_json = ?,
                        education_level_hint = ?,
                        years_experience_min = ?,
                        management_track = ?,
                        individual_contributor = ?,
                        domain_signals_json = ?,
                        responsibility_scope = ?,
                        external_context_status = ?,
                        external_context_updated_at = ?,
                        match_readiness_score = ?,
                        updated_at = ?
                    WHERE canonical_job_id = ?
                    """,
                    (
                        feature.feature_version,
                        feature.role_family,
                        feature.job_discipline,
                        feature.department_family,
                        serialized_title_tokens,
                        serialized_skill_terms,
                        serialized_required_skill_terms,
                        serialized_preferred_skill_terms,
                        serialized_external_requirement_terms,
                        serialized_external_technology_terms,
                        serialized_external_responsibility_terms,
                        serialized_location_tokens,
                        serialized_language_requirements,
                        feature.education_level_hint,
                        feature.years_experience_min,
                        int(feature.management_track),
                        int(feature.individual_contributor),
                        serialized_domain_signals,
                        feature.responsibility_scope,
                        feature.external_context_status,
                        feature.external_context_updated_at,
                        feature.match_readiness_score,
                        feature.updated_at,
                        feature.canonical_job_id,
                    ),
                )

        refreshed = self.get_canonical_job_feature(canonical_job_id=feature.canonical_job_id)
        if refreshed is None:
            raise RuntimeError("Failed to reload canonical job feature.")
        return refreshed

    def list_canonical_job_features(
        self,
        *,
        active_only: bool = False,
    ) -> list[CanonicalJobFeature]:
        if active_only:
            cursor = self.connection.execute(
                """
                SELECT
                    features.id,
                    features.canonical_job_id,
                    features.feature_version,
                    features.role_family,
                    features.job_discipline,
                    features.department_family,
                    features.title_tokens_json,
                    features.skill_terms_json,
                    features.required_skill_terms_json,
                    features.preferred_skill_terms_json,
                    features.external_requirement_terms_json,
                features.external_technology_terms_json,
                features.external_responsibility_terms_json,
                features.location_tokens_json,
                    features.language_requirements_json,
                    features.education_level_hint,
                    features.years_experience_min,
                    features.management_track,
                    features.individual_contributor,
                    features.domain_signals_json,
                    features.responsibility_scope,
                    features.external_context_status,
                    features.external_context_updated_at,
                    features.match_readiness_score,
                    features.created_at,
                    features.updated_at
                FROM canonical_job_features AS features
                INNER JOIN canonical_jobs AS jobs
                    ON jobs.id = features.canonical_job_id
                WHERE jobs.is_active = 1
                ORDER BY features.match_readiness_score DESC, features.updated_at DESC, features.id DESC
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    canonical_job_id,
                    feature_version,
                    role_family,
                    job_discipline,
                    department_family,
                    title_tokens_json,
                    skill_terms_json,
                    required_skill_terms_json,
                    preferred_skill_terms_json,
                    external_requirement_terms_json,
                    external_technology_terms_json,
                    external_responsibility_terms_json,
                    location_tokens_json,
                    language_requirements_json,
                    education_level_hint,
                    years_experience_min,
                    management_track,
                    individual_contributor,
                    domain_signals_json,
                    responsibility_scope,
                    external_context_status,
                    external_context_updated_at,
                    match_readiness_score,
                    created_at,
                    updated_at
                FROM canonical_job_features
                ORDER BY match_readiness_score DESC, updated_at DESC, id DESC
                """
            )
        return [_row_to_canonical_job_feature(row) for row in cursor.fetchall()]

    def prune_canonical_job_features_for_inactive_jobs(self) -> int:
        with self.connection:
            cursor = self.connection.execute(
                """
                DELETE FROM canonical_job_features
                WHERE canonical_job_id IN (
                    SELECT id
                    FROM canonical_jobs
                    WHERE is_active = 0
                )
                """
            )
        return cursor.rowcount

    def get_subscriber_profile_feature(
        self,
        *,
        subscriber_id: int,
    ) -> SubscriberProfileFeature | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                feature_version,
                role_families_json,
                discipline_preferences_json,
                title_tokens_json,
                skill_terms_json,
                experience_evidence_terms_json,
                preferred_location_tokens_json,
                language_capabilities_json,
                education_level,
                years_experience_total,
                remote_preference,
                management_preference,
                profile_strength_score,
                seniority_level,
                domain_signals_json,
                responsibility_scope,
                ownership_signals_json,
                impact_signals_json,
                created_at,
                updated_at
            FROM subscriber_profile_features
            WHERE subscriber_id = ?
            """,
            (subscriber_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber_profile_feature(row)

    def upsert_subscriber_profile_feature(
        self,
        feature: SubscriberProfileFeature,
    ) -> SubscriberProfileFeature:
        existing = self.get_subscriber_profile_feature(subscriber_id=feature.subscriber_id)
        serialized_role_families = json.dumps(list(feature.role_families), ensure_ascii=False)
        serialized_discipline_preferences = json.dumps(
            list(feature.discipline_preferences),
            ensure_ascii=False,
        )
        serialized_title_tokens = json.dumps(list(feature.title_tokens), ensure_ascii=False)
        serialized_skill_terms = json.dumps(list(feature.skill_terms), ensure_ascii=False)
        serialized_experience_evidence_terms = json.dumps(
            list(feature.experience_evidence_terms),
            ensure_ascii=False,
        )
        serialized_preferred_location_tokens = json.dumps(
            list(feature.preferred_location_tokens),
            ensure_ascii=False,
        )
        serialized_language_capabilities = json.dumps(
            list(feature.language_capabilities),
            ensure_ascii=False,
        )
        management_preference = (
            None if feature.management_preference is None else int(feature.management_preference)
        )
        serialized_domain_signals = json.dumps(list(feature.domain_signals), ensure_ascii=False)
        serialized_ownership_signals = json.dumps(list(feature.ownership_signals), ensure_ascii=False)
        serialized_impact_signals = json.dumps(list(feature.impact_signals), ensure_ascii=False)

        if existing is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO subscriber_profile_features (
                        subscriber_id,
                        feature_version,
                        role_families_json,
                        discipline_preferences_json,
                        title_tokens_json,
                        skill_terms_json,
                        experience_evidence_terms_json,
                        preferred_location_tokens_json,
                        language_capabilities_json,
                        education_level,
                        years_experience_total,
                        remote_preference,
                        management_preference,
                        profile_strength_score,
                        seniority_level,
                        domain_signals_json,
                        responsibility_scope,
                        ownership_signals_json,
                        impact_signals_json,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feature.subscriber_id,
                        feature.feature_version,
                        serialized_role_families,
                        serialized_discipline_preferences,
                        serialized_title_tokens,
                        serialized_skill_terms,
                        serialized_experience_evidence_terms,
                        serialized_preferred_location_tokens,
                        serialized_language_capabilities,
                        feature.education_level,
                        feature.years_experience_total,
                        feature.remote_preference,
                        management_preference,
                        feature.profile_strength_score,
                        feature.seniority_level,
                        serialized_domain_signals,
                        feature.responsibility_scope,
                        serialized_ownership_signals,
                        serialized_impact_signals,
                        feature.created_at,
                        feature.updated_at,
                    ),
                )
        else:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE subscriber_profile_features
                    SET
                        feature_version = ?,
                        role_families_json = ?,
                        discipline_preferences_json = ?,
                        title_tokens_json = ?,
                        skill_terms_json = ?,
                        experience_evidence_terms_json = ?,
                        preferred_location_tokens_json = ?,
                        language_capabilities_json = ?,
                        education_level = ?,
                        years_experience_total = ?,
                        remote_preference = ?,
                        management_preference = ?,
                        profile_strength_score = ?,
                        seniority_level = ?,
                        domain_signals_json = ?,
                        responsibility_scope = ?,
                        ownership_signals_json = ?,
                        impact_signals_json = ?,
                        updated_at = ?
                    WHERE subscriber_id = ?
                    """,
                    (
                        feature.feature_version,
                        serialized_role_families,
                        serialized_discipline_preferences,
                        serialized_title_tokens,
                        serialized_skill_terms,
                        serialized_experience_evidence_terms,
                        serialized_preferred_location_tokens,
                        serialized_language_capabilities,
                        feature.education_level,
                        feature.years_experience_total,
                        feature.remote_preference,
                        management_preference,
                        feature.profile_strength_score,
                        feature.seniority_level,
                        serialized_domain_signals,
                        feature.responsibility_scope,
                        serialized_ownership_signals,
                        serialized_impact_signals,
                        feature.updated_at,
                        feature.subscriber_id,
                    ),
                )

        refreshed = self.get_subscriber_profile_feature(subscriber_id=feature.subscriber_id)
        if refreshed is None:
            raise RuntimeError("Failed to reload subscriber profile feature.")
        return refreshed

    def get_subscriber_job_interaction(
        self,
        *,
        subscriber_id: int,
        api_job_id: int,
    ) -> SubscriberJobInteraction | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                api_job_id,
                job_kind,
                canonical_job_id,
                legacy_job_id,
                impression_count,
                open_count,
                save_count,
                apply_click_count,
                total_dwell_seconds,
                max_dwell_seconds,
                affinity_score,
                first_interacted_at,
                last_interacted_at,
                last_source_surface,
                created_at,
                updated_at
            FROM subscriber_job_interactions
            WHERE subscriber_id = ?
              AND api_job_id = ?
            """,
            (subscriber_id, api_job_id),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber_job_interaction(row)

    def record_subscriber_job_interaction(
        self,
        *,
        subscriber_id: int,
        api_job_id: int,
        job_kind: str,
        canonical_job_id: int | None,
        legacy_job_id: int | None,
        interaction_type: str,
        interacted_at: str,
        source_surface: str | None = None,
        dwell_seconds: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SubscriberJobInteraction:
        if interaction_type not in {"impression", "open", "dwell", "save", "apply_click"}:
            raise ValueError(f"Unsupported interaction type: {interaction_type}")
        if job_kind not in {"legacy", "canonical"}:
            raise ValueError(f"Unsupported job kind: {job_kind}")
        normalized_dwell_seconds = 0 if dwell_seconds is None else int(dwell_seconds)
        if normalized_dwell_seconds < 0:
            raise ValueError("dwell_seconds must be non-negative.")
        metadata_json = json.dumps(metadata or {}, sort_keys=True)

        existing = self.get_subscriber_job_interaction(
            subscriber_id=subscriber_id,
            api_job_id=api_job_id,
        )
        impression_increment = 1 if interaction_type == "impression" else 0
        open_increment = 1 if interaction_type == "open" else 0
        save_increment = 1 if interaction_type == "save" else 0
        apply_increment = 1 if interaction_type == "apply_click" else 0
        dwell_increment = normalized_dwell_seconds if interaction_type == "dwell" else 0
        max_dwell_increment = normalized_dwell_seconds if interaction_type == "dwell" else 0

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_job_interaction_events (
                    subscriber_id,
                    api_job_id,
                    job_kind,
                    canonical_job_id,
                    legacy_job_id,
                    interaction_type,
                    source_surface,
                    dwell_seconds,
                    metadata_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscriber_id,
                    api_job_id,
                    job_kind,
                    canonical_job_id,
                    legacy_job_id,
                    interaction_type,
                    source_surface,
                    normalized_dwell_seconds if interaction_type == "dwell" else None,
                    metadata_json,
                    interacted_at,
                ),
            )

            if existing is None:
                affinity_score = _compute_behavioral_affinity_score(
                    impression_count=impression_increment,
                    open_count=open_increment,
                    save_count=save_increment,
                    apply_click_count=apply_increment,
                    total_dwell_seconds=dwell_increment,
                )
                self.connection.execute(
                    """
                    INSERT INTO subscriber_job_interactions (
                        subscriber_id,
                        api_job_id,
                        job_kind,
                        canonical_job_id,
                        legacy_job_id,
                        impression_count,
                        open_count,
                        save_count,
                        apply_click_count,
                        total_dwell_seconds,
                        max_dwell_seconds,
                        affinity_score,
                        first_interacted_at,
                        last_interacted_at,
                        last_source_surface,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        api_job_id,
                        job_kind,
                        canonical_job_id,
                        legacy_job_id,
                        impression_increment,
                        open_increment,
                        save_increment,
                        apply_increment,
                        dwell_increment,
                        max_dwell_increment,
                        affinity_score,
                        interacted_at,
                        interacted_at,
                        source_surface,
                        interacted_at,
                        interacted_at,
                    ),
                )
            else:
                impression_count = existing.impression_count + impression_increment
                open_count = existing.open_count + open_increment
                save_count = existing.save_count + save_increment
                apply_click_count = existing.apply_click_count + apply_increment
                total_dwell_seconds = existing.total_dwell_seconds + dwell_increment
                max_dwell_seconds = max(existing.max_dwell_seconds, max_dwell_increment)
                affinity_score = _compute_behavioral_affinity_score(
                    impression_count=impression_count,
                    open_count=open_count,
                    save_count=save_count,
                    apply_click_count=apply_click_count,
                    total_dwell_seconds=total_dwell_seconds,
                )
                self.connection.execute(
                    """
                    UPDATE subscriber_job_interactions
                    SET
                        job_kind = ?,
                        canonical_job_id = ?,
                        legacy_job_id = ?,
                        impression_count = ?,
                        open_count = ?,
                        save_count = ?,
                        apply_click_count = ?,
                        total_dwell_seconds = ?,
                        max_dwell_seconds = ?,
                        affinity_score = ?,
                        last_interacted_at = ?,
                        last_source_surface = ?,
                        updated_at = ?
                    WHERE subscriber_id = ?
                      AND api_job_id = ?
                    """,
                    (
                        job_kind,
                        canonical_job_id,
                        legacy_job_id,
                        impression_count,
                        open_count,
                        save_count,
                        apply_click_count,
                        total_dwell_seconds,
                        max_dwell_seconds,
                        affinity_score,
                        interacted_at,
                        source_surface or existing.last_source_surface,
                        interacted_at,
                        subscriber_id,
                        api_job_id,
                    ),
                )

        refreshed = self.get_subscriber_job_interaction(
            subscriber_id=subscriber_id,
            api_job_id=api_job_id,
        )
        if refreshed is None:
            raise RuntimeError("Failed to reload subscriber job interaction.")
        return refreshed

    def list_subscriber_job_interaction_events(
        self,
        *,
        subscriber_id: int,
        api_job_id: int | None = None,
        limit: int = 100,
    ) -> list[SubscriberJobInteractionEvent]:
        params: list[Any] = [subscriber_id]
        query = """
            SELECT
                id,
                subscriber_id,
                api_job_id,
                job_kind,
                canonical_job_id,
                legacy_job_id,
                interaction_type,
                source_surface,
                dwell_seconds,
                metadata_json,
                created_at
            FROM subscriber_job_interaction_events
            WHERE subscriber_id = ?
        """
        if api_job_id is not None:
            query += " AND api_job_id = ?"
            params.append(api_job_id)
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        cursor = self.connection.execute(query, tuple(params))
        return [_row_to_subscriber_job_interaction_event(row) for row in cursor.fetchall()]

    def list_subscriber_job_behavioral_affinity_scores(
        self,
        *,
        subscriber_id: int,
        canonical_job_ids: Iterable[int] | None = None,
        active_only: bool = True,
    ) -> dict[int, float]:
        params: list[Any] = [subscriber_id]
        query = """
            SELECT
                interactions.canonical_job_id AS canonical_job_id,
                interactions.affinity_score AS affinity_score
            FROM subscriber_job_interactions AS interactions
        """
        if active_only:
            query += """
                INNER JOIN canonical_jobs AS jobs
                    ON jobs.id = interactions.canonical_job_id
            """
        query += " WHERE interactions.subscriber_id = ? AND interactions.canonical_job_id IS NOT NULL"
        if active_only:
            query += " AND jobs.is_active = 1"
        normalized_ids = tuple(sorted({job_id for job_id in (canonical_job_ids or ()) if job_id > 0}))
        if normalized_ids:
            placeholders = ", ".join("?" for _ in normalized_ids)
            query += f" AND interactions.canonical_job_id IN ({placeholders})"
            params.extend(normalized_ids)
        cursor = self.connection.execute(query, tuple(params))
        return {int(row["canonical_job_id"]): float(row["affinity_score"]) for row in cursor.fetchall()}


    def list_matchable_canonical_job_feature_pairs(
        self,
        *,
        active_only: bool = True,
        limit: int | None = None,
    ) -> list[tuple[CanonicalJob, CanonicalJobFeature]]:
        where_clause = "WHERE jobs.is_active = 1" if active_only else ""
        query = f"""
            SELECT
                jobs.id AS job_id,
                jobs.canonical_key,
                jobs.normalized_title,
                jobs.normalized_company_name,
                jobs.display_title,
                jobs.display_company_name,
                jobs.location_city,
                jobs.district,
                jobs.country,
                jobs.workplace_type,
                jobs.employment_type,
                jobs.seniority,
                jobs.category,
                jobs.department,
                jobs.description_text,
                jobs.description_html,
                jobs.posted_at,
                jobs.apply_url,
                jobs.trust_score,
                jobs.freshness_score,
                jobs.is_active AS job_is_active,
                jobs.created_at AS job_created_at,
                jobs.updated_at AS job_updated_at,
                features.id AS feature_id,
                features.canonical_job_id,
                features.feature_version,
                features.role_family,
                features.job_discipline,
                features.department_family,
                features.title_tokens_json,
                features.skill_terms_json,
                features.required_skill_terms_json,
                features.preferred_skill_terms_json,
                features.external_requirement_terms_json,
                features.external_technology_terms_json,
                features.external_responsibility_terms_json,
                features.location_tokens_json,
                features.language_requirements_json,
                features.education_level_hint,
                features.years_experience_min,
                features.management_track,
                features.individual_contributor,
                features.domain_signals_json,
                features.responsibility_scope,
                features.external_context_status,
                features.external_context_updated_at,
                features.match_readiness_score,
                features.created_at AS feature_created_at,
                features.updated_at AS feature_updated_at
            FROM canonical_jobs AS jobs
            INNER JOIN canonical_job_features AS features
                ON features.canonical_job_id = jobs.id
            {where_clause}
            ORDER BY
                ((jobs.trust_score * 0.35) + (jobs.freshness_score * 0.25) + (features.match_readiness_score * 0.40)) DESC,
                jobs.updated_at DESC,
                jobs.id DESC
        """
        params: tuple[int, ...] = ()
        if limit is not None:
            query += "\n LIMIT ?"
            params = (limit,)

        cursor = self.connection.execute(query, params)
        results: list[tuple[CanonicalJob, CanonicalJobFeature]] = []
        for row in cursor.fetchall():
            job = CanonicalJob(
                id=row["job_id"],
                canonical_key=row["canonical_key"],
                normalized_title=row["normalized_title"],
                normalized_company_name=row["normalized_company_name"],
                display_title=row["display_title"],
                display_company_name=row["display_company_name"],
                location_city=row["location_city"],
                district=row["district"],
                country=row["country"],
                workplace_type=row["workplace_type"],
                employment_type=row["employment_type"],
                seniority=row["seniority"],
                category=row["category"],
                department=row["department"],
                description_text=row["description_text"],
                description_html=row["description_html"],
                posted_at=row["posted_at"],
                apply_url=row["apply_url"],
                trust_score=float(row["trust_score"]),
                freshness_score=float(row["freshness_score"]),
                is_active=bool(row["job_is_active"]),
                created_at=row["job_created_at"],
                updated_at=row["job_updated_at"],
            )
            feature = CanonicalJobFeature(
                id=row["feature_id"],
                canonical_job_id=row["canonical_job_id"],
                feature_version=row["feature_version"],
                role_family=row["role_family"],
                job_discipline=row["job_discipline"],
                department_family=row["department_family"],
                title_tokens=tuple(json.loads(row["title_tokens_json"] or "[]")),
                skill_terms=tuple(json.loads(row["skill_terms_json"] or "[]")),
                required_skill_terms=tuple(json.loads(row["required_skill_terms_json"] or "[]")),
                preferred_skill_terms=tuple(json.loads(row["preferred_skill_terms_json"] or "[]")),
                external_requirement_terms=tuple(json.loads(row["external_requirement_terms_json"] or "[]")),
                external_technology_terms=tuple(json.loads(row["external_technology_terms_json"] or "[]")),
                external_responsibility_terms=tuple(json.loads(row["external_responsibility_terms_json"] or "[]")),
                location_tokens=tuple(json.loads(row["location_tokens_json"] or "[]")),
                language_requirements=tuple(json.loads(row["language_requirements_json"] or "[]")),
                education_level_hint=row["education_level_hint"],
                years_experience_min=row["years_experience_min"],
                management_track=bool(row["management_track"]),
                individual_contributor=bool(row["individual_contributor"]),
                domain_signals=tuple(json.loads(row["domain_signals_json"] or "[]")),
                responsibility_scope=row["responsibility_scope"],
                external_context_status=row["external_context_status"],
                external_context_updated_at=row["external_context_updated_at"],
                match_readiness_score=float(row["match_readiness_score"]),
                created_at=row["feature_created_at"],
                updated_at=row["feature_updated_at"],
            )
            results.append((job, feature))
        return results

    def upsert_canonical_job_link(self, link: CanonicalJobLink) -> CanonicalJobLink:
        cursor = self.connection.execute(
            """
            SELECT
                canonical_job_id,
                source_job_id,
                merge_reason,
                confidence,
                created_at,
                updated_at
            FROM canonical_job_links
            WHERE source_job_id = ?
            """,
            (link.source_job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO canonical_job_links (
                        canonical_job_id,
                        source_job_id,
                        merge_reason,
                        confidence,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        link.canonical_job_id,
                        link.source_job_id,
                        link.merge_reason,
                        link.confidence,
                        link.created_at,
                        link.updated_at,
                    ),
                )
        else:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE canonical_job_links
                    SET
                        canonical_job_id = ?,
                        merge_reason = ?,
                        confidence = ?,
                        updated_at = ?
                    WHERE source_job_id = ?
                    """,
                    (
                        link.canonical_job_id,
                        link.merge_reason,
                        link.confidence,
                        link.updated_at,
                        link.source_job_id,
                    ),
                )

        cursor = self.connection.execute(
            """
            SELECT
                canonical_job_id,
                source_job_id,
                merge_reason,
                confidence,
                created_at,
                updated_at
            FROM canonical_job_links
            WHERE source_job_id = ?
            """,
            (link.source_job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to reload canonical job link.")
        return _row_to_canonical_job_link(row)

    def list_canonical_job_links(self, *, canonical_job_id: int) -> list[CanonicalJobLink]:
        cursor = self.connection.execute(
            """
            SELECT
                canonical_job_id,
                source_job_id,
                merge_reason,
                confidence,
                created_at,
                updated_at
            FROM canonical_job_links
            WHERE canonical_job_id = ?
            ORDER BY confidence DESC, source_job_id ASC
            """,
            (canonical_job_id,),
        )
        return [_row_to_canonical_job_link(row) for row in cursor.fetchall()]

    def prune_canonical_job_links_for_inactive_source_records(self) -> int:
        with self.connection:
            cursor = self.connection.execute(
                """
                DELETE FROM canonical_job_links
                WHERE source_job_id IN (
                    SELECT id
                    FROM job_source_records
                    WHERE is_active = 0
                )
                """
            )
        return cursor.rowcount

    def mark_missing_canonical_jobs_inactive(
        self,
        *,
        seen_canonical_keys: Iterable[str],
        updated_at: str,
    ) -> int:
        canonical_keys = tuple(seen_canonical_keys)

        if canonical_keys:
            placeholders = ", ".join(["?"] * len(canonical_keys))
            query = f"""
                UPDATE canonical_jobs
                SET is_active = 0, updated_at = ?
                WHERE is_active = 1
                  AND canonical_key NOT IN ({placeholders})
            """
            params: tuple[str, ...] = (updated_at, *canonical_keys)
        else:
            query = """
                UPDATE canonical_jobs
                SET is_active = 0, updated_at = ?
                WHERE is_active = 1
            """
            params = (updated_at,)

        with self.connection:
            cursor = self.connection.execute(query, params)
        return cursor.rowcount

    def get_subscriber_by_id(self, subscriber_id: int) -> Subscriber | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                password_hash,
                password_updated_at,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            WHERE id = ?
            """,
            (subscriber_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber(row)

    def create_subscriber_magic_link(
        self,
        *,
        subscriber_id: int,
        token_hash: str,
        expires_at: str,
        created_at: str,
    ) -> SubscriberMagicLinkToken:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_magic_links (
                    subscriber_id,
                    token_hash,
                    expires_at,
                    consumed_at,
                    created_at
                )
                VALUES (?, ?, ?, NULL, ?)
                """,
                (
                    subscriber_id,
                    token_hash,
                    expires_at,
                    created_at,
                ),
            )

        return SubscriberMagicLinkToken(
            id=int(cursor.lastrowid),
            subscriber_id=subscriber_id,
            token_hash=token_hash,
            expires_at=expires_at,
            consumed_at=None,
            created_at=created_at,
        )

    def get_subscriber_magic_link_by_hash(
        self,
        token_hash: str,
    ) -> SubscriberMagicLinkToken | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                token_hash,
                expires_at,
                consumed_at,
                created_at
            FROM subscriber_magic_links
            WHERE token_hash = ?
            """,
            (token_hash,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return SubscriberMagicLinkToken(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            consumed_at=row["consumed_at"],
            created_at=row["created_at"],
        )

    def consume_subscriber_magic_link(
        self,
        link_id: int,
        *,
        consumed_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscriber_magic_links
                SET consumed_at = ?
                WHERE id = ?
                  AND consumed_at IS NULL
                """,
                (consumed_at, link_id),
            )
        return cursor.rowcount > 0


    def create_or_replace_subscriber_signup_verification(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str,
        verification_code_hash: str,
        expires_at: str,
        created_at: str,
        updated_at: str,
    ) -> SubscriberSignupVerification:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_signup_verifications (
                    email,
                    full_name,
                    password_hash,
                    verification_code_hash,
                    expires_at,
                    consumed_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    full_name = excluded.full_name,
                    password_hash = excluded.password_hash,
                    verification_code_hash = excluded.verification_code_hash,
                    expires_at = excluded.expires_at,
                    consumed_at = NULL,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    email,
                    full_name,
                    password_hash,
                    verification_code_hash,
                    expires_at,
                    created_at,
                    updated_at,
                ),
            )

        verification = self.get_subscriber_signup_verification_by_email(email)
        if verification is None:
            raise RuntimeError(
                "Signup verification upsert succeeded but record could not be reloaded."
            )
        return verification

    def get_subscriber_signup_verification_by_email(
        self,
        email: str,
    ) -> SubscriberSignupVerification | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                email,
                full_name,
                password_hash,
                verification_code_hash,
                expires_at,
                consumed_at,
                created_at,
                updated_at
            FROM subscriber_signup_verifications
            WHERE email = ?
            """,
            (email,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber_signup_verification(row)

    def consume_subscriber_signup_verification(
        self,
        verification_id: int,
        *,
        consumed_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscriber_signup_verifications
                SET
                    consumed_at = ?,
                    updated_at = ?
                WHERE id = ?
                  AND consumed_at IS NULL
                """,
                (consumed_at, consumed_at, verification_id),
            )
        return cursor.rowcount > 0

    def create_subscriber_password_reset_token(
        self,
        *,
        subscriber_id: int,
        token_hash: str,
        expires_at: str,
        created_at: str,
    ) -> SubscriberPasswordResetToken:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_password_reset_tokens (
                    subscriber_id,
                    token_hash,
                    expires_at,
                    consumed_at,
                    created_at
                )
                VALUES (?, ?, ?, NULL, ?)
                """,
                (
                    subscriber_id,
                    token_hash,
                    expires_at,
                    created_at,
                ),
            )

        return SubscriberPasswordResetToken(
            id=int(cursor.lastrowid),
            subscriber_id=subscriber_id,
            token_hash=token_hash,
            expires_at=expires_at,
            consumed_at=None,
            created_at=created_at,
        )

    def get_subscriber_password_reset_token_by_hash(
        self,
        token_hash: str,
    ) -> SubscriberPasswordResetToken | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                subscriber_id,
                token_hash,
                expires_at,
                consumed_at,
                created_at
            FROM subscriber_password_reset_tokens
            WHERE token_hash = ?
            """,
            (token_hash,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_subscriber_password_reset_token(row)

    def consume_subscriber_password_reset_token(
        self,
        token_id: int,
        *,
        consumed_at: str,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscriber_password_reset_tokens
                SET consumed_at = ?
                WHERE id = ?
                  AND consumed_at IS NULL
                """,
                (consumed_at, token_id),
            )
        return cursor.rowcount > 0

    def list_jobs_paginated(
        self,
        *,
        q: str | None = None,
        source_name: str | None = None,
        company_name: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[JobRecord], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        normalized_q = q.strip() if q else ""
        if normalized_q:
            pattern = f"%{normalized_q}%"
            where_clauses.append(
                """
                (
                    title LIKE ?
                    OR company_name LIKE ?
                    OR COALESCE(location, '') LIKE ?
                    OR canonical_url LIKE ?
                )
                """
            )
            params.extend([pattern, pattern, pattern, pattern])

        if source_name:
            where_clauses.append("source_name = ?")
            params.append(source_name)

        if company_name:
            where_clauses.append("company_name = ?")
            params.append(company_name)

        if is_active is not None:
            where_clauses.append("is_active = ?")
            params.append(int(is_active))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM jobs
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
            SELECT
                id,
                source_name,
                title,
                company_name,
                location,
                canonical_url,
                source_type,
                source_job_id,
                raw_posted_at,
                posted_at,
                fingerprint,
                first_seen_at,
                last_seen_at,
                is_active,
                scraped_at
            FROM jobs
            {where_sql}
            ORDER BY first_seen_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_job_record(row) for row in cursor.fetchall()], total_items)

    def list_crawl_runs_paginated(
        self,
        *,
        source_name: str | None = None,
        success: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[CrawlRun], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        if source_name:
            where_clauses.append("source_name = ?")
            params.append(source_name)

        if success is not None:
            where_clauses.append("success = ?")
            params.append(int(success))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM crawl_runs
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
            SELECT
                id,
                started_at,
                finished_at,
                source_name,
                success,
                notes
            FROM crawl_runs
            {where_sql}
            ORDER BY started_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_crawl_run(row) for row in cursor.fetchall()], total_items)

    def list_notification_runs_paginated(
        self,
        *,
        notification_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[NotificationRun], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        if notification_type:
            where_clauses.append("notification_type = ?")
            params.append(notification_type)

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM notification_runs
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
            SELECT
                id,
                notification_type,
                started_at,
                finished_at,
                status,
                recipient_count,
                new_jobs_count,
                since,
                subject,
                error_message
            FROM notification_runs
            {where_sql}
            ORDER BY started_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_notification_run(row) for row in cursor.fetchall()], total_items)

    def list_subscribers_paginated(
        self,
        *,
        email_query: str | None = None,
        is_active: bool | None = None,
        digest_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Subscriber], int]:
        where_clauses: list[str] = []
        params: list[Any] = []

        normalized_query = email_query.strip() if email_query else ""
        if normalized_query:
            pattern = f"%{normalized_query}%"
            where_clauses.append(
                """
                (
                    email LIKE ?
                    OR COALESCE(full_name, '') LIKE ?
                )
                """
            )
            params.extend([pattern, pattern])

        if is_active is not None:
            where_clauses.append("is_active = ?")
            params.append(int(is_active))

        if digest_enabled is not None:
            where_clauses.append("digest_enabled = ?")
            params.append(int(digest_enabled))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM subscribers
            {where_sql}
            """,
            tuple(params),
        )
        count_row = count_cursor.fetchone()
        total_items = 0 if count_row is None else int(count_row["total_items"])

        offset = (page - 1) * page_size
        cursor = self.connection.execute(
            f"""
            SELECT
                id,
                email,
                full_name,
                password_hash,
                password_updated_at,
                is_active,
                digest_enabled,
                created_at,
                updated_at
            FROM subscribers
            {where_sql}
            ORDER BY updated_at DESC, email ASC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        )

        return ([_row_to_subscriber(row) for row in cursor.fetchall()], total_items)

    def update_subscriber_fields_by_id(
        self,
        subscriber_id: int,
        *,
        fields: dict[str, Any],
        updated_at: str,
    ) -> Subscriber | None:
        if not fields:
            raise ValueError("fields must not be empty.")

        allowed_keys = {"full_name", "password_hash", "password_updated_at", "is_active", "digest_enabled"}
        unknown_keys = sorted(set(fields) - allowed_keys)
        if unknown_keys:
            joined = ", ".join(unknown_keys)
            raise ValueError(f"Unknown subscriber update field(s): {joined}")

        assignments: list[str] = []
        params: list[Any] = []

        if "full_name" in fields:
            assignments.append("full_name = ?")
            params.append(fields["full_name"])

        if "password_hash" in fields:
            assignments.append("password_hash = ?")
            params.append(fields["password_hash"])

        if "password_updated_at" in fields:
            assignments.append("password_updated_at = ?")
            params.append(fields["password_updated_at"])

        if "is_active" in fields:
            assignments.append("is_active = ?")
            params.append(int(fields["is_active"]))

        if "digest_enabled" in fields:
            assignments.append("digest_enabled = ?")
            params.append(int(fields["digest_enabled"]))

        assignments.append("updated_at = ?")
        params.append(updated_at)
        params.append(subscriber_id)

        with self.connection:
            cursor = self.connection.execute(
                f"""
                UPDATE subscribers
                SET {", ".join(assignments)}
                WHERE id = ?
                """,
                tuple(params),
            )

        if cursor.rowcount == 0:
            return None

        return self.get_subscriber_by_id(subscriber_id)


    def get_retrieval_source(self, source_id: int) -> RetrievalSource | None:
        cursor = self.connection.execute(
            """
            SELECT
                id, subscriber_id, source_type, source_ref, title, locale, status,
                checksum, metadata_json, created_at, updated_at, last_ingested_at, error_message
            FROM retrieval_sources
            WHERE id = ?
            """,
            (source_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_retrieval_source(row)

    def get_retrieval_source_by_key(
        self,
        subscriber_id: int,
        source_type: str,
        source_ref: str,
    ) -> RetrievalSource | None:
        cursor = self.connection.execute(
            """
            SELECT
                id, subscriber_id, source_type, source_ref, title, locale, status,
                checksum, metadata_json, created_at, updated_at, last_ingested_at, error_message
            FROM retrieval_sources
            WHERE subscriber_id = ? AND source_type = ? AND source_ref = ?
            """,
            (subscriber_id, source_type, source_ref),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_retrieval_source(row)

    def list_retrieval_sources(
        self,
        subscriber_id: int,
        *,
        source_type: str | None = None,
    ) -> list[RetrievalSource]:
        if source_type is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id, subscriber_id, source_type, source_ref, title, locale, status,
                    checksum, metadata_json, created_at, updated_at, last_ingested_at, error_message
                FROM retrieval_sources
                WHERE subscriber_id = ?
                ORDER BY updated_at DESC, id DESC
                """,
                (subscriber_id,),
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id, subscriber_id, source_type, source_ref, title, locale, status,
                    checksum, metadata_json, created_at, updated_at, last_ingested_at, error_message
                FROM retrieval_sources
                WHERE subscriber_id = ? AND source_type = ?
                ORDER BY updated_at DESC, id DESC
                """,
                (subscriber_id, source_type),
            )
        return [_row_to_retrieval_source(row) for row in cursor.fetchall()]

    def upsert_retrieval_source(
        self,
        subscriber_id: int,
        *,
        source_type: str,
        source_ref: str,
        title: str | None,
        locale: str | None,
        status: str,
        checksum: str | None,
        metadata_json: dict[str, Any] | None,
        updated_at: str,
        last_ingested_at: str | None = None,
        error_message: str | None = None,
    ) -> RetrievalSource:
        metadata_payload = json.dumps(metadata_json or {}, ensure_ascii=False, sort_keys=True)
        existing = self.get_retrieval_source_by_key(subscriber_id, source_type, source_ref)

        with self.connection:
            if existing is None:
                cursor = self.connection.execute(
                    """
                    INSERT INTO retrieval_sources (
                        subscriber_id, source_type, source_ref, title, locale, status, checksum,
                        metadata_json, created_at, updated_at, last_ingested_at, error_message
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        source_type,
                        source_ref,
                        title,
                        locale,
                        status,
                        checksum,
                        metadata_payload,
                        updated_at,
                        updated_at,
                        last_ingested_at,
                        error_message,
                    ),
                )
                source_id = int(cursor.lastrowid)
            else:
                source_id = existing.id or 0
                self.connection.execute(
                    """
                    UPDATE retrieval_sources
                    SET title = ?, locale = ?, status = ?, checksum = ?, metadata_json = ?,
                        updated_at = ?, last_ingested_at = ?, error_message = ?
                    WHERE id = ?
                    """,
                    (
                        title,
                        locale,
                        status,
                        checksum,
                        metadata_payload,
                        updated_at,
                        last_ingested_at,
                        error_message,
                        source_id,
                    ),
                )

        source = self.get_retrieval_source(source_id)
        if source is None:
            raise RuntimeError("Failed to load retrieval source after upsert.")
        return source

    def update_retrieval_source_lifecycle(
        self,
        source_id: int,
        *,
        status: str,
        updated_at: str,
        last_ingested_at: str | None = None,
        error_message: str | None = None,
    ) -> RetrievalSource:
        with self.connection:
            self.connection.execute(
                """
                UPDATE retrieval_sources
                SET status = ?, updated_at = ?, last_ingested_at = COALESCE(?, last_ingested_at), error_message = ?
                WHERE id = ?
                """,
                (status, updated_at, last_ingested_at, error_message, source_id),
            )

        source = self.get_retrieval_source(source_id)
        if source is None:
            raise RuntimeError("Failed to load retrieval source after lifecycle update.")
        return source

    def get_retrieval_document(self, document_id: int) -> RetrievalDocument | None:
        cursor = self.connection.execute(
            """
            SELECT id, source_id, document_kind, title, body_text, metadata_json, checksum, status, version, created_at, updated_at
            FROM retrieval_documents
            WHERE id = ?
            """,
            (document_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_retrieval_document(row)

    def get_retrieval_document_by_kind(
        self,
        source_id: int,
        document_kind: str,
    ) -> RetrievalDocument | None:
        cursor = self.connection.execute(
            """
            SELECT id, source_id, document_kind, title, body_text, metadata_json, checksum, status, version, created_at, updated_at
            FROM retrieval_documents
            WHERE source_id = ? AND document_kind = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (source_id, document_kind),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_retrieval_document(row)

    def list_retrieval_documents(self, source_id: int) -> list[RetrievalDocument]:
        cursor = self.connection.execute(
            """
            SELECT id, source_id, document_kind, title, body_text, metadata_json, checksum, status, version, created_at, updated_at
            FROM retrieval_documents
            WHERE source_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (source_id,),
        )
        return [_row_to_retrieval_document(row) for row in cursor.fetchall()]

    def upsert_retrieval_document(
        self,
        source_id: int,
        *,
        document_kind: str,
        title: str | None,
        body_text: str,
        metadata_json: dict[str, Any] | None,
        checksum: str | None,
        status: str,
        version: int,
        updated_at: str,
    ) -> RetrievalDocument:
        metadata_payload = json.dumps(metadata_json or {}, ensure_ascii=False, sort_keys=True)
        existing = self.get_retrieval_document_by_kind(source_id, document_kind)

        with self.connection:
            if existing is None:
                cursor = self.connection.execute(
                    """
                    INSERT INTO retrieval_documents (
                        source_id, document_kind, title, body_text, metadata_json, checksum, status, version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (source_id, document_kind, title, body_text, metadata_payload, checksum, status, version, updated_at, updated_at),
                )
                document_id = int(cursor.lastrowid)
            else:
                document_id = existing.id or 0
                self.connection.execute(
                    """
                    UPDATE retrieval_documents
                    SET title = ?, body_text = ?, metadata_json = ?, checksum = ?, status = ?, version = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, body_text, metadata_payload, checksum, status, version, updated_at, document_id),
                )

        document = self.get_retrieval_document(document_id)
        if document is None:
            raise RuntimeError("Failed to load retrieval document after upsert.")
        return document

    def update_retrieval_document_lifecycle(
        self,
        document_id: int,
        *,
        status: str,
        updated_at: str,
        checksum: str | None = None,
        version: int | None = None,
    ) -> RetrievalDocument:
        current = self.get_retrieval_document(document_id)
        if current is None:
            raise RuntimeError("Retrieval document not found for lifecycle update.")

        with self.connection:
            self.connection.execute(
                """
                UPDATE retrieval_documents
                SET checksum = ?, status = ?, version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    checksum if checksum is not None else current.checksum,
                    status,
                    version if version is not None else current.version,
                    updated_at,
                    document_id,
                ),
            )

        document = self.get_retrieval_document(document_id)
        if document is None:
            raise RuntimeError("Failed to load retrieval document after lifecycle update.")
        return document

    def list_retrieval_chunks(self, document_id: int) -> list[RetrievalChunk]:
        cursor = self.connection.execute(
            """
            SELECT id, document_id, chunk_index, content, token_estimate, metadata_json, embedding_status, created_at
            FROM retrieval_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC, id ASC
            """,
            (document_id,),
        )
        return [_row_to_retrieval_chunk(row) for row in cursor.fetchall()]

    def replace_retrieval_chunks(
        self,
        document_id: int,
        *,
        chunks: Iterable[RetrievalChunk],
        created_at: str,
    ) -> list[RetrievalChunk]:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM retrieval_embedding_jobs
                WHERE chunk_id IN (SELECT id FROM retrieval_chunks WHERE document_id = ?)
                """,
                (document_id,),
            )
            self.connection.execute(
                """
                DELETE FROM retrieval_embeddings
                WHERE chunk_id IN (SELECT id FROM retrieval_chunks WHERE document_id = ?)
                """,
                (document_id,),
            )
            self.connection.execute(
                "DELETE FROM retrieval_chunks WHERE document_id = ?",
                (document_id,),
            )

            for index, chunk in enumerate(chunks):
                metadata_payload = json.dumps(chunk.metadata_json or {}, ensure_ascii=False, sort_keys=True)
                self.connection.execute(
                    """
                    INSERT INTO retrieval_chunks (
                        document_id, chunk_index, content, token_estimate, metadata_json, embedding_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        chunk.chunk_index if chunk.chunk_index >= 0 else index,
                        chunk.content,
                        chunk.token_estimate,
                        metadata_payload,
                        chunk.embedding_status,
                        created_at,
                    ),
                )

        return self.list_retrieval_chunks(document_id)

    def create_retrieval_embedding(
        self,
        chunk_id: int,
        *,
        provider: str,
        model: str,
        vector_ref: str | None,
        vector_json: str | None,
        dimensions: int | None,
        created_at: str,
    ) -> RetrievalEmbedding:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO retrieval_embeddings (
                    chunk_id, provider, model, vector_ref, vector_json, dimensions, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, provider, model, vector_ref, vector_json, dimensions, created_at),
            )

        embedding_id = int(cursor.lastrowid)
        cursor = self.connection.execute(
            """
            SELECT id, chunk_id, provider, model, vector_ref, vector_json, dimensions, created_at
            FROM retrieval_embeddings
            WHERE id = ?
            """,
            (embedding_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to load retrieval embedding after creation.")
        return _row_to_retrieval_embedding(row)

    def list_retrieval_embeddings(self, chunk_id: int) -> list[RetrievalEmbedding]:
        cursor = self.connection.execute(
            """
            SELECT id, chunk_id, provider, model, vector_ref, vector_json, dimensions, created_at
            FROM retrieval_embeddings
            WHERE chunk_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (chunk_id,),
        )
        return [_row_to_retrieval_embedding(row) for row in cursor.fetchall()]

    def get_subscriber_ai_copilot_conversation(
        self,
        subscriber_id: int,
        conversation_id: int,
    ) -> SubscriberAiCopilotConversation | None:
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, title, locale, status, created_at, updated_at, last_message_at
            FROM subscriber_ai_copilot_conversations
            WHERE id = ? AND subscriber_id = ?
            """,
            (conversation_id, subscriber_id),
        )
        row = cursor.fetchone()
        return None if row is None else _row_to_subscriber_ai_copilot_conversation(row)

    def list_subscriber_ai_copilot_conversations(
        self,
        subscriber_id: int,
        *,
        limit: int = 20,
    ) -> list[SubscriberAiCopilotConversation]:
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, title, locale, status, created_at, updated_at, last_message_at
            FROM subscriber_ai_copilot_conversations
            WHERE subscriber_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (subscriber_id, limit),
        )
        return [_row_to_subscriber_ai_copilot_conversation(row) for row in cursor.fetchall()]

    def create_subscriber_ai_copilot_conversation(
        self,
        subscriber_id: int,
        *,
        title: str,
        locale: str | None,
        created_at: str,
        updated_at: str | None = None,
        status: str = "active",
    ) -> SubscriberAiCopilotConversation:
        resolved_updated_at = updated_at or created_at
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_ai_copilot_conversations (
                    subscriber_id, title, locale, status, created_at, updated_at, last_message_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (subscriber_id, title, locale, status, created_at, resolved_updated_at, created_at),
            )
        conversation_id = int(cursor.lastrowid)
        conversation = self.get_subscriber_ai_copilot_conversation(subscriber_id, conversation_id)
        if conversation is None:
            raise RuntimeError("Failed to load copilot conversation after creation.")
        return conversation

    def update_subscriber_ai_copilot_conversation(
        self,
        subscriber_id: int,
        conversation_id: int,
        *,
        title: str | None = None,
        status: str | None = None,
        updated_at: str,
        last_message_at: str | None = None,
    ) -> SubscriberAiCopilotConversation:
        current = self.get_subscriber_ai_copilot_conversation(subscriber_id, conversation_id)
        if current is None:
            raise LookupError("Copilot conversation could not be found.")
        with self.connection:
            self.connection.execute(
                """
                UPDATE subscriber_ai_copilot_conversations
                SET title = ?, status = ?, updated_at = ?, last_message_at = ?
                WHERE id = ? AND subscriber_id = ?
                """,
                (
                    title if title is not None else current.title,
                    status if status is not None else current.status,
                    updated_at,
                    last_message_at if last_message_at is not None else current.last_message_at,
                    conversation_id,
                    subscriber_id,
                ),
            )
        updated = self.get_subscriber_ai_copilot_conversation(subscriber_id, conversation_id)
        if updated is None:
            raise RuntimeError("Failed to load copilot conversation after update.")
        return updated

    def create_subscriber_ai_copilot_message(
        self,
        subscriber_id: int,
        *,
        conversation_id: int,
        role: str,
        content: str,
        metadata_json: dict[str, Any] | None = None,
        created_at: str,
    ) -> SubscriberAiCopilotMessage:
        metadata_payload = json.dumps(metadata_json or {}, ensure_ascii=False, sort_keys=True)
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_ai_copilot_messages (
                    conversation_id, subscriber_id, role, content, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (conversation_id, subscriber_id, role, content, metadata_payload, created_at),
            )
        message_id = int(cursor.lastrowid)
        cursor = self.connection.execute(
            """
            SELECT id, conversation_id, subscriber_id, role, content, metadata_json, created_at
            FROM subscriber_ai_copilot_messages
            WHERE id = ? AND subscriber_id = ?
            """,
            (message_id, subscriber_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to load copilot message after creation.")
        return _row_to_subscriber_ai_copilot_message(row)

    def list_subscriber_ai_copilot_messages(
        self,
        subscriber_id: int,
        *,
        conversation_id: int,
        limit: int = 24,
    ) -> list[SubscriberAiCopilotMessage]:
        cursor = self.connection.execute(
            """
            SELECT id, conversation_id, subscriber_id, role, content, metadata_json, created_at
            FROM subscriber_ai_copilot_messages
            WHERE subscriber_id = ? AND conversation_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (subscriber_id, conversation_id, limit),
        )
        rows = cursor.fetchall()
        rows.reverse()
        return [_row_to_subscriber_ai_copilot_message(row) for row in rows]

    def get_career_knowledge_document_by_slug(self, slug: str) -> CareerKnowledgeDocument | None:
        cursor = self.connection.execute(
            """
            SELECT id, slug, title, category, locale, source_name, source_url, trust_level,
                   freshness_label, body_text, metadata_json, checksum, created_at, updated_at
            FROM career_knowledge_documents
            WHERE slug = ?
            """,
            (slug,),
        )
        row = cursor.fetchone()
        return None if row is None else _row_to_career_knowledge_document(row)

    def upsert_career_knowledge_document(
        self,
        *,
        slug: str,
        title: str,
        category: str,
        locale: str | None,
        source_name: str | None,
        source_url: str | None,
        trust_level: str,
        freshness_label: str,
        body_text: str,
        metadata_json: dict[str, Any] | None,
        checksum: str | None,
        updated_at: str,
    ) -> CareerKnowledgeDocument:
        metadata_payload = json.dumps(metadata_json or {}, ensure_ascii=False, sort_keys=True)
        existing = self.get_career_knowledge_document_by_slug(slug)
        with self.connection:
            if existing is None:
                cursor = self.connection.execute(
                    """
                    INSERT INTO career_knowledge_documents (
                        slug, title, category, locale, source_name, source_url, trust_level,
                        freshness_label, body_text, metadata_json, checksum, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        slug,
                        title,
                        category,
                        locale,
                        source_name,
                        source_url,
                        trust_level,
                        freshness_label,
                        body_text,
                        metadata_payload,
                        checksum,
                        updated_at,
                        updated_at,
                    ),
                )
                document_id = int(cursor.lastrowid)
            else:
                document_id = existing.id or 0
                self.connection.execute(
                    """
                    UPDATE career_knowledge_documents
                    SET title = ?, category = ?, locale = ?, source_name = ?, source_url = ?,
                        trust_level = ?, freshness_label = ?, body_text = ?, metadata_json = ?,
                        checksum = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        title,
                        category,
                        locale,
                        source_name,
                        source_url,
                        trust_level,
                        freshness_label,
                        body_text,
                        metadata_payload,
                        checksum,
                        updated_at,
                        document_id,
                    ),
                )
        cursor = self.connection.execute(
            """
            SELECT id, slug, title, category, locale, source_name, source_url, trust_level,
                   freshness_label, body_text, metadata_json, checksum, created_at, updated_at
            FROM career_knowledge_documents
            WHERE id = ?
            """,
            (document_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to load career knowledge document after upsert.")
        return _row_to_career_knowledge_document(row)

    def list_career_knowledge_documents(
        self,
        *,
        locale: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[CareerKnowledgeDocument]:
        clauses: list[str] = []
        params: list[Any] = []
        if locale is not None:
            clauses.append("(locale = ? OR locale IS NULL)")
            params.append(locale)
        if category is not None:
            clauses.append("category = ?")
            params.append(category)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor = self.connection.execute(
            f"""
            SELECT id, slug, title, category, locale, source_name, source_url, trust_level,
                   freshness_label, body_text, metadata_json, checksum, created_at, updated_at
            FROM career_knowledge_documents
            {where}
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (*params, limit),
        )
        return [_row_to_career_knowledge_document(row) for row in cursor.fetchall()]

    def get_subscriber_ai_learned_memory_by_key(
        self,
        subscriber_id: int,
        memory_key: str,
    ) -> SubscriberAiLearnedMemory | None:
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, memory_key, memory_note, source_type, confidence,
                   times_reinforced, last_observed_at, created_at, updated_at
            FROM subscriber_ai_learned_memories
            WHERE subscriber_id = ? AND memory_key = ?
            """,
            (subscriber_id, memory_key),
        )
        row = cursor.fetchone()
        return None if row is None else _row_to_subscriber_ai_learned_memory(row)

    def upsert_subscriber_ai_learned_memory(
        self,
        subscriber_id: int,
        *,
        memory_key: str,
        memory_note: str,
        source_type: str,
        confidence: float,
        observed_at: str,
    ) -> SubscriberAiLearnedMemory:
        existing = self.get_subscriber_ai_learned_memory_by_key(subscriber_id, memory_key)
        with self.connection:
            if existing is None:
                cursor = self.connection.execute(
                    """
                    INSERT INTO subscriber_ai_learned_memories (
                        subscriber_id, memory_key, memory_note, source_type, confidence,
                        times_reinforced, last_observed_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscriber_id,
                        memory_key,
                        memory_note,
                        source_type,
                        confidence,
                        1,
                        observed_at,
                        observed_at,
                        observed_at,
                    ),
                )
                memory_id = int(cursor.lastrowid)
            else:
                memory_id = existing.id or 0
                self.connection.execute(
                    """
                    UPDATE subscriber_ai_learned_memories
                    SET memory_note = ?, source_type = ?, confidence = ?,
                        times_reinforced = ?, last_observed_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        memory_note,
                        source_type,
                        max(existing.confidence, confidence),
                        existing.times_reinforced + 1,
                        observed_at,
                        observed_at,
                        memory_id,
                    ),
                )
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, memory_key, memory_note, source_type, confidence,
                   times_reinforced, last_observed_at, created_at, updated_at
            FROM subscriber_ai_learned_memories
            WHERE id = ?
            """,
            (memory_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to load learned memory after upsert.")
        return _row_to_subscriber_ai_learned_memory(row)

    def list_subscriber_ai_learned_memories(
        self,
        subscriber_id: int,
        *,
        limit: int = 20,
    ) -> list[SubscriberAiLearnedMemory]:
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, memory_key, memory_note, source_type, confidence,
                   times_reinforced, last_observed_at, created_at, updated_at
            FROM subscriber_ai_learned_memories
            WHERE subscriber_id = ?
            ORDER BY confidence DESC, updated_at DESC, id DESC
            LIMIT ?
            """,
            (subscriber_id, limit),
        )
        return [_row_to_subscriber_ai_learned_memory(row) for row in cursor.fetchall()]

    def get_job_external_context_snapshot_by_url(
        self,
        source_url: str,
    ) -> JobExternalContextSnapshot | None:
        cursor = self.connection.execute(
            """
            SELECT
                id,
                source_url,
                final_url,
                source_domain,
                fetch_status,
                http_status,
                page_title,
                site_name,
                meta_description,
                clean_text,
                content_digest,
                site_specific_requirements_json,
                company_culture_clues_json,
                responsibility_clues_json,
                technology_stack_terms_json,
                source_metadata_json,
                warning,
                fetched_at,
                expires_at,
                updated_at
            FROM job_external_context_snapshots
            WHERE source_url = ?
            """,
            (source_url,),
        )
        row = cursor.fetchone()
        return None if row is None else _row_to_job_external_context_snapshot(row)

    def upsert_job_external_context_snapshot(
        self,
        snapshot: JobExternalContextSnapshot,
    ) -> JobExternalContextSnapshot:
        existing = self.get_job_external_context_snapshot_by_url(snapshot.source_url)
        requirements_json = json.dumps(list(snapshot.site_specific_requirements), ensure_ascii=False)
        culture_json = json.dumps(list(snapshot.company_culture_clues), ensure_ascii=False)
        responsibilities_json = json.dumps(list(snapshot.responsibility_clues), ensure_ascii=False)
        technology_json = json.dumps(list(snapshot.technology_stack_terms), ensure_ascii=False)
        metadata_json = json.dumps(snapshot.source_metadata_json or {}, ensure_ascii=False, sort_keys=True)

        with self.connection:
            if existing is None:
                self.connection.execute(
                    """
                    INSERT INTO job_external_context_snapshots (
                        source_url,
                        final_url,
                        source_domain,
                        fetch_status,
                        http_status,
                        page_title,
                        site_name,
                        meta_description,
                        clean_text,
                        content_digest,
                        site_specific_requirements_json,
                        company_culture_clues_json,
                        responsibility_clues_json,
                        technology_stack_terms_json,
                        source_metadata_json,
                        warning,
                        fetched_at,
                        expires_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot.source_url,
                        snapshot.final_url,
                        snapshot.source_domain,
                        snapshot.fetch_status,
                        snapshot.http_status,
                        snapshot.page_title,
                        snapshot.site_name,
                        snapshot.meta_description,
                        snapshot.clean_text,
                        snapshot.content_digest,
                        requirements_json,
                        culture_json,
                        responsibilities_json,
                        technology_json,
                        metadata_json,
                        snapshot.warning,
                        snapshot.fetched_at,
                        snapshot.expires_at,
                        snapshot.updated_at,
                    ),
                )
            else:
                self.connection.execute(
                    """
                    UPDATE job_external_context_snapshots
                    SET
                        final_url = ?,
                        source_domain = ?,
                        fetch_status = ?,
                        http_status = ?,
                        page_title = ?,
                        site_name = ?,
                        meta_description = ?,
                        clean_text = ?,
                        content_digest = ?,
                        site_specific_requirements_json = ?,
                        company_culture_clues_json = ?,
                        responsibility_clues_json = ?,
                        technology_stack_terms_json = ?,
                        source_metadata_json = ?,
                        warning = ?,
                        fetched_at = ?,
                        expires_at = ?,
                        updated_at = ?
                    WHERE source_url = ?
                    """,
                    (
                        snapshot.final_url,
                        snapshot.source_domain,
                        snapshot.fetch_status,
                        snapshot.http_status,
                        snapshot.page_title,
                        snapshot.site_name,
                        snapshot.meta_description,
                        snapshot.clean_text,
                        snapshot.content_digest,
                        requirements_json,
                        culture_json,
                        responsibilities_json,
                        technology_json,
                        metadata_json,
                        snapshot.warning,
                        snapshot.fetched_at,
                        snapshot.expires_at,
                        snapshot.updated_at,
                        snapshot.source_url,
                    ),
                )

        refreshed = self.get_job_external_context_snapshot_by_url(snapshot.source_url)
        if refreshed is None:
            raise RuntimeError("Failed to load job external context snapshot after upsert.")
        return refreshed

    def close(self) -> None:
        self.connection.close()

    def get_retrieval_chunk(self, chunk_id: int) -> RetrievalChunk | None:
        cursor = self.connection.execute(
            """
            SELECT id, document_id, chunk_index, content, token_estimate, metadata_json, embedding_status, created_at
            FROM retrieval_chunks
            WHERE id = ?
            """,
            (chunk_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_retrieval_chunk(row)



    def update_retrieval_chunk_embedding_status(
        self,
        chunk_id: int,
        *,
        embedding_status: str,
    ) -> RetrievalChunk:
        with self.connection:
            self.connection.execute(
                """
                UPDATE retrieval_chunks
                SET embedding_status = ?
                WHERE id = ?
                """,
                (embedding_status, chunk_id),
            )

        chunk = self.get_retrieval_chunk(chunk_id)
        if chunk is None:
            raise RuntimeError("Failed to load retrieval chunk after embedding status update.")
        return chunk



    def delete_retrieval_embeddings_for_chunk(self, chunk_id: int) -> None:
        with self.connection:
            self.connection.execute(
                "DELETE FROM retrieval_embeddings WHERE chunk_id = ?",
                (chunk_id,),
            )



    def list_retrieval_search_candidates(
        self,
        *,
        subscriber_id: int,
        provider: str | None = None,
        model: str | None = None,
        source_types: Iterable[str] | None = None,
        document_kinds: Iterable[str] | None = None,
    ) -> list[RetrievalSearchCandidate]:
        conditions = [
            "rs.subscriber_id = ?",
            "rs.status = 'ready'",
            "rd.status = 'ready'",
            "rc.embedding_status = 'ready'",
            "re.vector_json IS NOT NULL",
        ]
        params: list[Any] = [subscriber_id]

        if provider is not None:
            conditions.append("re.provider = ?")
            params.append(provider)
        if model is not None:
            conditions.append("re.model = ?")
            params.append(model)
        if source_types:
            source_types_tuple = tuple(source_types)
            placeholders = ", ".join("?" for _ in source_types_tuple)
            conditions.append(f"rs.source_type IN ({placeholders})")
            params.extend(source_types_tuple)
        if document_kinds:
            document_kinds_tuple = tuple(document_kinds)
            placeholders = ", ".join("?" for _ in document_kinds_tuple)
            conditions.append(f"rd.document_kind IN ({placeholders})")
            params.extend(document_kinds_tuple)

        where_clause = " AND ".join(conditions)
        cursor = self.connection.execute(
            f"""
            SELECT
                rc.id AS chunk_id,
                rc.document_id AS document_id,
                rd.source_id AS source_id,
                rs.subscriber_id AS subscriber_id,
                rs.source_type AS source_type,
                rs.source_ref AS source_ref,
                rs.title AS source_title,
                rs.locale AS source_locale,
                rs.status AS source_status,
                rd.document_kind AS document_kind,
                rd.title AS document_title,
                rd.status AS document_status,
                rd.version AS document_version,
                rc.chunk_index AS chunk_index,
                rc.content AS chunk_content,
                rc.token_estimate AS token_estimate,
                rc.metadata_json AS chunk_metadata_json,
                rc.embedding_status AS chunk_embedding_status,
                re.id AS embedding_id,
                re.provider AS embedding_provider,
                re.model AS embedding_model,
                re.vector_json AS embedding_vector_json,
                re.dimensions AS embedding_dimensions
            FROM retrieval_chunks rc
            INNER JOIN retrieval_documents rd ON rd.id = rc.document_id
            INNER JOIN retrieval_sources rs ON rs.id = rd.source_id
            INNER JOIN retrieval_embeddings re ON re.chunk_id = rc.id
            WHERE {where_clause}
            ORDER BY rd.updated_at DESC, rc.chunk_index ASC, rc.id ASC, re.created_at DESC, re.id DESC
            """,
            tuple(params),
        )
        return [_row_to_retrieval_search_candidate(row) for row in cursor.fetchall()]



    def list_retrieval_embedding_jobs(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        status: str | None = None,
        chunk_id: int | None = None,
    ) -> list[RetrievalEmbeddingJob]:
        conditions: list[str] = []
        params: list[Any] = []
        if provider is not None:
            conditions.append("provider = ?")
            params.append(provider)
        if model is not None:
            conditions.append("model = ?")
            params.append(model)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if chunk_id is not None:
            conditions.append("chunk_id = ?")
            params.append(chunk_id)
        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        cursor = self.connection.execute(
            f"""
            SELECT
                id, chunk_id, provider, model, status, attempt_count, last_error,
                created_at, updated_at, claimed_at, completed_at
            FROM retrieval_embedding_jobs
            {where_sql}
            ORDER BY created_at ASC, id ASC
            """,
            tuple(params),
        )
        return [_row_to_retrieval_embedding_job(row) for row in cursor.fetchall()]

    def get_retrieval_embedding_job(self, job_id: int) -> RetrievalEmbeddingJob | None:
        cursor = self.connection.execute(
            """
            SELECT
                id, chunk_id, provider, model, status, attempt_count, last_error,
                created_at, updated_at, claimed_at, completed_at
            FROM retrieval_embedding_jobs
            WHERE id = ?
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_retrieval_embedding_job(row)



    def find_active_retrieval_embedding_job(
        self,
        chunk_id: int,
        *,
        provider: str,
        model: str,
    ) -> RetrievalEmbeddingJob | None:
        cursor = self.connection.execute(
            """
            SELECT
                id, chunk_id, provider, model, status, attempt_count, last_error,
                created_at, updated_at, claimed_at, completed_at
            FROM retrieval_embedding_jobs
            WHERE chunk_id = ? AND provider = ? AND model = ? AND status IN ('queued', 'processing')
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (chunk_id, provider, model),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_retrieval_embedding_job(row)



    def enqueue_retrieval_embedding_job(
        self,
        chunk_id: int,
        *,
        provider: str,
        model: str,
        created_at: str,
    ) -> RetrievalEmbeddingJob:
        active = self.find_active_retrieval_embedding_job(
            chunk_id,
            provider=provider,
            model=model,
        )
        if active is not None:
            return active

        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO retrieval_embedding_jobs (
                    chunk_id, provider, model, status, attempt_count, last_error,
                    created_at, updated_at, claimed_at, completed_at
                ) VALUES (?, ?, ?, 'queued', 0, NULL, ?, ?, NULL, NULL)
                """,
                (chunk_id, provider, model, created_at, created_at),
            )
            self.connection.execute(
                """
                UPDATE retrieval_chunks
                SET embedding_status = 'queued'
                WHERE id = ?
                """,
                (chunk_id,),
            )

        job = self.get_retrieval_embedding_job(int(cursor.lastrowid))
        if job is None:
            raise RuntimeError("Failed to load retrieval embedding job after enqueue.")
        return job



    def claim_next_retrieval_embedding_job(
        self,
        *,
        provider: str,
        model: str,
        claimed_at: str,
    ) -> RetrievalEmbeddingJob | None:
        with self.connection:
            cursor = self.connection.execute(
                """
                SELECT id, chunk_id
                FROM retrieval_embedding_jobs
                WHERE provider = ? AND model = ? AND status = 'queued'
                ORDER BY created_at ASC, id ASC
                LIMIT 1
                """,
                (provider, model),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            job_id = int(row["id"])
            chunk_id = int(row["chunk_id"])
            self.connection.execute(
                """
                UPDATE retrieval_embedding_jobs
                SET status = 'processing',
                    attempt_count = attempt_count + 1,
                    updated_at = ?,
                    claimed_at = ?,
                    completed_at = NULL,
                    last_error = NULL
                WHERE id = ?
                """,
                (claimed_at, claimed_at, job_id),
            )
            self.connection.execute(
                """
                UPDATE retrieval_chunks
                SET embedding_status = 'processing'
                WHERE id = ?
                """,
                (chunk_id,),
            )

        return self.get_retrieval_embedding_job(job_id)



    def complete_retrieval_embedding_job(
        self,
        job_id: int,
        *,
        completed_at: str,
    ) -> RetrievalEmbeddingJob:
        with self.connection:
            self.connection.execute(
                """
                UPDATE retrieval_embedding_jobs
                SET status = 'completed',
                    updated_at = ?,
                    completed_at = ?,
                    last_error = NULL
                WHERE id = ?
                """,
                (completed_at, completed_at, job_id),
            )

        job = self.get_retrieval_embedding_job(job_id)
        if job is None:
            raise RuntimeError("Failed to load retrieval embedding job after completion.")
        return job



    def fail_retrieval_embedding_job(
        self,
        job_id: int,
        *,
        error_message: str,
        failed_at: str,
    ) -> RetrievalEmbeddingJob:
        job = self.get_retrieval_embedding_job(job_id)
        if job is None:
            raise RuntimeError("Retrieval embedding job not found for failure update.")

        with self.connection:
            self.connection.execute(
                """
                UPDATE retrieval_embedding_jobs
                SET status = 'failed',
                    updated_at = ?,
                    completed_at = ?,
                    last_error = ?
                WHERE id = ?
                """,
                (failed_at, failed_at, error_message, job_id),
            )
            self.connection.execute(
                """
                UPDATE retrieval_chunks
                SET embedding_status = 'failed'
                WHERE id = ?
                """,
                (job.chunk_id,),
            )

        failed_job = self.get_retrieval_embedding_job(job_id)
        if failed_job is None:
            raise RuntimeError("Failed to load retrieval embedding job after failure update.")
        return failed_job

    # ── Saved Jobs ──────────────────────────────────────────────────

    @staticmethod
    def _row_to_saved_job(row: sqlite3.Row) -> SubscriberSavedJob:
        return SubscriberSavedJob(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            job_id=row["job_id"],
            api_job_id=row["api_job_id"],
            status=row["status"],
            match_score=row["match_score"],
            deadline_at=row["deadline_at"],
            interview_at=row["interview_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_saved_job_note(row: sqlite3.Row) -> SubscriberSavedJobNote:
        return SubscriberSavedJobNote(
            id=row["id"],
            saved_job_id=row["saved_job_id"],
            subscriber_id=row["subscriber_id"],
            content=row["content"],
            created_at=row["created_at"],
        )

    def save_job(
        self,
        *,
        subscriber_id: int,
        job_id: int,
        match_score: int | None = None,
        now: str,
        api_job_id: int | None = None,
    ) -> SubscriberSavedJob:
        resolved_api_job_id = api_job_id or job_id
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_saved_jobs
                    (subscriber_id, job_id, api_job_id, status, match_score, created_at, updated_at)
                VALUES (?, ?, ?, 'reviewing', ?, ?, ?)
                """,
                (subscriber_id, job_id, resolved_api_job_id, match_score, now, now),
            )
        return self.get_saved_job(subscriber_id=subscriber_id, job_id=resolved_api_job_id)  # type: ignore[return-value]

    def unsave_job(self, *, subscriber_id: int, job_id: int) -> bool:
        with self.connection:
            # First resolve the saved_job record ID so we can delete its notes.
            # Notes have a FK onto subscriber_saved_jobs.id (FK enforcement ON),
            # so the parent row cannot be deleted while child notes exist.
            row = self.connection.execute(
                """
                SELECT id FROM subscriber_saved_jobs
                WHERE subscriber_id = ?
                  AND (api_job_id = ? OR (api_job_id IS NULL AND job_id = ?))
                LIMIT 1
                """,
                (subscriber_id, job_id, job_id),
            ).fetchone()
            if row is None:
                return False
            saved_job_id = row["id"]
            self.connection.execute(
                "DELETE FROM subscriber_saved_job_notes WHERE saved_job_id = ?",
                (saved_job_id,),
            )
            cursor = self.connection.execute(
                "DELETE FROM subscriber_saved_jobs WHERE id = ?",
                (saved_job_id,),
            )
        return cursor.rowcount > 0

    def get_saved_job(
        self, *, subscriber_id: int, job_id: int
    ) -> SubscriberSavedJob | None:
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, job_id, api_job_id, status, match_score,
                   deadline_at, interview_at, created_at, updated_at
            FROM subscriber_saved_jobs
            WHERE subscriber_id = ? AND api_job_id = ?
            """,
            (subscriber_id, job_id),
        )
        row = cursor.fetchone()
        return self._row_to_saved_job(row) if row else None

    def get_saved_job_by_id(
        self, saved_job_id: int, *, subscriber_id: int
    ) -> SubscriberSavedJob | None:
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, job_id, api_job_id, status, match_score,
                   deadline_at, interview_at, created_at, updated_at
            FROM subscriber_saved_jobs
            WHERE id = ? AND subscriber_id = ?
            """,
            (saved_job_id, subscriber_id),
        )
        row = cursor.fetchone()
        return self._row_to_saved_job(row) if row else None

    def list_saved_jobs(self, subscriber_id: int) -> list[SubscriberSavedJob]:
        cursor = self.connection.execute(
            """
            SELECT id, subscriber_id, job_id, api_job_id, status, match_score,
                   deadline_at, interview_at, created_at, updated_at
            FROM subscriber_saved_jobs
            WHERE subscriber_id = ?
            ORDER BY created_at DESC
            """,
            (subscriber_id,),
        )
        return [self._row_to_saved_job(row) for row in cursor.fetchall()]

    def update_saved_job_status(
        self,
        saved_job_id: int,
        *,
        subscriber_id: int,
        status: str,
        now: str,
        deadline_at: str | None = None,
        interview_at: str | None = None,
    ) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE subscriber_saved_jobs
                SET status = ?,
                    deadline_at = COALESCE(?, deadline_at),
                    interview_at = COALESCE(?, interview_at),
                    updated_at = ?
                WHERE id = ? AND subscriber_id = ?
                """,
                (status, deadline_at, interview_at, now, saved_job_id, subscriber_id),
            )
        return cursor.rowcount > 0

    def add_saved_job_note(
        self,
        *,
        saved_job_id: int,
        subscriber_id: int,
        content: str,
        now: str,
    ) -> SubscriberSavedJobNote:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_saved_job_notes
                    (saved_job_id, subscriber_id, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (saved_job_id, subscriber_id, content, now),
            )
        note_id = int(cursor.lastrowid)
        row = self.connection.execute(
            "SELECT * FROM subscriber_saved_job_notes WHERE id = ?",
            (note_id,),
        ).fetchone()
        return self._row_to_saved_job_note(row)

    def list_saved_job_notes(
        self, saved_job_id: int, *, subscriber_id: int
    ) -> list[SubscriberSavedJobNote]:
        cursor = self.connection.execute(
            """
            SELECT id, saved_job_id, subscriber_id, content, created_at
            FROM subscriber_saved_job_notes
            WHERE saved_job_id = ? AND subscriber_id = ?
            ORDER BY created_at DESC
            """,
            (saved_job_id, subscriber_id),
        )
        return [self._row_to_saved_job_note(row) for row in cursor.fetchall()]

    def update_saved_job_note(
        self, *, note_id: int, subscriber_id: int, content: str
    ) -> bool:
        with self.connection:
            c = self.connection.execute(
                """
                UPDATE subscriber_saved_job_notes
                SET content = ?
                WHERE id = ? AND subscriber_id = ?
                """,
                (content, note_id, subscriber_id),
            )
        return c.rowcount > 0

    # ── Sessions ────────────────────────────────────────────────────

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> SubscriberSession:
        return SubscriberSession(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            session_token_hash=row["session_token_hash"],
            device_label=row["device_label"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            is_current=bool(row["is_current"]),
            created_at=row["created_at"],
            last_active_at=row["last_active_at"],
            expired_at=row["expired_at"],
        )

    def create_session(
        self,
        *,
        subscriber_id: int,
        session_token_hash: str,
        device_label: str,
        ip_address: str,
        user_agent: str,
        now: str,
    ) -> SubscriberSession:
        with self.connection:
            # Expire any existing active session from the same device+IP to
            # prevent duplicate session rows accumulating on repeated logins.
            self.connection.execute(
                """
                UPDATE subscriber_sessions SET expired_at = ?
                WHERE subscriber_id = ? AND device_label = ? AND ip_address = ?
                  AND expired_at IS NULL
                """,
                (now, subscriber_id, device_label, ip_address),
            )
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_sessions
                    (subscriber_id, session_token_hash, device_label,
                     ip_address, user_agent, is_current, created_at, last_active_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (subscriber_id, session_token_hash, device_label,
                 ip_address, user_agent, now, now),
            )
        sid = int(cursor.lastrowid)
        row = self.connection.execute(
            "SELECT * FROM subscriber_sessions WHERE id = ?", (sid,)
        ).fetchone()
        return self._row_to_session(row)

    def list_active_sessions(self, subscriber_id: int) -> list[SubscriberSession]:
        cursor = self.connection.execute(
            """
            SELECT * FROM subscriber_sessions
            WHERE subscriber_id = ? AND expired_at IS NULL
            ORDER BY last_active_at DESC
            """,
            (subscriber_id,),
        )
        return [self._row_to_session(r) for r in cursor.fetchall()]

    def touch_session(self, session_id: int, *, now: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE subscriber_sessions SET last_active_at = ? WHERE id = ?",
                (now, session_id),
            )

    def expire_session(self, session_id: int, *, subscriber_id: int, now: str) -> bool:
        with self.connection:
            c = self.connection.execute(
                """
                UPDATE subscriber_sessions SET expired_at = ?
                WHERE id = ? AND subscriber_id = ? AND expired_at IS NULL
                """,
                (now, session_id, subscriber_id),
            )
        return c.rowcount > 0

    def expire_all_other_sessions(
        self, *, subscriber_id: int, keep_session_id: int | None, now: str
    ) -> int:
        if keep_session_id:
            with self.connection:
                c = self.connection.execute(
                    """
                    UPDATE subscriber_sessions SET expired_at = ?
                    WHERE subscriber_id = ? AND id != ? AND expired_at IS NULL
                    """,
                    (now, subscriber_id, keep_session_id),
                )
        else:
            with self.connection:
                c = self.connection.execute(
                    """
                    UPDATE subscriber_sessions SET expired_at = ?
                    WHERE subscriber_id = ? AND expired_at IS NULL
                    """,
                    (now, subscriber_id),
                )
        return c.rowcount

    def get_session_by_token_hash(self, token_hash: str) -> SubscriberSession | None:
        row = self.connection.execute(
            "SELECT * FROM subscriber_sessions WHERE session_token_hash = ?",
            (token_hash,),
        ).fetchone()
        return self._row_to_session(row) if row else None

    # ── Login History ───────────────────────────────────────────────

    @staticmethod
    def _row_to_login_history(row: sqlite3.Row) -> SubscriberLoginHistoryEntry:
        return SubscriberLoginHistoryEntry(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            event_type=row["event_type"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            detail=row["detail"],
            created_at=row["created_at"],
        )

    def add_login_history(
        self,
        *,
        subscriber_id: int,
        event_type: str,
        ip_address: str,
        user_agent: str,
        detail: str | None = None,
        now: str,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_login_history
                    (subscriber_id, event_type, ip_address, user_agent, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (subscriber_id, event_type, ip_address, user_agent, detail, now),
            )

    def list_login_history(
        self, subscriber_id: int, *, limit: int = 20
    ) -> list[SubscriberLoginHistoryEntry]:
        cursor = self.connection.execute(
            """
            SELECT * FROM subscriber_login_history
            WHERE subscriber_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (subscriber_id, limit),
        )
        return [self._row_to_login_history(r) for r in cursor.fetchall()]

    # ── Email Change ────────────────────────────────────────────────

    def create_email_change_request(
        self,
        *,
        subscriber_id: int,
        new_email: str,
        verification_code_hash: str,
        expires_at: str,
        now: str,
    ) -> int:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_email_change_requests
                    (subscriber_id, new_email, verification_code_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (subscriber_id, new_email, verification_code_hash, expires_at, now),
            )
        return int(cursor.lastrowid)

    def get_latest_email_change_request(
        self, subscriber_id: int
    ) -> SubscriberEmailChangeRequest | None:
        row = self.connection.execute(
            """
            SELECT * FROM subscriber_email_change_requests
            WHERE subscriber_id = ? AND consumed_at IS NULL
            ORDER BY created_at DESC LIMIT 1
            """,
            (subscriber_id,),
        ).fetchone()
        if row is None:
            return None
        return SubscriberEmailChangeRequest(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            new_email=row["new_email"],
            verification_code_hash=row["verification_code_hash"],
            expires_at=row["expires_at"],
            consumed_at=row["consumed_at"],
            created_at=row["created_at"],
        )

    def consume_email_change_request(self, request_id: int, *, consumed_at: str) -> bool:
        with self.connection:
            c = self.connection.execute(
                """
                UPDATE subscriber_email_change_requests SET consumed_at = ?
                WHERE id = ? AND consumed_at IS NULL
                """,
                (consumed_at, request_id),
            )
        return c.rowcount > 0

    def update_subscriber_email(
        self, subscriber_id: int, *, new_email: str, updated_at: str
    ) -> bool:
        with self.connection:
            c = self.connection.execute(
                "UPDATE subscribers SET email = ?, updated_at = ? WHERE id = ?",
                (new_email, updated_at, subscriber_id),
            )
        return c.rowcount > 0

    # ── TOTP ────────────────────────────────────────────────────────

    def upsert_totp_secret(
        self, *, subscriber_id: int, secret_encrypted: str, now: str
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_totp_secrets
                    (subscriber_id, secret_encrypted, is_verified, created_at)
                VALUES (?, ?, 0, ?)
                ON CONFLICT(subscriber_id) DO UPDATE SET
                    secret_encrypted = excluded.secret_encrypted,
                    is_verified = 0,
                    verified_at = NULL,
                    created_at = excluded.created_at
                """,
                (subscriber_id, secret_encrypted, now),
            )

    def get_totp_secret(self, subscriber_id: int) -> SubscriberTotpSecret | None:
        row = self.connection.execute(
            "SELECT * FROM subscriber_totp_secrets WHERE subscriber_id = ?",
            (subscriber_id,),
        ).fetchone()
        if row is None:
            return None
        return SubscriberTotpSecret(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            secret_encrypted=row["secret_encrypted"],
            is_verified=bool(row["is_verified"]),
            created_at=row["created_at"],
            verified_at=row["verified_at"],
        )

    def verify_totp_secret(self, subscriber_id: int, *, verified_at: str) -> bool:
        with self.connection:
            c = self.connection.execute(
                """
                UPDATE subscriber_totp_secrets
                SET is_verified = 1, verified_at = ?
                WHERE subscriber_id = ? AND is_verified = 0
                """,
                (verified_at, subscriber_id),
            )
        return c.rowcount > 0

    def delete_totp_secret(self, subscriber_id: int) -> bool:
        with self.connection:
            c = self.connection.execute(
                "DELETE FROM subscriber_totp_secrets WHERE subscriber_id = ?",
                (subscriber_id,),
            )
        return c.rowcount > 0

    # ── Account Deletion ────────────────────────────────────────────

    def delete_subscriber_account(
        self, subscriber_id: int, *, email: str, reason: str | None, deleted_at: str
    ) -> bool:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO subscriber_account_deletions
                    (subscriber_id, email, reason, deleted_at)
                VALUES (?, ?, ?, ?)
                """,
                (subscriber_id, email, reason, deleted_at),
            )
            self.connection.execute(
                "DELETE FROM subscriber_saved_job_notes WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            self.connection.execute(
                "DELETE FROM subscriber_saved_jobs WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            self.connection.execute(
                "DELETE FROM subscriber_sessions WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            self.connection.execute(
                "DELETE FROM subscriber_login_history WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            self.connection.execute(
                "DELETE FROM subscriber_email_change_requests WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            self.connection.execute(
                "DELETE FROM subscriber_totp_secrets WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            self.connection.execute(
                "DELETE FROM subscriber_keyword_preferences WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            self.connection.execute(
                "DELETE FROM subscriber_ai_learned_memories WHERE subscriber_id = ?",
                (subscriber_id,),
            )
            c = self.connection.execute(
                "DELETE FROM subscribers WHERE id = ?",
                (subscriber_id,),
            )
        return c.rowcount > 0

    # ------------------------------------------------------------------ #
    # Google OAuth — state tokens                                          #
    # ------------------------------------------------------------------ #

    def create_oauth_state(
        self,
        *,
        state_token_hash: str,
        redirect_path: str,
        nonce: str,
        expires_at: str,
        created_at: str,
    ) -> SubscriberOAuthState:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_oauth_states
                    (state_token_hash, redirect_path, nonce, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (state_token_hash, redirect_path, nonce, expires_at, created_at),
            )
            sid = cursor.lastrowid
        row = self.connection.execute(
            "SELECT * FROM subscriber_oauth_states WHERE id = ?", (sid,)
        ).fetchone()
        return SubscriberOAuthState(
            id=row["id"],
            state_token_hash=row["state_token_hash"],
            redirect_path=row["redirect_path"],
            nonce=row["nonce"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
        )

    def get_and_delete_oauth_state(
        self, state_token_hash: str
    ) -> SubscriberOAuthState | None:
        row = self.connection.execute(
            "SELECT * FROM subscriber_oauth_states WHERE state_token_hash = ?",
            (state_token_hash,),
        ).fetchone()
        if row is None:
            return None
        with self.connection:
            self.connection.execute(
                "DELETE FROM subscriber_oauth_states WHERE id = ?", (row["id"],)
            )
        return SubscriberOAuthState(
            id=row["id"],
            state_token_hash=row["state_token_hash"],
            redirect_path=row["redirect_path"],
            nonce=row["nonce"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
        )

    # ------------------------------------------------------------------ #
    # Google OAuth — provider links                                        #
    # ------------------------------------------------------------------ #

    def get_oauth_provider(
        self, *, provider: str, provider_user_id: str
    ) -> SubscriberOAuthProvider | None:
        row = self.connection.execute(
            """
            SELECT * FROM subscriber_oauth_providers
            WHERE provider = ? AND provider_user_id = ?
            """,
            (provider, provider_user_id),
        ).fetchone()
        if row is None:
            return None
        return SubscriberOAuthProvider(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            provider=row["provider"],
            provider_user_id=row["provider_user_id"],
            email_at_provider=row["email_at_provider"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_oauth_provider_link(
        self,
        *,
        subscriber_id: int,
        provider: str,
        provider_user_id: str,
        email_at_provider: str,
        now: str,
    ) -> SubscriberOAuthProvider:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO subscriber_oauth_providers
                    (subscriber_id, provider, provider_user_id, email_at_provider,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (subscriber_id, provider, provider_user_id, email_at_provider, now, now),
            )
            sid = cursor.lastrowid
        row = self.connection.execute(
            "SELECT * FROM subscriber_oauth_providers WHERE id = ?", (sid,)
        ).fetchone()
        return SubscriberOAuthProvider(
            id=row["id"],
            subscriber_id=row["subscriber_id"],
            provider=row["provider"],
            provider_user_id=row["provider_user_id"],
            email_at_provider=row["email_at_provider"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
