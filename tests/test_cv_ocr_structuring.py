"""Tests for Ollama-assisted OCR structuring and hallucination guard."""
from __future__ import annotations

import pytest

from hiring_radar.services.cv_ocr_structuring import (
    _build_draft_from_extraction,
    _validate_extraction,
    extract_cv_structure_with_ollama,
)

# ---------------------------------------------------------------------------
# Hallucination guard (_validate_extraction)
# ---------------------------------------------------------------------------

_OLIVIA_TEXT = (
    "OLIVIA CAMPOS\n"
    "Senior Software Engineer\n"
    "olivia.campos@email.com\n"
    "(123) 456-7890\n"
    "San Francisco, CA\n"
    "SKILLS\n"
    "Python Django JavaScript Angular\n"
    "WORK EXPERIENCE\n"
    "Senior Software Engineer\nWish\n2024 - current San Francisco, CA\n"
    "Full-Stack Engineer\nPostMates\n2021 - 2024 San Francisco, CA\n"
    "EDUCATION\n"
    "Computer Science UCLA 2016 - 2020 Los Angeles, CA\n"
)

_VALID_EXTRACTION = {
    "full_name": "OLIVIA CAMPOS",
    "headline": "Senior Software Engineer",
    "email": "olivia.campos@email.com",
    "phone": "(123) 456-7890",
    "contact_location": "San Francisco, CA",
    "summary": "Experienced full-stack engineer with 5+ years at fast-growing tech companies.",
    "target_roles": ["Senior Software Engineer"],
    "preferred_locations": [],
    "skills": ["Python", "Django", "JavaScript", "Angular"],
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Wish",
            "start_year": 2024,
            "end_year": None,
            "description": "Built APIs and improved performance for Wish's e-commerce platform.",
        },
        {
            "title": "Full-Stack Engineer",
            "company": "PostMates",
            "start_year": 2021,
            "end_year": 2024,
            "description": None,
        },
    ],
    "education": [
        {"school": "UCLA", "degree": "Computer Science", "field": None, "start_year": 2016, "end_year": 2020},
    ],
}


def test_validate_extraction_accepts_grounded_values() -> None:
    result = _validate_extraction(_VALID_EXTRACTION, source_text=_OLIVIA_TEXT)
    assert result is not None
    assert result["full_name"] == "OLIVIA CAMPOS"
    assert result["headline"] == "Senior Software Engineer"
    assert result["email"] == "olivia.campos@email.com"
    assert len(result["experience"]) == 2
    assert result["experience"][0]["company"] == "Wish"
    assert len(result["education"]) == 1
    assert result["education"][0]["school"] == "UCLA"


def test_validate_extraction_rejects_hallucinated_name() -> None:
    raw = {**_VALID_EXTRACTION, "full_name": "John Doe XYZ Nobody"}
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    # "John Doe XYZ Nobody" is not in the source text → should be nulled
    assert result["full_name"] is None


def test_validate_extraction_rejects_hallucinated_company() -> None:
    raw = dict(_VALID_EXTRACTION)
    raw["experience"] = [
        {"title": "Senior Engineer", "company": "FakeCompanyXYZ", "start_year": 2020, "end_year": 2024},
    ]
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    # "FakeCompanyXYZ" not in source → experience entry dropped
    assert len(result["experience"]) == 0


def test_validate_extraction_accepts_experience_when_grounded() -> None:
    result = _validate_extraction(_VALID_EXTRACTION, source_text=_OLIVIA_TEXT)
    assert result is not None
    titles = [e["title"] for e in result["experience"]]
    assert "Senior Software Engineer" in titles
    assert "Full-Stack Engineer" in titles


def test_validate_extraction_filters_invalid_years() -> None:
    raw = dict(_VALID_EXTRACTION)
    raw["experience"] = [
        {"title": "Engineer", "company": "Wish", "start_year": 1850, "end_year": 9999},
    ]
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    if result["experience"]:
        exp = result["experience"][0]
        assert exp["start_year"] is None or 1900 <= exp["start_year"] <= 2100
        assert exp["end_year"] is None or 1900 <= exp["end_year"] <= 2100


