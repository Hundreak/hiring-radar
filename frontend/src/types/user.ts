export type SupportedLocale = 'tr' | 'en' | 'de';

export type RemotePreference = 'remote' | 'hybrid' | 'onsite' | null;

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export type UserCvFieldReviewSeverity =
  | 'safe'
  | 'review_recommended'
  | 'review_required';

export type UserCvFieldReviewReasonCode =
  | 'low_confidence'
  | 'medium_confidence'
  | 'high_confidence'
  | 'missing_value'
  | 'sparse_content'
  | 'ocr_source'
  | 'manual_review_flow'
  | 'low_text_volume'
  | 'medium_text_volume'
  | 'extraction_review_hint'
  | 'selected_risky_change'
  | 'selected_review_recommended';

export interface UserAuthMe {
  subscriber_id: number;
  email: string;
  authenticated: boolean;
}

export interface UserPasswordLoginRequest {
  email: string;
  password: string;
}

export type UserPasswordLoginResponse = UserAuthMe;

export interface EmployerLoginRequest {
  email: string;
  password: string;
}

export interface EmployerCompanySummary {
  id: number;
  slug: string;
  name: string;
  default_locale: string;
  plan_tier: string;
  status: string;
}

export interface EmployerAuthSession {
  ok: boolean;
  user_id: number;
  company_id: number;
  member_id: number | null;
  email: string;
  name?: string | null;
  full_name?: string | null;
  company_name: string;
  role: 'employer' | string;
  role_key: string;
  email_verified?: boolean;
  created_at?: string | null;
  company?: EmployerCompanySummary;
}

