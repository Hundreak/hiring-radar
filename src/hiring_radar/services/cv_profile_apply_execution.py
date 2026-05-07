from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from hiring_radar.models import (
    SubscriberCertificationEntry,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
    SubscriberProfile,
)
from hiring_radar.services.cv_profile_apply_plan import (
    CV_APPLY_ACTION_ADD_UNIQUE,
    CV_APPLY_ACTION_FILL_MISSING,
    CV_APPLY_ACTION_REVIEW_REQUIRED,
    CvEducationEntryApplyPlan,
    CvCertificationEntryApplyPlan,
    CvExperienceEntryApplyPlan,
    CvLanguageEntryApplyPlan,
    CvProfileApplyPlan,
)

CV_PARSE_RUN_APPLY_STATUS_PENDING = "pending"
CV_PARSE_RUN_APPLY_STATUS_PARTIALLY_APPLIED = "partially_applied"
CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED = "fully_applied"


@dataclass(slots=True, frozen=True)
class CvSelectedApplyOperations:
    """Represents the user-selected CV apply operations.

    Attributes:
        scalar_fields: Selected scalar fields to apply.
        list_fields: Selected list fields to apply.
        education_entry_indexes: Selected education entry plan indexes.
        experience_entry_indexes: Selected experience entry plan indexes.
        language_entry_indexes: Selected language entry plan indexes.
        certification_entry_indexes: Selected certification entry plan indexes.
    """

    scalar_fields: tuple[str, ...] = ()
    list_fields: tuple[str, ...] = ()
    education_entry_indexes: tuple[int, ...] = ()
    experience_entry_indexes: tuple[int, ...] = ()
    language_entry_indexes: tuple[int, ...] = ()
    certification_entry_indexes: tuple[int, ...] = ()

    def change_count(self) -> int:
        """Return the total number of selected operations.

        Returns:
            Total selected operation count.
        """
        return (
            len(self.scalar_fields)
            + len(self.list_fields)
            + len(self.education_entry_indexes)
            + len(self.experience_entry_indexes)
            + len(self.language_entry_indexes)
            + len(self.certification_entry_indexes)
        )


@dataclass(slots=True, frozen=True)
class CvProfileApplyExecutionResult:
    """Represents the resulting persisted state after selected apply operations.

    Attributes:
        profile: Updated subscriber profile state.
        education_entries: Updated education entries.
        experience_entries: Updated experience entries.
        language_entries: Updated language entries.
        applied_scalar_fields: Applied scalar field names.
        applied_list_fields: Applied list field names.
        applied_education_entry_indexes: Applied education entry indexes.
        applied_experience_entry_indexes: Applied experience entry indexes.
        applied_language_entry_indexes: Applied language entry indexes.
        applied_certification_entry_indexes: Applied certification entry indexes.
        applied_change_count: Total applied operation count.
    """

    profile: SubscriberProfile
    education_entries: tuple[SubscriberEducationEntry, ...]
    experience_entries: tuple[SubscriberExperienceEntry, ...]
    language_entries: tuple[SubscriberLanguageEntry, ...]
    certification_entries: tuple[SubscriberCertificationEntry, ...]
    applied_scalar_fields: tuple[str, ...]
    applied_list_fields: tuple[str, ...]
    applied_education_entry_indexes: tuple[int, ...]
    applied_experience_entry_indexes: tuple[int, ...]
    applied_language_entry_indexes: tuple[int, ...]
    applied_certification_entry_indexes: tuple[int, ...]
    applied_change_count: int


