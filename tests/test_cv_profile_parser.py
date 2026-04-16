from __future__ import annotations

from hiring_radar.services.cv_profile_parser import (
    HEURISTIC_CV_PARSER_VERSION,
    parse_cv_text_to_profile_draft,
)


def test_parse_cv_text_to_profile_draft_extracts_core_fields_from_english_cv() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Professional Summary
Backend engineer with 8+ years of experience building FastAPI services and
data-intensive backend systems.

Technical Skills
Python, FastAPI, SQL, Docker, AWS

Desired Position
Staff Backend Engineer, Platform Engineer

Work Experience
Senior Backend Engineer | ACME | 2021 - Present
Built matching systems for job intelligence products.

Backend Engineer | Example GmbH
2018 - 2021

Education
METU | BSc Electrical Engineering | 2012 - 2017

Languages
English - C1
Turkish - Native
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert HEURISTIC_CV_PARSER_VERSION == "heuristic-v0"
    assert draft.headline == "Senior Backend Engineer"
    assert "FastAPI" in draft.summary
    assert draft.skills == ("Python", "FastAPI", "SQL", "Docker", "AWS")
    assert draft.target_roles == ("Staff Backend Engineer", "Platform Engineer")
    assert draft.preferred_locations == ("Berlin",)
    assert draft.remote_preference == "remote"

    assert len(draft.language_entries) == 2
    assert draft.language_entries[0].language_name == "English"
    assert draft.language_entries[0].proficiency_level == "C1"
    assert draft.language_entries[1].language_name == "Turkish"
    assert draft.language_entries[1].proficiency_level == "Native"

    assert len(draft.experience_entries) == 2
    assert draft.experience_entries[0].title == "Senior Backend Engineer"
    assert draft.experience_entries[0].company_name == "ACME"
    assert draft.experience_entries[0].start_year == 2021
    assert draft.experience_entries[0].end_year is None

    assert len(draft.education_entries) == 1
    assert draft.education_entries[0].school_name == "METU"
    assert draft.education_entries[0].degree_name == "BSc Electrical Engineering"
    assert draft.education_entries[0].start_year == 2012
    assert draft.education_entries[0].end_year == 2017


