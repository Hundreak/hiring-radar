'use client';

import {useEffect} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';

import {ApiError, api} from '@/lib/api';
import {classifyApiError, type ErrorRecoveryInfo} from '@/lib/api-error-ui';
import {queryKeys} from '@/lib/query-keys';
import type {PaginationParams} from '@/lib/pagination';
import {dispatchSavedJobsChanged, onSavedJobsChanged} from '@/lib/saved-jobs-events';
import type {JobListResponse} from '@/types/job';
import type {EmployerAuditQueryParams} from '@/types/user';
import type {SavedJob, SavedJobListResponse, SavedJobStatus} from '@/types/saved';

type SavedJobsQueryParams = PaginationParams & {status?: SavedJobStatus | null};

export function getQueryErrorMessage(error: unknown): string | null {
  if (!error) {
    return null;
  }

  if (error instanceof ApiError && error.status === 401) {
    return null;
  }

  return classifyApiError(error).detail;
}

export function getQueryErrorRecovery(error: unknown): ErrorRecoveryInfo | null {
  return error ? classifyApiError(error) : null;
}

export function useUserSessionQuery() {
  return useQuery({
    queryKey: queryKeys.auth.session,
    queryFn: () => api.getSession(),
  });
}

export function useUserProfileQuery() {
  return useQuery({
    queryKey: queryKeys.user.profile,
    queryFn: () => api.getProfile(),
  });
}

export function useUserProfileAggregateQuery() {
  return useQuery({
    queryKey: queryKeys.user.profileAggregate,
    queryFn: () => api.getUserProfileAggregate(),
  });
}

export function useJobsQuery(query = '', params: PaginationParams = {}) {
  return useQuery({
    queryKey: queryKeys.jobs.list(query, params),
    queryFn: () => api.getJobs({query, ...params}),
    placeholderData: (previous) => previous,
  });
}

export function useMatchesQuery(params: PaginationParams = {}) {
  return useQuery({
    queryKey: queryKeys.jobs.matches(params),
    queryFn: () => api.getMatches(params),
    placeholderData: (previous) => previous,
  });
}

export function useMatchInsightsQuery() {
  return useQuery({
    queryKey: queryKeys.jobs.matchInsights,
    queryFn: () => api.getMatchInsights(),
  });
}

export function useSavedJobsQuery(params: SavedJobsQueryParams = {}) {
  return useQuery({
    queryKey: queryKeys.jobs.saved(params),
    queryFn: () => api.getSavedJobs(params),
    placeholderData: (previous) => previous,
  });
}

function updateSavedJobsCache(
  current: SavedJobListResponse | undefined,
  jobId: number,
  action: 'saved' | 'unsaved',
  savedJob?: SavedJob
): SavedJobListResponse | undefined {
  if (!current) {
    return current;
  }

  if (action === 'unsaved') {
    return {
      ...current,
      items: current.items.filter((item) => item.job_id !== jobId),
    };
  }

  if (!savedJob || current.items.some((item) => item.job_id === jobId)) {
    return current;
  }

  return {
    ...current,
    items: [savedJob, ...current.items],
  };
}

function patchJobSavedState(
  current: JobListResponse | undefined,
  jobId: number,
  saved: boolean
): JobListResponse | undefined {
  if (!current) {
    return current;
  }

  return {
    ...current,
    items: current.items.map((job) =>
      job.id === jobId ? {...job, saved} : job
    ),
  } as JobListResponse;
}

function invalidateJobSurfaces(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({queryKey: ['jobs']});
}

export function useSavedJobsEventBridge() {
  const queryClient = useQueryClient();

  useEffect(() => {
    return onSavedJobsChanged(({jobId, action}) => {
      queryClient.setQueriesData<SavedJobListResponse>({queryKey: ['jobs', 'saved']}, (current) =>
        updateSavedJobsCache(current, jobId, action)
      );
      void queryClient.invalidateQueries({queryKey: ['jobs', 'saved']});
    });
  }, [queryClient]);
}

export function useSaveJobMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({jobId, matchScore}: {jobId: number; matchScore?: number | null}) =>
      api.saveJob(jobId, matchScore),
    onSuccess(savedJob, variables) {
      queryClient.setQueriesData<SavedJobListResponse>({queryKey: ['jobs', 'saved']}, (current) =>
        updateSavedJobsCache(current, variables.jobId, 'saved', savedJob)
      );
      queryClient.setQueriesData<JobListResponse>({queryKey: ['jobs', 'list']}, (current) =>
        patchJobSavedState(current, variables.jobId, true)
      );
      queryClient.setQueriesData<JobListResponse>({queryKey: ['jobs', 'matches']}, (current) =>
        patchJobSavedState(current, variables.jobId, true)
      );
      dispatchSavedJobsChanged({jobId: variables.jobId, action: 'saved'});
    },
    onSettled() {
      invalidateJobSurfaces(queryClient);
    },
  });
}

