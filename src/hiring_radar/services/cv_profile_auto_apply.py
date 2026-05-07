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
    CvProfileApplyPlan,
)
from hiring_radar.services.cv_profile_draft import CvProfileDraftSnapshot


@dataclass(slots=True, frozen=True)
class CvProfileAutoApplyResult:
    profile: SubscriberProfile
    education_entries: tuple[SubscriberEducationEntry, ...]
    experience_entries: tuple[SubscriberExperienceEntry, ...]
    language_entries: tuple[SubscriberLanguageEntry, ...]
    certification_entries: tuple[SubscriberCertificationEntry, ...]
    applied_scalar_fields: tuple[str, ...]
    applied_list_fields: tuple[str, ...]
    applied_contact_fields: tuple[str, ...]
    added_education_entry_count: int
    added_experience_entry_count: int
    added_language_entry_count: int
    added_certification_entry_count: int
    replaced_education_entries: bool = False
    replaced_experience_entries: bool = False
    replaced_language_entries: bool = False
    replaced_certification_entries: bool = False

    @property
    def total_applied_changes(self) -> int:
        return (
            len(self.applied_scalar_fields)
            + len(self.applied_list_fields)
            + len(self.applied_contact_fields)
            + self.added_education_entry_count
            + self.added_experience_entry_count
            + self.added_language_entry_count
            + self.added_certification_entry_count
        )


def auto_apply_cv_profile_draft(
    *,
    snapshot: CvProfileDraftSnapshot,
    apply_plan: CvProfileApplyPlan,
    profile: SubscriberProfile,
    education_entries: Sequence[SubscriberEducationEntry],
    experience_entries: Sequence[SubscriberExperienceEntry],
    language_entries: Sequence[SubscriberLanguageEntry],
    certification_entries: Sequence[SubscriberCertificationEntry] = (),
) -> CvProfileAutoApplyResult:
    """Apply all safe additive CV draft operations non-destructively.

    Fills missing scalar fields, appends unique list items, appends unique
    education/experience/language entries, and populates missing contact
    fields (phone) from the draft. Never overwrites existing non-empty data.
    """
    updated_profile = profile
    applied_scalar_fields: list[str] = []
    applied_list_fields: list[str] = []
    applied_contact_fields: list[str] = []

    for plan in (apply_plan.headline, apply_plan.summary, apply_plan.remote_preference):
        if plan.action == CV_APPLY_ACTION_FILL_MISSING and plan.default_selected:
            updated_profile = replace(
                updated_profile,
                **{plan.field_name: plan.suggested_value},
            )
            applied_scalar_fields.append(plan.field_name)

    for plan in (apply_plan.skills, apply_plan.target_roles, apply_plan.preferred_locations):
        if plan.action == CV_APPLY_ACTION_ADD_UNIQUE and plan.default_selected and plan.items_to_add:
            existing = getattr(updated_profile, plan.field_name)
            updated_profile = replace(
                updated_profile,
                **{plan.field_name: tuple(existing) + tuple(plan.items_to_add)},
            )
            applied_list_fields.append(plan.field_name)

    draft_phone = (snapshot.draft.phone or "").strip()
    if draft_phone and not (updated_profile.phone or "").strip():
        updated_profile = replace(updated_profile, phone=draft_phone)
        applied_contact_fields.append("phone")

    updated_education = list(education_entries)
    added_edu = 0
    for plan in apply_plan.education_entries:
        if plan.action != CV_APPLY_ACTION_ADD_UNIQUE or not plan.default_selected:
            continue
        updated_education.append(
            SubscriberEducationEntry(
                subscriber_id=profile.subscriber_id,
                school_name=plan.draft_entry.school_name,
                degree_name=plan.draft_entry.degree_name,
                field_of_study=plan.draft_entry.field_of_study,
                start_year=plan.draft_entry.start_year,
                end_year=plan.draft_entry.end_year,
            )
        )
        added_edu += 1

    updated_experience = list(experience_entries)
    added_exp = 0
    for plan in apply_plan.experience_entries:
        if plan.action != CV_APPLY_ACTION_ADD_UNIQUE or not plan.default_selected:
            continue
        updated_experience.append(
            SubscriberExperienceEntry(
                subscriber_id=profile.subscriber_id,
                title=plan.draft_entry.title,
                company_name=plan.draft_entry.company_name,
                start_year=plan.draft_entry.start_year,
                end_year=plan.draft_entry.end_year,
                summary=plan.draft_entry.summary,
            )
        )
        added_exp += 1

    updated_language = list(language_entries)
    added_lang = 0
    for plan in apply_plan.language_entries:
        if plan.action != CV_APPLY_ACTION_ADD_UNIQUE or not plan.default_selected:
            continue
        updated_language.append(
            SubscriberLanguageEntry(
                subscriber_id=profile.subscriber_id,
                language_name=plan.draft_entry.language_name,
                proficiency_level=plan.draft_entry.proficiency_level,
                notes=plan.draft_entry.notes,
            )
        )
        added_lang += 1

    updated_certification = list(certification_entries)
    added_cert = 0
    for plan in apply_plan.certification_entries:
        if plan.action != CV_APPLY_ACTION_ADD_UNIQUE or not plan.default_selected:
            continue
        updated_certification.append(
            SubscriberCertificationEntry(
                subscriber_id=profile.subscriber_id,
                certificate_name=plan.draft_entry.certificate_name,
                issuer_name=plan.draft_entry.issuer_name,
                issued_year=plan.draft_entry.issued_year,
            )
        )
        added_cert += 1

    return CvProfileAutoApplyResult(
        profile=updated_profile,
        education_entries=tuple(updated_education),
        experience_entries=tuple(updated_experience),
        language_entries=tuple(updated_language),
        certification_entries=tuple(updated_certification),
        applied_scalar_fields=tuple(applied_scalar_fields),
        applied_list_fields=tuple(applied_list_fields),
        applied_contact_fields=tuple(applied_contact_fields),
        added_education_entry_count=added_edu,
        added_experience_entry_count=added_exp,
        added_language_entry_count=added_lang,
        added_certification_entry_count=added_cert,
    )


