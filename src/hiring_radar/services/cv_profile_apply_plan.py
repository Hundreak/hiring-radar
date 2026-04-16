from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from hiring_radar.models import (
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
    SubscriberProfile,
)
from hiring_radar.services.cv_profile_draft import (
    CvDraftEducationEntry,
    CvDraftExperienceEntry,
    CvDraftLanguageEntry,
    CvProfileDraftSnapshot,
)

CV_APPLY_ACTION_NOOP = "noop"
CV_APPLY_ACTION_FILL_MISSING = "fill_missing"
CV_APPLY_ACTION_REVIEW_REQUIRED = "review_required"
CV_APPLY_ACTION_ADD_UNIQUE = "add_unique"


@dataclass(slots=True, frozen=True)
class CvScalarFieldApplyPlan:
    """Represents a proposed apply decision for a scalar profile field.

    Attributes:
        field_name: Canonical profile field name.
        current_value: Current persisted value.
        suggested_value: Value suggested by the CV parser.
        action: Planned apply action.
        default_selected: Whether the action is safe to apply by default.
    """

    field_name: str
    current_value: str | None
    suggested_value: str | None
    action: str
    default_selected: bool


@dataclass(slots=True, frozen=True)
class CvListFieldApplyPlan:
    """Represents a proposed apply decision for a token list field.

    Attributes:
        field_name: Canonical profile field name.
        current_items: Current persisted items.
        suggested_items: Parsed items from the CV draft.
        items_to_add: Safe unique items that can be appended.
        action: Planned apply action.
        default_selected: Whether the action is safe to apply by default.
    """

    field_name: str
    current_items: tuple[str, ...]
    suggested_items: tuple[str, ...]
    items_to_add: tuple[str, ...]
    action: str
    default_selected: bool


@dataclass(slots=True, frozen=True)
class CvEducationEntryApplyPlan:
    """Represents a proposed apply decision for an education entry."""

    draft_entry: CvDraftEducationEntry
    matched_existing_id: int | None
    action: str
    default_selected: bool


@dataclass(slots=True, frozen=True)
class CvExperienceEntryApplyPlan:
    """Represents a proposed apply decision for an experience entry."""

    draft_entry: CvDraftExperienceEntry
    matched_existing_id: int | None
    action: str
    default_selected: bool


@dataclass(slots=True, frozen=True)
class CvLanguageEntryApplyPlan:
    """Represents a proposed apply decision for a language entry."""

    draft_entry: CvDraftLanguageEntry
    matched_existing_id: int | None
    action: str
    default_selected: bool