export interface EmployerLoginResponse extends EmployerAuthSession {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface EmployerRegisterRequest {
  company_name: string;
  company_email: string;
  contact_name: string;
  password: string;
  password_confirmation: string;
}

export type EmployerRegisterResponse = EmployerLoginResponse;


export interface EmployerCommunicationPreferences {
  candidate_alerts_enabled: boolean;
  campaign_review_enabled: boolean;
  weekly_leadership_digest_enabled: boolean;
  product_updates_enabled: boolean;
  security_alerts_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
  timezone: string;
  default_channel: 'email' | 'in_app' | 'email_and_in_app' | string;
  notification_emails: string[];
  route_overdue_candidates_to: 'owner' | 'admin' | 'recruiter' | 'hiring_manager' | string;
  route_hot_candidates_to: 'owner' | 'admin' | 'recruiter' | 'hiring_manager' | string;
  route_campaign_review_to: 'owner' | 'admin' | 'recruiter' | 'hiring_manager' | string;
  route_weekly_digest_to: 'owner' | 'admin' | 'recruiter' | 'hiring_manager' | string;
}

export type UpdateEmployerCommunicationPreferencesRequest = Partial<EmployerCommunicationPreferences>;

export interface EmployerCommunicationTeamSummary {
  active_members: number;
  invited_members: number;
  roles: Record<string, number>;
}

export interface EmployerCommunicationPreferencesResponse {
  ok: boolean;
  company_id: number;
  preferences: EmployerCommunicationPreferences;
  team_summary: EmployerCommunicationTeamSummary;
  updated_at: string | null;
}


export interface EmployerAuditActor {
  user_id: number | null;
  name: string | null;
  email: string | null;
}

export type EmployerAuditSensitivity = 'low' | 'medium' | 'high';

export interface EmployerAuditEvent {
  id: number;
  company_id: number;
  actor: EmployerAuditActor;
  event_type: string;
  resource_type: string;
  resource_id: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  metadata: Record<string, unknown>;
  sensitivity: EmployerAuditSensitivity;
  created_at: string;
}

export interface EmployerAuditEventListResponse {
  ok: boolean;
  items: EmployerAuditEvent[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  filters: Record<string, unknown>;
}

export interface EmployerAuditExportResponse {
  ok: boolean;
  format: 'json' | 'csv';
  exported_items: number;
  generated_at: string;
  items: EmployerAuditEvent[] | null;
}

// Tip takma adi olarak tanimli: arayuzlerin ortuk index imzasi olmadigi icin
// Record<string, unknown> bekleyen query-key yardimcilarina gecirilemiyorlar.
export type EmployerAuditQueryParams = {
  page?: number;
  pageSize?: number;
  eventType?: string;
  resourceType?: string;
  resourceId?: string;
  actorUserId?: number;
  createdFrom?: string;
  createdTo?: string;
};

export interface EmployerRuntimeStatus {
  ok: boolean;
  environment: string;
  production: boolean;
  demo_mode_enabled: boolean;
  mock_auth_enabled: boolean;
  data_mode: 'demo' | 'production' | string;
}

export interface PublicSignupChallengeResponse {
  challenge_id: string;
  prompt: string;
  hint: string | null;
}

export interface PublicSignupRequest {
  full_name: string;
  email: string;
  password: string;
  password_confirmation: string;
  challenge_id: string;
  challenge_answer: string;
}

export interface PublicSignupResponse {
  subscriber_id: number;
  email: string;
  full_name: string | null;
  authenticated: boolean;
  message: string;
}

export interface UserProfile {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  digest_enabled: boolean;
}


export interface UserNotificationPreference {
  subscriber_id: number;
  job_digest_enabled: boolean;
  product_updates_enabled: boolean;
  employer_messages_enabled: boolean;
  security_alerts_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
  timezone: string;
  updated_at: string | null;
}

export interface UpdateUserNotificationPreferenceRequest {
  job_digest_enabled?: boolean;
  product_updates_enabled?: boolean;
  employer_messages_enabled?: boolean;
  security_alerts_enabled?: boolean;
  quiet_hours_enabled?: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  timezone?: string;
}

export interface UserEducationEntry {
  id: number | null;
  school_name: string;
  degree_name: string | null;
  field_of_study: string | null;
  start_year: number | null;
  end_year: number | null;
  display_order: number;
}

export interface UserExperienceEntry {
  id: number | null;
  title: string;
  company_name: string | null;
  start_year: number | null;
  end_year: number | null;
  summary: string | null;
  display_order: number;
}

export interface UserLanguageEntry {
  id: number | null;
  language_name: string;
  proficiency_level: string | null;
  notes: string | null;
  display_order: number;
}

export interface UserLanguageCertificate {
  id: number | null;
  subscriber_id: number;
  language_entry_id: number | null;
  certificate_name: string;
  issuer_name: string | null;
  file_name: string | null;
  storage_path: string | null;
  uploaded_at: string | null;
}

export interface UserSkillDetail {
  id: number | null;
  skill_name: string;
  category: string | null;
  proficiency_hint: string | null;
  years_hint: number | null;
  evidence_note: string | null;
  evidence_file_name: string | null;
  uploaded_at: string | null;
}

export interface UserProfileCompleteness {
  score: number;
  completed_items: string[];
  missing_items: string[];
}


export interface UserCvWorkspaceContext {
  latest_cv_upload: UserCvUpload | null;
  language_certificates: UserLanguageCertificate[];
}

export interface UserCvWorkspaceProfile {
  full_name: string | null;
  email: string;
  phone: string | null;
  headline: string | null;
  summary: string | null;
  target_roles: string[];
  skills: string[];
  preferred_locations: string[];
  remote_preference: RemotePreference;
  education_entries: UserEducationEntry[];
  experience_entries: UserExperienceEntry[];
  language_entries: UserLanguageEntry[];
  language_certificates: UserLanguageCertificate[];
  completeness: UserProfileCompleteness;
  latest_cv_upload: UserCvUpload | null;
}


export interface UserFilterPolicy {
  profile_quality_score: number;
  profile_quality_band: 'low' | 'medium' | 'high';
  has_keyword_preferences: boolean;
  keyword_preview_count: number;
  recommended_actions: string[];
}

export interface UserKeywordPreference {
  include_keywords: string[];
  exclude_keywords: string[];
  match_title: boolean;
  match_location: boolean;
  match_company_name: boolean;
  updated_at: string | null;
  enabled: boolean;
}

export interface KeywordPreferencePreviewJob {
  id: number;
  title: string;
  company_name: string;
  location: string | null;
  canonical_url: string;
  source_name: string;
  posted_at: string | null;
}

export interface KeywordPreferencePreviewResponse {
  total_matches: number;
  passed_jobs: number;
  rejected_jobs: number;
  blocked_jobs: number;
  filtered_out_jobs: number;
  active_fields: string[];
  sample_jobs: KeywordPreferencePreviewJob[];
}

export interface UserCvExtractionMetadata {
  file_format: string;
  extraction_method: string;
  uses_ocr: boolean;
  parse_status_detail: string;
  extraction_quality: string;
  review_hints: string[];
  needs_manual_review: boolean;
  is_safe_for_default_apply: boolean;
  fallback_reason: string | null;
  recommended_next_action: string;
}

export interface UserCvEnterpriseFingerprintSummary {
  document_sha256: string | null;
  content_sha256: string | null;
  person_fingerprint_available: boolean;
  relation: string;
  similarity: number | null;
  reason_codes: string[];
}

export interface UserCvEnterpriseCacheSummary {
  cache_key: string | null;
  status: string;
  exact_reusable: boolean;
  partial_reusable: boolean;
  reusable_section_names: string[];
  changed_section_names: string[];
  reason_codes: string[];
}

export interface UserCvEnterpriseAtsSummary {
  score: number | null;
  level: 'low' | 'medium' | 'high' | null;
  issue_codes: string[];
  recommendations: string[];
}

export interface UserCvEnterpriseRedactionSummary {
  available: boolean;
  pii_findings_count: number;
  pii_types: string[];
  warnings: string[];
}

export type UserCvEnterpriseAts = UserCvEnterpriseAtsSummary;
export type UserCvEnterpriseRedaction = UserCvEnterpriseRedactionSummary;

export interface UserCvEnterpriseMetadata {
  fingerprint: UserCvEnterpriseFingerprintSummary;
  cache: UserCvEnterpriseCacheSummary;
  ats: UserCvEnterpriseAtsSummary;
  redaction: UserCvEnterpriseRedactionSummary;
}

export interface UserCvUpload {
  id: number;
  original_filename: string;
  content_type: string | null;
  file_size_bytes: number | null;
  parse_status: string;
  uploaded_at: string | null;
  parsed_at: string | null;
  extraction_metadata: UserCvExtractionMetadata;
  enterprise_metadata?: UserCvEnterpriseMetadata | null;
}

export interface UserCvDraftEducationEntry {
  school_name: string;
  degree_name: string | null;
  field_of_study: string | null;
  start_year: number | null;
  end_year: number | null;
}

export interface UserCvDraftExperienceEntry {
  title: string;
  company_name: string | null;
  start_year: number | null;
  end_year: number | null;
  summary: string | null;
}

export interface UserCvDraftLanguageEntry {
  language_name: string;
  proficiency_level: string | null;
  notes: string | null;
}

export interface UserCvDraftSnapshot {
  headline: string | null;
  summary: string | null;
  skills: string[];
  target_roles: string[];
  preferred_locations: string[];
  remote_preference: string | null;
  education_entries: UserCvDraftEducationEntry[];
  experience_entries: UserCvDraftExperienceEntry[];
  language_entries: UserCvDraftLanguageEntry[];
}

export type UserCvConfidenceFieldName =
  | 'headline'
  | 'summary'
  | 'skills'
  | 'target_roles'
  | 'preferred_locations'
  | 'remote_preference'
  | 'education_entries'
  | 'experience_entries'
  | 'language_entries';

export interface UserCvFieldConfidenceResponse {
  field_name: UserCvConfidenceFieldName;
  level: ConfidenceLevel;
  has_value: boolean;
  item_count: number;
  signals: string[];
}
export type UserCvFieldConfidence = UserCvFieldConfidenceResponse;

export type UserCvProfileConfidenceReport =
  UserCvProfileConfidenceReportResponse;

export interface UserCvProfileConfidenceReportResponse {
  headline: UserCvFieldConfidenceResponse;
  summary: UserCvFieldConfidenceResponse;
  skills: UserCvFieldConfidenceResponse;
  target_roles: UserCvFieldConfidenceResponse;
  preferred_locations: UserCvFieldConfidenceResponse;
  remote_preference: UserCvFieldConfidenceResponse;
  education_entries: UserCvFieldConfidenceResponse;
  experience_entries: UserCvFieldConfidenceResponse;
  language_entries: UserCvFieldConfidenceResponse;
}

export interface UserCvFieldReviewItem {
  field_name: UserCvConfidenceFieldName;
  severity: UserCvFieldReviewSeverity;
  reason_codes: UserCvFieldReviewReasonCode[];
  confidence_level: ConfidenceLevel;
  has_value: boolean;
  item_count: number;
}

export type UserCvFieldReviewInsight = UserCvFieldReviewItem;

export interface UserCvReviewSummary {
  total_field_count: number;
  safe_field_count: number;
  review_recommended_count: number;
  review_required_count: number;
  highest_severity: UserCvFieldReviewSeverity;
  focus_field_names: UserCvConfidenceFieldName[];
  manual_review_flow: boolean;
}

export interface UserCvParseSnapshot {
  parse_run_id: number;
  generated_at: string;
  source_upload_id: number;
  source_filename: string;
  source_parse_status: string;
  parser_version: string | null;
  draft: UserCvDraftSnapshot;
  extraction_metadata: UserCvExtractionMetadata;
  enterprise_metadata?: UserCvEnterpriseMetadata | null;
  confidence?: UserCvProfileConfidenceReportResponse | null;
  field_review?: UserCvFieldReviewItem[] | null;
  review_summary?: UserCvReviewSummary | null;
}

export interface UserCvScalarSuggestion {
  field_name: 'headline' | 'summary' | 'remote_preference';
  current_value: string | null;
  suggested_value: string | null;
  action: 'noop' | 'fill_missing' | 'review_required';
  default_selected: boolean;
}

export interface UserCvListSuggestion {
  field_name: 'skills' | 'target_roles' | 'preferred_locations';
  current_items: string[];
  suggested_items: string[];
  items_to_add: string[];
  action: 'noop' | 'add_unique';
  default_selected: boolean;
}

export interface UserCvEducationEntrySuggestion {
  draft_entry: UserCvDraftEducationEntry;
  matched_existing_id: number | null;
  action: 'noop' | 'add_unique';
  default_selected: boolean;
}

export interface UserCvExperienceEntrySuggestion {
  draft_entry: UserCvDraftExperienceEntry;
  matched_existing_id: number | null;
  action: 'noop' | 'add_unique';
  default_selected: boolean;
}

export interface UserCvLanguageEntrySuggestion {
  draft_entry: UserCvDraftLanguageEntry;
  matched_existing_id: number | null;
  action: 'noop' | 'add_unique';
  default_selected: boolean;
}

export interface UserCvProfileApplyPlan {
  parse_run_id: number;
  generated_at: string;
  source_upload_id: number;
  source_filename: string;
  source_parse_status: string;
  parser_version: string | null;
  extraction_metadata: UserCvExtractionMetadata;
  enterprise_metadata?: UserCvEnterpriseMetadata | null;
  has_actionable_changes: boolean;
  default_selected_change_count: number;
  confidence: UserCvProfileConfidenceReportResponse;
  field_review: UserCvFieldReviewItem[];
  review_summary: UserCvReviewSummary;
  headline: UserCvScalarSuggestion;
  summary: UserCvScalarSuggestion;
  remote_preference: UserCvScalarSuggestion;
  skills: UserCvListSuggestion;
  target_roles: UserCvListSuggestion;
  preferred_locations: UserCvListSuggestion;
  education_entries: UserCvEducationEntrySuggestion[];
  experience_entries: UserCvExperienceEntrySuggestion[];
  language_entries: UserCvLanguageEntrySuggestion[];
}

export interface UserCvApplySelectedRequest {
  parse_run_id: number;
  scalar_fields: string[];
  list_fields: string[];
  education_entry_indexes: number[];
  experience_entry_indexes: number[];
  language_entry_indexes: number[];
  manual_review_acknowledged: boolean;
}


export interface UserCvApplySelectedResponse {
  parse_run_id: number;
  apply_audit_id: number;
  resulting_parse_run_apply_status: string;
  remaining_actionable_change_count: number;
  applied_change_count: number;
  applied_scalar_fields: string[];
  applied_list_fields: string[];
  applied_education_entry_indexes: number[];
  applied_experience_entry_indexes: number[];
  applied_language_entry_indexes: number[];
  workspace_refresh_required: boolean;
}