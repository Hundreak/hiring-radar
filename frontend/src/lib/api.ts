import type {JobListResponse} from '@/types/job';
import type {SavedJob, SavedJobListResponse, SavedJobNote, SavedJobStatus} from '@/types/saved';

export interface SessionItem {
  id: number;
  device_label: string;
  ip_address: string;
  is_current: boolean;
  created_at: string | null;
  last_active_at: string | null;
}

export interface LoginHistoryItem {
  id: number;
  event_type: string;
  ip_address: string;
  detail: string | null;
  created_at: string | null;
}

export interface TotpSetupResponse {
  secret: string;
  otpauth_uri: string;
}

export interface TotpStatusResponse {
  enabled: boolean;
  verified: boolean;
}

export interface SkillStrength {
  keyword: string;
  match_count: number;
  total_jobs: number;
}

export interface SkillGap {
  keyword: string;
  demand_count: number;
  demand_pct: number;
}

export interface MatchInsightsData {
  total_matched: number;
  remote_count: number;
  strengths: SkillStrength[];
  gaps: SkillGap[];
}
import type {AiAuditLog, AiAuditRevertResponse, AiCopilotChatRequest, AiCopilotChatResponse, AiEvaluationHookItem, AiHeadlineSummaryRequest, AiHeadlineSummaryResponse, AiRoleFocusRequest, AiRoleFocusResponse,
  AiSkillEvidenceRequest,
  AiSkillEvidenceResponse,
  AiSkillGroupingResponse,
  CreateAiAuditLogRequest,
  FinalizeAiAuditLogRequest,
  AiSystemHealthResponse
} from '@/types/ai';
import type {
  CreateEducationRequest,
  CreateExperienceRequest,
  CreateLanguageRequest,
  CreateSkillRequest,
  ProfileAvatarUploadResponse,
  UpdateBasicInfoRequest,
  UpdateEducationRequest,
  UpdateExperienceRequest,
  UpdateLanguageRequest,
  UpdatePreferencesRequest,
  UpdateSkillRequest,
  UserProfileAggregateResponse,
} from '@/types/profile';
import type {
  KeywordPreferencePreviewJob,
  KeywordPreferencePreviewResponse,
  UserAuthMe,
  UserCvApplySelectedRequest,
  UserCvApplySelectedResponse,
  UserCvParseSnapshot,
  UserCvProfileApplyPlan,
  UserCvUpload,
  UserCvWorkspaceContext,
  UserFilterPolicy,
  UserKeywordPreference,
  UserLanguageCertificate,
  UserSkillDetail,
  UserPasswordLoginRequest,
  UserPasswordLoginResponse,
  UserProfile,
  EmployerLoginRequest,
  EmployerLoginResponse,
  EmployerRegisterRequest,
  EmployerRegisterResponse,
} from '@/types/user';

export interface SignupVerificationStartRequest {
  full_name: string;
  email: string;
  password: string;
  password_confirmation: string;
}

export interface SignupVerificationStartResponse {
  ok: boolean;
  email: string;
  message: string;
}

export interface SignupVerificationConfirmRequest {
  email: string;
  verification_code: string;
}

export interface SignupVerificationConfirmResponse extends UserAuthMe {
  full_name: string | null;
  message: string;
}

export interface RequestPasswordResetResponse {
  ok: boolean;
  message: string;
}

export interface ConfirmPasswordResetRequest {
  token: string;
  password: string;
  password_confirmation: string;
}

export interface ConfirmPasswordResetResponse extends UserAuthMe {
  message: string;
}

export class ApiError extends Error {
  status: number;
  statusCode: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.statusCode = status;
    this.detail = detail;
  }
}