@dataclass(slots=True, frozen=True)
class CvProfileApplyPlan:
    """Represents a safe, non-destructive apply plan for a parsed CV draft.

    Attributes:
        source_parse_status: Source parse status from the snapshot.
        headline: Scalar plan for headline.
        summary: Scalar plan for summary.
        remote_preference: Scalar plan for remote preference.
        skills: List plan for skills.
        target_roles: List plan for target roles.
        preferred_locations: List plan for preferred locations.
        education_entries: Entry plans for education suggestions.
        experience_entries: Entry plans for experience suggestions.
        language_entries: Entry plans for language suggestions.
    """

    source_parse_status: str | None
    headline: CvScalarFieldApplyPlan
    summary: CvScalarFieldApplyPlan
    remote_preference: CvScalarFieldApplyPlan
    skills: CvListFieldApplyPlan
    target_roles: CvListFieldApplyPlan
    preferred_locations: CvListFieldApplyPlan
    education_entries: tuple[CvEducationEntryApplyPlan, ...]
    experience_entries: tuple[CvExperienceEntryApplyPlan, ...]
    language_entries: tuple[CvLanguageEntryApplyPlan, ...]

    def has_actionable_changes(self) -> bool:
        """Return whether the plan contains at least one actionable change.

        Returns:
            True if at least one plan item is selectable or needs review.
        """
        scalar_plans = (self.headline, self.summary, self.remote_preference)
        list_plans = (self.skills, self.target_roles, self.preferred_locations)

        if any(plan.action != CV_APPLY_ACTION_NOOP for plan in scalar_plans):
            return True
        if any(plan.action != CV_APPLY_ACTION_NOOP for plan in list_plans):
            return True
        if any(plan.action != CV_APPLY_ACTION_NOOP for plan in self.education_entries):
            return True
        if any(plan.action != CV_APPLY_ACTION_NOOP for plan in self.experience_entries):
            return True
        if any(plan.action != CV_APPLY_ACTION_NOOP for plan in self.language_entries):
            return True

        return False


    def actionable_change_count(self) -> int:
        """Count all currently actionable plan items.

        Returns:
            Number of plan items whose action is not ``noop``.
        """
        total = 0

        scalar_plans = (self.headline, self.summary, self.remote_preference)
        list_plans = (self.skills, self.target_roles, self.preferred_locations)

        total += sum(1 for plan in scalar_plans if plan.action != CV_APPLY_ACTION_NOOP)
        total += sum(1 for plan in list_plans if plan.action != CV_APPLY_ACTION_NOOP)
        total += sum(
            1 for plan in self.education_entries if plan.action != CV_APPLY_ACTION_NOOP
        )
        total += sum(
            1 for plan in self.experience_entries if plan.action != CV_APPLY_ACTION_NOOP
        )
        total += sum(
            1 for plan in self.language_entries if plan.action != CV_APPLY_ACTION_NOOP
        )

        return total
    
    def default_selected_change_count(self) -> int:
        """Count safe default-selected changes in the plan.

        Returns:
            Number of changes that are safe to auto-select in the UI.
        """
        total = 0

        scalar_plans = (self.headline, self.summary, self.remote_preference)
        list_plans = (self.skills, self.target_roles, self.preferred_locations)

        total += sum(1 for plan in scalar_plans if plan.default_selected)
        total += sum(1 for plan in list_plans if plan.default_selected)
        total += sum(1 for plan in self.education_entries if plan.default_selected)
        total += sum(1 for plan in self.experience_entries if plan.default_selected)
        total += sum(1 for plan in self.language_entries if plan.default_selected)

        return total


def build_cv_profile_apply_plan(
    *,
    snapshot: CvProfileDraftSnapshot,
    profile: SubscriberProfile,
    education_entries: Sequence[SubscriberEducationEntry],
    experience_entries: Sequence[SubscriberExperienceEntry],
    language_entries: Sequence[SubscriberLanguageEntry],
) -> CvProfileApplyPlan:
    """Build a non-destructive apply plan from a parsed CV snapshot.

    Args:
        snapshot: Parsed CV draft snapshot.
        profile: Current persisted subscriber profile.
        education_entries: Current persisted education entries.
        experience_entries: Current persisted experience entries.
        language_entries: Current persisted language entries.

    Returns:
        A deterministic apply plan that prefers safe, additive changes.
    """
    draft = snapshot.draft

    return CvProfileApplyPlan(
        source_parse_status=snapshot.source_parse_status,
        headline=_build_scalar_field_plan(
            field_name="headline",
            current_value=profile.headline,
            suggested_value=draft.headline,
        ),
        summary=_build_scalar_field_plan(
            field_name="summary",
            current_value=profile.summary,
            suggested_value=draft.summary,
        ),
        remote_preference=_build_scalar_field_plan(
            field_name="remote_preference",
            current_value=profile.remote_preference,
            suggested_value=draft.remote_preference,
        ),
        skills=_build_list_field_plan(
            field_name="skills",
            current_items=profile.skills,
            suggested_items=draft.skills,
        ),
        target_roles=_build_list_field_plan(
            field_name="target_roles",
            current_items=profile.target_roles,
            suggested_items=draft.target_roles,
        ),
        preferred_locations=_build_list_field_plan(
            field_name="preferred_locations",
            current_items=profile.preferred_locations,
            suggested_items=draft.preferred_locations,
        ),
        education_entries=_build_education_entry_plans(
            draft.education_entries,
            education_entries,
        ),
        experience_entries=_build_experience_entry_plans(
            draft.experience_entries,
            experience_entries,
        ),
        language_entries=_build_language_entry_plans(
            draft.language_entries,
            language_entries,
        ),
    )


