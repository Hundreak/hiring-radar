import {emitSessionExpired, getSessionSurfaceForPath, shouldEmitSessionExpired} from '@/lib/auth-session-events';

import type {
  CandidateWorkflowById,
  CandidateWorkflowState,
  EmployerOutreachCampaign,
  EmployerOutreachCampaignCreatePayload,
  EmployerSendQueue,
  EmployerSendQueuePreparePayload,
} from '@/types/employer-outreach';

type WorkflowApiResponse = {
  ok: boolean;
  workflow?: Record<string, CandidateWorkflowState>;
};

type CampaignListApiResponse = {
  ok: boolean;
  items?: EmployerOutreachCampaign[];
};

type CampaignCreateApiResponse = {
  ok: boolean;
  campaign?: EmployerOutreachCampaign;
  workflow?: Record<string, CandidateWorkflowState>;
};

type SendQueueApiResponse = {
  ok: boolean;
  queue?: EmployerSendQueue | null;
};

function workflowFromApi(workflow?: Record<string, CandidateWorkflowState>): CandidateWorkflowById {
  if (!workflow) return {};
  return Object.entries(workflow).reduce<CandidateWorkflowById>((acc, [candidateId, state]) => {
    const numericId = Number(candidateId);
    if (Number.isFinite(numericId)) {
      acc[numericId] = {
        tags: Array.isArray(state?.tags) ? state.tags : [],
        notes: Array.isArray(state?.notes) ? state.notes : [],
      };
    }
    return acc;
  }, {});
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload?.ok) {
    const detail = payload?.detail || `Employer outreach API failed: ${response.status}`;
    if (shouldEmitSessionExpired(path, response.status)) {
      emitSessionExpired({
        surface: getSessionSurfaceForPath(path),
        path,
        detail,
        requestId: response.headers.get('X-Request-ID'),
        status: response.status,
      });
    }
    throw new Error(detail);
  }
  return payload as T;
}

export async function loadEmployerTalentWorkflow(): Promise<CandidateWorkflowById> {
  const payload = await apiFetch<WorkflowApiResponse>('/api/employer/talent/workflow');
  return workflowFromApi(payload.workflow);
}

export async function listEmployerOutreachCampaigns(): Promise<EmployerOutreachCampaign[]> {
  const payload = await apiFetch<CampaignListApiResponse>('/api/employer/outreach/campaigns');
  return payload.items ?? [];
}

export async function createEmployerOutreachCampaign(payload: EmployerOutreachCampaignCreatePayload): Promise<{
  campaign: EmployerOutreachCampaign;
  workflow: CandidateWorkflowById;
}> {
  const response = await apiFetch<CampaignCreateApiResponse>('/api/employer/outreach/campaigns', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!response.campaign) throw new Error('Campaign was not returned by the API');
  return {campaign: response.campaign, workflow: workflowFromApi(response.workflow)};
}

export async function bulkTagEmployerCandidates(candidateIds: number[], tag: string): Promise<CandidateWorkflowById> {
  const payload = await apiFetch<WorkflowApiResponse>('/api/employer/talent/workflow/bulk-tags', {
    method: 'POST',
    body: JSON.stringify({candidate_ids: candidateIds, tag}),
  });
  return workflowFromApi(payload.workflow);
}

export async function bulkNoteEmployerCandidates(candidateIds: number[], note: string): Promise<CandidateWorkflowById> {
  const payload = await apiFetch<WorkflowApiResponse>('/api/employer/talent/workflow/bulk-notes', {
    method: 'POST',
    body: JSON.stringify({candidate_ids: candidateIds, note}),
  });
  return workflowFromApi(payload.workflow);
}

export async function removeEmployerCandidateTag(candidateId: number, tag: string): Promise<CandidateWorkflowById> {
  const payload = await apiFetch<WorkflowApiResponse>(
    `/api/employer/talent/workflow/candidates/${candidateId}/tags/${encodeURIComponent(tag)}`,
    {method: 'DELETE'}
  );
  return workflowFromApi(payload.workflow);
}

export async function loadEmployerCampaignSendQueue(campaignId: string): Promise<EmployerSendQueue | null> {
  const payload = await apiFetch<SendQueueApiResponse>(`/api/employer/outreach/campaigns/${campaignId}/send-queue`);
  return payload.queue ?? null;
}

export async function prepareEmployerCampaignSendQueue(campaignId: string, payload: EmployerSendQueuePreparePayload): Promise<EmployerSendQueue> {
  const response = await apiFetch<SendQueueApiResponse>(`/api/employer/outreach/campaigns/${campaignId}/send-queue/prepare`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!response.queue) throw new Error('Send queue was not returned by the API');
  return response.queue;
}


export async function updateEmployerCampaignSendQueueItem(
  campaignId: string,
  itemId: string,
  payload: {
    status?: import('@/types/employer-outreach').EmployerSendQueueItemStatus;
    checks?: string[];
    actor?: string;
    note?: string;
  }
): Promise<EmployerSendQueue> {
  const response = await apiFetch<SendQueueApiResponse>(
    `/api/employer/outreach/campaigns/${campaignId}/send-queue/items/${itemId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }
  );
  if (!response.queue) throw new Error('Updated send queue was not returned by the API');
  return response.queue;
}