def test_validate_extraction_returns_none_for_empty_result() -> None:
    raw = {
        "full_name": "Xyz Qwerty Blarg",  # not in source
        "headline": None,
        "email": None,
        "phone": None,
        "location": None,
        "skills": [],
        "experience": [],
        "education": [],
    }
    result = _validate_extraction(raw, source_text="some short text")
    assert result is None


# ---------------------------------------------------------------------------
# Draft builder
# ---------------------------------------------------------------------------

def test_build_draft_from_extraction_produces_correct_draft() -> None:
    data = {
        "full_name": "OLIVIA CAMPOS",
        "headline": "Senior Software Engineer",
        "email": "olivia.campos@email.com",
        "phone": "(123) 456-7890",
        "contact_location": "San Francisco, CA",  # contact location — NOT mapped to preferred_locations
        "summary": "Experienced software engineer specializing in full-stack development.",
        "target_roles": ["Senior Software Engineer", "Full-Stack Engineer"],
        "preferred_locations": [],  # no explicit preference stated
        "skills": ["Python", "JavaScript"],
        "experience": [
            {
                "title": "Senior SWE",
                "company": "Wish",
                "start_year": 2024,
                "end_year": None,
                "description": "Led performance improvements and API development.",
            },
        ],
        "education": [
            {"school": "UCLA", "degree": "CS", "field": None, "start_year": 2016, "end_year": 2020},
        ],
    }
    draft = _build_draft_from_extraction(data)
    assert draft.full_name == "Olivia Campos"
    assert draft.headline == "Senior Software Engineer"
    assert draft.email == "olivia.campos@email.com"
    assert "Python" in draft.skills
    assert len(draft.experience_entries) == 1
    exp = draft.experience_entries[0]
    assert exp.company_name == "Wish"
    assert exp.summary == "Led performance improvements and API development."
    assert len(draft.education_entries) == 1
    assert draft.education_entries[0].school_name == "UCLA"
    # contact_location must NOT propagate to preferred_locations
    assert draft.preferred_locations == ()
    assert draft.summary == "Experienced software engineer specializing in full-stack development."
    assert "Senior Software Engineer" in draft.target_roles


def test_build_draft_from_extraction_explicit_preferred_locations_are_preserved() -> None:
    data = {
        "full_name": "Jane Doe",
        "headline": "Engineer",
        "email": None,
        "phone": None,
        "contact_location": "Berlin",
        "summary": None,
        "target_roles": [],
        "preferred_locations": ["Remote", "New York, NY"],
        "skills": [],
        "experience": [],
        "education": [],
    }
    draft = _build_draft_from_extraction(data)
    assert "Remote" in draft.preferred_locations
    assert "New York, NY" in draft.preferred_locations


def test_build_draft_from_extraction_handles_empty_fields() -> None:
    data = {
        "full_name": None,
        "headline": None,
        "email": None,
        "phone": None,
        "contact_location": None,
        "summary": None,
        "target_roles": [],
        "preferred_locations": [],
        "skills": [],
        "experience": [],
        "education": [],
    }
    draft = _build_draft_from_extraction(data)
    assert draft.full_name is None
    assert draft.skills == ()
    assert draft.experience_entries == ()
    assert draft.education_entries == ()


# ---------------------------------------------------------------------------
# extract_cv_structure_with_ollama — unavailability handling
# ---------------------------------------------------------------------------

def test_extract_cv_structure_with_ollama_returns_none_when_unreachable() -> None:
    # Use an invalid port so the connection is refused immediately.
    result = extract_cv_structure_with_ollama(
        "Alice Engineer\nSenior Developer\nalice@example.com",
        base_url="http://127.0.0.1:19999",
        timeout_seconds=2,
    )
    assert result is None


def test_extract_cv_structure_with_ollama_returns_none_for_empty_text() -> None:
    result = extract_cv_structure_with_ollama("")
    assert result is None

    result = extract_cv_structure_with_ollama(None)
    assert result is None


# ---------------------------------------------------------------------------
# Column-aware OCR + quality scoring (integration smoke test without real images)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# validate_extraction — new fields (summary, target_roles, preferred_locations, description)
# ---------------------------------------------------------------------------

def test_validate_extraction_passes_through_summary_without_grounding_check() -> None:
    raw = {**_VALID_EXTRACTION, "summary": "A synthesized professional summary about Olivia's engineering career."}
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    # summary is generated content — should not be killed by grounding check
    assert result["summary"] is not None
    assert "summary" in result


