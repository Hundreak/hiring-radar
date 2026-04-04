from __future__ import annotations

from hiring_radar.filtering.engine import (
    KeywordFieldMatch,
    evaluate_job_text_against_keyword_filter,
)
from hiring_radar.filtering.models import FilterableJobText, KeywordFilterSettings


def test_filter_passes_when_include_keyword_matches_title() -> None:
    job = FilterableJobText(
        title="Senior Python Engineer",
        location="Istanbul",
        company_name="Trendyol",
    )
    settings = KeywordFilterSettings(
        include_keywords=("python",),
        exclude_keywords=(),
        match_title=True,
        match_location=False,
        match_company_name=False,
    )

    result = evaluate_job_text_against_keyword_filter(
        job=job,
        settings=settings,
    )

    assert result.passed is True
    assert result.include_matched is True
    assert result.exclude_matched is False
    assert result.include_matches == (
        KeywordFieldMatch(
            field_name="title",
            keyword="python",
            field_value="Senior Python Engineer",
        ),
    )
    assert result.exclude_matches == ()


def test_filter_rejects_when_exclude_keyword_matches_even_if_include_matches() -> None:
    job = FilterableJobText(
        title="Python Intern",
        location="Remote",
        company_name="ExampleCo",
    )
    settings = KeywordFilterSettings(
        include_keywords=("python",),
        exclude_keywords=("intern",),
        match_title=True,
        match_location=False,
        match_company_name=False,
    )

    result = evaluate_job_text_against_keyword_filter(
        job=job,
        settings=settings,
    )

    assert result.passed is False
    assert result.include_matched is True
    assert result.exclude_matched is True
    assert result.include_matches == (
        KeywordFieldMatch(
            field_name="title",
            keyword="python",
            field_value="Python Intern",
        ),
    )
    assert result.exclude_matches == (
        KeywordFieldMatch(
            field_name="title",
            keyword="intern",
            field_value="Python Intern",
        ),
    )


def test_filter_passes_when_include_keywords_are_empty_and_no_exclude_match_exists() -> None:
    job = FilterableJobText(
        title="Backend Engineer",
        location="Ankara",
        company_name="ExampleCo",
    )
    settings = KeywordFilterSettings(
        include_keywords=(),
        exclude_keywords=("intern",),
        match_title=True,
        match_location=True,
        match_company_name=True,
    )

    result = evaluate_job_text_against_keyword_filter(
        job=job,
        settings=settings,
    )

    assert result.passed is True
    assert result.include_matched is False
    assert result.exclude_matched is False
    assert result.include_matches == ()
    assert result.exclude_matches == ()


def test_filter_can_match_location_and_company_name_fields() -> None:
    job = FilterableJobText(
        title="Software Engineer",
        location="Istanbul / Hybrid",
        company_name="Security Labs",
    )
    settings = KeywordFilterSettings(
        include_keywords=("istanbul", "security"),
        exclude_keywords=(),
        match_title=False,
        match_location=True,
        match_company_name=True,
    )

    result = evaluate_job_text_against_keyword_filter(
        job=job,
        settings=settings,
    )

    assert result.passed is True
    assert result.include_matched is True
    assert result.exclude_matched is False
    assert result.include_matches == (
        KeywordFieldMatch(
            field_name="location",
            keyword="istanbul",
            field_value="Istanbul / Hybrid",
        ),
        KeywordFieldMatch(
            field_name="company_name",
            keyword="security",
            field_value="Security Labs",
        ),
    )


def test_filter_treats_disabled_filter_as_pass_with_no_matches() -> None:
    job = FilterableJobText(
        title="Data Engineer",
        location=None,
        company_name="ExampleCo",
    )
    settings = KeywordFilterSettings()

    result = evaluate_job_text_against_keyword_filter(
        job=job,
        settings=settings,
    )

    assert result.passed is True
    assert result.include_matched is False
    assert result.exclude_matched is False
    assert result.include_matches == ()
    assert result.exclude_matches == ()