def replace_profile_from_cv_draft(
    *,
    snapshot: CvProfileDraftSnapshot,
    profile: SubscriberProfile,
    education_entries: Sequence[SubscriberEducationEntry],
    experience_entries: Sequence[SubscriberExperienceEntry],
    language_entries: Sequence[SubscriberLanguageEntry],
    certification_entries: Sequence[SubscriberCertificationEntry] = (),
) -> CvProfileAutoApplyResult:
    """Treat the uploaded CV as the new source of truth for the profile.

    Unlike :func:`auto_apply_cv_profile_draft`, this helper overwrites
    scalar fields and fully replaces structured sections when the draft
    provides meaningful data. It is used by the CV upload flow so that a
    freshly uploaded CV actually becomes the active profile content
    instead of being blocked by stale values left from an earlier CV.

    Behavior:
      * Scalar fields (headline, summary, remote_preference, phone):
        overwritten when the draft supplies a non-empty value.
      * List fields (skills, target_roles, preferred_locations):
        replaced with the draft list when the draft has at least one
        item; otherwise preserved.
      * Structured sections (education, experience, languages):
        replaced wholesale when the draft has at least one entry of that
        kind; otherwise the existing entries are preserved unchanged.

    The helper never wipes existing values when the draft is empty for
    that field, so a failed OCR run does not destroy a populated profile.
    """
    draft = snapshot.draft
    updated_profile = profile
    applied_scalar_fields: list[str] = []
    applied_list_fields: list[str] = []
    applied_contact_fields: list[str] = []

    for field_name in ("headline", "summary", "remote_preference"):
        draft_value = _clean_optional(getattr(draft, field_name))
        if draft_value is None:
            continue
        current_value = _clean_optional(getattr(updated_profile, field_name))
        if current_value == draft_value:
            continue
        updated_profile = replace(updated_profile, **{field_name: draft_value})
        applied_scalar_fields.append(field_name)

    for field_name in ("skills", "target_roles", "preferred_locations"):
        draft_values = _normalize_unique(getattr(draft, field_name))
        if not draft_values:
            continue
        current_values = getattr(updated_profile, field_name)
        if tuple(current_values) == draft_values:
            continue
        updated_profile = replace(updated_profile, **{field_name: draft_values})
        applied_list_fields.append(field_name)

    draft_phone = _clean_optional(draft.phone)
    if draft_phone is not None and draft_phone != _clean_optional(updated_profile.phone):
        updated_profile = replace(updated_profile, phone=draft_phone)
        applied_contact_fields.append("phone")

    if draft.education_entries:
        updated_education = list(
            education_entries_from_draft(
                draft.education_entries, subscriber_id=profile.subscriber_id,
            )
        )
        replaced_education = True
        added_edu = len(updated_education)
    else:
        updated_education = list(education_entries)
        replaced_education = False
        added_edu = 0

    if draft.experience_entries:
        updated_experience = list(
            experience_entries_from_draft(
                draft.experience_entries, subscriber_id=profile.subscriber_id,
            )
        )
        replaced_experience = True
        added_exp = len(updated_experience)
    else:
        updated_experience = list(experience_entries)
        replaced_experience = False
        added_exp = 0

    if draft.language_entries:
        updated_language = list(
            language_entries_from_draft(
                draft.language_entries, subscriber_id=profile.subscriber_id,
            )
        )
        replaced_language = True
        added_lang = len(updated_language)
    else:
        updated_language = list(language_entries)
        replaced_language = False
        added_lang = 0

    if draft.certification_entries:
        updated_certification = list(
            certification_entries_from_draft(
                draft.certification_entries, subscriber_id=profile.subscriber_id,
            )
        )
        replaced_certification = True
        added_cert = len(updated_certification)
    else:
        updated_certification = list(certification_entries)
        replaced_certification = False
        added_cert = 0

    return CvProfileAutoApplyResult(
        profile=updated_profile,
        education_entries=tuple(updated_education),
        experience_entries=tuple(updated_experience),
        language_entries=tuple(updated_language),
        certification_entries=tuple(updated_certification),
        applied_scalar_fields=tuple(applied_scalar_fields),
        applied_list_fields=tuple(applied_list_fields),
        applied_contact_fields=tuple(applied_contact_fields),
        added_education_entry_count=added_edu,
        added_experience_entry_count=added_exp,
        added_language_entry_count=added_lang,
        added_certification_entry_count=added_cert,
        replaced_education_entries=replaced_education,
        replaced_experience_entries=replaced_experience,
        replaced_language_entries=replaced_language,
        replaced_certification_entries=replaced_certification,
    )


