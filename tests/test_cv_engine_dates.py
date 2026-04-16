from __future__ import annotations

from hiring_radar.services.cv_engine.parsing.dates import parse_date_range



def test_parse_date_range_supports_english_month_names() -> None:
    parsed = parse_date_range("Jan 2020 - Present", "en")

    assert parsed is not None
    assert parsed.start_year == 2020
    assert parsed.start_month == 1
    assert parsed.is_present is True



def test_parse_date_range_supports_turkish_month_names() -> None:
    parsed = parse_date_range("Ocak 2021 - Devam", "tr")

    assert parsed is not None
    assert parsed.start_year == 2021
    assert parsed.start_month == 1
    assert parsed.is_present is True



def test_parse_date_range_supports_german_month_names() -> None:
    parsed = parse_date_range("Januar 2019 - Heute", "de")

    assert parsed is not None
    assert parsed.start_year == 2019
    assert parsed.start_month == 1
    assert parsed.is_present is True



def test_parse_date_range_supports_numeric_month_year() -> None:
    parsed = parse_date_range("03/2021 - 11/2023", "en")

    assert parsed is not None
    assert parsed.start_year == 2021
    assert parsed.start_month == 3
    assert parsed.end_year == 2023
    assert parsed.end_month == 11
    assert parsed.is_present is False



def test_parse_date_range_supports_year_only() -> None:
    parsed = parse_date_range("2020", "en")

    assert parsed is not None
    assert parsed.start_year == 2020
    assert parsed.start_month is None
    assert parsed.end_year is None
