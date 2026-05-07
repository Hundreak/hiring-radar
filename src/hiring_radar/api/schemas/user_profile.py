from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserEducationEntryResponse(BaseModel):
    id: int | None
    school_name: str
    degree_name: str | None
    field_of_study: str | None
    start_year: int | None
    end_year: int | None
    display_order: int


class UserExperienceEntryResponse(BaseModel):
    id: int | None
    title: str
    company_name: str | None
    start_year: int | None
    end_year: int | None
    summary: str | None
    display_order: int


class UserLanguageEntryResponse(BaseModel):
    id: int | None
    language_name: str
    proficiency_level: str | None
    notes: str | None
    display_order: int


class UserLanguageCertificateResponse(BaseModel):
    id: int | None
    language_entry_id: int | None
    certificate_name: str
    issuer_name: str | None
    file_name: str | None
    uploaded_at: str | None


class UserCertificationEntryResponse(BaseModel):
    id: int | None
    certificate_name: str
    issuer_name: str | None
    issued_year: int | None
    file_name: str | None
    uploaded_at: str | None
    display_order: int


class UserProfileAvatarUploadResponse(BaseModel):
    asset_id: str
    url: str
    status: str

class UserSkillDetailResponse(BaseModel):
    id: int | None
    skill_name: str
    category: str | None
    proficiency_hint: str | None
    years_hint: int | None
    evidence_note: str | None
    evidence_file_name: str | None
    uploaded_at: str | None


class UserCvUploadExtractionMetadataResponse(BaseModel):
    file_format: str
    extraction_method: str
    uses_ocr: bool
    parse_status_detail: str
    extraction_quality: str
    review_hints: list[str]
    needs_manual_review: bool
    is_safe_for_default_apply: bool
    fallback_reason: str | None
    recommended_next_action: str


class UserCvEnterpriseFingerprintResponse(BaseModel):
    document_sha256: str | None
    content_sha256: str | None
    person_fingerprint_available: bool
    relation: str
    similarity: float | None
    reason_codes: list[str]


class UserCvEnterpriseCacheResponse(BaseModel):
    cache_key: str | None
    status: str
    exact_reusable: bool
    partial_reusable: bool
    reusable_section_names: list[str]
    changed_section_names: list[str]
    reason_codes: list[str]


class UserCvEnterpriseAtsResponse(BaseModel):
    score: int | None
    level: str | None
    issue_codes: list[str]
    recommendations: list[str]


class UserCvEnterpriseRedactionResponse(BaseModel):
    available: bool
    pii_findings_count: int
    pii_types: list[str]
    warnings: list[str]


class UserCvEnterpriseMetadataResponse(BaseModel):
    fingerprint: UserCvEnterpriseFingerprintResponse
    cache: UserCvEnterpriseCacheResponse
    ats: UserCvEnterpriseAtsResponse
    redaction: UserCvEnterpriseRedactionResponse


class UserCvUploadResponse(BaseModel):
    id: int | None
    original_filename: str
    content_type: str | None
    file_size_bytes: int | None
    parse_status: str
    uploaded_at: str | None
    parsed_at: str | None
    extraction_metadata: UserCvUploadExtractionMetadataResponse
    enterprise_metadata: UserCvEnterpriseMetadataResponse | None = None


class UserCvWorkspaceContextResponse(BaseModel):
    latest_cv_upload: UserCvUploadResponse | None
    language_certificates: list[UserLanguageCertificateResponse]


class UserCvFieldReviewInsightResponse(BaseModel):
    """Field-level review metadata derived from confidence and extraction context."""

    field_name: str
    severity: str
    reason_codes: list[str]
    confidence_level: str
    has_value: bool
    item_count: int


class UserCvReviewSummaryResponse(BaseModel):
    """High-level summary of field review severities for a parsed CV."""

    total_field_count: int
    safe_field_count: int
    review_recommended_count: int
    review_required_count: int
    highest_severity: str
    focus_field_names: list[str]
    manual_review_flow: bool


class UserCvDraftEducationEntryResponse(BaseModel):
    """Serialized education entry derived from a parsed CV draft."""

    school_name: str
    degree_name: str | None
    field_of_study: str | None
    start_year: int | None
    end_year: int | None


class UserCvDraftExperienceEntryResponse(BaseModel):
    """Serialized experience entry derived from a parsed CV draft."""

    title: str
    company_name: str | None
    start_year: int | None
    end_year: int | None
    summary: str | None


class UserCvDraftLanguageEntryResponse(BaseModel):
    """Serialized language entry derived from a parsed CV draft."""

    language_name: str
    proficiency_level: str | None
    notes: str | None


class UserCvDraftCertificationEntryResponse(BaseModel):
    """Serialized generic certification derived from a parsed CV draft."""

    certificate_name: str
    issuer_name: str | None
    issued_year: int | None