def _build_scalar_field_plan(
    *,
    field_name: str,
    current_value: str | None,
    suggested_value: str | None,
) -> CvScalarFieldApplyPlan:
    """Build an apply plan for a scalar string field.

    Args:
        field_name: Canonical profile field name.
        current_value: Current persisted value.
        suggested_value: Value suggested by the parser.

    Returns:
        A scalar field apply plan.
    """
    cleaned_current = _clean_optional_string(current_value)
    cleaned_suggested = _clean_optional_string(suggested_value)

    if cleaned_suggested is None:
        return CvScalarFieldApplyPlan(
            field_name=field_name,
            current_value=cleaned_current,
            suggested_value=None,
            action=CV_APPLY_ACTION_NOOP,
            default_selected=False,
        )

    if cleaned_current is None:
        return CvScalarFieldApplyPlan(
            field_name=field_name,
            current_value=None,
            suggested_value=cleaned_suggested,
            action=CV_APPLY_ACTION_FILL_MISSING,
            default_selected=True,
        )

    if _string_key(cleaned_current) == _string_key(cleaned_suggested):
        return CvScalarFieldApplyPlan(
            field_name=field_name,
            current_value=cleaned_current,
            suggested_value=cleaned_suggested,
            action=CV_APPLY_ACTION_NOOP,
            default_selected=False,
        )

    return CvScalarFieldApplyPlan(
        field_name=field_name,
        current_value=cleaned_current,
        suggested_value=cleaned_suggested,
        action=CV_APPLY_ACTION_REVIEW_REQUIRED,
        default_selected=False,
    )


def _build_list_field_plan(
    *,
    field_name: str,
    current_items: tuple[str, ...],
    suggested_items: tuple[str, ...],
) -> CvListFieldApplyPlan:
    """Build an apply plan for a token list field.

    Args:
        field_name: Canonical profile field name.
        current_items: Current persisted list items.
        suggested_items: Parsed list items from the draft.

    Returns:
        A list field apply plan that only proposes unique additions.
    """
    normalized_current = _normalize_token_sequence(current_items)
    normalized_suggested = _normalize_token_sequence(suggested_items)
    current_keys = {_string_key(item) for item in normalized_current}

    items_to_add = tuple(
        item for item in normalized_suggested if _string_key(item) not in current_keys
    )

    if not items_to_add:
        return CvListFieldApplyPlan(
            field_name=field_name,
            current_items=normalized_current,
            suggested_items=normalized_suggested,
            items_to_add=(),
            action=CV_APPLY_ACTION_NOOP,
            default_selected=False,
        )

    return CvListFieldApplyPlan(
        field_name=field_name,
        current_items=normalized_current,
        suggested_items=normalized_suggested,
        items_to_add=items_to_add,
        action=CV_APPLY_ACTION_ADD_UNIQUE,
        default_selected=True,
    )


def _build_education_entry_plans(
    draft_entries: tuple[CvDraftEducationEntry, ...],
    existing_entries: Sequence[SubscriberEducationEntry],
) -> tuple[CvEducationEntryApplyPlan, ...]:
    """Build apply plans for education entries.

    Args:
        draft_entries: Parsed education draft entries.
        existing_entries: Persisted education entries.

    Returns:
        Entry plans that mark only new entries as addable.
    """
    existing_by_key = {
        _education_entry_key(entry): entry for entry in existing_entries
    }
    plans: list[CvEducationEntryApplyPlan] = []

    for draft_entry in draft_entries:
        matching_entry = existing_by_key.get(_education_entry_key(draft_entry))
        if matching_entry is None:
            plans.append(
                CvEducationEntryApplyPlan(
                    draft_entry=draft_entry,
                    matched_existing_id=None,
                    action=CV_APPLY_ACTION_ADD_UNIQUE,
                    default_selected=True,
                )
            )
            continue

        plans.append(
            CvEducationEntryApplyPlan(
                draft_entry=draft_entry,
                matched_existing_id=matching_entry.id,
                action=CV_APPLY_ACTION_NOOP,
                default_selected=False,
            )
        )

    return tuple(plans)


