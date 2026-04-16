from __future__ import annotations

import re
from dataclasses import dataclass

from hiring_radar.services.cv_profile_draft import (
    CvDraftEducationEntry,
    CvDraftExperienceEntry,
    CvDraftLanguageEntry,
    CvProfileDraftSnapshot,
)

CV_CONFIDENCE_LOW = "low"
CV_CONFIDENCE_MEDIUM = "medium"
CV_CONFIDENCE_HIGH = "high"

_EMAIL_RE = re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_ROLE_HINT_KEYWORDS = frozenset(
    {
        "engineer",
        "developer",
        "manager",
        "specialist",
        "architect",
        "analyst",
        "lead",
        "director",
        "consultant",
        "scientist",
        "designer",
    }
)

_REMOTE_PREFERENCE_VALUES = frozenset(
    {
        "remote",
        "hybrid",
        "onsite",
        "uzaktan",
        "hibrit",
        "ofiste",
    }
)


@dataclass(slots=True, frozen=True)
class CvFieldConfidence:
    """Represents confidence metadata for a single parsed profile field.

    Attributes:
        field_name: Canonical field identifier.
        level: Confidence level.
        has_value: Whether the field contains a usable value.
        item_count: Number of parsed items contributing to the field.
        signals: Human-readable heuristic signals supporting the score.
    """

    field_name: str
    level: str
    has_value: bool
    item_count: int
    signals: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class CvProfileConfidenceReport:
    """Represents a field-level confidence report for a parsed CV snapshot."""

    headline: CvFieldConfidence
    summary: CvFieldConfidence
    skills: CvFieldConfidence
    target_roles: CvFieldConfidence
    preferred_locations: CvFieldConfidence
    remote_preference: CvFieldConfidence
    education_entries: CvFieldConfidence
    experience_entries: CvFieldConfidence
    language_entries: CvFieldConfidence

    def high_confidence_field_count(self) -> int:
        """Count fields marked as high confidence.

        Returns:
            Number of fields whose level is ``high``.
        """
        return sum(
            1
            for field in self._iter_fields()
            if field.level == CV_CONFIDENCE_HIGH
        )

    def low_confidence_field_names(self) -> tuple[str, ...]:
        """List low-confidence field names.

        Returns:
            Field names currently marked as ``low``.
        """
        return tuple(
            field.field_name
            for field in self._iter_fields()
            if field.level == CV_CONFIDENCE_LOW
        )

    def _iter_fields(self) -> tuple[CvFieldConfidence, ...]:
        """Iterate through all field confidence objects."""
        return (
            self.headline,
            self.summary,
            self.skills,
            self.target_roles,
            self.preferred_locations,
            self.remote_preference,
            self.education_entries,
            self.experience_entries,
            self.language_entries,
        )


def build_cv_profile_confidence_report(
    snapshot: CvProfileDraftSnapshot,
) -> CvProfileConfidenceReport:
    """Build a heuristic confidence report for a parsed CV snapshot.

    Args:
        snapshot: Parsed CV profile draft snapshot.

    Returns:
        A deterministic field-level confidence report.
    """
    draft = snapshot.draft

    return CvProfileConfidenceReport(
        headline=_build_headline_confidence(draft.headline),
        summary=_build_summary_confidence(draft.summary),
        skills=_build_token_list_confidence("skills", draft.skills),
        target_roles=_build_target_roles_confidence(draft.target_roles),
        preferred_locations=_build_location_confidence(draft.preferred_locations),
        remote_preference=_build_remote_preference_confidence(
            draft.remote_preference
        ),
        education_entries=_build_education_confidence(draft.education_entries),
        experience_entries=_build_experience_confidence(draft.experience_entries),
        language_entries=_build_language_confidence(draft.language_entries),
    )


