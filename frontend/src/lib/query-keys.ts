import type {PaginationParams} from '@/lib/pagination';
import type {SavedJobStatus} from '@/types/saved';

type SavedJobsQueryParams = PaginationParams & {status?: SavedJobStatus | null};

export const queryKeys = {
  auth: {
    session: ['auth', 'session'] as const,
  },
  user: {
    profile: ['user', 'profile'] as const,
    profileAggregate: ['user', 'profile', 'aggregate'] as const,
    cvWorkspaceContext: ['user', 'profile', 'cv', 'workspace-context'] as const,
    skillDetails: ['user', 'profile', 'skills', 'details'] as const,
    keywordPreferences: ['user', 'keyword-preferences'] as const,
    filterPolicy: ['user', 'filter-policy'] as const,
    security: {
      sessions: ['user', 'security', 'sessions'] as const,
      loginHistory: ['user', 'security', 'login-history'] as const,
      totpStatus: ['user', 'security', 'totp-status'] as const,
    },
  },
  jobs: {
    list: (query = '', params: PaginationParams = {}) => ['jobs', 'list', {query, ...params}] as const,
    matches: (params: PaginationParams = {}) => ['jobs', 'matches', params] as const,
    matchInsights: ['jobs', 'match-insights'] as const,
    saved: (params: SavedJobsQueryParams = {}) => ['jobs', 'saved', params] as const,
  },
  employer: {
    session: ['employer', 'session'] as const,
    runtime: ['employer', 'runtime'] as const,
    communicationPreferences: ['employer', 'communication-preferences'] as const,
    auditEvents: (params: Record<string, unknown> = {}) => ['employer', 'audit-events', params] as const,
  },
  ai: {
    systemHealth: ['ai', 'system-health'] as const,
  },
} as const;