def build_cv_selected_apply_operations(
    *,
    scalar_fields: Sequence[str],
    list_fields: Sequence[str],
    education_entry_indexes: Sequence[int],
    experience_entry_indexes: Sequence[int],
    language_entry_indexes: Sequence[int],
    certification_entry_indexes: Sequence[int] = (),
) -> CvSelectedApplyOperations:
    """Build and validate a normalized selection payload.

    Args:
        scalar_fields: Selected scalar fields.
        list_fields: Selected list fields.
        education_entry_indexes: Selected education plan indexes.
        experience_entry_indexes: Selected experience plan indexes.
        language_entry_indexes: Selected language plan indexes.
        certification_entry_indexes: Selected certification plan indexes.

    Returns:
        A normalized and deduplicated selection object.

    Raises:
        ValueError: If the selection payload is empty or malformed.
    """
    selection = CvSelectedApplyOperations(
        scalar_fields=_normalize_unique_field_names(
            scalar_fields,
            logical_name="scalar_fields",
        ),
        list_fields=_normalize_unique_field_names(
            list_fields,
            logical_name="list_fields",
        ),
        education_entry_indexes=_normalize_unique_indexes(
            education_entry_indexes,
            logical_name="education_entry_indexes",
        ),
        experience_entry_indexes=_normalize_unique_indexes(
            experience_entry_indexes,
            logical_name="experience_entry_indexes",
        ),
        language_entry_indexes=_normalize_unique_indexes(
            language_entry_indexes,
            logical_name="language_entry_indexes",
        ),
        certification_entry_indexes=_normalize_unique_indexes(
            certification_entry_indexes,
            logical_name="certification_entry_indexes",
        ),
    )

    if selection.change_count() == 0:
        raise ValueError("At least one CV apply operation must be selected.")

    return selection


def apply_selected_cv_profile_operations(
    *,
    apply_plan: CvProfileApplyPlan,
    selection: CvSelectedApplyOperations,
    profile: SubscriberProfile,
    education_entries: Sequence[SubscriberEducationEntry],
    experience_entries: Sequence[SubscriberExperienceEntry],
    language_entries: Sequence[SubscriberLanguageEntry],
    certification_entries: Sequence[SubscriberCertificationEntry] = (),
) -> CvProfileApplyExecutionResult:
    """Apply selected operations against the current subscriber profile state.

    This function is intentionally deterministic and non-magical. Only operations
    explicitly selected by the user and validated against the current apply plan
    are executed.

    Args:
        apply_plan: Current deterministic apply plan.
        selection: User-selected operations.
        profile: Current persisted subscriber profile.
        education_entries: Current persisted education entries.
        experience_entries: Current persisted experience entries.
        language_entries: Current persisted language entries.
        certification_entries: Current persisted generic certification entries.

    Returns:
        The updated in-memory profile state and the list-oriented entry sets.

    Raises:
        ValueError: If a selected operation is invalid or no longer applicable.
    """
    updated_profile = profile
    updated_education_entries = list(education_entries)
    updated_experience_entries = list(experience_entries)
    updated_language_entries = list(language_entries)
    updated_certification_entries = list(certification_entries)

    applied_scalar_fields = _apply_selected_scalar_fields(
        apply_plan=apply_plan,
        selection=selection,
        profile=updated_profile,
    )
    updated_profile = applied_scalar_fields.updated_profile

    applied_list_fields = _apply_selected_list_fields(
        apply_plan=apply_plan,
        selection=selection,
        profile=updated_profile,
    )
    updated_profile = applied_list_fields.updated_profile

    applied_education_entry_indexes = _apply_selected_education_entries(
        entry_plans=apply_plan.education_entries,
        selected_indexes=selection.education_entry_indexes,
        subscriber_id=profile.subscriber_id,
        existing_entries=updated_education_entries,
    )
    applied_experience_entry_indexes = _apply_selected_experience_entries(
        entry_plans=apply_plan.experience_entries,
        selected_indexes=selection.experience_entry_indexes,
        subscriber_id=profile.subscriber_id,
        existing_entries=updated_experience_entries,
    )
    applied_language_entry_indexes = _apply_selected_language_entries(
        entry_plans=apply_plan.language_entries,
        selected_indexes=selection.language_entry_indexes,
        subscriber_id=profile.subscriber_id,
        existing_entries=updated_language_entries,
    )
    applied_certification_entry_indexes = _apply_selected_certification_entries(
        entry_plans=apply_plan.certification_entries,
        selected_indexes=selection.certification_entry_indexes,
        subscriber_id=profile.subscriber_id,
        existing_entries=updated_certification_entries,
    )

    return CvProfileApplyExecutionResult(
        profile=updated_profile,
        education_entries=tuple(updated_education_entries),
        experience_entries=tuple(updated_experience_entries),
        language_entries=tuple(updated_language_entries),
        certification_entries=tuple(updated_certification_entries),
        applied_scalar_fields=applied_scalar_fields.applied_field_names,
        applied_list_fields=applied_list_fields.applied_field_names,
        applied_education_entry_indexes=applied_education_entry_indexes,
        applied_experience_entry_indexes=applied_experience_entry_indexes,
        applied_language_entry_indexes=applied_language_entry_indexes,
        applied_certification_entry_indexes=applied_certification_entry_indexes,
        applied_change_count=selection.change_count(),
    )


