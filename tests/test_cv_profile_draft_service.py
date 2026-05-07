from __future__ import annotations

from hiring_radar.services.cv_profile_draft import (
    CvProfileDraft,
    build_cv_draft_certification_entry,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
    normalize_year,
)


def test_normalize_year_accepts_valid_integer_and_digit_string_values() -> None:
    assert normalize_year(2024) == 2024
    assert normalize_year(" 2019 ") == 2019


def test_normalize_year_rejects_invalid_values() -> None:
    assert normalize_year(None) is None
    assert normalize_year(1899) is None
    assert normalize_year("present") is None
    assert normalize_year("  ") is None


def test_build_cv_profile_draft_normalizes_lists_and_deduplicates() -> None:
    education_entry = build_cv_draft_education_entry(
        school_name="  METU  ",
        degree_name="  BSc ",
        field_of_study=" Electrical Engineering ",
        start_year="2016",
        end_year="2021",
    )
    experience_entry = build_cv_draft_experience_entry(
        title=" Senior Python Developer ",
        company_name=" ACME ",
        start_year="2021",
        end_year=None,
        summary=" Built matching systems ",
    )
    language_entry = build_cv_draft_language_entry(
        language_name=" English ",
        proficiency_level=" C1 ",
        notes=" Professional working proficiency ",
    )
    certification_entry = build_cv_draft_certification_entry(
        certificate_name=" Certified Reliability Engineer ",
        issuer_name=" ASQ ",
        issued_year="2013",
    )

    draft = build_cv_profile_draft(
        headline="  Senior Backend Engineer  ",
        summary="  Experienced in FastAPI and data pipelines.  ",
        skills=["Python", " python ", "FastAPI", " ", "SQL"],
        target_roles=["Backend Engineer", "backend engineer", "Platform Engineer"],
        preferred_locations=["Berlin", " berlin ", "Remote"],
        remote_preference=" hybrid ",
        education_entries=[education_entry],
        experience_entries=[experience_entry],
        language_entries=[language_entry],
        certification_entries=[certification_entry],
    )

    assert draft.headline == "Senior Backend Engineer"
    assert draft.summary == "Experienced in FastAPI and data pipelines."
    assert draft.skills == ("Python", "FastAPI", "SQL")
    assert draft.target_roles == ("Backend Engineer", "Platform Engineer")
    assert draft.preferred_locations == ("Berlin", "Remote")
    assert draft.remote_preference == "hybrid"
    assert draft.education_entries[0].school_name == "METU"
    assert draft.education_entries[0].start_year == 2016
    assert draft.experience_entries[0].title == "Senior Python Developer"
    assert draft.language_entries[0].language_name == "English"
    assert draft.certification_entries[0].certificate_name == "Certified Reliability Engineer"
    assert draft.certification_entries[0].issuer_name == "ASQ"
    assert draft.certification_entries[0].issued_year == 2013




def test_build_cv_profile_draft_normalizes_all_caps_name_for_display() -> None:
    draft = build_cv_profile_draft(full_name="BULUT KARABULUT")

    assert draft.full_name == "Bulut Karabulut"


def test_build_cv_profile_draft_preserves_mixed_case_and_initials_in_name() -> None:
    assert build_cv_profile_draft(full_name="Leyla Aydin").full_name == "Leyla Aydin"
    assert build_cv_profile_draft(full_name="AJ LEE").full_name == "AJ LEE"

def test_build_cv_profile_draft_formats_compact_turkish_phone() -> None:
    draft = build_cv_profile_draft(phone="02121252425")

    assert draft.phone == "0212 125 24 25"


def test_build_cv_profile_draft_preserves_international_phone_prefix() -> None:
    draft = build_cv_profile_draft(phone="+90 212 125 24 25")

    assert draft.phone == "+90 212 125 24 25"

def test_build_cv_profile_draft_drops_empty_nested_entries() -> None:
    draft = build_cv_profile_draft(
        education_entries=[build_cv_draft_education_entry(school_name=" ")],
        experience_entries=[build_cv_draft_experience_entry(title=None)],
        language_entries=[build_cv_draft_language_entry(language_name="")],
        certification_entries=[build_cv_draft_certification_entry(certificate_name=" ")],
    )

    assert draft == CvProfileDraft()


def test_build_cv_profile_draft_snapshot_keeps_source_metadata() -> None:
    draft = build_cv_profile_draft(skills=["Python"])

    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=42,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T10:30:00Z",
        draft=draft,
    )

    assert snapshot.source_upload_id == 42
    assert snapshot.source_filename == "alice_cv.pdf"
    assert snapshot.source_parse_status == "parsed"
    assert snapshot.parser_version == "heuristic-v0"
    assert snapshot.generated_at == "2026-04-06T10:30:00Z"
    assert snapshot.draft.skills == ("Python",)