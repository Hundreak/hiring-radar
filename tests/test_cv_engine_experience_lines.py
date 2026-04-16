from __future__ import annotations

from hiring_radar.services.cv_engine.parsing.experience_lines import parse_experience_block



def test_parse_experience_block_supports_multiline_role_company_date() -> None:
    parsed = parse_experience_block(
        [
            "Software Engineer",
            "Google LLC",
            "Jan 2020 - Present",
            "Built internal platforms.",
        ],
        language="en",
    )

    assert parsed.title == "Software Engineer"
    assert parsed.company_name == "Google LLC"
    assert parsed.date_range is not None
    assert parsed.date_range.start_year == 2020
    assert parsed.date_range.is_present is True
    assert parsed.summary_lines == ["Built internal platforms."]



def test_parse_experience_block_supports_inline_title_company() -> None:
    parsed = parse_experience_block(
        [
            "Senior Backend Engineer at ACME",
            "Berlin",
            "2021 - Present",
            "Designed matching systems.",
        ],
        language="en",
    )

    assert parsed.title == "Senior Backend Engineer"
    assert parsed.company_name == "ACME"
    assert parsed.date_range is not None
    assert parsed.date_range.start_year == 2021
    assert parsed.confidence > 0.7
