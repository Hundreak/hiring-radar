"""Tests that the profile aggregate language builder filters non-spoken language entries."""
from __future__ import annotations

from hiring_radar.services.profile_aggregate import _build_languages


def _make_lang(language_name: str, proficiency_level: str | None = None) -> dict:
    return {
        "id": 1,
        "language_name": language_name,
        "proficiency_level": proficiency_level,
        "display_order": 0,
        "source_type": "extracted",
        "source_confidence": None,
        "is_user_edited": False,
        "is_suppressed": False,
        "certificate_name": None,
    }


class TestBuildLanguagesFilter:
    def test_real_spoken_languages_pass_through(self) -> None:
        result = _build_languages([
            _make_lang("English", "advanced"),
            _make_lang("Turkish", "native_or_bilingual"),
        ])
        names = {lang.language_name for lang in result}
        assert "English" in names
        assert "Turkish" in names

    def test_tech_names_filtered_from_language_entries(self) -> None:
        result = _build_languages([
            _make_lang("English", "advanced"),
            _make_lang("Python"),
            _make_lang("Django"),
            _make_lang("Techstack & Skills"),
            _make_lang("Flask"),
            _make_lang("Turkish", "native_or_bilingual"),
        ])
        names = {lang.language_name for lang in result}
        assert "English" in names
        assert "Turkish" in names
        assert "Python" not in names
        assert "Django" not in names
        assert "Techstack & Skills" not in names
        assert "Flask" not in names

    def test_empty_language_name_excluded(self) -> None:
        result = _build_languages([_make_lang(""), _make_lang("   ")])
        assert result == []

    def test_no_language_entries_produces_empty_list(self) -> None:
        result = _build_languages([])
        assert result == []