def pivot_profile_to_cv_draft(
    *,
    snapshot: CvProfileDraftSnapshot,
    profile: SubscriberProfile,
    education_entries: Sequence[SubscriberEducationEntry],
    experience_entries: Sequence[SubscriberExperienceEntry],
    language_entries: Sequence[SubscriberLanguageEntry],
    certification_entries: Sequence[SubscriberCertificationEntry] = (),
) -> CvProfileAutoApplyResult:
    """Fully pivot the profile's CV-derived fields to the new CV draft.

    Intended for the successful-extraction path of the CV upload flow
    where the freshly uploaded CV must become the authoritative source
    of the profile's CV-derived content. Unlike
    :func:`replace_profile_from_cv_draft`, this helper *also clears*
    fields when the new CV's draft has no value for them, so stale
    scalars / list items / structured entries left over from an earlier
    CV upload cannot keep shadowing the newly uploaded CV.

    Behavior:
      * Scalars (headline, summary, remote_preference): overwritten with
        the draft value when present; set to ``None`` when the draft is
        empty for that field.
      * List fields (skills, target_roles, preferred_locations):
        replaced with the draft list even if empty.
      * Structured sections (education, experience, languages):
        replaced wholesale with the draft entries even when the draft
        has no entries of that kind.
      * Contact fields (phone): overwritten only when the draft has a
        non-empty value — we do not wipe a phone number just because
        the CV had no phone on it.

    This helper is only safe to call when extraction produced a real,
    non-empty draft. Callers on failure paths must use
    :func:`replace_profile_from_cv_draft` instead so a failed OCR run
    cannot destroy a populated profile.
    """
    draft = snapshot.draft
    updated_profile = profile
    applied_scalar_fields: list[str] = []
    applied_list_fields: list[str] = []
    applied_contact_fields: list[str] = []

    for field_name in ("headline", "summary", "remote_preference"):
        draft_value = _clean_optional(getattr(draft, field_name))
        current_value = _clean_optional(getattr(updated_profile, field_name))
        if draft_value == current_value:
            continue
        updated_profile = replace(updated_profile, **{field_name: draft_value})
        applied_scalar_fields.append(field_name)

    for field_name in ("skills", "target_roles", "preferred_locations"):
        draft_values = _normalize_unique(getattr(draft, field_name))
        current_values = tuple(getattr(updated_profile, field_name))
        if current_values == draft_values:
            continue
        updated_profile = replace(updated_profile, **{field_name: draft_values})
        applied_list_fields.append(field_name)

    draft_phone = _clean_optional(draft.phone)
    if draft_phone is not None and draft_phone != _clean_optional(updated_profile.phone):
        updated_profile = replace(updated_profile, phone=draft_phone)
        applied_contact_fields.append("phone")

    updated_education = list(
        education_entries_from_draft(
            draft.education_entries, subscriber_id=profile.subscriber_id,
        )
    )
    if draft.experience_entries:
        updated_experience = list(
            experience_entries_from_draft(
                draft.experience_entries, subscriber_id=profile.subscriber_id,
            )
        )
        replaced_experience = True
    else:
        updated_experience = list(experience_entries)
        replaced_experience = False

    if draft.language_entries:
        updated_language = list(
            language_entries_from_draft(
                draft.language_entries, subscriber_id=profile.subscriber_id,
            )
        )
        replaced_language = True
    else:
        updated_language = list(language_entries)
        replaced_language = False

    if draft.certification_entries:
        updated_certification = list(
            certification_entries_from_draft(
                draft.certification_entries, subscriber_id=profile.subscriber_id,
            )
        )
        replaced_certification = True
    else:
        updated_certification = list(certification_entries)
        replaced_certification = False

    return CvProfileAutoApplyResult(
        profile=updated_profile,
        education_entries=tuple(updated_education),
        experience_entries=tuple(updated_experience),
        language_entries=tuple(updated_language),
        certification_entries=tuple(updated_certification),
        applied_scalar_fields=tuple(applied_scalar_fields),
        applied_list_fields=tuple(applied_list_fields),
        applied_contact_fields=tuple(applied_contact_fields),
        added_education_entry_count=len(updated_education),
        added_experience_entry_count=len(updated_experience),
        added_language_entry_count=len(updated_language),
        added_certification_entry_count=len(updated_certification),
        replaced_education_entries=True,
        replaced_experience_entries=replaced_experience,
        replaced_language_entries=replaced_language,
        replaced_certification_entries=replaced_certification,
    )


