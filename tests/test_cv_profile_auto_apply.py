from __future__ import annotations

import pytest

from hiring_radar.models import (
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
    SubscriberProfile,
)
from hiring_radar.services.cv_profile_auto_apply import pivot_profile_to_cv_draft
from hiring_radar.services.cv_profile_draft import (
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)


def _make_profile(subscriber_id: int = 1) -> SubscriberProfile:
    return SubscriberProfile(
        subscriber_id=subscriber_id,
        headline="Engineer",
        skills=("Python",),
    )


def _make_experience(
    title: str, subscriber_id: int = 1
) -> SubscriberExperienceEntry:
    return SubscriberExperienceEntry(
        id=1,
        subscriber_id=subscriber_id,
        title=title,
    )


def _make_language(
    name: str, subscriber_id: int = 1
) -> SubscriberLanguageEntry:
    return SubscriberLanguageEntry(
        id=1,
        subscriber_id=subscriber_id,
        language_name=name,
    )


class TestPivotProfileToCvDraft:
    def test_pivot_saves_experience_entries_from_draft(self) -> None:
        """When draft has experience entries, they must replace existing ones."""
        draft = build_cv_profile_draft(
            headline="Senior Engineer",
            experience_entries=[
                build_cv_draft_experience_entry(
                    title="Senior Backend Engineer",
                    company_name="ACME",
                    start_year=2021,
                )
            ],
        )
        snapshot = build_cv_profile_draft_snapshot(draft=draft)

        result = pivot_profile_to_cv_draft(
            snapshot=snapshot,
            profile=_make_profile(),
            education_entries=[],
            experience_entries=[],
            language_entries=[],
        )

        assert result.replaced_experience_entries is True
        assert len(result.experience_entries) == 1
        assert result.experience_entries[0].title == "Senior Backend Engineer"

    def test_pivot_does_not_wipe_experiences_when_draft_has_none(self) -> None:
        """Pivot must preserve existing experience entries when the CV draft is empty.

        This is the regression guard: previously the pivot always replaced
        experience entries, which wiped user-entered or prior-CV data when
        the latest parse produced no experience entries.
        """
        existing_exp = _make_experience("Backend Engineer at Startup")
        draft = build_cv_profile_draft(
            headline="Engineer",
            skills=("Python", "Django"),
        )
        snapshot = build_cv_profile_draft_snapshot(draft=draft)

        result = pivot_profile_to_cv_draft(
            snapshot=snapshot,
            profile=_make_profile(),
            education_entries=[],
            experience_entries=[existing_exp],
            language_entries=[],
        )

        assert result.replaced_experience_entries is False, (
            "replaced_experience_entries must be False when draft has no entries "
            "(to prevent wiping existing experiences)"
        )
        assert len(result.experience_entries) == 1
        assert result.experience_entries[0].title == "Backend Engineer at Startup"

    def test_pivot_does_not_wipe_languages_when_draft_has_none(self) -> None:
        """Pivot must preserve existing language entries when CV draft has none."""
        existing_lang = _make_language("English")
        draft = build_cv_profile_draft(
            headline="Engineer",
            skills=("Python",),
        )
        snapshot = build_cv_profile_draft_snapshot(draft=draft)

        result = pivot_profile_to_cv_draft(
            snapshot=snapshot,
            profile=_make_profile(),
            education_entries=[],
            experience_entries=[],
            language_entries=[existing_lang],
        )

        assert result.replaced_language_entries is False
        assert len(result.language_entries) == 1
        assert result.language_entries[0].language_name == "English"

    def test_pivot_replaces_languages_when_draft_has_entries(self) -> None:
        """When draft has language entries, they must replace existing ones."""
        existing_lang = _make_language("German")
        draft = build_cv_profile_draft(
            language_entries=[
                build_cv_draft_language_entry(language_name="English", proficiency_level="C1"),
                build_cv_draft_language_entry(language_name="Turkish", proficiency_level="Native"),
            ]
        )
        snapshot = build_cv_profile_draft_snapshot(draft=draft)

        result = pivot_profile_to_cv_draft(
            snapshot=snapshot,
            profile=_make_profile(),
            education_entries=[],
            experience_entries=[],
            language_entries=[existing_lang],
        )

        assert result.replaced_language_entries is True
        names = {e.language_name for e in result.language_entries}
        assert names == {"English", "Turkish"}
        assert "German" not in names

    def test_pivot_preserves_experiences_then_cv_is_rerun_with_entries(self) -> None:
        """After empty-draft pivot preserves entries, a re-run with entries replaces."""
        existing_exp = _make_experience("Old Role")
        draft_with_entries = build_cv_profile_draft(
            experience_entries=[
                build_cv_draft_experience_entry(
                    title="New Role",
                    company_name="New Co",
                    start_year=2023,
                )
            ]
        )
        snapshot = build_cv_profile_draft_snapshot(draft=draft_with_entries)

        result = pivot_profile_to_cv_draft(
            snapshot=snapshot,
            profile=_make_profile(),
            education_entries=[],
            experience_entries=[existing_exp],
            language_entries=[],
        )

        assert result.replaced_experience_entries is True
        assert len(result.experience_entries) == 1
        assert result.experience_entries[0].title == "New Role"
