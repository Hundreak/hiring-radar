export type CandidateWorkflowNote = {
  id: string;
  author: string;
  body: string;
  createdAt: string;
  tone?: 'neutral' | 'success' | 'warning' | 'ai';
};

export type CandidateWorkflowState = {
  tags: string[];
  notes: CandidateWorkflowNote[];
};

export type CandidateWorkflowById = Record<number, CandidateWorkflowState>;

export type EmployerOutreachChannel = 'email' | 'linkedin' | 'whatsapp';
export type EmployerOutreachTone = 'warm' | 'direct' | 'premium' | 'technical';
export type EmployerOutreachTemplate = 'role-fit' | 'quick-intro' | 'technical-depth' | 'salary-transparent';

export type EmployerOutreachCampaign = {
  id: string;
  name: string;
  status: 'draft' | 'queued' | 'sent' | string;
  candidate_ids: number[];
  channel: EmployerOutreachChannel;
  tone: EmployerOutreachTone;
  template: EmployerOutreachTemplate;
  include_salary: boolean;
  include_calendar: boolean;
  message_preview: string;
  response_rate: number;
  created_at: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
};

export type EmployerOutreachCampaignCreatePayload = {
  name?: string;
  candidate_ids: number[];
  channel: EmployerOutreachChannel;
  tone: EmployerOutreachTone;
  template: EmployerOutreachTemplate;
  include_salary: boolean;
  include_calendar: boolean;
  message_preview?: string;
  response_rate: number;
  metadata?: Record<string, unknown>;
};

export type EmployerSendQueueItemStatus = 'ready' | 'review' | 'blocked';

export type EmployerSendQueueAuditEvent = {
  id: string;
  action: string;
  actor: string;
  note: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};

export type EmployerSendQueueItem = {
  id: string;
  candidate_id: number;
  subject: string;
  message: string;
  response_score: number;
  status: EmployerSendQueueItemStatus;
  checks: string[];
  metadata?: Record<string, unknown>;
  updated_at?: string;
};

export type EmployerSendQueue = {
  id: string;
  campaign_id: string;
  employer_id?: string;
  status: 'ready_for_review' | 'blocked' | string;
  channel?: EmployerOutreachChannel;
  items: EmployerSendQueueItem[];
  ready_count: number;
  review_count: number;
  blocked_count: number;
  created_at: string;
  updated_at: string;
  audit: EmployerSendQueueAuditEvent[];
};

export type EmployerSendQueuePreparePayload = {
  items: Array<{
    candidate_id: number;
    subject: string;
    message: string;
    response_score: number;
    status: EmployerSendQueueItemStatus;
    checks: string[];
    metadata?: Record<string, unknown>;
  }>;
  actor?: string;
  note?: string;
};

export type EmployerSendQueueItemUpdatePayload = {
  status?: EmployerSendQueueItemStatus;
  checks?: string[];
  actor?: string;
  note?: string;
};