@dataclass(slots=True, frozen=True)
class _AppliedProfileMutation:
    """Internal container for profile field mutations."""

    updated_profile: SubscriberProfile
    applied_field_names: tuple[str, ...]


def _apply_selected_scalar_fields(
    *,
    apply_plan: CvProfileApplyPlan,
    selection: CvSelectedApplyOperations,
    profile: SubscriberProfile,
) -> _AppliedProfileMutation:
    """Apply selected scalar field operations.

    Args:
        apply_plan: Current apply plan.
        selection: User-selected operations.
        profile: Current subscriber profile.

    Returns:
        Mutated profile and applied field names.

    Raises:
        ValueError: If a selected scalar field is not applicable.
    """
    scalar_plans = {
        apply_plan.headline.field_name: apply_plan.headline,
        apply_plan.summary.field_name: apply_plan.summary,
        apply_plan.remote_preference.field_name: apply_plan.remote_preference,
    }
    updated_profile = profile
    applied_field_names: list[str] = []

    for field_name in selection.scalar_fields:
        plan = scalar_plans.get(field_name)
        if plan is None:
            raise ValueError(f"Unsupported scalar apply field: {field_name}.")

        if plan.action not in {
            CV_APPLY_ACTION_FILL_MISSING,
            CV_APPLY_ACTION_REVIEW_REQUIRED,
        }:
            raise ValueError(f"Selected scalar field is not applicable: {field_name}.")

        updated_profile = replace(
            updated_profile,
            **{field_name: plan.suggested_value},
        )
        applied_field_names.append(field_name)

    return _AppliedProfileMutation(
        updated_profile=updated_profile,
        applied_field_names=tuple(applied_field_names),
    )


def _apply_selected_list_fields(
    *,
    apply_plan: CvProfileApplyPlan,
    selection: CvSelectedApplyOperations,
    profile: SubscriberProfile,
) -> _AppliedProfileMutation:
    """Apply selected list field operations.

    Args:
        apply_plan: Current apply plan.
        selection: User-selected operations.
        profile: Current subscriber profile.

    Returns:
        Mutated profile and applied field names.

    Raises:
        ValueError: If a selected list field is not applicable.
    """
    list_plans = {
        apply_plan.skills.field_name: apply_plan.skills,
        apply_plan.target_roles.field_name: apply_plan.target_roles,
        apply_plan.preferred_locations.field_name: apply_plan.preferred_locations,
    }
    updated_profile = profile
    applied_field_names: list[str] = []

    for field_name in selection.list_fields:
        plan = list_plans.get(field_name)
        if plan is None:
            raise ValueError(f"Unsupported list apply field: {field_name}.")

        if plan.action != CV_APPLY_ACTION_ADD_UNIQUE:
            raise ValueError(f"Selected list field is not applicable: {field_name}.")

        existing_items = getattr(updated_profile, field_name)
        updated_profile = replace(
            updated_profile,
            **{field_name: tuple(existing_items) + tuple(plan.items_to_add)},
        )
        applied_field_names.append(field_name)

    return _AppliedProfileMutation(
        updated_profile=updated_profile,
        applied_field_names=tuple(applied_field_names),
    )