def _build_experience_entry_plans(
    draft_entries: tuple[CvDraftExperienceEntry, ...],
    existing_entries: Sequence[SubscriberExperienceEntry],
) -> tuple[CvExperienceEntryApplyPlan, ...]:
    """Build apply plans for experience entries.

    Args:
        draft_entries: Parsed experience draft entries.
        existing_entries: Persisted experience entries.

    Returns:
        Entry plans that mark only new entries as addable.
    """
    existing_by_key = {
        _experience_entry_key(entry): entry for entry in existing_entries
    }
    plans: list[CvExperienceEntryApplyPlan] = []

    for draft_entry in draft_entries:
        matching_entry = existing_by_key.get(_experience_entry_key(draft_entry))
        if matching_entry is None:
            plans.append(
                CvExperienceEntryApplyPlan(
                    draft_entry=draft_entry,
                    matched_existing_id=None,
                    action=CV_APPLY_ACTION_ADD_UNIQUE,
                    default_selected=True,
                )
            )
            continue

        plans.append(
            CvExperienceEntryApplyPlan(
                draft_entry=draft_entry,
                matched_existing_id=matching_entry.id,
                action=CV_APPLY_ACTION_NOOP,
                default_selected=False,
            )
        )

    return tuple(plans)


def _build_language_entry_plans(
    draft_entries: tuple[CvDraftLanguageEntry, ...],
    existing_entries: Sequence[SubscriberLanguageEntry],
) -> tuple[CvLanguageEntryApplyPlan, ...]:
    """Build apply plans for language entries.

    Args:
        draft_entries: Parsed language draft entries.
        existing_entries: Persisted language entries.

    Returns:
        Entry plans that mark only missing languages as addable.
    """
    existing_by_key = {
        _language_entry_key(entry): entry for entry in existing_entries
    }
    plans: list[CvLanguageEntryApplyPlan] = []

    for draft_entry in draft_entries:
        matching_entry = existing_by_key.get(_language_entry_key(draft_entry))
        if matching_entry is None:
            plans.append(
                CvLanguageEntryApplyPlan(
                    draft_entry=draft_entry,
                    matched_existing_id=None,
                    action=CV_APPLY_ACTION_ADD_UNIQUE,
                    default_selected=True,
                )
            )
            continue

        plans.append(
            CvLanguageEntryApplyPlan(
                draft_entry=draft_entry,
                matched_existing_id=matching_entry.id,
                action=CV_APPLY_ACTION_NOOP,
                default_selected=False,
            )
        )

    return tuple(plans)


def _clean_optional_string(value: str | None) -> str | None:
    """Normalize an optional string.

    Args:
        value: Input string.

    Returns:
        Stripped value or None when empty.
    """
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _normalize_token_sequence(values: Sequence[str]) -> tuple[str, ...]:
    """Normalize and deduplicate a string sequence while preserving order.

    Args:
        values: Input token sequence.

    Returns:
        A normalized tuple with stable ordering.
    """
    normalized: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = _clean_optional_string(value)
        if cleaned is None:
            continue

        key = _string_key(cleaned)
        if key in seen:
            continue

        seen.add(key)
        normalized.append(cleaned)

    return tuple(normalized)


def _string_key(value: str) -> str:
    """Build a canonical key for case-insensitive comparisons.

    Args:
        value: Input value.

    Returns:
        Canonical normalized comparison key.
    """
    return value.strip().casefold()


def _education_entry_key(
    entry: CvDraftEducationEntry | SubscriberEducationEntry,
) -> tuple[str, str, str, int | None, int | None]:
    """Build a stable comparison key for education entries.

    Args:
        entry: Draft or persisted education entry.

    Returns:
        A canonical tuple key.
    """
    return (
        _string_key(entry.school_name),
        _string_key(entry.degree_name or ""),
        _string_key(entry.field_of_study or ""),
        entry.start_year,
        entry.end_year,
    )


def _experience_entry_key(
    entry: CvDraftExperienceEntry | SubscriberExperienceEntry,
) -> tuple[str, str, int | None, int | None]:
    """Build a stable comparison key for experience entries.

    Args:
        entry: Draft or persisted experience entry.

    Returns:
        A canonical tuple key.
    """
    return (
        _string_key(entry.title),
        _string_key(entry.company_name or ""),
        entry.start_year,
        entry.end_year,
    )


def _language_entry_key(
    entry: CvDraftLanguageEntry | SubscriberLanguageEntry,
) -> str:
    """Build a stable comparison key for language entries.

    Args:
        entry: Draft or persisted language entry.

    Returns:
        A canonical comparison key.
    """
    return _string_key(entry.language_name)