class UserCvProfileDraftResponse(BaseModel):
    """Normalized profile draft generated from parsed CV text."""

    headline: str | None
    summary: str | None
    skills: list[str]
    target_roles: list[str]
    preferred_locations: list[str]
    remote_preference: str | None
    education_entries: list[UserCvDraftEducationEntryResponse]
    experience_entries: list[UserCvDraftExperienceEntryResponse]
    language_entries: list[UserCvDraftLanguageEntryResponse]
    certification_entries: list[UserCvDraftCertificationEntryResponse]


class UserCvFieldConfidenceResponse(BaseModel):
    """Typed confidence metadata for a single parsed field."""

    field_name: str
    level: str
    has_value: bool
    item_count: int
    signals: list[str]


class UserCvProfileConfidenceReportResponse(BaseModel):
    """Typed field-level confidence report for a parsed CV snapshot."""

    headline: UserCvFieldConfidenceResponse
    summary: UserCvFieldConfidenceResponse
    skills: UserCvFieldConfidenceResponse
    target_roles: UserCvFieldConfidenceResponse
    preferred_locations: UserCvFieldConfidenceResponse
    remote_preference: UserCvFieldConfidenceResponse
    education_entries: UserCvFieldConfidenceResponse
    experience_entries: UserCvFieldConfidenceResponse
    language_entries: UserCvFieldConfidenceResponse
    certification_entries: UserCvFieldConfidenceResponse


class UserCvParseSnapshotResponse(BaseModel):
    """Latest persisted CV parse snapshot exposed to the user dashboard."""

    parse_run_id: int
    generated_at: str
    source_upload_id: int | None
    source_filename: str | None
    source_parse_status: str | None
    parser_version: str | None
    extraction_metadata: UserCvUploadExtractionMetadataResponse
    confidence: UserCvProfileConfidenceReportResponse
    field_review: list[UserCvFieldReviewInsightResponse]
    review_summary: UserCvReviewSummaryResponse
    enterprise_metadata: UserCvEnterpriseMetadataResponse | None = None
    draft: UserCvProfileDraftResponse


class UserCvScalarFieldApplyPlanResponse(BaseModel):
    """Serialized apply plan for a scalar profile field."""

    field_name: str
    current_value: str | None
    suggested_value: str | None
    action: str
    default_selected: bool


class UserCvListFieldApplyPlanResponse(BaseModel):
    """Serialized apply plan for a list-based profile field."""

    field_name: str
    current_items: list[str]
    suggested_items: list[str]
    items_to_add: list[str]
    action: str
    default_selected: bool


class UserCvEducationEntryApplyPlanResponse(BaseModel):
    """Serialized apply plan for an education entry."""

    draft_entry: UserCvDraftEducationEntryResponse
    matched_existing_id: int | None
    action: str
    default_selected: bool


class UserCvExperienceEntryApplyPlanResponse(BaseModel):
    """Serialized apply plan for an experience entry."""

    draft_entry: UserCvDraftExperienceEntryResponse
    matched_existing_id: int | None
    action: str
    default_selected: bool


class UserCvLanguageEntryApplyPlanResponse(BaseModel):
    """Serialized apply plan for a language entry."""

    draft_entry: UserCvDraftLanguageEntryResponse
    matched_existing_id: int | None
    action: str
    default_selected: bool


class UserCvCertificationEntryApplyPlanResponse(BaseModel):
    """Serialized apply plan for a generic certification entry."""

    draft_entry: UserCvDraftCertificationEntryResponse
    matched_existing_id: int | None
    action: str
    default_selected: bool


class UserCvProfileApplyPlanResponse(BaseModel):
    """Typed response for the latest CV apply plan."""

    parse_run_id: int
    generated_at: str
    source_upload_id: int | None
    source_filename: str | None
    source_parse_status: str | None
    parser_version: str | None
    extraction_metadata: UserCvUploadExtractionMetadataResponse
    has_actionable_changes: bool
    default_selected_change_count: int
    headline: UserCvScalarFieldApplyPlanResponse
    summary: UserCvScalarFieldApplyPlanResponse
    remote_preference: UserCvScalarFieldApplyPlanResponse
    skills: UserCvListFieldApplyPlanResponse
    target_roles: UserCvListFieldApplyPlanResponse
    preferred_locations: UserCvListFieldApplyPlanResponse
    education_entries: list[UserCvEducationEntryApplyPlanResponse]
    experience_entries: list[UserCvExperienceEntryApplyPlanResponse]
    language_entries: list[UserCvLanguageEntryApplyPlanResponse]
    certification_entries: list[UserCvCertificationEntryApplyPlanResponse]
    confidence: UserCvProfileConfidenceReportResponse
    field_review: list[UserCvFieldReviewInsightResponse]
    review_summary: UserCvReviewSummaryResponse
    enterprise_metadata: UserCvEnterpriseMetadataResponse | None = None


