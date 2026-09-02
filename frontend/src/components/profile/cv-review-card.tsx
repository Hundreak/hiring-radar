'use client';

import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
  useTransition,
} from 'react';
import {useParams, useRouter} from 'next/navigation';

import {
  buildSelectionAwareFieldReviewItems,
  buildSelectionAwareReviewSummary,
  findSelectionAwareFieldReviewItem,
  type SelectionAwareFieldReviewItem,
  type SelectionAwareFieldReviewReasonCode,
} from '@/lib/cv-review-insights';
import {api} from '@/lib/api';
import {
  buildEnterpriseSignalNote,
  formatEnterpriseAtsValue,
  formatEnterpriseCacheStatusValue,
  formatEnterprisePiiTypes,
  formatEnterpriseRedactionValue,
  formatEnterpriseRelationValue,
  getEnterpriseSignalIntent,
} from '@/lib/cv-enterprise-display';
import type {
  UserCvApplySelectedRequest,
  UserCvFieldConfidence,
  UserCvFieldReviewSeverity,
  UserCvProfileApplyPlan,
} from '@/types/user';
import {CV_REVIEW_COPY as COPY} from '@/components/profile/cv-review-copy';
import type {CvReviewCopy as CopyShape, CvReviewLocaleKey as LocaleKey} from '@/components/profile/cv-review-copy';

type CvReviewCardProps = {
  className?: string;
  onApplyCompleted?: () => void | Promise<void>;
};

function resolveLocale(value: unknown): LocaleKey {
  if (typeof value !== 'string') {
    return 'en';
  }
  if (value.startsWith('tr')) {
    return 'tr';
  }
  if (value.startsWith('de')) {
    return 'de';
  }
  return 'en';
}

function getErrorMessage(reason: unknown, fallback: string): string {
  if (reason instanceof Error && reason.message.trim()) {
    return reason.message;
  }

  if (
    typeof reason === 'object' &&
    reason !== null &&
    'message' in reason &&
    typeof (reason as {message: string}).message === 'string'
  ) {
    return (reason as {message: string}).message;
  }

  return fallback;
}

function toggleStringItem(values: string[], fieldName: string): string[] {
  return values.includes(fieldName)
    ? values.filter((value) => value !== fieldName)
    : [...values, fieldName];
}

function toggleNumberItem(values: number[], index: number): number[] {
  return values.includes(index)
    ? values.filter((value) => value !== index)
    : [...values, index];
}

function countSelectedOperations(selection: UserCvApplySelectedRequest): number {
  return (
    selection.scalar_fields.length +
    selection.list_fields.length +
    selection.education_entry_indexes.length +
    selection.experience_entry_indexes.length +
    selection.language_entry_indexes.length
  );
}

function buildDefaultSelection(
  plan: UserCvProfileApplyPlan
): UserCvApplySelectedRequest {
  return {
    parse_run_id: plan.parse_run_id,
    scalar_fields: [plan.headline, plan.summary, plan.remote_preference]
      .filter((item) => item.default_selected)
      .map((item) => item.field_name),
    list_fields: [plan.skills, plan.target_roles, plan.preferred_locations]
      .filter((item) => item.default_selected)
      .map((item) => item.field_name),
    education_entry_indexes: plan.education_entries
      .map((item, index) => ({item, index}))
      .filter(({item}) => item.default_selected)
      .map(({index}) => index),
    experience_entry_indexes: plan.experience_entries
      .map((item, index) => ({item, index}))
      .filter(({item}) => item.default_selected)
      .map(({index}) => index),
    language_entry_indexes: plan.language_entries
      .map((item, index) => ({item, index}))
      .filter(({item}) => item.default_selected)
      .map(({index}) => index),
    manual_review_acknowledged: false,
  };
}

function formatDateTime(value: string | null | undefined, locale: LocaleKey): string {
  if (!value) {
    return '—';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed);
}

function fieldLabel(copy: CopyShape, fieldName: string): string {
  const mapping: Record<string, string> = {
    headline: copy.headline,
    summary: copy.summary,
    remote_preference: copy.remotePreference,
    skills: copy.skills,
    target_roles: copy.targetRoles,
    preferred_locations: copy.preferredLocations,
    education_entries: copy.education,
    experience_entries: copy.experience,
    language_entries: copy.languages,
  };

  return mapping[fieldName] ?? fieldName;
}

function formatParseStatus(value: string | null | undefined, copy: CopyShape): string {
  if (!value) {
    return '—';
  }

  return copy.parseStatusValues[value] ?? value;
}

function formatExtractionFileFormat(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }

  return value.toUpperCase();
}

function formatExtractionMethod(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }

  const mapping: Record<string, string> = {
    pdf_text: 'PDF Text',
    docx_text: 'DOCX Text',
    image_ocr: 'Image OCR',
  };

  return mapping[value] ?? value;
}

