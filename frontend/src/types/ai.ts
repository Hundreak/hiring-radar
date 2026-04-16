export type AiHeadlineSuggestion = {
  title: string;
  rationale: string | null;
};

export type AiSummarySuggestion = {
  text: string;
  rationale: string | null;
};

export type AiHeadlineSummaryResponse = {
  headline_options: AiHeadlineSuggestion[];
  summary_options: AiSummarySuggestion[];
  warnings: string[];
  confidence_band: 'low' | 'medium' | 'high' | string | null;
  telemetry_ref: string | null;
};

export type AiHeadlineSummaryRequest = {
  locale: string;
  headline_option_count?: number;
  summary_option_count?: number;
};


export type AiRoleFocusSuggestion = {
  role_name: string;
  fit_reason: string;
  missing_signals: string[];
  priority: number;
};

export type AiRoleFocusResponse = {
  role_suggestions: AiRoleFocusSuggestion[];
  warnings: string[];
  confidence_band: 'low' | 'medium' | 'high' | string | null;
  telemetry_ref: string | null;
};

export type AiRoleFocusRequest = {
  locale: string;
  suggestion_count?: number;
};

export type AiSkillEvidenceResponse = {
  description_suggestions: string[];
  evidence_note_suggestions: string[];
  proof_ideas: string[];
  missing_signals: string[];
  strengthening_note: string | null;
  warnings: string[];
  confidence_band: 'low' | 'medium' | 'high' | string | null;
  telemetry_ref: string | null;
};

export type AiSkillEvidenceRequest = {
  locale: string;
  skill_name: string;
  category?: string | null;
  existing_evidence_note?: string | null;
};


export type AiSkillGroup = {
  group_name: string;
  skills: string[];
  notes: string | null;
};

export type AiSkillGroupingResponse = {
  groups: AiSkillGroup[];
  duplicates: string[];
  normalization_suggestions: string[];
  warnings: string[];
  confidence_band: 'low' | 'medium' | 'high' | string | null;
  telemetry_ref: string | null;
};


export type AiAuditLog = {
  id: number;
  telemetry_ref: string | null;
  target_field: string;
  target_entity_id: string | null;
  action_type: 'replace' | 'append' | string;
  source_panel: string | null;
  before_snapshot: unknown;
  after_snapshot: unknown;
  persistence_status: 'unsaved' | 'saved' | string;
  evaluation_status: 'accepted' | 'rejected' | 'modified' | 'reverted' | string | null;
  evaluation_score: number | null;
  manual_edit_distance: number | null;
  request_ref: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  reverted_at: string | null;
};

export type CreateAiAuditLogRequest = {
  telemetry_ref?: string | null;
  target_field: string;
  target_entity_id?: string | null;
  action_type: 'replace' | 'append' | string;
  source_panel?: string | null;
  before_snapshot: unknown;
  after_snapshot: unknown;
  persistence_status?: 'unsaved' | 'saved' | string;
  evaluation_status?: string | null;
  metadata?: Record<string, unknown>;
};

export type FinalizeAiAuditLogRequest = {
  persistence_status?: 'saved' | 'unsaved' | string;
  saved_snapshot?: unknown;
  evaluation_status?: 'accepted' | 'rejected' | 'modified' | 'reverted' | string | null;
  metadata?: Record<string, unknown>;
};

export type AiAuditRevertResponse = {
  audit_log: AiAuditLog;
  aggregate: import('./profile').UserProfileAggregateResponse;
};

export type AiEvaluationHookItem = {
  audit_log_id: number;
  telemetry_ref: string | null;
  target_field: string;
  action_type: string;
  persistence_status: string;
  evaluation_status: string | null;
  evaluation_score: number | null;
  manual_edit_distance: number | null;
  source_panel: string | null;
  created_at: string | null;
};

export type AiAuditEvent = {
  audit_log_id: number;
  telemetry_ref: string | null;
  target_field: string;
  target_entity_id: string | null;
  action_type: string;
  before_snapshot: unknown;
  after_snapshot: unknown;
  created_at: string | null;
};

export type AiAuditMarker = {
  target_field: string;
  target_entity_id: string | null;
  audit_log_id: number;
  action_type: string;
  created_at: string | null;
};

export type AiSystemHealthResponse = {
  status: string;
  request_ref: string | null;
  database: Record<string, unknown>;
  ai_runtime: Record<string, unknown>;
};


export type AiCopilotGroundingSource = {
  label: string;
  source_type: string;
  title: string | null;
  snippet: string | null;
  trust_level: string | null;
  freshness_label: string | null;
};

export type AiCopilotChatRequest = {
  locale: string;
  message: string;
  conversation_id?: string | null;
};

export type AiCopilotChatResponse = {
  answer: string;
  follow_up_suggestions: string[];
  sources: AiCopilotGroundingSource[];
  learned_memory_notes: string[];
  warnings: string[];
  confidence_band: 'low' | 'medium' | 'high' | string | null;
  telemetry_ref: string | null;
  conversation_id: string | null;
  message_id: string | null;
};