def _build_headline_confidence(value: str | None) -> CvFieldConfidence:
    """Build confidence metadata for headline."""
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return CvFieldConfidence(
            field_name="headline",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    signals: list[str] = ["non_empty"]
    if len(cleaned.split()) >= 2:
        signals.append("multi_token")
    if _contains_role_hint(cleaned):
        signals.append("role_hint")
    if not _EMAIL_RE.search(cleaned) and not _YEAR_RE.search(cleaned):
        signals.append("non_contact_like")

    level = CV_CONFIDENCE_MEDIUM
    if {
        "multi_token",
        "role_hint",
        "non_contact_like",
    }.issubset(signals):
        level = CV_CONFIDENCE_HIGH

    return CvFieldConfidence(
        field_name="headline",
        level=level,
        has_value=True,
        item_count=1,
        signals=tuple(signals),
    )

def _build_summary_confidence(value: str | None) -> CvFieldConfidence:
    """Build confidence metadata for summary."""
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return CvFieldConfidence(
            field_name="summary",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    signals: list[str] = ["non_empty"]
    if len(cleaned) >= 30:
        signals.append("sentence_like")
    if len(cleaned) >= 80:
        signals.append("rich_length")

    if len(cleaned) >= 80:
        level = CV_CONFIDENCE_HIGH
    elif len(cleaned) >= 30:
        level = CV_CONFIDENCE_MEDIUM
    else:
        level = CV_CONFIDENCE_LOW

    return CvFieldConfidence(
        field_name="summary",
        level=level,
        has_value=True,
        item_count=1,
        signals=tuple(signals),
    )


def _build_token_list_confidence(
    field_name: str,
    values: tuple[str, ...],
) -> CvFieldConfidence:
    """Build confidence metadata for list-like token fields."""
    count = len(values)
    if count == 0:
        return CvFieldConfidence(
            field_name=field_name,
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    signals = ["non_empty_list", f"count:{count}"]
    if count >= 4:
        level = CV_CONFIDENCE_HIGH
        signals.append("rich_list")
    elif count >= 2:
        level = CV_CONFIDENCE_MEDIUM
        signals.append("multi_item")
    else:
        level = CV_CONFIDENCE_LOW
        signals.append("single_item")

    return CvFieldConfidence(
        field_name=field_name,
        level=level,
        has_value=True,
        item_count=count,
        signals=tuple(signals),
    )


def _build_target_roles_confidence(values: tuple[str, ...]) -> CvFieldConfidence:
    """Build confidence metadata for target roles."""
    count = len(values)
    if count == 0:
        return CvFieldConfidence(
            field_name="target_roles",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    signals = ["non_empty_list", f"count:{count}"]
    if any(_contains_role_hint(value) for value in values):
        signals.append("role_hint")

    level = CV_CONFIDENCE_HIGH if "role_hint" in signals else CV_CONFIDENCE_MEDIUM

    return CvFieldConfidence(
        field_name="target_roles",
        level=level,
        has_value=True,
        item_count=count,
        signals=tuple(signals),
    )


def _build_location_confidence(values: tuple[str, ...]) -> CvFieldConfidence:
    """Build confidence metadata for preferred locations."""
    count = len(values)
    if count == 0:
        return CvFieldConfidence(
            field_name="preferred_locations",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    signals = ["non_empty_list", f"count:{count}"]
    level = CV_CONFIDENCE_MEDIUM
    if count >= 2:
        level = CV_CONFIDENCE_HIGH
        signals.append("multi_location")

    return CvFieldConfidence(
        field_name="preferred_locations",
        level=level,
        has_value=True,
        item_count=count,
        signals=tuple(signals),
    )


def _build_remote_preference_confidence(value: str | None) -> CvFieldConfidence:
    """Build confidence metadata for remote preference."""
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return CvFieldConfidence(
            field_name="remote_preference",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    normalized = cleaned.casefold()
    signals = ["non_empty"]
    if normalized in _REMOTE_PREFERENCE_VALUES:
        signals.append("known_preference_value")
        level = CV_CONFIDENCE_MEDIUM
    else:
        level = CV_CONFIDENCE_LOW

    return CvFieldConfidence(
        field_name="remote_preference",
        level=level,
        has_value=True,
        item_count=1,
        signals=tuple(signals),
    )


def _build_education_confidence(
    entries: tuple[CvDraftEducationEntry, ...],
) -> CvFieldConfidence:
    """Build confidence metadata for education entries."""
    if not entries:
        return CvFieldConfidence(
            field_name="education_entries",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    strong_entries = sum(
        1
        for entry in entries
        if entry.school_name
        and entry.degree_name
        and (entry.start_year is not None or entry.end_year is not None)
    )
    partial_entries = sum(1 for entry in entries if entry.school_name)

    signals = [f"count:{len(entries)}", f"strong:{strong_entries}"]
    if strong_entries >= 1:
        level = CV_CONFIDENCE_HIGH
        signals.append("structured_timeline")
    elif partial_entries >= 1:
        level = CV_CONFIDENCE_MEDIUM
        signals.append("partial_structure")
    else:
        level = CV_CONFIDENCE_LOW

    return CvFieldConfidence(
        field_name="education_entries",
        level=level,
        has_value=True,
        item_count=len(entries),
        signals=tuple(signals),
    )


def _build_experience_confidence(
    entries: tuple[CvDraftExperienceEntry, ...],
) -> CvFieldConfidence:
    """Build confidence metadata for experience entries."""
    if not entries:
        return CvFieldConfidence(
            field_name="experience_entries",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    strong_entries = sum(
        1
        for entry in entries
        if entry.title
        and entry.company_name
        and entry.start_year is not None
    )
    partial_entries = sum(1 for entry in entries if entry.title)

    signals = [f"count:{len(entries)}", f"strong:{strong_entries}"]
    if strong_entries >= 1:
        level = CV_CONFIDENCE_HIGH
        signals.append("role_company_timeline")
    elif partial_entries >= 1:
        level = CV_CONFIDENCE_MEDIUM
        signals.append("title_only")
    else:
        level = CV_CONFIDENCE_LOW

    return CvFieldConfidence(
        field_name="experience_entries",
        level=level,
        has_value=True,
        item_count=len(entries),
        signals=tuple(signals),
    )


def _build_language_confidence(
    entries: tuple[CvDraftLanguageEntry, ...],
) -> CvFieldConfidence:
    """Build confidence metadata for language entries."""
    if not entries:
        return CvFieldConfidence(
            field_name="language_entries",
            level=CV_CONFIDENCE_LOW,
            has_value=False,
            item_count=0,
            signals=("missing",),
        )

    proficiency_count = sum(
        1 for entry in entries if _clean_optional_string(entry.proficiency_level)
    )

    signals = [f"count:{len(entries)}", f"with_proficiency:{proficiency_count}"]
    if proficiency_count >= 2:
        level = CV_CONFIDENCE_HIGH
        signals.append("multi_language_structured")
    elif proficiency_count >= 1:
        level = CV_CONFIDENCE_MEDIUM
        signals.append("single_language_structured")
    else:
        level = CV_CONFIDENCE_LOW

    return CvFieldConfidence(
        field_name="language_entries",
        level=level,
        has_value=True,
        item_count=len(entries),
        signals=tuple(signals),
    )


def _clean_optional_string(value: str | None) -> str | None:
    """Normalize an optional string."""
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _contains_role_hint(value: str) -> bool:
    """Check whether a value contains a role-like keyword."""
    lowered = value.casefold()
    return any(keyword in lowered for keyword in _ROLE_HINT_KEYWORDS)