def test_validate_extraction_keeps_grounded_preferred_locations() -> None:
    raw = {**_VALID_EXTRACTION, "preferred_locations": ["San Francisco, CA"]}
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    assert "San Francisco, CA" in result["preferred_locations"]


def test_validate_extraction_rejects_hallucinated_preferred_location() -> None:
    raw = {**_VALID_EXTRACTION, "preferred_locations": ["ZZZ Faketown Nowhere"]}
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    assert result["preferred_locations"] == []


def test_validate_extraction_empty_preferred_locations_stays_empty() -> None:
    raw = {**_VALID_EXTRACTION, "preferred_locations": []}
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    assert result["preferred_locations"] == []


def test_validate_extraction_experience_description_passed_through() -> None:
    raw = dict(_VALID_EXTRACTION)
    raw["experience"] = [
        {
            "title": "Senior Software Engineer",
            "company": "Wish",
            "start_year": 2024,
            "end_year": None,
            "description": "Built APIs and improved e-commerce performance.",
        }
    ]
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    assert result["experience"][0]["description"] == "Built APIs and improved e-commerce performance."


def test_validate_extraction_target_roles_passed_through() -> None:
    raw = {**_VALID_EXTRACTION, "target_roles": ["Senior Software Engineer", "Full-Stack Engineer"]}
    result = _validate_extraction(raw, source_text=_OLIVIA_TEXT)
    assert result is not None
    assert "Senior Software Engineer" in result["target_roles"]


# ---------------------------------------------------------------------------
# Section detection fix — icon-prefixed headings (OCR template style)
# ---------------------------------------------------------------------------

def test_icon_prefixed_section_headings_are_detected() -> None:
    from hiring_radar.services.cv_profile_parser import _detect_section_name
    assert _detect_section_name("© EDUCATION") == "education"
    assert _detect_section_name("# SKILLS") == "skills"
    assert _detect_section_name("& WORK EXPERIENCE") == "experience"
    assert _detect_section_name("★ Experience") == "experience"
    assert _detect_section_name("● Skills") == "skills"


def test_split_role_title_is_merged_in_preparation() -> None:
    from hiring_radar.services.cv_profile_parser import _prepare_cv_text_for_parsing, _extract_headline
    text = "OLIVIA CAMPOS\nSenior Software\nEngineer\nolivia.campos@email.com"
    prepared = _prepare_cv_text_for_parsing(text)
    # "Senior Software" + "Engineer" should merge into "Senior Software Engineer"
    assert "Senior Software Engineer" in prepared
    lines = [l for l in prepared.splitlines() if l.strip()]
    headline = _extract_headline(lines)
    assert headline == "Senior Software Engineer"


def test_cv_ocr_quality_gate_still_rejects_garbage_text() -> None:
    from hiring_radar.services.cv_ocr_quality import score_ocr_quality
    garbage = "s}914u03 aBsaw Y pazUaAds Jeyy SA!DUd}SISUOSU! weal odds ay} 10 SINOY 4 YSOM"
    report = score_ocr_quality(garbage, extraction_method="image_ocr")
    assert report.band in ("unusable", "low"), f"Expected unusable/low, got {report.band!r}"
    assert report.is_trustworthy_for_pivot is False


def test_cv_ocr_quality_gate_accepts_clean_cv_text() -> None:
    from hiring_radar.services.cv_ocr_quality import score_ocr_quality
    clean = (
        "OLIVIA CAMPOS\nSenior Software Engineer\nolivia.campos@email.com\n"
        "(123) 456-7890\nSan Francisco, CA\n\n"
        "SKILLS\nPython Django JavaScript Angular HTML CSS AWS SQL Git\n\n"
        "WORK EXPERIENCE\nSenior Software Engineer\nWish\n2024 - current\n"
        "Full-Stack Engineer\nPostMates\n2021 - 2024\n"
        "Software Engineer Intern\nMosaic\n2020 - 2021\n\n"
        "EDUCATION\nComputer Science UCLA 2016 - 2020 Los Angeles, CA"
    )
    report = score_ocr_quality(clean, extraction_method="image_ocr")
    assert report.band in ("high", "medium"), f"Expected high/medium, got {report.band!r}"
    assert report.is_trustworthy_for_apply is True