def _apply_selected_education_entries(
    *,
    entry_plans: Sequence[CvEducationEntryApplyPlan],
    selected_indexes: Sequence[int],
    subscriber_id: int,
    existing_entries: list[SubscriberEducationEntry],
) -> tuple[int, ...]:
    """Apply selected education entry operations.

    Args:
        entry_plans: Education entry apply plans.
        selected_indexes: Selected education plan indexes.
        subscriber_id: Subscriber identifier.
        existing_entries: Mutable education entry list.

    Returns:
        Applied education entry indexes.

    Raises:
        ValueError: If a selected entry is invalid or not applicable.
    """
    applied_indexes: list[int] = []

    for index in selected_indexes:
        plan = _get_selected_entry_plan(
            entry_plans,
            index=index,
            logical_name="education",
        )
        existing_entries.append(
            SubscriberEducationEntry(
                subscriber_id=subscriber_id,
                school_name=plan.draft_entry.school_name,
                degree_name=plan.draft_entry.degree_name,
                field_of_study=plan.draft_entry.field_of_study,
                start_year=plan.draft_entry.start_year,
                end_year=plan.draft_entry.end_year,
            )
        )
        applied_indexes.append(index)

    return tuple(applied_indexes)


def _apply_selected_experience_entries(
    *,
    entry_plans: Sequence[CvExperienceEntryApplyPlan],
    selected_indexes: Sequence[int],
    subscriber_id: int,
    existing_entries: list[SubscriberExperienceEntry],
) -> tuple[int, ...]:
    """Apply selected experience entry operations.

    Args:
        entry_plans: Experience entry apply plans.
        selected_indexes: Selected experience plan indexes.
        subscriber_id: Subscriber identifier.
        existing_entries: Mutable experience entry list.

    Returns:
        Applied experience entry indexes.

    Raises:
        ValueError: If a selected entry is invalid or not applicable.
    """
    applied_indexes: list[int] = []

    for index in selected_indexes:
        plan = _get_selected_entry_plan(
            entry_plans,
            index=index,
            logical_name="experience",
        )
        existing_entries.append(
            SubscriberExperienceEntry(
                subscriber_id=subscriber_id,
                title=plan.draft_entry.title,
                company_name=plan.draft_entry.company_name,
                start_year=plan.draft_entry.start_year,
                end_year=plan.draft_entry.end_year,
                summary=plan.draft_entry.summary,
            )
        )
        applied_indexes.append(index)

    return tuple(applied_indexes)


def _apply_selected_language_entries(
    *,
    entry_plans: Sequence[CvLanguageEntryApplyPlan],
    selected_indexes: Sequence[int],
    subscriber_id: int,
    existing_entries: list[SubscriberLanguageEntry],
) -> tuple[int, ...]:
    """Apply selected language entry operations.

    Args:
        entry_plans: Language entry apply plans.
        selected_indexes: Selected language plan indexes.
        subscriber_id: Subscriber identifier.
        existing_entries: Mutable language entry list.

    Returns:
        Applied language entry indexes.

    Raises:
        ValueError: If a selected entry is invalid or not applicable.
    """
    applied_indexes: list[int] = []

    for index in selected_indexes:
        plan = _get_selected_entry_plan(
            entry_plans,
            index=index,
            logical_name="language",
        )
        existing_entries.append(
            SubscriberLanguageEntry(
                subscriber_id=subscriber_id,
                language_name=plan.draft_entry.language_name,
                proficiency_level=plan.draft_entry.proficiency_level,
                notes=plan.draft_entry.notes,
            )
        )
        applied_indexes.append(index)

    return tuple(applied_indexes)


def _apply_selected_certification_entries(
    *,
    entry_plans: Sequence[CvCertificationEntryApplyPlan],
    selected_indexes: Sequence[int],
    subscriber_id: int,
    existing_entries: list[SubscriberCertificationEntry],
) -> tuple[int, ...]:
    """Apply selected certification entry operations."""
    applied_indexes: list[int] = []

    for index in selected_indexes:
        plan = _get_selected_entry_plan(
            entry_plans,
            index=index,
            logical_name="certification",
        )
        existing_entries.append(
            SubscriberCertificationEntry(
                subscriber_id=subscriber_id,
                certificate_name=plan.draft_entry.certificate_name,
                issuer_name=plan.draft_entry.issuer_name,
                issued_year=plan.draft_entry.issued_year,
            )
        )
        applied_indexes.append(index)

    return tuple(applied_indexes)


