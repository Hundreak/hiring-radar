from __future__ import annotations

from hiring_radar.services.cv_profile_parser import (
    HEURISTIC_CV_PARSER_VERSION,
    is_valid_spoken_language,
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


def test_parse_cv_text_to_profile_draft_extracts_grouped_skill_categories() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Technical Skills
Backend: Python, FastAPI, Django
Databases: PostgreSQL, Redis
Frameworks & Tools — React, Docker, Kubernetes
Programming Languages: Python, TypeScript
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert "Python" in draft.skills
    assert "FastAPI" in draft.skills
    assert "Django" in draft.skills
    assert "PostgreSQL" in draft.skills
    assert "Redis" in draft.skills
    assert "React" in draft.skills
    assert "Docker" in draft.skills
    assert "Kubernetes" in draft.skills
    assert "TypeScript" in draft.skills
    assert "Backend" not in draft.skills
    assert "Databases" not in draft.skills
    assert "Frameworks & Tools" not in draft.skills


def test_parse_cv_text_to_profile_draft_recovers_contact_from_anywhere_in_cv() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer

Professional Summary
Backend engineer focused on FastAPI and data platforms.

Contact
alice.example@example.com
+49 (30) 1234 5678
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.email == "alice.example@example.com"
    assert draft.phone is not None
    assert "30" in draft.phone
    assert draft.phone.startswith("+49")


def test_parse_cv_text_to_profile_draft_uses_new_experience_aliases() -> None:
    extracted_text = """
Mehmet Yılmaz
Senior Data Engineer
mehmet@example.com | Istanbul | Remote

Kariyer Geçmişi
Senior Data Engineer | ABC Teknoloji | 2022 - Devam

Eğitim Durumu
İTÜ | Elektrik Elektronik Mühendisliği | 2014 - 2019

Yabancı Diller
Türkçe - Ana dil
English - C1
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert len(draft.experience_entries) == 1
    assert draft.experience_entries[0].company_name == "ABC Teknoloji"
    assert len(draft.education_entries) == 1
    assert draft.education_entries[0].school_name == "İTÜ"
    assert len(draft.language_entries) == 2
    assert draft.language_entries[0].language_name == "Türkçe"


def test_parse_cv_text_to_profile_draft_handles_ocr_icon_prefixed_section_headings() -> None:
    """OCR templates often prefix headings with icon characters (@ © # &).
    The parser must strip those and still detect the section correctly."""
    extracted_text = """
OLIVIA CAMPOS
Senior Software Engineer
olivia.campos@email.com

@ CONTACT
(123) 456-7890
San Francisco, CA

© EDUCATION
Computer Science
UCLA
2016 - 2020

# SKILLS
Python
JavaScript

& WORK EXPERIENCE
Senior Software Engineer
Acme Corp
2022 - 2024
Built APIs and improved performance.
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.full_name == "Olivia Campos"
    assert draft.headline == "Senior Software Engineer"
    assert draft.email == "olivia.campos@email.com"
    assert len(draft.education_entries) >= 1
    assert draft.education_entries[0].school_name == "UCLA"
    assert len(draft.skills) >= 1
    assert len(draft.experience_entries) >= 1
    assert draft.experience_entries[0].company_name == "Acme Corp"
    # Contact location must NOT leak into target_roles or summary
    assert draft.summary != "San Francisco, CA"


def test_parse_cv_text_to_profile_draft_merges_ocr_split_role_title() -> None:
    """When OCR wraps 'Senior Software\nEngineer' across two lines the
    parser must merge them into the correct headline."""
    extracted_text = """
OLIVIA CAMPOS
Senior Software
Engineer
olivia.campos@email.com

WORK EXPERIENCE
Senior Software Engineer
Acme Corp
2022 - 2024
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.headline == "Senior Software Engineer"
    assert draft.full_name == "Olivia Campos"
    # The merged headline must appear in target_roles too
    assert "Senior Software Engineer" in (draft.target_roles or ())


def test_parse_cv_text_to_profile_draft_preserves_degree_string_without_connector() -> None:
    extracted_text = """
Alice Example
Senior Backend Engineer

Education
METU | BSc Electrical Engineering | 2012 - 2017
TUM | MSc in Computer Science | 2017 - 2019
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.education_entries[0].degree_name == "BSc Electrical Engineering"
    assert draft.education_entries[0].field_of_study is None

    assert draft.education_entries[1].degree_name == "MSc"
    assert draft.education_entries[1].field_of_study == "Computer Science"


# ---------------------------------------------------------------------------
# Language filtering: tech terms must not leak into Languages
# ---------------------------------------------------------------------------

def test_techstack_skills_section_header_does_not_pollute_languages() -> None:
    """'Techstack & Skills' is a section header; its content must go to skills."""
    extracted_text = """
Alice Example
Backend Engineer
alice@example.com

Languages
English C1
Russian C1
Turkish (Native)
Techstack & Skills
Python
Django
Flask
FastAPI
Javascript

Work Experience
Backend Engineer | ACME Ltd | 2020 - Present

Education
Sakarya University | Bachelor of Computer Engineering | 2015 - 2019
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    language_names = {entry.language_name.lower() for entry in draft.language_entries}
    assert "english" in language_names
    assert "russian" in language_names
    assert "turkish" in language_names

    # Tech terms must NOT appear in languages
    for tech in ("python", "django", "flask", "fastapi", "javascript"):
        assert tech not in language_names, f"{tech!r} must not appear in language_entries"

    # "Techstack & Skills" must NOT appear as a language entry
    assert "techstack & skills" not in language_names
    assert "techstack" not in language_names


def test_tech_framework_names_are_rejected_from_language_entries() -> None:
    """Tech names that appear in a 'Languages' section must be filtered out."""
    extracted_text = """
Alice Example
Backend Engineer

Languages
English - C1
Python
Django
React Native
CSS
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    language_names = {entry.language_name.lower() for entry in draft.language_entries}
    assert "english" in language_names
    for tech in ("python", "django", "css"):
        assert tech not in language_names, f"{tech!r} should not be a language"
    # "React Native" — "react" is a tech term; should not appear as language
    assert "react" not in language_names


def test_react_native_framework_not_parsed_as_react_language_with_native_proficiency() -> None:
    """'React Native' must not be parsed as language='React' + proficiency='Native'."""
    extracted_text = """
Alice Example
Backend Engineer

Languages
React Native
English C1
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    language_names = {entry.language_name.lower() for entry in draft.language_entries}
    assert "react" not in language_names, "'React' must not appear as a language entry"
    assert "english" in language_names


def test_language_section_with_only_tech_terms_leaves_languages_empty() -> None:
    """When a 'Languages' section contains only tech terms, languages must be empty."""
    extracted_text = """
Alice Example
Backend Engineer

Languages
Python
Django
Flask
FastAPI
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.language_entries == (), (
        "language_entries must be empty when only tech terms appear under Languages"
    )


def test_real_spoken_languages_are_accepted_with_proficiency() -> None:
    """Spoken languages with proficiency markers must parse correctly."""
    extracted_text = """
Alice Example
Backend Engineer

Languages
English - C1
Russian - B2
Turkish - Native
German - A2
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert len(draft.language_entries) == 4
    names = {e.language_name.lower() for e in draft.language_entries}
    assert names == {"english", "russian", "turkish", "german"}


# ---------------------------------------------------------------------------
# Experience persistence: CV-derived entries must survive
# ---------------------------------------------------------------------------

def test_experience_entries_are_extracted_from_sectioned_cv() -> None:
    """Experiences from a clearly structured CV must be present in the draft."""
    extracted_text = """
Alice Example
Backend Engineer
alice@example.com

Techstack & Skills
Python, Django, FastAPI, React

Languages
English C1
Turkish Native

Work Experience
Senior Backend Engineer | ACME Ltd | 2021 - Present
Led the backend team on matching and intelligence features.

Backend Engineer | StartupCo | 2018 - 2021

Education
Sakarya University | Bachelor of Computer Engineering | 2015 - 2019
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert len(draft.experience_entries) >= 1, (
        "Experience entries must be extracted when a work experience section is present"
    )
    titles = {e.title for e in draft.experience_entries}
    assert "Senior Backend Engineer" in titles


def test_system_engineer_cv_with_no_spoken_languages_leaves_language_entries_empty() -> None:
    """A tech-heavy CV (like system-engineer.png) with no spoken language section
    must produce empty language_entries — SQL Server, MATLAB, PHP, Ansible, etc.
    must not be mistaken for spoken languages."""
    extracted_text = """
JOHN SMITH
Systems Engineer
john.smith@example.com | +1 555 000 1234

Professional Summary
Experienced systems engineer with expertise in cloud infrastructure and automation.

Skills
SQL Server, MATLAB, AWS, PHP, PL/SQL, XML, Ansible, Scrum, Git, Linux

Work Experience
Systems Engineer | Acme Corp | 2019 - Present
Managed cloud infrastructure and automated deployment pipelines.

Junior Systems Engineer | TechCorp | 2016 - 2019

Education
State University | BSc Computer Science | 2012 - 2016
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.language_entries == (), (
        "language_entries must be empty when the CV has no spoken languages section; "
        "SQL Server, MATLAB, Ansible, etc. must not appear as language entries"
    )
    # Skills must be populated
    assert len(draft.skills) > 0
    # Experience must survive
    assert len(draft.experience_entries) >= 1


def test_experiences_and_languages_coexist_when_techstack_section_present() -> None:
    """Techstack section between Languages and Experience must not disrupt either."""
    extracted_text = """
Alice Example
Backend Engineer

Languages
English C1
Russian C1
Turkish (Native)

Techstack & Skills
Python, Django, Flask, FastAPI, JS, React, CSS

Work Experience
Senior Backend Engineer | ACME | 2021 - Present

Education
Sakarya University | Bachelor of Computer Engineering | 2015 - 2019
"""
    draft = parse_cv_text_to_profile_draft(extracted_text)

    # Languages must be clean
    lang_names = {e.language_name.lower() for e in draft.language_entries}
    assert "english" in lang_names
    assert "russian" in lang_names
    assert "turkish" in lang_names
    for tech in ("python", "django", "flask", "fastapi", "js", "react", "css"):
        assert tech not in lang_names

    # Experience must be extracted
    assert len(draft.experience_entries) >= 1
    assert draft.experience_entries[0].title == "Senior Backend Engineer"


# ---------------------------------------------------------------------------
# is_valid_spoken_language public API
# ---------------------------------------------------------------------------

def test_is_valid_spoken_language_accepts_known_spoken_languages() -> None:
    for name in ("English", "Turkish", "German", "Russian", "French", "Spanish"):
        assert is_valid_spoken_language(name), f"{name!r} must be accepted"


def test_is_valid_spoken_language_rejects_tech_frameworks() -> None:
    for name in (
        "Python", "Django", "Flask", "FastAPI", "React", "React Native",
        "JavaScript", "CSS", "AWS", "Docker", "Ansible", "MATLAB",
        "Techstack & Skills", "Tech Stack", "Technologies", "Frameworks",
    ):
        assert not is_valid_spoken_language(name), f"{name!r} must be rejected"


def test_is_valid_spoken_language_rejects_none_and_empty() -> None:
    assert not is_valid_spoken_language(None)
    assert not is_valid_spoken_language("")
    assert not is_valid_spoken_language("   ")


def test_parse_cv_text_to_profile_draft_handles_two_column_ocr_resume_lab_layout() -> None:
    extracted_text = """
Cormac Turing
Mechanical Engineer
Detailed-oriented mechanical engineer with 10+ years of experience in planning, designing, and
developing state-of-the-art mechanical equipment. With XYZ Corp, optimized equipment layouts
and space requirements to increase efficiency by 16% in two quarters. Completed 4 projects with
budgets over $100,000. Seeking to join ABC Company to help deliver the upcoming projects on
time, 5-10% below budget, and within specifications.
Experience
2014 Senior Mechanical Engineer
present XYZ Corp, New York City, NY
• Supervised the procurement of work. Managed multi-disciplinary project teams
of 15+ colleagues.
2010 Mechanical Engineer
2013 Acme, Queens, NY
• Performed condition assessments of mechanical systems service of Acme's
physical assets, including plumbing, HVAC, electrical and other mechanical systems.
2007 Junior Engineering Assistant
2010 LMNO Company, New York City, NY
• Performed engineering design and redesign of plumbing, piping, fire protection systems.
Education
2008 BSc in Mechanical Engineering, MIT, Cambridge, MA

Personal Info
Phone
512-215-1256
E-mail
cormac.c.turing@gmail.com
LinkedIn
linkedin.com/in/cormaccturing11
Skills
3D CAD
00000
Pro-E CREO CAD
0000
Engineering Product Data
Management Software (EPDMS)
0000
Provide Cost Estimates for Materials,
Equipment, or Labor
Communication With Non-Technical
Clients and Colleagues
00000
Leadership
0000
Time-management
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.full_name == "Cormac Turing"
    assert draft.email == "cormac.c.turing@gmail.com"
    assert draft.phone == "512-215-1256"
    assert draft.linkedin_url == "https://linkedin.com/in/cormaccturing11"
    assert draft.summary is not None
    assert "within specifications" in draft.summary
    assert draft.preferred_locations == ()
    assert draft.skills == (
        "3D CAD",
        "Pro-E CREO CAD",
        "Engineering Product Data Management Software (EPDMS)",
        "Provide Cost Estimates for Materials, Equipment, or Labor",
        "Communication With Non-Technical Clients and Colleagues",
        "Leadership",
        "Time-management",
    )

    assert len(draft.experience_entries) == 3
    assert draft.experience_entries[0].title == "Senior Mechanical Engineer"
    assert draft.experience_entries[0].company_name == "XYZ Corp"
    assert draft.experience_entries[0].start_year == 2014
    assert draft.experience_entries[0].end_year is None
    assert draft.experience_entries[1].title == "Mechanical Engineer"
    assert draft.experience_entries[1].company_name == "Acme"
    assert draft.experience_entries[1].start_year == 2010
    assert draft.experience_entries[1].end_year == 2013
    assert draft.experience_entries[2].title == "Junior Engineering Assistant"
    assert draft.experience_entries[2].company_name == "LMNO Company"
    assert draft.experience_entries[2].start_year == 2007
    assert draft.experience_entries[2].end_year == 2010

    assert len(draft.education_entries) == 1
    assert draft.education_entries[0].school_name == "MIT"
    assert draft.education_entries[0].degree_name == "BSc"
    assert draft.education_entries[0].field_of_study == "Mechanical Engineering"
    assert draft.education_entries[0].start_year == 2008


def test_parse_turkish_two_column_ocr_text_extracts_experience_and_education() -> None:
    extracted_text = """
Leyla Aydin
Proje Mühendisi
0212 123 24 25
merhaba@harikasite.web.tr
Atatiirk Mah. Gazi Bulvan No: 12 Balikesir
www.harikasite.web.tr
PROFIL
QA/QC politikalarında deneyimli, karmaşık mühendislik projelerini kavramsallastırmadan
tamamlamaya kadar yönetme konusunda beş yılı aşkın deneyime sahip, sonuç odaklı proje
mühendisi. Standart Uyumluluk Ajansı tarafından akredite edilmiş lisanslı bir inşaat mühendisi.

İŞ DENEYİMİ
Proje Koordinatörü
Üst Düzey Mühendislik
2035-günümüz
+ Güvenlik ve performans standartlarına
uyumu sağlar
+ Karmaşık mühendislik projeleri
programlar geliştirir ve sürdürür
+ Telefon: 123-456-7890
Kidemli Miihendis
Mevcut İnşaatçılar
2032-2035
* 15 projeyi denetledi ve bir yıl içinde
tamamlanma oranında 9630 artış
+ Referans: Philippe Stolvan, Yönetici
« hello@reallygreatsite.com

EĞİTİM
Batı Eyalet Üniversitesi
Proje Mühendisliği Yüksek Lisansı
Haziran 2034
* Capstone Proje Mükemmellik Ödülü
* Yayınlanmış 2 Hakemli Araştırma
Makalesi
için Mezuniyet Konuşmacısı, 2034
Kuzey Şehir Koleji
İnşaat Mühendisliği Lisansı
Haziran 2030
* Dekan Listesi - 2026-2028
» Proje Mükemmellik Ödülü, 2029
* Öğrenci Konseyi Başkanı (2029-2030)
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.full_name == "Leyla Aydin"
    assert draft.email == "merhaba@harikasite.web.tr"
    assert draft.phone == "0212 123 24 25"
    assert draft.headline == "Proje Mühendisi"
    assert draft.target_roles == ("Proje Mühendisi",)
    assert draft.skills == ()
    assert draft.summary is not None
    assert "kavramsallaştırmadan" in draft.summary

    assert len(draft.experience_entries) == 2
    assert draft.experience_entries[0].title == "Proje Koordinatörü"
    assert draft.experience_entries[0].company_name == "Üst Düzey Mühendislik"
    assert draft.experience_entries[0].start_year == 2035
    assert draft.experience_entries[0].end_year is None
    assert "123-456-7890" not in (draft.experience_entries[0].summary or "")
    assert draft.experience_entries[1].title == "Kıdemli Mühendis"
    assert draft.experience_entries[1].company_name == "Mevcut İnşaatçılar"
    assert draft.experience_entries[1].start_year == 2032
    assert draft.experience_entries[1].end_year == 2035
    assert "hello@reallygreatsite.com" not in (draft.experience_entries[1].summary or "")
    assert "%30 artış" in (draft.experience_entries[1].summary or "")

    assert len(draft.education_entries) == 2
    assert draft.education_entries[0].school_name == "Batı Eyalet Üniversitesi"
    assert draft.education_entries[0].degree_name == "Proje Mühendisliği Yüksek Lisansı"
    assert draft.education_entries[0].start_year == 2034
    assert draft.education_entries[1].school_name == "Kuzey Şehir Koleji"
    assert draft.education_entries[1].degree_name == "İnşaat Mühendisliği Lisansı"
    assert draft.education_entries[1].start_year == 2030

def test_parse_turkish_ocr_compact_phone_formats_without_digit_guessing() -> None:
    extracted_text = """
Leyla Aydin
Proje Mühendisi
02121252425
merhaba@harikasite.web.tr
PROFIL
QA/QC politikalarında deneyimli proje mühendisi.
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.phone == "0212 125 24 25"



def test_parse_company_first_english_turkey_ocr_resume_layout() -> None:
    extracted_text = """
BULUT KARABULUT
PERSONAL INFORMATION
Date of Birth : August 25,1992
Address : Maslak Mah. Anka Sk. Bina No:5A Daire:199 Eclipse Maslak Sariyer/Istanbul
Phone Number : +90-530-443-0188
E-mail : bulutkarabulut © yandex.com
EDUCATION
Istanbul Technical University Istanbul, Turkey
Bachelor of Science in Mechanical Engineering September 201 1-June 2016
Mugla High School Of Science Mugla, Turkey
Mathematics September 2007-June 2011
WORK EXPERIENCE
Turkish Airlines Technic Inc. Istanbul, Turkey
Project Coordinator February 2018-
¢ Coordinating the C Checks projects of the Aircrafts according to the projects’ plan.
e Communicating with the customer airlines’ representatives about the project’s status.
¢ Provide communication between the Turkish Technic teams and the customer airlines.
Ersan Kaucuk Sanayi Tic. Inc. Istanbul, Turkey
Intern Engineer May 2016- June 2016
e CAD/CAM process of the materials ordered by international automotive industries.
® Manufacturing process of the materials drawn in CAD/CAM process.
© Quality control process of the manufactured materials.
Ekip Arac Ustu Ekipmanlari Mugla, Turkey
R&D, Manufacturing Intern Engineer June 2014-July 2014
Preparation of the special products ordered by customers.
Technical drawing of products and projects in research and development department.
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.full_name == "Bulut Karabulut"
    assert draft.email == "bulutkarabulut@yandex.com"
    assert draft.phone == "+90-530-443-0188"
    assert draft.headline == "Project Coordinator"
    assert draft.target_roles == ("Project Coordinator",)
    assert draft.skills == ()
    assert draft.preferred_locations == ()

    assert len(draft.education_entries) == 2
    assert draft.education_entries[0].school_name == "Istanbul Technical University"
    assert draft.education_entries[0].degree_name == "Bachelor of Science"
    assert draft.education_entries[0].field_of_study == "Mechanical Engineering"
    assert draft.education_entries[0].start_year == 2011
    assert draft.education_entries[0].end_year == 2016
    assert draft.education_entries[1].school_name == "Mugla High School Of Science"
    assert draft.education_entries[1].degree_name is None
    assert draft.education_entries[1].field_of_study == "Mathematics"
    assert draft.education_entries[1].start_year == 2007
    assert draft.education_entries[1].end_year == 2011

    assert len(draft.experience_entries) == 3
    first, second, third = draft.experience_entries
    assert first.company_name == "Turkish Airlines Technic Inc."
    assert first.title == "Project Coordinator"
    assert first.start_year == 2018
    assert first.end_year is None
    assert "Ersan Kaucuk" not in (first.summary or "")
    assert second.company_name == "Ersan Kaucuk Sanayi Tic. Inc."
    assert second.title == "Intern Engineer"
    assert second.start_year == 2016
    assert second.end_year == 2016
    assert "Ekip Arac" not in (second.summary or "")
    assert third.company_name == "Ekip Arac Ustu Ekipmanlari"
    assert third.title == "R&D, Manufacturing Intern Engineer"
    assert third.start_year == 2014
    assert third.end_year == 2014


def test_parse_text_pdf_engineering_cv_keeps_employment_out_of_education_and_skills() -> None:
    extracted_text = """
JOE BLOGGS
Apartment 2, Cobh, Co. Cork / Mob: 086 1234567 / E-mail: j.bloggs@yahoo.com

PROFILE
Professional qualified Electrical Engineer with experience in the Construction and Electronics
sectors. Possess excellent organisational and team-working skills.
Career objective: to develop a career within XXX.

EDUCATION
Bachelor of Electrical Engineering
1999 - 2003
Cork Institute of Technology (1 st Class Honours)

Final Year Subjects:
Applied Power Electronics & Motion, Digital Signal Processing , Electrical & Electronic Power
Systems, Telecommunications , Microwave Electronics, Control Engineering

Final Year Project
Team project which investigated X. Researched data, gained an in-depth knowledge of
telecommunications. Used C++ and LINUX Operating System. Prepared and delivered a
presentation to the lecturer and classmates.

Other Projects
Wrote programs in C, C++ and in VHDL code for digital signal processing. Implemented filters
using micro converter code. Built, tested and debugged circuits.
Leaving Certificate: 500 Points including an A1 in Honours Physics
1993 - 1999

RELEVANT EMPLOYMENT
Assistant Engineer - ABC Construction Contractors, Co. Galway
2003 - 2004
 Liaised with Engineers and reported to the Project Manager on all tasks.
 Conducted demolition work which included working with dangerous chemicals such as
asbestos.
 Completed survey work using laser instruments.
 Ensured health & safety procedures were adhered to and reported any breaches.

Trainee Engineer - Robinson Electronic Design Services, Co. Cork
2002 - 2003
 Reported to the Senior Engineer at the weekly team meeting.
 Assisted with the designing and building of web pages.
 Liaised with engineering staff on all aspects of web content relevant to the industry sector.
 Trained on Microsoft Front Page Editor for web design.

OTHER EMPLOYMENT
Information Assistant - Aura Gym, Fermoy
1999 - 2002
 Checked membership cards at the information desk.
 Provided assistance and information to customers.
 Collected money for aerobics and yoga classes.
 Managed special group bookings of facilities.

SKILLS
Technical:
Working knowledge of programming languages, C, C++. Highly
proficient at Access, Excel, Word & PowerPoint. Knowledge of
Matamatica and Electronics Workbench and experience of HTML,
VHDL and assembly code.
Presentation:
Produce reports and presentations to a professional standard.
Analysis & Evaluation:
Proficient in assessing data and formulating solutions.
Organisational:
Effective at time management and prioritising tasks to achieve
deadlines.
Communication:
Strong team working, leadership and communication skills.

INTERESTS & ACHIEVEMENTS
Travel:
Widespread travel through Australia and Asia during 2003-2004. This
included periods of travelling on my own.
REFERENCES
Available on request.
"""

    draft = parse_cv_text_to_profile_draft(extracted_text)

    assert draft.full_name == "Joe Bloggs"
    assert draft.email == "j.bloggs@yahoo.com"
    assert draft.phone == "086 1234567"
    assert draft.headline == "Electrical Engineer"
    assert draft.target_roles == ("Electrical Engineer",)
    assert draft.preferred_locations == ()

    assert len(draft.education_entries) == 2
    assert draft.education_entries[0].school_name == "Cork Institute of Technology (1 st Class Honours)"
    assert draft.education_entries[0].degree_name == "Bachelor"
    assert draft.education_entries[0].field_of_study == "Electrical Engineering"
    assert draft.education_entries[0].start_year == 1999
    assert draft.education_entries[0].end_year == 2003
    assert draft.education_entries[1].school_name == "Leaving Certificate: 500 Points including an A1 in Honours Physics"
    assert draft.education_entries[1].start_year == 1993
    assert draft.education_entries[1].end_year == 1999

    assert len(draft.experience_entries) == 3
    assert draft.experience_entries[0].title == "Assistant Engineer"
    assert draft.experience_entries[0].company_name == "ABC Construction Contractors, Co. Galway"
    assert draft.experience_entries[0].start_year == 2003
    assert draft.experience_entries[0].end_year == 2004
    assert "asbestos" in (draft.experience_entries[0].summary or "")
    assert draft.experience_entries[1].title == "Trainee Engineer"
    assert draft.experience_entries[2].title == "Information Assistant"

    assert "C++" in draft.skills
    assert "C" in draft.skills
    assert "Access" in draft.skills
    assert "Excel" in draft.skills
    assert "PowerPoint" in draft.skills
    assert "HTML" in draft.skills
    assert "VHDL" in draft.skills
    assert "INTERESTS & ACHIEVEMENTS" not in draft.skills
    assert "Available on request." not in draft.skills
    assert draft.certification_entries == ()
