import type {
  UserCvApplySelectedRequest,
  UserCvFieldReviewItem,
  UserCvFieldReviewReasonCode,
  UserCvFieldReviewSeverity,
  UserCvProfileApplyPlan,
} from '@/types/user';

export type SelectionAwareFieldReviewReasonCode =
  | UserCvFieldReviewReasonCode
  | 'selected_risky_change'
  | 'selected_review_recommended';

export interface SelectionAwareFieldReviewItem extends UserCvFieldReviewItem {
  is_selected: boolean;
  is_selected_risky: boolean;
  is_selected_review_recommended: boolean;
  presentation_reason_codes: SelectionAwareFieldReviewReasonCode[];
}

export interface SelectionAwareReviewSummary {
  total_field_count: number;
  safe_field_count: number;
  review_recommended_count: number;
  review_required_count: number;
  highest_severity: UserCvFieldReviewSeverity;
  focus_field_names: string[];
  selected_review_recommended_count: number;
  selected_review_required_count: number;
}

const FIELD_SORT_ORDER: Record<string, number> = {
  headline: 0,
  summary: 1,
  skills: 2,
  target_roles: 3,
  preferred_locations: 4,
  remote_preference: 5,
  education_entries: 6,
  experience_entries: 7,
  language_entries: 8,
};

const SEVERITY_SORT_ORDER: Record<UserCvFieldReviewSeverity, number> = {
  review_required: 0,
  review_recommended: 1,
  safe: 2,
};

export function buildSelectionAwareFieldReviewItems(
  plan: UserCvProfileApplyPlan,
  selection: UserCvApplySelectedRequest | null
): SelectionAwareFieldReviewItem[] {
  return [...plan.field_review]
    .map((item) => {
      const isSelected = isFieldSelected(selection, item.field_name);
      const isSelectedRisky =
        isSelected && item.severity === 'review_required';
      const isSelectedReviewRecommended =
        isSelected && item.severity === 'review_recommended';

      const presentationReasonCodes = [...item.reason_codes];
      if (isSelectedRisky) {
        presentationReasonCodes.push('selected_risky_change');
      } else if (isSelectedReviewRecommended) {
        presentationReasonCodes.push('selected_review_recommended');
      }

      return {
        ...item,
        is_selected: isSelected,
        is_selected_risky: isSelectedRisky,
        is_selected_review_recommended: isSelectedReviewRecommended,
        presentation_reason_codes: dedupeReasonCodes(presentationReasonCodes),
      };
    })
    .sort(sortSelectionAwareFieldReviewItems);
}

export function buildSelectionAwareReviewSummary(
  plan: UserCvProfileApplyPlan,
  selection: UserCvApplySelectedRequest | null
): SelectionAwareReviewSummary {
  const items = buildSelectionAwareFieldReviewItems(plan, selection);
  const {review_summary: summary} = plan;

  return {
    total_field_count: summary.total_field_count,
    safe_field_count: summary.safe_field_count,
    review_recommended_count: summary.review_recommended_count,
    review_required_count: summary.review_required_count,
    highest_severity: summary.highest_severity,
    focus_field_names: [...summary.focus_field_names],
    selected_review_recommended_count: items.filter(
      (item) => item.is_selected_review_recommended
    ).length,
    selected_review_required_count: items.filter(
      (item) => item.is_selected_risky
    ).length,
  };
}

export function findSelectionAwareFieldReviewItem(
  items: SelectionAwareFieldReviewItem[],
  fieldName: string
): SelectionAwareFieldReviewItem | null {
  return items.find((item) => item.field_name === fieldName) ?? null;
}

function isFieldSelected(
  selection: UserCvApplySelectedRequest | null,
  fieldName: string
): boolean {
  if (!selection) {
    return false;
  }

  if (selection.scalar_fields.includes(fieldName)) {
    return true;
  }

  if (selection.list_fields.includes(fieldName)) {
    return true;
  }

  if (fieldName === 'education_entries') {
    return selection.education_entry_indexes.length > 0;
  }

  if (fieldName === 'experience_entries') {
    return selection.experience_entry_indexes.length > 0;
  }

  if (fieldName === 'language_entries') {
    return selection.language_entry_indexes.length > 0;
  }

  return false;
}

function dedupeReasonCodes(
  values: SelectionAwareFieldReviewReasonCode[]
): SelectionAwareFieldReviewReasonCode[] {
  return [...new Set(values)];
}

function sortSelectionAwareFieldReviewItems(
  left: SelectionAwareFieldReviewItem,
  right: SelectionAwareFieldReviewItem
): number {
  if (left.is_selected_risky !== right.is_selected_risky) {
    return left.is_selected_risky ? -1 : 1;
  }

  if (
    left.is_selected_review_recommended !==
    right.is_selected_review_recommended
  ) {
    return left.is_selected_review_recommended ? -1 : 1;
  }

  const severityDelta =
    SEVERITY_SORT_ORDER[left.severity] - SEVERITY_SORT_ORDER[right.severity];
  if (severityDelta !== 0) {
    return severityDelta;
  }

  return FIELD_SORT_ORDER[left.field_name] - FIELD_SORT_ORDER[right.field_name];
}