def _get_selected_entry_plan(
    entry_plans: Sequence[
        CvEducationEntryApplyPlan
        | CvExperienceEntryApplyPlan
        | CvLanguageEntryApplyPlan
        | CvCertificationEntryApplyPlan
    ],
    *,
    index: int,
    logical_name: str,
):
    """Fetch and validate a selected nested entry plan.

    Args:
        entry_plans: Available entry plans.
        index: Requested plan index.
        logical_name: Human-readable entry type.

    Returns:
        The validated selected plan.

    Raises:
        ValueError: If the index is invalid or the entry is not applicable.
    """
    if index < 0 or index >= len(entry_plans):
        raise ValueError(
            f"Selected {logical_name} entry index is out of range: {index}."
        )

    plan = entry_plans[index]
    if plan.action != CV_APPLY_ACTION_ADD_UNIQUE:
        raise ValueError(
            f"Selected {logical_name} entry is not applicable: {index}."
        )

    return plan


def _normalize_unique_field_names(
    values: Sequence[str],
    *,
    logical_name: str,
) -> tuple[str, ...]:
    """Normalize and deduplicate selected field names.

    Args:
        values: Raw selected field names.
        logical_name: Logical field group name.

    Returns:
        A normalized tuple preserving stable order.

    Raises:
        ValueError: If a field name is invalid.
    """
    normalized: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{logical_name} must only contain strings.")

        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{logical_name} must not contain empty field names.")

        key = cleaned.casefold()
        if key in seen:
            continue

        seen.add(key)
        normalized.append(cleaned)

    return tuple(normalized)


def _normalize_unique_indexes(
    values: Sequence[int],
    *,
    logical_name: str,
) -> tuple[int, ...]:
    """Normalize and deduplicate selected nested entry indexes.

    Args:
        values: Raw selected indexes.
        logical_name: Logical field group name.

    Returns:
        A normalized tuple preserving stable order.

    Raises:
        ValueError: If an index is invalid.
    """
    normalized: list[int] = []
    seen: set[int] = set()

    for value in values:
        if not isinstance(value, int):
            raise ValueError(f"{logical_name} must only contain integers.")
        if value < 0:
            raise ValueError(f"{logical_name} must only contain non-negative integers.")
        if value in seen:
            continue

        seen.add(value)
        normalized.append(value)

    return tuple(normalized)


def derive_parse_run_apply_status(
    *,
    remaining_actionable_change_count: int,
) -> str:
    """Derive the resulting parse-run consumption state.

    Args:
        remaining_actionable_change_count: Remaining actionable plan item count.

    Returns:
        ``fully_applied`` when no actionable items remain, otherwise
        ``partially_applied``.
    """
    if remaining_actionable_change_count == 0:
        return CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED

    return CV_PARSE_RUN_APPLY_STATUS_PARTIALLY_APPLIED


def selected_apply_operations_to_dict(
    selection: CvSelectedApplyOperations,
) -> dict[str, object]:
    """Serialize selected apply operations to a JSON-ready dictionary.

    Args:
        selection: Normalized selection payload.

    Returns:
        JSON-ready selection payload.
    """
    payload = {
        "scalar_fields": list(selection.scalar_fields),
        "list_fields": list(selection.list_fields),
        "education_entry_indexes": list(selection.education_entry_indexes),
        "experience_entry_indexes": list(selection.experience_entry_indexes),
        "language_entry_indexes": list(selection.language_entry_indexes),
    }
    if selection.certification_entry_indexes:
        payload["certification_entry_indexes"] = list(
            selection.certification_entry_indexes
        )
    return payload


def applied_execution_result_to_dict(
    result: CvProfileApplyExecutionResult,
) -> dict[str, object]:
    """Serialize the applied execution summary to a JSON-ready dictionary.

    Args:
        result: Execution result.

    Returns:
        JSON-ready applied-operation summary.
    """
    return {
        "applied_scalar_fields": list(result.applied_scalar_fields),
        "applied_list_fields": list(result.applied_list_fields),
        "applied_education_entry_indexes": list(
            result.applied_education_entry_indexes
        ),
        "applied_experience_entry_indexes": list(
            result.applied_experience_entry_indexes
        ),
        "applied_language_entry_indexes": list(
            result.applied_language_entry_indexes
        ),
        "applied_certification_entry_indexes": list(
            result.applied_certification_entry_indexes
        ),
        "applied_change_count": result.applied_change_count,
    }