class UserCvApplySelectedRequest(BaseModel):
    """Request payload for applying selected CV-derived operations."""

    model_config = ConfigDict(extra="forbid")

    parse_run_id: int
    scalar_fields: list[str] = Field(default_factory=list)
    list_fields: list[str] = Field(default_factory=list)
    education_entry_indexes: list[int] = Field(default_factory=list)
    experience_entry_indexes: list[int] = Field(default_factory=list)
    language_entry_indexes: list[int] = Field(default_factory=list)
    certification_entry_indexes: list[int] = Field(default_factory=list)
    manual_review_acknowledged: bool = False


class UserCvApplySelectedResponse(BaseModel):
    """Response payload for a completed selected-operation apply action."""

    parse_run_id: int
    apply_audit_id: int
    resulting_parse_run_apply_status: str
    remaining_actionable_change_count: int
    applied_change_count: int
    applied_scalar_fields: list[str]
    applied_list_fields: list[str]
    applied_education_entry_indexes: list[int]
    applied_experience_entry_indexes: list[int]
    applied_language_entry_indexes: list[int]
    applied_certification_entry_indexes: list[int]
    workspace_refresh_required: bool = True


class UserProfileCompletenessResponse(BaseModel):
    score: int
    completed_items: list[str]
    missing_items: list[str]


class UserProfileResponse(BaseModel):
    subscriber_id: int
    email: str
    full_name: str | None
    phone: str | None
    headline: str | None
    summary: str | None
    target_roles: list[str]
    skills: list[str]
    preferred_locations: list[str]
    remote_preference: str | None
    cv_filename: str | None
    cv_uploaded_at: str | None
    education_entries: list[UserEducationEntryResponse]
    experience_entries: list[UserExperienceEntryResponse]
    language_entries: list[UserLanguageEntryResponse]
    language_certificates: list[UserLanguageCertificateResponse]
    certification_entries: list[UserCertificationEntryResponse]
    latest_cv_upload: UserCvUploadResponse | None
    completeness: UserProfileCompletenessResponse
    created_at: str | None
    updated_at: str | None


class UserEducationEntryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    school_name: str
    degree_name: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class UserExperienceEntryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    company_name: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    summary: str | None = None


class UserLanguageEntryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language_name: str
    proficiency_level: str | None = None
    notes: str | None = None


class UserCertificationEntryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    certificate_name: str
    issuer_name: str | None = None
    issued_year: int | None = None
    file_name: str | None = None
    uploaded_at: str | None = None


class UserProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    phone: str | None = None
    headline: str | None = None
    summary: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: str | None = None
    education_entries: list[UserEducationEntryUpdate] = Field(default_factory=list)
    experience_entries: list[UserExperienceEntryUpdate] = Field(default_factory=list)
    language_entries: list[UserLanguageEntryUpdate] = Field(default_factory=list)
    certification_entries: list[UserCertificationEntryUpdate] = Field(default_factory=list)


class CreateUserAiAuditLogRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    telemetry_ref: str | None = None
    target_field: str
    target_entity_id: str | None = None
    action_type: str
    source_panel: str | None = None
    before_snapshot: Any = None
    after_snapshot: Any = None
    persistence_status: str = "unsaved"
    evaluation_status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FinalizeUserAiAuditLogRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    persistence_status: str = "saved"
    saved_snapshot: Any = None
    evaluation_status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserAiAuditLogResponse(BaseModel):
    id: int
    telemetry_ref: str | None = None
    target_field: str
    target_entity_id: str | None = None
    action_type: str
    source_panel: str | None = None
    before_snapshot: Any = None
    after_snapshot: Any = None
    persistence_status: str
    evaluation_status: str | None = None
    evaluation_score: float | None = None
    manual_edit_distance: int | None = None
    request_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None
    reverted_at: str | None = None


class UserAiAuditRevertResponse(BaseModel):
    audit_log: UserAiAuditLogResponse
    aggregate: dict[str, Any]


class UserAiEvaluationHookItemResponse(BaseModel):
    audit_log_id: int
    telemetry_ref: str | None = None
    target_field: str
    action_type: str
    persistence_status: str
    evaluation_status: str | None = None
    evaluation_score: float | None = None
    manual_edit_distance: int | None = None
    source_panel: str | None = None
    created_at: str | None = None


class UserAiSystemHealthResponse(BaseModel):
    status: str
    request_ref: str | None = None
    database: dict[str, Any] = Field(default_factory=dict)
    ai_runtime: dict[str, Any] = Field(default_factory=dict)