function formatBooleanValue(value: boolean | null | undefined, copy: CopyShape): string {
  if (value === true) {
    return copy.manualReviewRequiredValue === 'Gerekli' ? 'Evet' : copy.manualReviewRequiredValue === 'Required' ? 'Yes' : 'Ja';
  }
  if (value === false) {
    return copy.manualReviewRequiredValue === 'Gerekli' ? 'Hayır' : copy.manualReviewRequiredValue === 'Required' ? 'No' : 'Nein';
  }
  return '—';
}

function formatExtractionQualityValue(
  value: string | null | undefined,
  copy: CopyShape
): string {
  switch (value) {
    case 'high':
      return copy.qualityHigh;
    case 'medium':
      return copy.qualityMedium;
    case 'low':
      return copy.qualityLow;
    default:
      return value ?? '—';
  }
}

function formatExtractionReviewHints(
  values: string[] | null | undefined,
  copy: CopyShape
): string {
  if (!values || values.length === 0) {
    return '—';
  }

  const mapping: Record<string, string> = {
    extraction_failed: copy.hintExtractionFailed,
    ocr_no_text_detected: copy.hintOcrNoTextDetected,
    no_text_detected: copy.hintNoTextDetected,
    ocr_source: copy.hintOcrSource,
    low_text_volume: copy.hintLowTextVolume,
    medium_text_volume: copy.hintMediumTextVolume,
    manual_review_recommended: copy.hintManualReviewRecommended,
  };

  return values.map((value) => mapping[value] ?? value).join(', ');
}

function formatManualReviewStatusValue(
  value: boolean | null | undefined,
  copy: CopyShape
): string {
  if (value === true) {
    return copy.manualReviewRequiredValue;
  }
  if (value === false) {
    return copy.manualReviewNotRequiredValue;
  }
  return '—';
}

function formatSafeForDefaultApplyValue(
  value: boolean | null | undefined,
  copy: CopyShape
): string {
  if (value === true) {
    return copy.defaultApplySafeValue;
  }
  if (value === false) {
    return copy.defaultApplyUnsafeValue;
  }
  return '—';
}

function formatFallbackReasonValue(
  value: string | null | undefined,
  copy: CopyShape
): string {
  switch (value) {
    case null:
    case undefined:
      return copy.fallbackReasonNone;
    case 'extraction_failed':
      return copy.fallbackReasonExtractionFailed;
    case 'no_text_detected':
      return copy.fallbackReasonNoTextDetected;
    case 'ocr_no_text_detected':
      return copy.fallbackReasonOcrNoTextDetected;
    case 'low_quality_ocr':
      return copy.fallbackReasonLowQualityOcr;
    case 'low_text_volume':
      return copy.fallbackReasonLowTextVolume;
    case 'ocr_review_recommended':
      return copy.fallbackReasonOcrReviewRecommended;
    default:
      return value;
  }
}

function formatRecommendedNextActionValue(
  value: string | null | undefined,
  copy: CopyShape
): string {
  switch (value) {
    case 'safe_to_apply':
      return copy.nextActionSafeToApply;
    case 'review_before_apply':
      return copy.nextActionReviewBeforeApply;
    case 'reupload_or_edit_manually':
      return copy.nextActionReuploadOrEditManually;
    case 'reupload_as_document':
      return copy.nextActionReuploadAsDocument;
    default:
      return value ?? '—';
  }
}

function formatSeverityLabel(
  severity: UserCvFieldReviewSeverity,
  copy: CopyShape
): string {
  switch (severity) {
    case 'review_required':
      return copy.reviewRequiredBadge;
    case 'review_recommended':
      return copy.reviewRecommendedBadge;
    default:
      return copy.safeBadge;
  }
}

function severityClasses(severity: UserCvFieldReviewSeverity): string {
  switch (severity) {
    case 'review_required':
      return 'border-rose-700/40 bg-rose-500/10 text-rose-200';
    case 'review_recommended':
      return 'border-amber-700/40 bg-amber-500/10 text-amber-200';
    default:
      return 'border-emerald-700/40 bg-emerald-500/10 text-emerald-200';
  }
}

function cardClasses(item: SelectionAwareFieldReviewItem): string {
  const base = severityClasses(item.severity);
  if (item.is_selected_risky) {
    return `${base} ring-2 ring-rose-400/40`;
  }
  if (item.is_selected_review_recommended) {
    return `${base} ring-2 ring-amber-400/35`;
  }
  return base;
}

function confidenceBadgeClass(level: string): string {
  switch (level) {
    case 'high':
      return 'border-emerald-700/40 bg-emerald-500/10 text-emerald-200';
    case 'medium':
      return 'border-amber-700/40 bg-amber-500/10 text-amber-200';
    case 'low':
      return 'border-rose-700/40 bg-rose-500/10 text-rose-200';
    default:
      return 'border-neutral-700 bg-neutral-900 text-neutral-200';
  }
}

function formatConfidenceLevel(level: string, copy: CopyShape): string {
  switch (level) {
    case 'high':
      return copy.qualityHigh;
    case 'medium':
      return copy.qualityMedium;
    case 'low':
      return copy.qualityLow;
    default:
      return level;
  }
}

