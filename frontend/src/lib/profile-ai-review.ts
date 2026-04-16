export type AiPanelKey = 'headline-summary' | 'role-focus' | 'skill-evidence';
export type AiFieldKey =
  | 'headline'
  | 'summary'
  | 'target_roles'
  | 'skill_proficiency_hint'
  | 'skill_evidence_note';
export type AiApplyMode = 'replace' | 'append';

export type AppliedAiAction = {
  key: string;
  panel: AiPanelKey;
  field: AiFieldKey;
  mode: AiApplyMode;
  summary: string;
  appliedAt: number;
  dirty: boolean;
};

export function buildAiAppliedKey(
  panel: AiPanelKey,
  field: AiFieldKey,
  mode: AiApplyMode,
  value: string,
) {
  return `${panel}::${field}::${mode}::${value.trim().toLocaleLowerCase('tr-TR')}`;
}

export function buildPreviewValue(
  currentValue: string,
  incomingValue: string,
  mode: AiApplyMode,
) {
  const normalizedCurrent = currentValue.trim();
  const normalizedIncoming = incomingValue.trim();

  if (mode === 'replace' || !normalizedCurrent) {
    return normalizedIncoming;
  }

  if (!normalizedIncoming) {
    return normalizedCurrent;
  }

  return `${normalizedCurrent}\n\n${normalizedIncoming}`;
}

export function mapAiErrorToProductCopy(locale: string, reason: unknown) {
  const fallback =
    locale === 'en'
      ? 'There was a connection hiccup. Please try again.'
      : locale === 'de'
        ? 'Bei der Verbindung ist ein Problem aufgetreten. Bitte versuche es erneut.'
        : 'Bağlantıda bir aksama oldu, lütfen tekrar dene.';

  if (typeof reason === 'string' && reason.trim()) {
    return reason;
  }

  if (reason instanceof Error && reason.message.trim()) {
    return reason.message;
  }

  return fallback;
}