def test_parse_cv_text_to_profile_draft_supports_mixed_language_section_aliases() -> None:
    extracted_text = """
Mehmet Yılmaz
Kıdemli Python Geliştirici
mehmet@example.com | Istanbul | Hibrit

Profil
Python, FastAPI ve veri işleme sistemlerinde uzman backend geliştirici.

Beceriler
Python; FastAPI; PostgreSQL; Docker

Hedef Pozisyon
Lead Backend Engineer

İş Deneyimi
Kıdemli Python Geliştirici | ABC Teknoloji | 2022 - Devam

Eğitim
İTÜ | Elektrik Elektronik Mühendisliği | 2014 - 2019

Diller
Türkçe - Ana dil
English - B2
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Kıdemli Python Geliştirici"
    assert "backend geliştirici" in draft.summary
    assert draft.skills == ("Python", "FastAPI", "PostgreSQL", "Docker")
    assert draft.target_roles == ("Lead Backend Engineer",)
    assert draft.preferred_locations == ("Istanbul",)
    assert draft.remote_preference == "hybrid"

    assert len(draft.experience_entries) == 1
    assert draft.experience_entries[0].title == "Kıdemli Python Geliştirici"
    assert draft.experience_entries[0].company_name == "ABC Teknoloji"
    assert draft.experience_entries[0].start_year == 2022
    assert draft.experience_entries[0].end_year is None

    assert len(draft.education_entries) == 1
    assert draft.education_entries[0].school_name == "İTÜ"
    assert draft.education_entries[0].degree_name == "Elektrik Elektronik Mühendisliği"

    assert len(draft.language_entries) == 2
    assert draft.language_entries[0].language_name == "Türkçe"
    assert draft.language_entries[0].proficiency_level == "Ana dil"
    assert draft.language_entries[1].language_name == "English"
    assert draft.language_entries[1].proficiency_level == "B2"


def test_parse_cv_text_to_profile_draft_returns_empty_draft_for_empty_input() -> None:
    draft = parse_cv_text_to_profile_draft("   ")

    assert draft.headline is None
    assert draft.summary is None
    assert draft.skills == ()
    assert draft.target_roles == ()
    assert draft.preferred_locations == ()
    assert draft.remote_preference is None
    assert draft.education_entries == ()
    assert draft.experience_entries == ()
    assert draft.language_entries == ()



def test_parse_cv_text_to_profile_draft_supports_inline_section_headers() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Professional Summary: Backend engineer with strong FastAPI, data platform and matching experience.
Technical Skills: Python, FastAPI, SQL, Docker
Desired Position: Staff Backend Engineer, Platform Engineer
Languages: English - C1, Turkish - Native
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Senior Backend Engineer"
    assert draft.summary == (
        "Backend engineer with strong FastAPI, data platform and matching experience."
    )
    assert draft.skills == ("Python", "FastAPI", "SQL", "Docker")
    assert draft.target_roles == ("Staff Backend Engineer", "Platform Engineer")
    assert draft.preferred_locations == ("Berlin",)
    assert draft.remote_preference == "remote"

    assert len(draft.language_entries) == 2
    assert draft.language_entries[0].language_name == "English"
    assert draft.language_entries[0].proficiency_level == "C1"
    assert draft.language_entries[1].language_name == "Turkish"
    assert draft.language_entries[1].proficiency_level == "Native"


def test_parse_cv_text_to_profile_draft_splits_dense_experience_blocks() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer

Work Experience
Senior Backend Engineer | ACME | 2021 - Present
Built matching systems and internal recruiter tooling.
Backend Engineer | Example GmbH | 2018 - 2021
Built backend APIs and search integrations.

Education
METU | BSc Electrical Engineering | 2012 - 2017
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert len(draft.experience_entries) == 2

    assert draft.experience_entries[0].title == "Senior Backend Engineer"
    assert draft.experience_entries[0].company_name == "ACME"
    assert draft.experience_entries[0].start_year == 2021
    assert draft.experience_entries[0].end_year is None
    assert "matching systems" in (draft.experience_entries[0].summary or "")

    assert draft.experience_entries[1].title == "Backend Engineer"
    assert draft.experience_entries[1].company_name == "Example GmbH"
    assert draft.experience_entries[1].start_year == 2018
    assert draft.experience_entries[1].end_year == 2021
    assert "search integrations" in (draft.experience_entries[1].summary or "")



def test_parse_cv_text_to_profile_draft_supports_sectionless_cv_fallbacks() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote
Backend engineer with 8+ years building FastAPI services and data platforms.
Python | FastAPI | SQL | Docker | AWS
Senior Backend Engineer | ACME | 2021 - Present
Built matching systems for recruiter workflows.
Backend Engineer | Example GmbH | 2018 - 2021
METU | BSc Electrical Engineering | 2012 - 2017
English - C1
Turkish - Native
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Senior Backend Engineer"
    assert draft.summary == (
        "Backend engineer with 8+ years building FastAPI services and data platforms."
    )
    assert draft.skills == ("Python", "FastAPI", "SQL", "Docker", "AWS")
    assert draft.target_roles == ("Senior Backend Engineer",)
    assert draft.preferred_locations == ("Berlin",)
    assert draft.remote_preference == "remote"

    assert len(draft.experience_entries) == 2
    assert draft.experience_entries[0].title == "Senior Backend Engineer"
    assert draft.experience_entries[0].company_name == "ACME"
    assert "recruiter workflows" in (draft.experience_entries[0].summary or "")

    assert len(draft.education_entries) == 1
    assert draft.education_entries[0].school_name == "METU"
    assert draft.education_entries[0].degree_name == "BSc Electrical Engineering"

    assert len(draft.language_entries) == 2
    assert draft.language_entries[0].language_name == "English"
    assert draft.language_entries[1].language_name == "Turkish"



def test_sectionless_fallback_ignores_company_lines_as_skills() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote
Python | FastAPI | SQL | Docker
ACME GmbH | Berlin | Remote
Senior Backend Engineer | ACME GmbH | 2021 - Present
Built matching systems for recruiter workflows.
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.skills == ("Python", "FastAPI", "SQL", "Docker")
    assert draft.preferred_locations == ("Berlin",)
    assert len(draft.experience_entries) == 1
    assert draft.experience_entries[0].title == "Senior Backend Engineer"
    assert draft.experience_entries[0].company_name == "ACME GmbH"


def test_sectionless_fallback_keeps_education_out_of_skills() -> None:
    extracted_text = """