async function readErrorDetail(response: Response): Promise<string> {
  const maybeJson = await response.json().catch(() => null);

  if (typeof maybeJson?.detail === 'string') {
    return maybeJson.detail;
  }

  if (typeof maybeJson?.message === 'string') {
    return maybeJson.message;
  }

  return 'Request failed.';
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const hasFormDataBody =
    typeof FormData !== 'undefined' && init?.body instanceof FormData;

  if (!hasFormDataBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  headers.set('Cache-Control', 'no-store');

  const response = await fetch(`/api${path}`, {
    credentials: 'include',
    cache: 'no-store',
    ...init,
    headers,
  });

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function normalizeKeywordPreference(
  response: Omit<UserKeywordPreference, 'enabled'> &
    Partial<Pick<UserKeywordPreference, 'enabled'>>
): UserKeywordPreference {
  const includeKeywords = Array.isArray(response.include_keywords)
    ? response.include_keywords
    : [];

  const excludeKeywords = Array.isArray(response.exclude_keywords)
    ? response.exclude_keywords
    : [];

  return {
    include_keywords: includeKeywords,
    exclude_keywords: excludeKeywords,
    match_title: Boolean(response.match_title),
    match_location: Boolean(response.match_location),
    match_company_name: Boolean(response.match_company_name),
    updated_at: response.updated_at ?? null,
    enabled:
      typeof response.enabled === 'boolean'
        ? response.enabled
        : includeKeywords.length > 0 || excludeKeywords.length > 0,
  };
}

export const api = {
  requestSignupVerification(payload: SignupVerificationStartRequest) {
    return apiFetch<SignupVerificationStartResponse>(
      '/public/auth/signup/request-verification',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  confirmSignupVerification(payload: SignupVerificationConfirmRequest) {
    return apiFetch<SignupVerificationConfirmResponse>(
      '/public/auth/signup/verify',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  requestMagicLink(email: string, redirectPath?: string) {
    return apiFetch<{ok: boolean; message: string}>(
      '/user/auth/request-magic-link',
      {
        method: 'POST',
        body: JSON.stringify({
          email,
          ...(redirectPath ? {redirect_path: redirectPath} : {}),
        }),
      }
    );
  },

  consumeMagicLink(token: string) {
    return apiFetch<UserAuthMe>('/user/auth/consume-magic-link', {
      method: 'POST',
      body: JSON.stringify({token}),
    });
  },

  requestPasswordReset(email: string) {
    return apiFetch<RequestPasswordResetResponse>(
      '/user/auth/request-password-reset',
      {
        method: 'POST',
        body: JSON.stringify({email}),
      }
    );
  },

  confirmPasswordReset(payload: ConfirmPasswordResetRequest) {
    return apiFetch<ConfirmPasswordResetResponse>(
      '/user/auth/confirm-password-reset',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  loginWithPassword(payload: UserPasswordLoginRequest) {
    return apiFetch<UserPasswordLoginResponse>('/user/auth/login-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  loginEmployer(payload: EmployerLoginRequest) {
    return apiFetch<EmployerLoginResponse>('/employer/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  registerEmployer(payload: EmployerRegisterRequest) {
    return apiFetch<EmployerRegisterResponse>('/employer/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getSession() {
    return apiFetch<UserAuthMe>('/user/auth/me');
  },

  logout() {
    return apiFetch<{ok: boolean}>('/user/auth/logout', {method: 'POST'});
  },

  getProfile() {
    return apiFetch<UserProfile>('/user/me');
  },

  updateProfile(payload: {
    full_name?: string | null;
    is_active?: boolean;
    digest_enabled?: boolean;
  }) {
    return apiFetch<UserProfile>('/user/me/preferences', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },
  getUserProfileAggregate() {
    return apiFetch<UserProfileAggregateResponse>('/user/profile/aggregate');
  },

  patchUserProfileBasicInfo(payload: UpdateBasicInfoRequest) {
    return apiFetch<UserProfileAggregateResponse>('/user/profile/basic-info', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  patchUserProfilePreferences(payload: UpdatePreferencesRequest) {
    return apiFetch<UserProfileAggregateResponse>('/user/profile/preferences', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  createUserProfileExperience(payload: CreateExperienceRequest) {
    return apiFetch<UserProfileAggregateResponse>('/user/profile/experiences', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  patchUserProfileExperience(
    experienceId: string,
    payload: UpdateExperienceRequest
  ) {
    return apiFetch<UserProfileAggregateResponse>(
      `/user/profile/experiences/${experienceId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }
    );
  },

  deleteUserProfileExperience(experienceId: string) {
    return apiFetch<UserProfileAggregateResponse>(
      `/user/profile/experiences/${experienceId}`,
      {method: 'DELETE'}
    );
  },

  createUserProfileEducation(payload: CreateEducationRequest) {
    return apiFetch<UserProfileAggregateResponse>('/user/profile/education', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  patchUserProfileEducation(
    educationId: string,
    payload: UpdateEducationRequest
  ) {
    return apiFetch<UserProfileAggregateResponse>(
      `/user/profile/education/${educationId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }
    );
  },

  deleteUserProfileEducation(educationId: string) {
    return apiFetch<UserProfileAggregateResponse>(
      `/user/profile/education/${educationId}`,
      {method: 'DELETE'}
    );
  },

  createUserProfileLanguage(payload: CreateLanguageRequest) {
    return apiFetch<UserProfileAggregateResponse>('/user/profile/languages', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  patchUserProfileLanguage(
    languageId: string,
    payload: UpdateLanguageRequest
  ) {
    return apiFetch<UserProfileAggregateResponse>(
      `/user/profile/languages/${languageId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }
    );
  },

  deleteUserProfileLanguage(languageId: string) {
    return apiFetch<UserProfileAggregateResponse>(
      `/user/profile/languages/${languageId}`,
      {method: 'DELETE'}
    );
  },

  createUserProfileSkill(payload: CreateSkillRequest) {
    return apiFetch<UserProfileAggregateResponse>('/user/profile/skills', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  patchUserProfileSkill(skillId: string, payload: UpdateSkillRequest) {
    return apiFetch<UserProfileAggregateResponse>(`/user/profile/skills/${skillId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  deleteUserProfileSkill(skillId: string) {
    return apiFetch<UserProfileAggregateResponse>(`/user/profile/skills/${skillId}`, {
      method: 'DELETE',
    });
  },

  getUserProfileSkillDetails() {
    return apiFetch<UserSkillDetail[]>('/user/profile/skills/details');
  },


  createUserProfileAiAuditEvent(payload: CreateAiAuditLogRequest) {
    return apiFetch<AiAuditLog>('/user/profile/ai-audit/events', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  finalizeUserProfileAiAuditEvent(auditLogId: number, payload: FinalizeAiAuditLogRequest) {
    return apiFetch<AiAuditLog>(`/user/profile/ai-audit/events/${auditLogId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  revertUserProfileAiAuditEvent(auditLogId: number) {
    return apiFetch<AiAuditRevertResponse>(`/user/profile/ai-audit/events/${auditLogId}/revert`, {
      method: 'POST',
    });
  },

  listUserProfileAiAuditEvents(limit = 50) {
    return apiFetch<AiAuditLog[]>(`/user/profile/ai-audit/events?limit=${limit}`);
  },

  getUserProfileAiEvaluationHook(limit = 100) {
    return apiFetch<AiEvaluationHookItem[]>(`/user/profile/ai-audit/evaluation-hook?limit=${limit}`);
  },

  async exportUserProfileAiAudit(format: 'json' | 'csv' = 'json') {
    const response = await fetch(`/api/user/profile/ai-audit/export?format=${format}`, {
      credentials: 'include',
      cache: 'no-store',
      headers: {'Cache-Control': 'no-store'},
    });

    if (!response.ok) {
      throw new ApiError(response.status, await readErrorDetail(response));
    }

    return response.text();
  },

  getSystemHealth() {
    return apiFetch<AiSystemHealthResponse>('/health/system');
  },

  uploadUserProfileSkillEvidence(payload: {
    skillId: string;
    file: File;
    evidence_note?: string | null;
  }) {
    const formData = new FormData();
    formData.append('file', payload.file);
    if (payload.evidence_note?.trim()) {
      formData.append('evidence_note', payload.evidence_note.trim());
    }

    return apiFetch<UserSkillDetail>(`/user/profile/skills/${payload.skillId}/evidence`, {
      method: 'POST',
      body: formData,
    });
  },

  getUserProfileSuggestions() {
    return apiFetch<UserProfileAggregateResponse['suggestions']>(
      '/user/profile/suggestions'
    );
  },

  getUserCvWorkspaceContext() {
    return apiFetch<UserCvWorkspaceContext>('/user/profile/cv/workspace-context');
  },

  uploadCv(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return apiFetch<UserCvUpload>('/user/profile/upload/cv', {
      method: 'POST',
      body: formData,
    });
  },

  uploadProfileAvatar(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return apiFetch<ProfileAvatarUploadResponse>('/user/profile/upload/avatar', {
      method: 'POST',
      body: formData,
    });
  },

  uploadLanguageCertificate(payload: {
    file: File;
    certificate_name: string;
    issuer_name?: string | null;
    language_entry_id?: number | null;
  }) {
    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('certificate_name', payload.certificate_name);

    if (payload.issuer_name?.trim()) {
      formData.append('issuer_name', payload.issuer_name.trim());
    }

    if (typeof payload.language_entry_id === 'number') {
      formData.append('language_entry_id', String(payload.language_entry_id));
    }

    return apiFetch<UserLanguageCertificate>(
      '/user/profile/upload/language-certificate',
      {
        method: 'POST',
        body: formData,
      }
    );
  },

  getLatestCvParseSnapshot() {
    return apiFetch<UserCvParseSnapshot | null>('/user/profile/cv/latest-parse');
  },

  getLatestCvProfileApplyPlan() {
    return apiFetch<UserCvProfileApplyPlan | null>(
      '/user/profile/cv/latest-apply-plan'
    );
  },

  applySelectedCvProfileOperations(payload: UserCvApplySelectedRequest) {
    return apiFetch<UserCvApplySelectedResponse>(
      '/user/profile/cv/apply-selected',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },


  suggestProfileHeadlineSummary(payload: AiHeadlineSummaryRequest) {
    return apiFetch<AiHeadlineSummaryResponse>('/user/ai/profile/headline-summary', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  suggestProfileRoleFocus(payload: AiRoleFocusRequest) {
    return apiFetch<AiRoleFocusResponse>('/user/ai/profile/role-focus', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  suggestProfileSkillGrouping(payload: {locale: string; group_limit: number; skill_limit_per_group: number}) {
    return apiFetch<AiSkillGroupingResponse>('/user/ai/profile/skill-grouping', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getFilterPolicy() {
    return apiFetch<UserFilterPolicy>('/user/me/filter-policy');
  },

  async getKeywordPreferences() {
    const response = await apiFetch<
      Omit<UserKeywordPreference, 'enabled'> &
        Partial<Pick<UserKeywordPreference, 'enabled'>>
    >('/user/me/keyword-preferences');

    return normalizeKeywordPreference(response);
  },

  async updateKeywordPreferences(payload: {
    include_keywords: string[];
    exclude_keywords: string[];
    match_title: boolean;
    match_location: boolean;
    match_company_name: boolean;
  }) {
    const response = await apiFetch<
      Omit<UserKeywordPreference, 'enabled'> &
        Partial<Pick<UserKeywordPreference, 'enabled'>>
    >('/user/me/keyword-preferences', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });

    return normalizeKeywordPreference(response);
  },

  async previewKeywordPreferences(payload: {
    keyword_preference: {
      include_keywords: string[];
      exclude_keywords: string[];
      match_title: boolean;
      match_location: boolean;
      match_company_name: boolean;
    };
    active_only: boolean;
    sample_limit: number;
  }) {
    const response = await apiFetch<
      Partial<KeywordPreferencePreviewResponse> & {
        total_matches?: number;
        passed_jobs?: number;
        rejected_jobs?: number;
        blocked_jobs?: number;
        filtered_out_jobs?: number;
        active_fields?: string[];
        sample_jobs?: KeywordPreferencePreviewJob[];
      }
    >('/user/me/keyword-preferences/preview', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    const passedJobs =
      typeof response.passed_jobs === 'number'
        ? response.passed_jobs
        : typeof response.total_matches === 'number'
          ? response.total_matches
          : 0;

    const rejectedJobs =
      typeof response.rejected_jobs === 'number'
        ? response.rejected_jobs
        : typeof response.blocked_jobs === 'number'
          ? response.blocked_jobs
          : typeof response.filtered_out_jobs === 'number'
            ? response.filtered_out_jobs
            : 0;

    const blockedJobs =
      typeof response.blocked_jobs === 'number'
        ? response.blocked_jobs
        : rejectedJobs;

    const filteredOutJobs =
      typeof response.filtered_out_jobs === 'number'
        ? response.filtered_out_jobs
        : rejectedJobs;

    return {
      total_matches:
        typeof response.total_matches === 'number'
          ? response.total_matches
          : passedJobs,
      passed_jobs: passedJobs,
      rejected_jobs: rejectedJobs,
      blocked_jobs: blockedJobs,
      filtered_out_jobs: filteredOutJobs,
      active_fields: Array.isArray(response.active_fields)
        ? response.active_fields
        : [],
      sample_jobs: Array.isArray(response.sample_jobs)
        ? response.sample_jobs
        : [],
    } satisfies KeywordPreferencePreviewResponse;
  },

  getJobs(query = '') {
    return apiFetch<JobListResponse>(`/user/jobs${query}`);
  },

  getMatches(query = '') {
    return apiFetch<JobListResponse>(`/user/matches${query}`);
  },

  getMatchInsights() {
    return apiFetch<MatchInsightsData>('/user/match-insights');
  },

  sendCopilotChat(payload: AiCopilotChatRequest) {
    return apiFetch<AiCopilotChatResponse>('/user/ai/copilot/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getSavedJobs() {
    return apiFetch<SavedJobListResponse>('/user/saved-jobs');
  },

  saveJob(jobId: number, matchScore?: number | null) {
    return apiFetch<SavedJob>('/user/saved-jobs', {
      method: 'POST',
      body: JSON.stringify({job_id: jobId, match_score: matchScore ?? null}),
    });
  },

  unsaveJob(jobId: number) {
    return apiFetch<void>(`/user/saved-jobs/${jobId}`, {method: 'DELETE'});
  },

  updateSavedJobStatus(
    savedJobId: number,
    status: SavedJobStatus,
    extra?: {deadline_at?: string; interview_at?: string}
  ) {
    return apiFetch<SavedJob>(`/user/saved-jobs/${savedJobId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({status, ...extra}),
    });
  },

  addSavedJobNote(savedJobId: number, content: string) {
    return apiFetch<SavedJobNote>(`/user/saved-jobs/${savedJobId}/notes`, {
      method: 'POST',
      body: JSON.stringify({content}),
    });
  },

  updateSavedJobNote(savedJobId: number, noteId: number, content: string) {
    return apiFetch<SavedJobNote>(`/user/saved-jobs/${savedJobId}/notes/${noteId}`, {
      method: 'PATCH',
      body: JSON.stringify({content}),
    });
  },

  // ── Security ──────────────────────────────────────────────────

  changePassword(currentPassword: string, newPassword: string, confirmation: string) {
    return apiFetch<{ok: boolean}>('/user/security/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirmation: confirmation,
      }),
    });
  },

  getSessions() {
    return apiFetch<SessionItem[]>('/user/security/sessions');
  },

  endSession(sessionId: number) {
    return apiFetch<void>(`/user/security/sessions/${sessionId}`, {method: 'DELETE'});
  },

  endAllOtherSessions() {
    return apiFetch<{ended: number}>('/user/security/sessions/end-all-others', {method: 'POST'});
  },

  getLoginHistory() {
    return apiFetch<LoginHistoryItem[]>('/user/security/login-history');
  },

  requestEmailChange(newEmail: string, currentPassword: string) {
    return apiFetch<{ok: boolean}>('/user/security/request-email-change', {
      method: 'POST',
      body: JSON.stringify({new_email: newEmail, current_password: currentPassword}),
    });
  },

  confirmEmailChange(verificationCode: string) {
    return apiFetch<{ok: boolean; new_email: string}>('/user/security/confirm-email-change', {
      method: 'POST',
      body: JSON.stringify({verification_code: verificationCode}),
    });
  },

  setupTotp() {
    return apiFetch<TotpSetupResponse>('/user/security/totp/setup', {method: 'POST'});
  },

  verifyTotp(code: string) {
    return apiFetch<{ok: boolean}>('/user/security/totp/verify', {
      method: 'POST',
      body: JSON.stringify({code}),
    });
  },

  disableTotp() {
    return apiFetch<void>('/user/security/totp', {method: 'DELETE'});
  },

  getTotpStatus() {
    return apiFetch<TotpStatusResponse>('/user/security/totp/status');
  },

  deleteAccount(currentPassword: string, reason?: string) {
    return apiFetch<{ok: boolean}>('/user/security/delete-account', {
      method: 'POST',
      body: JSON.stringify({current_password: currentPassword, reason: reason || null}),
    });
  },
};

export function suggestProfileSkillEvidence(
  payload: AiSkillEvidenceRequest,
): Promise<AiSkillEvidenceResponse> {
  return apiFetch<AiSkillEvidenceResponse>('/user/ai/profile/skill-evidence', {
    method: 'POST',
    body: JSON.stringify({
      locale: payload.locale,
      skill_name: payload.skill_name,
      category: payload.category ?? null,
      existing_evidence_note: payload.existing_evidence_note ?? null,
    }),
  });
}