export function useUnsaveJobMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: number) => api.unsaveJob(jobId),
    onSuccess(_result, jobId) {
      queryClient.setQueriesData<SavedJobListResponse>({queryKey: ['jobs', 'saved']}, (current) =>
        updateSavedJobsCache(current, jobId, 'unsaved')
      );
      queryClient.setQueriesData<JobListResponse>({queryKey: ['jobs', 'list']}, (current) =>
        patchJobSavedState(current, jobId, false)
      );
      queryClient.setQueriesData<JobListResponse>({queryKey: ['jobs', 'matches']}, (current) =>
        patchJobSavedState(current, jobId, false)
      );
      dispatchSavedJobsChanged({jobId, action: 'unsaved'});
    },
    onSettled() {
      invalidateJobSurfaces(queryClient);
    },
  });
}

export function useUpdateSavedJobStatusMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      savedJobId,
      status,
      extra,
    }: {
      savedJobId: number;
      status: SavedJobStatus;
      extra?: {deadline_at?: string; interview_at?: string};
    }) => api.updateSavedJobStatus(savedJobId, status, extra),
    onSuccess(updated) {
      queryClient.setQueriesData<SavedJobListResponse>({queryKey: ['jobs', 'saved']}, (current) => {
        if (!current) return current;
        return {
          ...current,
          items: current.items.map((item) => (item.id === updated.id ? updated : item)),
        };
      });
    },
    onSettled() {
      void queryClient.invalidateQueries({queryKey: ['jobs', 'saved']});
    },
  });
}

export function useAddSavedJobNoteMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({savedJobId, content}: {savedJobId: number; content: string}) =>
      api.addSavedJobNote(savedJobId, content),
    onSuccess(note, variables) {
      queryClient.setQueriesData<SavedJobListResponse>({queryKey: ['jobs', 'saved']}, (current) => {
        if (!current) return current;
        return {
          ...current,
          items: current.items.map((item) =>
            item.id === variables.savedJobId
              ? {...item, notes: [note, ...item.notes]}
              : item
          ),
        };
      });
    },
    onSettled() {
      void queryClient.invalidateQueries({queryKey: ['jobs', 'saved']});
    },
  });
}

export function useUpdateSavedJobNoteMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({savedJobId, noteId, content}: {savedJobId: number; noteId: number; content: string}) =>
      api.updateSavedJobNote(savedJobId, noteId, content),
    onSuccess(note, variables) {
      queryClient.setQueriesData<SavedJobListResponse>({queryKey: ['jobs', 'saved']}, (current) => {
        if (!current) return current;
        return {
          ...current,
          items: current.items.map((item) =>
            item.id === variables.savedJobId
              ? {
                  ...item,
                  notes: item.notes.map((existingNote) =>
                    existingNote.id === variables.noteId ? note : existingNote
                  ),
                }
              : item
          ),
        };
      });
    },
    onSettled() {
      void queryClient.invalidateQueries({queryKey: ['jobs', 'saved']});
    },
  });
}


export function useEmployerSessionQuery() {
  return useQuery({
    queryKey: queryKeys.employer.session,
    queryFn: () => api.getEmployerSession(),
  });
}

export function useEmployerRuntimeQuery() {
  return useQuery({
    queryKey: queryKeys.employer.runtime,
    queryFn: () => api.getEmployerRuntime(),
    staleTime: 60_000,
  });
}

export function useEmployerCommunicationPreferencesQuery() {
  return useQuery({
    queryKey: queryKeys.employer.communicationPreferences,
    queryFn: () => api.getEmployerCommunicationPreferences(),
    staleTime: 60_000,
  });
}

export function useEmployerAuditEventsQuery(params: EmployerAuditQueryParams = {}) {
  return useQuery({
    queryKey: queryKeys.employer.auditEvents(params),
    queryFn: () => api.getEmployerAuditEvents(params),
    placeholderData: (previous) => previous,
  });
}

export function useUpdateEmployerCommunicationPreferencesMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.updateEmployerCommunicationPreferences,
    onSuccess(data) {
      queryClient.setQueryData(queryKeys.employer.communicationPreferences, data);
    },
    onSettled() {
      void queryClient.invalidateQueries({queryKey: queryKeys.employer.communicationPreferences});
    },
  });
}

export function useEmployerLogoutMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.logoutEmployer(),
    onSettled() {
      queryClient.clear();
    },
  });
}