function normalizeSignal(value: string): string {
  return value.replaceAll('_', ' ');
}

function formatReasonCode(
  code: SelectionAwareFieldReviewReasonCode,
  copy: CopyShape
): string {
  const mapping: Record<SelectionAwareFieldReviewReasonCode, string> = {
    low_confidence: copy.reasonLowConfidence,
    medium_confidence: copy.reasonMediumConfidence,
    high_confidence: copy.reasonHighConfidence,
    missing_value: copy.reasonMissingValue,
    sparse_content: copy.reasonSparseContent,
    ocr_source: copy.reasonOcrSource,
    manual_review_flow: copy.reasonManualReviewFlow,
    low_text_volume: copy.reasonLowTextVolume,
    medium_text_volume: copy.reasonMediumTextVolume,
    extraction_review_hint: copy.reasonExtractionReviewHint,
    selected_risky_change: copy.reasonSelectedRiskyChange,
    selected_review_recommended: copy.reasonSelectedReviewRecommended,
  };

  return mapping[code] ?? code;
}

function selectedCountToneClass(value: number): string {
  if (value > 0) {
    return 'border-rose-700/40 bg-rose-500/10 text-rose-200';
  }
  return 'border-neutral-800 bg-neutral-900/70 text-neutral-200';
}


function enterpriseNoteToneClass(
  intent: 'neutral' | 'positive' | 'caution'
): string {
  switch (intent) {
    case 'positive':
      return 'border-emerald-900/50 bg-emerald-950/20 text-emerald-200';
    case 'caution':
      return 'border-amber-900/50 bg-amber-950/20 text-amber-200';
    case 'neutral':
    default:
      return 'border-neutral-800 bg-neutral-900/70 text-neutral-200';
  }
}

function InfoTile({label, value}: {label: string; value: string}) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900/70 px-4 py-3">
      <p className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
        {label}
      </p>
      <p className="mt-2 text-sm text-neutral-100">{value}</p>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  className,
}: {
  label: string;
  value: number;
  className?: string;
}) {
  return (
    <div className={`rounded-3xl border px-5 py-4 ${className ?? ''}`}>
      <p className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
        {label}
      </p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
        {value}
      </p>
    </div>
  );
}

