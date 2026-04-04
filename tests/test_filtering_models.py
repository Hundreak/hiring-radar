from __future__ import annotations

import pytest

from hiring_radar.filtering.models import FilterableJobText, KeywordFilterSettings


def test_keyword_filter_settings_normalizes_and_deduplicates_keywords() -> None:
    settings = KeywordFilterSettings(
        include_keywords=(
            " Python ",
            "python",
            "Data",
            "",
            "  data  ",
        ),
        exclude_keywords=(
            "intern",
            " Intern ",
            "  ",
        ),
    )

    assert settings.include_keywords == ("Python", "Data")
    assert settings.exclude_keywords == ("intern",)
    assert settings.is_enabled() is True


def test_keyword_filter_settings_can_be_disabled_with_empty_keywords() -> None:
    settings = KeywordFilterSettings()

    assert settings.include_keywords == ()
    assert settings.exclude_keywords == ()
    assert settings.is_enabled() is False
    assert settings.active_fields() == ("title", "location", "company_name")


def test_keyword_filter_settings_requires_at_least_one_enabled_field() -> None:
    with pytest.raises(ValueError) as exc_info:
        KeywordFilterSettings(
            match_title=False,
            match_location=False,
            match_company_name=False,
        )

    assert "at least one enabled match field" in str(exc_info.value)


def test_filterable_job_text_returns_selected_field_values() -> None:
    job = FilterableJobText(
        title="Senior Python Engineer",
        location="Istanbul",
        company_name="Trendyol",
    )
    settings = KeywordFilterSettings(
        match_title=True,
        match_location=False,
        match_company_name=True,
    )

    assert job.selected_field_values(settings=settings) == (
        "Senior Python Engineer",
        "Trendyol",
    )


def test_filterable_job_text_converts_none_location_to_empty_string() -> None:
    job = FilterableJobText(
        title="Backend Engineer",
        location=None,
        company_name="Corelight",
    )
    settings = KeywordFilterSettings(
        match_title=False,
        match_location=True,
        match_company_name=False,
    )

    assert job.selected_field_values(settings=settings) == ("",)


def test_keyword_filter_settings_to_dict_returns_serializable_structure() -> None:
    settings = KeywordFilterSettings(
        include_keywords=("python", "security"),
        exclude_keywords=("intern",),
        match_title=True,
        match_location=False,
        match_company_name=True,
    )

    assert settings.to_dict() == {
        "include_keywords": ["python", "security"],
        "exclude_keywords": ["intern"],
        "match_title": True,
        "match_location": False,
        "match_company_name": True,
    }