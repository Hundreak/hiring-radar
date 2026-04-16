import type {AiAuditEvent, AiAuditMarker} from '@/types/ai';
import type {AiAuditFinalizeContext} from '@/types/profile';

export const PROFILE_AI_AUDIT_STORAGE_KEY = 'coresift:profile-ai-audit';

export type PersistedProfileAiAuditState = {
  basicDraft: {
    headline: string;
    summary: string;
  } | null;
  preferencesDraft: {
    target_roles: string;
  } | null;
  skillEditor: {
    mode: 'create' | 'edit';
    targetId: string | null;
    skill_name: string;
    proficiency_hint: string;
    evidence_note: string;
  } | null;
  auditEvents: AiAuditEvent[];
  auditMarkers: AiAuditMarker[];
};

export function loadPersistedProfileAiAuditState(): PersistedProfileAiAuditState | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(PROFILE_AI_AUDIT_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as PersistedProfileAiAuditState;
  } catch {
    return null;
  }
}

export function savePersistedProfileAiAuditState(state: PersistedProfileAiAuditState | null): void {
  if (typeof window === 'undefined') return;
  if (!state) {
    window.sessionStorage.removeItem(PROFILE_AI_AUDIT_STORAGE_KEY);
    return;
  }
  window.sessionStorage.setItem(PROFILE_AI_AUDIT_STORAGE_KEY, JSON.stringify(state));
}

export function buildAiAuditFinalizeContext(auditEventIds: string[]): AiAuditFinalizeContext | null {
  const unique = Array.from(new Set(auditEventIds.filter(Boolean)));
  if (unique.length === 0) return null;
  return {audit_event_ids: unique};
}

export function markerKey(targetField: string, targetEntityId?: string | null): string {
  return `${targetField}::${targetEntityId ?? ''}`;
}

export function upsertAuditMarker(markers: AiAuditMarker[], nextMarker: AiAuditMarker): AiAuditMarker[] {
  const key = markerKey(nextMarker.target_field, nextMarker.target_entity_id);
  const remaining = markers.filter((item) => markerKey(item.target_field, item.target_entity_id) !== key);
  return [nextMarker, ...remaining];
}
