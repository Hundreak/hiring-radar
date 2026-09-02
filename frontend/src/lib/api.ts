import {emitSessionExpiredFromApiError} from '@/lib/auth-session-events';
import {buildPaginationQuery, type PaginationParams} from '@/lib/pagination';
import type {JobListResponse} from '@/types/job';
import type {SavedJob, SavedJobListResponse, SavedJobNote, SavedJobStatus} from '@/types/saved';

type JobsQueryParams = PaginationParams & {query?: string};
type SavedJobsQueryParams = PaginationParams & {status?: SavedJobStatus | null};

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
  UpdateUserNotificationPreferenceRequest,
  UserNotificationPreference,
  UserPasswordLoginRequest,
  UserPasswordLoginResponse,
  UserProfile,
  EmployerAuthSession,
  EmployerLoginRequest,
  EmployerLoginResponse,
  EmployerRegisterRequest,
  EmployerRegisterResponse,
  EmployerRuntimeStatus,
  EmployerCommunicationPreferencesResponse,
  UpdateEmployerCommunicationPreferencesRequest,
  EmployerAuditEventListResponse,
  EmployerAuditExportResponse,
  EmployerAuditQueryParams,
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


const CSRF_COOKIE_NAME = process.env.NEXT_PUBLIC_CSRF_COOKIE_NAME ?? 'hiring_radar_csrf';
const CSRF_HEADER_NAME = process.env.NEXT_PUBLIC_CSRF_HEADER_NAME ?? 'X-CSRF-Token';
const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function readBrowserCookie(name: string): string | null {
  if (typeof document === 'undefined') {
    return null;
  }

  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${name}=`));

  if (!cookie) {
    return null;
  }

  return decodeURIComponent(cookie.slice(name.length + 1));
}

function shouldAttachCsrfToken(init?: RequestInit): boolean {
  const method = (init?.method ?? 'GET').toUpperCase();
  return UNSAFE_METHODS.has(method);
}

export class ApiError extends Error {
  status: number;
  statusCode: number;
  detail: string;
  requestId: string | null;
  retryAfterSeconds: number | null;

  constructor(
    status: number,
    detail: string,
    options: {requestId?: string | null; retryAfterSeconds?: number | null} = {}
  ) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.statusCode = status;
    this.detail = detail;
    this.requestId = options.requestId ?? null;
    this.retryAfterSeconds = options.retryAfterSeconds ?? null;
  }
}

function parseRetryAfterHeader(value: string | null): number | null {
  if (!value) {
    return null;
  }

  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds > 0) {
    return Math.ceil(seconds);
  }

  const dateMs = Date.parse(value);
  if (Number.isFinite(dateMs)) {
    const deltaSeconds = Math.ceil((dateMs - Date.now()) / 1000);
    return deltaSeconds > 0 ? deltaSeconds : null;
  }

  return null;
}

async function readErrorDetail(response: Response): Promise<string> {
  const maybeJson = await response.json().catch(() => null);

  if (typeof maybeJson?.detail === 'string') {
    return maybeJson.detail;
  }

  if (typeof maybeJson?.message === 'string') {
    return maybeJson.message;
  }

  if (typeof maybeJson?.error?.message === 'string') {
    return maybeJson.error.message;
  }

  return 'Request failed.';
}

async function createApiError(response: Response): Promise<ApiError> {
  return new ApiError(response.status, await readErrorDetail(response), {
    requestId: response.headers.get('X-Request-ID'),
    retryAfterSeconds: parseRetryAfterHeader(response.headers.get('Retry-After')),
  });
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const hasFormDataBody =
    typeof FormData !== 'undefined' && init?.body instanceof FormData;

  if (!hasFormDataBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  headers.set('Cache-Control', 'no-store');

  if (shouldAttachCsrfToken(init) && !headers.has(CSRF_HEADER_NAME)) {
    const csrfToken = readBrowserCookie(CSRF_COOKIE_NAME);
    if (csrfToken) {
      headers.set(CSRF_HEADER_NAME, csrfToken);
    }
  }

  const response = await fetch(`/api${path}`, {
    credentials: 'include',
    cache: 'no-store',
    ...init,
    headers,
  });

  if (!response.ok) {
    const error = await createApiError(response);
    emitSessionExpiredFromApiError(path, error);
    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function toQueryString(params: URLSearchParams): string {
  const value = params.toString();
  return value ? `?${value}` : '';
}

function buildJobsQuery(params: string | JobsQueryParams = ''): string {
  if (typeof params === 'string') {
    return params;
  }

  const searchParams = buildPaginationQuery(params);
  const query = params.query?.trim();
  if (query) {
    searchParams.set('q', query);
  }
  return toQueryString(searchParams);
}

function buildSavedJobsQuery(params: SavedJobsQueryParams = {}): string {
  const searchParams = buildPaginationQuery(params);
  if (params.status) {
    searchParams.set('status', params.status);
  }
  return toQueryString(searchParams);
}


function buildEmployerAuditQuery(params: EmployerAuditQueryParams = {}): string {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.eventType?.trim()) searchParams.set('event_type', params.eventType.trim());
  if (params.resourceType?.trim()) searchParams.set('resource_type', params.resourceType.trim());
  if (params.resourceId?.trim()) searchParams.set('resource_id', params.resourceId.trim());
  if (params.actorUserId) searchParams.set('actor_user_id', String(params.actorUserId));
  if (params.createdFrom?.trim()) searchParams.set('created_from', params.createdFrom.trim());
  if (params.createdTo?.trim()) searchParams.set('created_to', params.createdTo.trim());
  return toQueryString(searchParams);
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
      body: JSON.stringify({
        company_name: payload.company_name,
        company_email: payload.company_email,
        full_name: payload.contact_name,
        password: payload.password,
        password_confirmation: payload.password_confirmation,
      }),
    });
  },

  getEmployerSession() {
    return apiFetch<EmployerAuthSession>('/employer/auth/me');
  },

  getEmployerRuntime() {
    return apiFetch<EmployerRuntimeStatus>('/employer/runtime');
  },

  getEmployerCommunicationPreferences() {
    return apiFetch<EmployerCommunicationPreferencesResponse>(
      '/employer/settings/communication-preferences'
    );
  },

  updateEmployerCommunicationPreferences(payload: UpdateEmployerCommunicationPreferencesRequest) {
    return apiFetch<EmployerCommunicationPreferencesResponse>(
      '/employer/settings/communication-preferences',
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }
    );
  },


  getEmployerAuditEvents(params: EmployerAuditQueryParams = {}) {
    return apiFetch<EmployerAuditEventListResponse>(
      `/employer/compliance/audit-events${buildEmployerAuditQuery(params)}`
    );
  },

  exportEmployerAuditEvents(params: EmployerAuditQueryParams & {format?: 'json' | 'csv'} = {}) {
    const query = buildEmployerAuditQuery(params);
    const separator = query ? `${query}&` : '?';
    const format = params.format ?? 'json';
    return apiFetch<EmployerAuditExportResponse>(
      `/employer/compliance/audit-events/export${separator}format=${format}`
    );
  },

  logoutEmployer() {
    return apiFetch<{ok: boolean}>('/employer/auth/logout', {method: 'POST'});
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

  getUserNotificationPreferences() {
    return apiFetch<UserNotificationPreference>('/user/me/notification-preferences');
  },

  updateUserNotificationPreferences(payload: UpdateUserNotificationPreferenceRequest) {
    return apiFetch<UserNotificationPreference>('/user/me/notification-preferences', {
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
      const error = await createApiError(response);
      emitSessionExpiredFromApiError('/user/profile/ai-audit/export', error);
      throw error;
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

  getJobs(params: string | JobsQueryParams = '') {
    return apiFetch<JobListResponse>(`/user/jobs${buildJobsQuery(params)}`);
  },

  getMatches(params: string | PaginationParams = '') {
    const query = typeof params === 'string' ? params : toQueryString(buildPaginationQuery(params));
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

  getSavedJobs(params: SavedJobsQueryParams = {}) {
    return apiFetch<SavedJobListResponse>(`/user/saved-jobs${buildSavedJobsQuery(params)}`);
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