def education_entries_from_draft(
    draft_entries,
    *,
    subscriber_id: int,
) -> tuple[SubscriberEducationEntry, ...]:
    return tuple(
        SubscriberEducationEntry(
            subscriber_id=subscriber_id,
            school_name=entry.school_name,
            degree_name=entry.degree_name,
            field_of_study=entry.field_of_study,
            start_year=entry.start_year,
            end_year=entry.end_year,
        )
        for entry in draft_entries
    )


def experience_entries_from_draft(
    draft_entries,
    *,
    subscriber_id: int,
) -> tuple[SubscriberExperienceEntry, ...]:
    return tuple(
        SubscriberExperienceEntry(
            subscriber_id=subscriber_id,
            title=entry.title,
            company_name=entry.company_name,
            start_year=entry.start_year,
            end_year=entry.end_year,
            summary=entry.summary,
        )
        for entry in draft_entries
    )


def language_entries_from_draft(
    draft_entries,
    *,
    subscriber_id: int,
) -> tuple[SubscriberLanguageEntry, ...]:
    return tuple(
        SubscriberLanguageEntry(
            subscriber_id=subscriber_id,
            language_name=entry.language_name,
            proficiency_level=entry.proficiency_level,
            notes=entry.notes,
        )
        for entry in draft_entries
    )


def certification_entries_from_draft(
    draft_entries,
    *,
    subscriber_id: int,
) -> tuple[SubscriberCertificationEntry, ...]:
    return tuple(
        SubscriberCertificationEntry(
            subscriber_id=subscriber_id,
            certificate_name=entry.certificate_name,
            issuer_name=entry.issuer_name,
            issued_year=entry.issued_year,
        )
        for entry in draft_entries
    )


def _clean_optional(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def _normalize_unique(values) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values or ():
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return tuple(out)