Alice Example
Embedded Systems Engineer
C, C++, Python, FreeRTOS
Technical University of Munich | MSc Electrical Engineering | 2016 - 2018
METU | BSc Electrical Engineering | 2012 - 2016
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.skills == ("C", "C++", "Python", "FreeRTOS")
    assert len(draft.education_entries) == 2
    assert draft.education_entries[0].school_name == "Technical University of Munich"
    assert draft.education_entries[1].school_name == "METU"



def test_parse_cv_text_to_profile_draft_merges_split_section_headers() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Professional
Summary
Backend engineer with strong FastAPI and platform experience.

Technical
Skills
Python, FastAPI, SQL, Docker

Desired
Position
Staff Backend Engineer

Work
Experience
Senior Backend Engineer | ACME | 2021 - Present

Languages
English - C1
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Senior Backend Engineer"
    assert "FastAPI" in (draft.summary or "")
    assert draft.skills == ("Python", "FastAPI", "SQL", "Docker")
    assert draft.target_roles == ("Staff Backend Engineer",)
    assert draft.preferred_locations == ("Berlin",)
    assert len(draft.experience_entries) == 1
    assert draft.experience_entries[0].company_name == "ACME"
    assert len(draft.language_entries) == 1
    assert draft.language_entries[0].language_name == "English"


def test_parse_cv_text_to_profile_draft_deduplicates_adjacent_noise_lines() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Technical Skills
Technical Skills
Python, FastAPI, SQL

Languages
Languages
English - C1
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Senior Backend Engineer"
    assert draft.skills == ("Python", "FastAPI", "SQL")
    assert draft.preferred_locations == ("Berlin",)
    assert len(draft.language_entries) == 1
    assert draft.language_entries[0].language_name == "English"


def test_parse_cv_text_to_profile_draft_supports_german_month_names_and_multiline_experience() -> None:
    extracted_text = """
Anna Beispiel
Senior Software Engineer
anna@example.com | Berlin | Hybrid

Berufserfahrung
Senior Software Engineer
Beispiel GmbH
Januar 2020 - Heute
Verantwortlich für Plattform-APIs und Suchsysteme.

Fähigkeiten
Python, FastAPI, PostgreSQL
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Senior Software Engineer"
    assert draft.skills == ("Python", "FastAPI", "PostgreSQL")
    assert len(draft.experience_entries) == 1
    assert draft.experience_entries[0].title == "Senior Software Engineer"
    assert draft.experience_entries[0].company_name == "Beispiel GmbH"
    assert draft.experience_entries[0].start_year == 2020
    assert draft.experience_entries[0].end_year is None
    assert "Suchsysteme" in (draft.experience_entries[0].summary or "")



def test_parse_cv_text_to_profile_draft_supports_composite_skills_heading() -> None:
    extracted_text = """
Alice Example
Staff Platform Engineer
alice@example.com | Berlin | Remote

Skills & Tools
Python, FastAPI, Docker, AWS
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Staff Platform Engineer"
    assert draft.skills == ("Python", "FastAPI", "Docker", "AWS")