function ConfidencePill({
  confidence,
  copy,
}: {
  confidence: UserCvFieldConfidence;
  copy: CopyShape;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${confidenceBadgeClass(
        confidence.level
      )}`}
    >
      {copy.confidenceTitle}: {formatConfidenceLevel(confidence.level, copy)}
    </span>
  );
}

function ReviewReasonChips({
  item,
  copy,
}: {
  item: SelectionAwareFieldReviewItem;
  copy: CopyShape;
}) {
  if (item.presentation_reason_codes.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
        {copy.riskReasonsTitle}
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {item.presentation_reason_codes.map((reasonCode) => (
          <span
            key={reasonCode}
            className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-neutral-200"
          >
            {formatReasonCode(reasonCode, copy)}
          </span>
        ))}
      </div>
    </div>
  );
}

function SelectionCard({
  title,
  checked,
  disabled,
  badge,
  confidence,
  item,
  copy,
  onToggle,
  children,
}: {
  title: string;
  checked: boolean;
  disabled: boolean;
  badge: string;
  confidence: UserCvFieldConfidence;
  item: SelectionAwareFieldReviewItem | null;
  copy: CopyShape;
  onToggle: () => void;
  children: ReactNode;
}) {
  const severity = item?.severity ?? 'safe';

  return (
    <label
      className={`block rounded-3xl border p-5 transition ${
        disabled
          ? 'cursor-not-allowed border-neutral-800 bg-neutral-900/40 opacity-65'
          : checked
            ? `${cardClasses(
                item ?? {
                  field_name: confidence.field_name,
                  severity,
                  reason_codes: [],
                  confidence_level: confidence.level,
                  has_value: confidence.has_value,
                  item_count: confidence.item_count,
                  is_selected: checked,
                  is_selected_risky: false,
                  is_selected_review_recommended: false,
                  presentation_reason_codes: [],
                }
              )} cursor-pointer`
            : 'cursor-pointer border-neutral-800 bg-neutral-900/70 hover:border-neutral-600'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-base font-semibold text-white">{title}</h4>
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${severityClasses(
                severity
              )}`}
            >
              {badge}
            </span>
            <ConfidencePill confidence={confidence} copy={copy} />
          </div>
          <p className="mt-3 text-sm text-neutral-300">
            {copy.severityToneDescription[severity]}
          </p>
        </div>
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={onToggle}
          className="mt-1 h-4 w-4 rounded border-neutral-700 bg-neutral-950 text-white"
        />
      </div>

      <div className="mt-5">{children}</div>

      {item ? <ReviewReasonChips item={item} copy={copy} /> : null}

      {confidence.signals.length > 0 ? (
        <div className="mt-4">
          <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
            {copy.signalsTitle}
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {confidence.signals.map((signal) => (
              <span
                key={signal}
                className="rounded-full border border-neutral-800 bg-neutral-950/60 px-2.5 py-1 text-[11px] text-neutral-300"
              >
                {normalizeSignal(signal)}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </label>
  );
}

function CollectionSection({
  title,
  confidence,
  reviewItem,
  items,
  copy,
}: {
  title: string;
  confidence: UserCvFieldConfidence;
  reviewItem: SelectionAwareFieldReviewItem | null;
  items: Array<{
    key: string;
    checked: boolean;
    disabled: boolean;
    onToggle: () => void;
    primary: string;
    secondary: string | null;
    meta: string;
  }>;
  copy: CopyShape;
}) {
  return (
    <section className="rounded-3xl border border-neutral-800 bg-neutral-950/65 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-base font-semibold text-white">{title}</h4>
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${severityClasses(
                reviewItem?.severity ?? 'safe'
              )}`}
            >
              {formatSeverityLabel(reviewItem?.severity ?? 'safe', copy)}
            </span>
            <ConfidencePill confidence={confidence} copy={copy} />
          </div>
          <p className="mt-3 text-sm text-neutral-300">
            {copy.severityToneDescription[reviewItem?.severity ?? 'safe']}
          </p>
        </div>
      </div>

      {reviewItem ? <ReviewReasonChips item={reviewItem} copy={copy} /> : null}

      {confidence.signals.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {confidence.signals.map((signal) => (
            <span
              key={signal}
              className="rounded-full border border-neutral-800 bg-neutral-950/60 px-2.5 py-1 text-[11px] text-neutral-300"
            >
              {normalizeSignal(signal)}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-5 grid gap-3">
        {items.length === 0 ? (
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 px-4 py-4 text-sm text-neutral-500">
            {copy.collectionEmpty}
          </div>
        ) : (
          items.map((entry) => (
            <label
              key={entry.key}
              className={`flex items-start gap-3 rounded-2xl border px-4 py-4 transition ${
                entry.disabled
                  ? 'cursor-not-allowed border-neutral-800 bg-neutral-900/40 opacity-65'
                  : entry.checked
                    ? `${cardClasses(
                        reviewItem ?? {
                          field_name: confidence.field_name,
                          severity: 'safe',
                          reason_codes: [],
                          confidence_level: confidence.level,
                          has_value: confidence.has_value,
                          item_count: confidence.item_count,
                          is_selected: entry.checked,
                          is_selected_risky: false,
                          is_selected_review_recommended: false,
                          presentation_reason_codes: [],
                        }
                      )} cursor-pointer`
                    : 'cursor-pointer border-neutral-800 bg-neutral-900/60 hover:border-neutral-600'
              }`}
            >
              <input
                type="checkbox"
                checked={entry.checked}
                disabled={entry.disabled}
                onChange={entry.onToggle}
                className="mt-1 h-4 w-4 rounded border-neutral-700 bg-neutral-950 text-white"
              />
              <div>
                <p className="text-sm font-medium text-white">{entry.primary}</p>
                {entry.secondary ? (
                  <p className="text-sm text-neutral-300">{entry.secondary}</p>
                ) : null}
                {entry.meta ? (
                  <p className="mt-1 text-xs text-neutral-500">{entry.meta}</p>
                ) : null}
              </div>
            </label>
          ))
        )}
      </div>
    </section>
  );
}

export function CvReviewCard({
  className,
  onApplyCompleted,
}: CvReviewCardProps) {
  const params = useParams();
  const router = useRouter();
  const locale = resolveLocale(params?.locale);
  const copy = COPY[locale];

  const [plan, setPlan] = useState<UserCvProfileApplyPlan | null>(null);
  const [selection, setSelection] = useState<UserCvApplySelectedRequest | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [applyMessage, setApplyMessage] = useState<string | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [manualReviewAcknowledged, setManualReviewAcknowledged] =
    useState(false);
  const [isPending, startTransition] = useTransition();

  const loadPlan = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setLoadError(null);

    try {
      const response = await api.getLatestCvProfileApplyPlan();
      setPlan(response);
      setSelection(response ? buildDefaultSelection(response) : null);
      setManualReviewAcknowledged(false);
    } catch (reason) {
      setLoadError(getErrorMessage(reason, copy.failedToLoad));
      setPlan(null);
      setSelection(null);
      setManualReviewAcknowledged(false);
    } finally {
      setIsLoading(false);
    }
  }, [copy.failedToLoad]);

  useEffect(() => {
    void loadPlan();
  }, [loadPlan]);

  const selectedChangeCount = useMemo(
    () => (selection ? countSelectedOperations(selection) : 0),
    [selection]
  );

  const fieldReviewItems = useMemo(() => {
    if (!plan) {
      return [];
    }

    return buildSelectionAwareFieldReviewItems(plan, selection);
  }, [plan, selection]);

  const reviewSummary = useMemo(() => {
    if (!plan) {
      return null;
    }

    return buildSelectionAwareReviewSummary(plan, selection);
  }, [plan, selection]);

  const requiresOperatorAcknowledgement =
    !!plan?.extraction_metadata.needs_manual_review;

  const canApplySelection =
    !!plan?.has_actionable_changes &&
    !!selection &&
    selectedChangeCount > 0 &&
    (!requiresOperatorAcknowledgement || manualReviewAcknowledged) &&
    !isPending;

  const operatorPanelToneClass = requiresOperatorAcknowledgement
    ? 'border-amber-700/40 bg-amber-500/10 text-amber-100'
    : 'border-emerald-700/40 bg-emerald-500/10 text-emerald-100';

  const applyButtonLabel = requiresOperatorAcknowledgement
    ? copy.applySelectedReviewed
    : copy.applySelectedSafe;

  function clearTransientMessages(): void {
    setApplyError(null);
    setApplyMessage(null);
  }

  function resetToDefaultSelection(): void {
    if (!plan) {
      return;
    }

    clearTransientMessages();
    setManualReviewAcknowledged(false);
    setSelection(buildDefaultSelection(plan));
  }

  function toggleScalarField(fieldName: string): void {
    clearTransientMessages();
    setSelection((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        scalar_fields: toggleStringItem(current.scalar_fields, fieldName),
      };
    });
  }

  function toggleListField(fieldName: string): void {
    clearTransientMessages();
    setSelection((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        list_fields: toggleStringItem(current.list_fields, fieldName),
      };
    });
  }

  function toggleEducationEntry(index: number): void {
    clearTransientMessages();
    setSelection((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        education_entry_indexes: toggleNumberItem(
          current.education_entry_indexes,
          index
        ),
      };
    });
  }

  function toggleExperienceEntry(index: number): void {
    clearTransientMessages();
    setSelection((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        experience_entry_indexes: toggleNumberItem(
          current.experience_entry_indexes,
          index
        ),
      };
    });
  }

  function toggleLanguageEntry(index: number): void {
    clearTransientMessages();
    setSelection((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        language_entry_indexes: toggleNumberItem(
          current.language_entry_indexes,
          index
        ),
      };
    });
  }

  function isScalarSelected(fieldName: string): boolean {
    return selection?.scalar_fields.includes(fieldName) ?? false;
  }

  function isListSelected(fieldName: string): boolean {
    return selection?.list_fields.includes(fieldName) ?? false;
  }

  function isEducationSelected(index: number): boolean {
    return selection?.education_entry_indexes.includes(index) ?? false;
  }

  function isExperienceSelected(index: number): boolean {
    return selection?.experience_entry_indexes.includes(index) ?? false;
  }

  function isLanguageSelected(index: number): boolean {
    return selection?.language_entry_indexes.includes(index) ?? false;
  }

  async function handleRefresh(): Promise<void> {
    clearTransientMessages();
    await loadPlan();
  }

  async function handleApplySelected(): Promise<void> {
    if (!selection || !plan) {
      return;
    }

    if (countSelectedOperations(selection) === 0) {
      setApplyError(copy.nothingSelected);
      setApplyMessage(null);
      return;
    }

    if (requiresOperatorAcknowledgement && !manualReviewAcknowledged) {
      setApplyError(copy.operatorAcknowledgeHint);
      setApplyMessage(null);
      return;
    }

    setApplyError(null);
    setApplyMessage(null);

    startTransition(() => {
      void (async () => {
        try {
          const response = await api.applySelectedCvProfileOperations({
            ...selection,
            manual_review_acknowledged: manualReviewAcknowledged,
          });

          await onApplyCompleted?.();
          setApplyMessage(
            response.remaining_actionable_change_count === 0
              ? copy.applySuccess
              : copy.applyPartial
          );

          await loadPlan();
          router.refresh();
        } catch (reason) {
          setApplyError(getErrorMessage(reason, copy.failedToApply));
        }
      })();
    });
  }

  if (isLoading) {
    return (
      <section
        className={`rounded-[30px] border border-neutral-800 bg-neutral-950/70 p-6 ${className ?? ''}`}
      >
        <p className="text-sm text-neutral-300">{copy.loading}</p>
      </section>
    );
  }

  if (loadError) {
    return (
      <section
        className={`rounded-[30px] border border-rose-700/40 bg-rose-500/10 p-6 ${className ?? ''}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="text-sm text-rose-100">{loadError}</p>
          <button
            type="button"
            onClick={() => void handleRefresh()}
            className="rounded-2xl border border-white/15 px-4 py-2 text-sm text-white transition hover:border-white/35"
          >
            {copy.refresh}
          </button>
        </div>
      </section>
    );
  }

  if (!plan || !selection || !reviewSummary) {
    return (
      <section
        className={`rounded-[30px] border border-neutral-800 bg-neutral-950/70 p-6 ${className ?? ''}`}
      >
        <h3 className="text-xl font-semibold tracking-tight text-white">
          {copy.title}
        </h3>
        <p className="mt-2 text-sm text-neutral-300">{copy.empty}</p>
      </section>
    );
  }

  const scalarPlans = [plan.headline, plan.summary, plan.remote_preference];
  const listPlans = [plan.skills, plan.target_roles, plan.preferred_locations];
  const enterpriseMetadata = plan.enterprise_metadata ?? null;
  const enterpriseRecommendations =
    enterpriseMetadata?.ats.recommendations.slice(0, 3) ?? [];
  const enterpriseNote = buildEnterpriseSignalNote(enterpriseMetadata, locale);
  const enterpriseIntent = getEnterpriseSignalIntent(enterpriseMetadata);

  return (
    <section
      className={`rounded-[32px] border border-neutral-800 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.06),_transparent_42%),linear-gradient(180deg,_rgba(23,23,23,0.92),_rgba(10,10,10,0.92))] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.35)] ${className ?? ''}`}
    >
      <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-3xl">
          <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-neutral-400">
            {copy.reviewSummaryTitle}
          </div>
          <h3 className="mt-4 text-2xl font-semibold tracking-tight text-white">
            {copy.title}
          </h3>
          <p className="mt-3 text-sm leading-6 text-neutral-300">
            {copy.subtitle}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={resetToDefaultSelection}
            disabled={isPending}
            className="rounded-2xl border border-white/10 px-4 py-2 text-sm text-neutral-100 transition hover:border-white/25 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {copy.resetSelection}
          </button>
          <button
            type="button"
            onClick={() => void handleRefresh()}
            disabled={isPending}
            className="rounded-2xl border border-white/10 px-4 py-2 text-sm text-neutral-100 transition hover:border-white/25 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {copy.refresh}
          </button>
          <button
            type="button"
            onClick={() => void handleApplySelected()}
            disabled={!canApplySelection}
            className="rounded-2xl bg-white px-5 py-2 text-sm font-medium text-neutral-950 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isPending ? copy.applying : applyButtonLabel}
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <SummaryStat
          label={copy.reviewRequiredCount}
          value={reviewSummary.review_required_count}
          className="border-rose-700/40 bg-rose-500/10"
        />
        <SummaryStat
          label={copy.reviewRecommendedCount}
          value={reviewSummary.review_recommended_count}
          className="border-amber-700/40 bg-amber-500/10"
        />
        <SummaryStat
          label={copy.safeCount}
          value={reviewSummary.safe_field_count}
          className="border-emerald-700/40 bg-emerald-500/10"
        />
        <SummaryStat
          label={copy.selectedRiskCount}
          value={reviewSummary.selected_review_required_count}
          className={selectedCountToneClass(
            reviewSummary.selected_review_required_count
          )}
        />
        <SummaryStat
          label={copy.selectedReviewRecommendedCount}
          value={reviewSummary.selected_review_recommended_count}
          className="border-amber-700/20 bg-neutral-900/70"
        />
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <div className={`rounded-3xl border px-5 py-5 ${operatorPanelToneClass}`}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-2xl">
              <h4 className="text-lg font-semibold text-white">
                {requiresOperatorAcknowledgement
                  ? copy.manualFlowTitle
                  : copy.safeFlowTitle}
              </h4>
              <p className="mt-2 text-sm leading-6 text-current/85">
                {requiresOperatorAcknowledgement
                  ? copy.manualFlowHint
                  : copy.safeFlowHint}
              </p>
            </div>
            <div className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-current/85">
              {requiresOperatorAcknowledgement
                ? copy.reviewRequiredBadge
                : copy.safeBadge}
            </div>
          </div>

          <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 px-4 py-4 text-sm text-current/90">
            <div className="font-medium">
              {requiresOperatorAcknowledgement
                ? copy.operatorManualReviewBanner
                : copy.operatorSafeBanner}
            </div>
            <div className="mt-2 text-current/80">
              {copy.recommendedNextAction}:{' '}
              {formatRecommendedNextActionValue(
                plan.extraction_metadata.recommended_next_action,
                copy
              )}
            </div>
          </div>

          {requiresOperatorAcknowledgement ? (
            <label className="mt-4 flex items-start gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-4 text-sm text-current/90">
              <input
                type="checkbox"
                checked={manualReviewAcknowledged}
                onChange={(event) =>
                  setManualReviewAcknowledged(event.target.checked)
                }
                className="mt-1 h-4 w-4 rounded border-white/20 bg-transparent text-white"
              />
              <div>
                <div className="font-medium text-white">
                  {copy.operatorAcknowledgeLabel}
                </div>
                <div className="mt-1 text-current/80">
                  {copy.operatorAcknowledgeHint}
                </div>
              </div>
            </label>
          ) : null}
        </div>

        <div className="rounded-3xl border border-neutral-800 bg-neutral-900/70 px-5 py-5">
          <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
            {copy.focusFieldsTitle}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {reviewSummary.focus_field_names.length > 0 ? (
              reviewSummary.focus_field_names.map((fieldName) => (
                <span
                  key={fieldName}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-neutral-100"
                >
                  {fieldLabel(copy, fieldName)}
                </span>
              ))
            ) : (
              <span className="text-sm text-neutral-400">—</span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <InfoTile label={copy.sourceFile} value={plan.source_filename ?? '—'} />
        <InfoTile label={copy.generatedAt} value={formatDateTime(plan.generated_at, locale)} />
        <InfoTile label={copy.parserVersion} value={plan.parser_version ?? '—'} />
        <InfoTile label={copy.parseStatus} value={formatParseStatus(plan.source_parse_status, copy)} />
        <InfoTile label={copy.selectedChanges} value={String(selectedChangeCount)} />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <InfoTile
          label={copy.sourceFormat}
          value={formatExtractionFileFormat(plan.extraction_metadata.file_format)}
        />
        <InfoTile
          label={copy.extractionMethod}
          value={formatExtractionMethod(plan.extraction_metadata.extraction_method)}
        />
        <InfoTile
          label={copy.ocrUsage}
          value={formatBooleanValue(plan.extraction_metadata.uses_ocr, copy)}
        />
        <InfoTile
          label={copy.extractionNote}
          value={plan.extraction_metadata.parse_status_detail}
        />
        <InfoTile
          label={copy.extractionQuality}
          value={formatExtractionQualityValue(
            plan.extraction_metadata.extraction_quality,
            copy
          )}
        />
        <InfoTile
          label={copy.reviewHints}
          value={formatExtractionReviewHints(
            plan.extraction_metadata.review_hints,
            copy
          )}
        />
        <InfoTile
          label={copy.manualReviewStatus}
          value={formatManualReviewStatusValue(
            plan.extraction_metadata.needs_manual_review,
            copy
          )}
        />
        <InfoTile
          label={copy.defaultApplySafety}
          value={formatSafeForDefaultApplyValue(
            plan.extraction_metadata.is_safe_for_default_apply,
            copy
          )}
        />
        <InfoTile
          label={copy.fallbackReason}
          value={formatFallbackReasonValue(
            plan.extraction_metadata.fallback_reason,
            copy
          )}
        />
        <InfoTile
          label={copy.recommendedNextAction}
          value={formatRecommendedNextActionValue(
            plan.extraction_metadata.recommended_next_action,
            copy
          )}
        />
      </div>

      {plan.extraction_metadata.uses_ocr ? (
        <div className="mt-4 rounded-2xl border border-amber-700/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          {copy.ocrBanner}
        </div>
      ) : null}

      {enterpriseMetadata ? (
        <div className="mt-4 rounded-3xl border border-neutral-800 bg-neutral-900/60 px-5 py-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                {copy.enterpriseSignalsTitle}
              </div>
              <p className="mt-2 text-sm leading-6 text-neutral-300">
                {copy.enterpriseSignalsSubtitle}
              </p>
            </div>
            {enterpriseNote ? (
              <div
                className={`rounded-2xl border px-4 py-3 text-sm ${enterpriseNoteToneClass(enterpriseIntent)}`}
              >
                {enterpriseNote}
              </div>
            ) : null}
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <InfoTile
              label={copy.enterpriseAtsLabel}
              value={formatEnterpriseAtsValue(enterpriseMetadata.ats, locale)}
            />
            <InfoTile
              label={copy.enterpriseDuplicateLabel}
              value={formatEnterpriseRelationValue(
                enterpriseMetadata.fingerprint.relation,
                locale
              )}
            />
            <InfoTile
              label={copy.enterpriseCacheLabel}
              value={formatEnterpriseCacheStatusValue(
                enterpriseMetadata.cache.status,
                locale
              )}
            />
            <InfoTile
              label={copy.enterpriseRedactionLabel}
              value={formatEnterpriseRedactionValue(
                enterpriseMetadata.redaction,
                locale
              )}
            />
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-[1.25fr_1fr]">
            <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
              <div className="text-[11px] uppercase tracking-[0.2em] text-neutral-500">
                {copy.enterprisePiiLabel}
              </div>
              <div className="mt-2 text-sm text-neutral-200">
                {formatEnterprisePiiTypes(
                  enterpriseMetadata.redaction.pii_types,
                  locale
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
              <div className="text-[11px] uppercase tracking-[0.2em] text-neutral-500">
                {copy.enterpriseRecommendationsTitle}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {enterpriseRecommendations.length > 0 ? (
                  enterpriseRecommendations.map((item) => (
                    <span
                      key={item}
                      className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-neutral-100"
                    >
                      {item}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-neutral-400">—</span>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {applyMessage ? (
        <div className="mt-4 rounded-2xl border border-emerald-700/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
          {applyMessage}
        </div>
      ) : null}

      {applyError ? (
        <div className="mt-4 rounded-2xl border border-rose-700/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
          {applyError}
        </div>
      ) : null}

      {plan.has_actionable_changes && selectedChangeCount === 0 ? (
        <div className="mt-4 rounded-2xl border border-amber-700/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          {copy.noSelectionState}
        </div>
      ) : null}

      {!plan.has_actionable_changes ? (
        <div className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 px-4 py-4 text-sm text-neutral-300">
          {copy.noActionableChanges}
        </div>
      ) : null}

      <div className="mt-8 space-y-6">
        <div className="grid gap-4 xl:grid-cols-3">
          {scalarPlans.map((item) => (
            <SelectionCard
              key={item.field_name}
              title={fieldLabel(copy, item.field_name)}
              checked={isScalarSelected(item.field_name)}
              disabled={item.action === 'noop'}
              badge={formatSeverityLabel(
                findSelectionAwareFieldReviewItem(
                  fieldReviewItems,
                  item.field_name
                )?.severity ?? 'safe',
                copy
              )}
              confidence={
                plan.confidence[item.field_name as keyof typeof plan.confidence]
              }
              item={findSelectionAwareFieldReviewItem(
                fieldReviewItems,
                item.field_name
              )}
              copy={copy}
              onToggle={() => toggleScalarField(item.field_name)}
            >
              <div className="grid gap-3 text-sm text-neutral-200">
                <div>
                  <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                    {copy.currentValue}
                  </div>
                  <div className="mt-2 rounded-2xl border border-white/5 bg-black/15 px-4 py-3">
                    {item.current_value ?? '—'}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                    {copy.suggestedValue}
                  </div>
                  <div className="mt-2 rounded-2xl border border-white/5 bg-black/15 px-4 py-3">
                    {item.suggested_value ?? '—'}
                  </div>
                </div>
              </div>
            </SelectionCard>
          ))}
        </div>

        <div className="grid gap-4 xl:grid-cols-3">
          {listPlans.map((item) => (
            <SelectionCard
              key={item.field_name}
              title={fieldLabel(copy, item.field_name)}
              checked={isListSelected(item.field_name)}
              disabled={item.action === 'noop'}
              badge={formatSeverityLabel(
                findSelectionAwareFieldReviewItem(
                  fieldReviewItems,
                  item.field_name
                )?.severity ?? 'safe',
                copy
              )}
              confidence={
                plan.confidence[item.field_name as keyof typeof plan.confidence]
              }
              item={findSelectionAwareFieldReviewItem(
                fieldReviewItems,
                item.field_name
              )}
              copy={copy}
              onToggle={() => toggleListField(item.field_name)}
            >
              <div>
                <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                  {copy.itemsToAdd}
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {item.items_to_add.length > 0 ? (
                    item.items_to_add.map((value) => (
                      <span
                        key={value}
                        className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-100"
                      >
                        {value}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-neutral-500">—</span>
                  )}
                </div>
              </div>
            </SelectionCard>
          ))}
        </div>

        <CollectionSection
          title={copy.education}
          confidence={plan.confidence.education_entries}
          reviewItem={findSelectionAwareFieldReviewItem(
            fieldReviewItems,
            'education_entries'
          )}
          items={plan.education_entries.map((item, index) => ({
            key: `education-${index}`,
            checked: isEducationSelected(index),
            disabled: item.action === 'noop',
            onToggle: () => toggleEducationEntry(index),
            primary: item.draft_entry.school_name,
            secondary: item.draft_entry.degree_name,
            meta: [item.draft_entry.start_year, item.draft_entry.end_year]
              .filter((value) => value !== null)
              .join(' – '),
          }))}
          copy={copy}
        />

        <CollectionSection
          title={copy.experience}
          confidence={plan.confidence.experience_entries}
          reviewItem={findSelectionAwareFieldReviewItem(
            fieldReviewItems,
            'experience_entries'
          )}
          items={plan.experience_entries.map((item, index) => ({
            key: `experience-${index}`,
            checked: isExperienceSelected(index),
            disabled: item.action === 'noop',
            onToggle: () => toggleExperienceEntry(index),
            primary: item.draft_entry.title,
            secondary: item.draft_entry.company_name,
            meta: [item.draft_entry.start_year, item.draft_entry.end_year]
              .filter((value) => value !== null)
              .join(' – '),
          }))}
          copy={copy}
        />

        <CollectionSection
          title={copy.languages}
          confidence={plan.confidence.language_entries}
          reviewItem={findSelectionAwareFieldReviewItem(
            fieldReviewItems,
            'language_entries'
          )}
          items={plan.language_entries.map((item, index) => ({
            key: `language-${index}`,
            checked: isLanguageSelected(index),
            disabled: item.action === 'noop',
            onToggle: () => toggleLanguageEntry(index),
            primary: item.draft_entry.language_name,
            secondary: item.draft_entry.proficiency_level,
            meta: item.draft_entry.notes ?? '',
          }))}
          copy={copy}
        />
      </div>
    </section>
  );
}