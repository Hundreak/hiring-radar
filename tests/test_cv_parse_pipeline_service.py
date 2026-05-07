from __future__ import annotations

from hiring_radar.models import SubscriberCvUpload
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_FAILED,
    CV_PARSE_STATUS_PARSED,
)
from hiring_radar.services.cv_parse_pipeline import (
    build_cv_profile_draft_snapshot_from_cv_upload,
    cv_profile_draft_snapshot_from_json,
    cv_profile_draft_snapshot_to_dict,
    cv_profile_draft_snapshot_to_json,
)
from hiring_radar.services.cv_profile_draft import CvProfileDraft
from hiring_radar.services.cv_profile_parser import HEURISTIC_CV_PARSER_VERSION


def test_build_cv_profile_draft_snapshot_from_parsed_upload_builds_draft() -> None:
    cv_upload = SubscriberCvUpload(
        id=7,
        subscriber_id=1,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=120_000,
        extracted_text="""
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Professional Summary
Backend engineer with strong FastAPI and distributed systems experience.

Technical Skills
Python, FastAPI, SQL

Desired Position
Staff Backend Engineer

Work Experience
Senior Backend Engineer | ACME | 2021 - Present

Education
METU | BSc Electrical Engineering | 2012 - 2017

Languages
English - C1
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-06T12:00:00Z",
        parsed_at="2026-04-06T12:01:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)

    assert snapshot.source_upload_id == 7
    assert snapshot.source_filename == "alice_cv.pdf"
    assert snapshot.source_parse_status == CV_PARSE_STATUS_PARSED
    assert snapshot.parser_version == HEURISTIC_CV_PARSER_VERSION
    assert snapshot.generated_at == "2026-04-06T12:01:00Z"

    assert snapshot.draft.headline == "Senior Backend Engineer"
    assert snapshot.draft.phone is None
    assert "FastAPI" in (snapshot.draft.summary or "")
    assert snapshot.draft.skills == ("Python", "FastAPI", "SQL")
    assert snapshot.draft.target_roles == ("Staff Backend Engineer",)
    assert snapshot.draft.preferred_locations == ("Berlin",)
    assert snapshot.draft.remote_preference == "remote"
    assert len(snapshot.draft.experience_entries) == 1
    assert len(snapshot.draft.education_entries) == 1
    assert len(snapshot.draft.language_entries) == 1


def test_build_cv_profile_draft_snapshot_from_failed_upload_returns_empty_draft() -> None:
    cv_upload = SubscriberCvUpload(
        id=8,
        subscriber_id=1,
        original_filename="broken_cv.pdf",
        storage_path="uploads/cv/broken_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=64_000,
        extracted_text=None,
        parse_status=CV_PARSE_STATUS_FAILED,
        uploaded_at="2026-04-06T12:05:00Z",
        parsed_at="2026-04-06T12:06:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)

    assert snapshot.source_upload_id == 8
    assert snapshot.source_filename == "broken_cv.pdf"
    assert snapshot.source_parse_status == CV_PARSE_STATUS_FAILED
    assert snapshot.parser_version is None
    assert snapshot.generated_at == "2026-04-06T12:06:00Z"
    assert snapshot.draft == CvProfileDraft()


def test_cv_profile_draft_snapshot_to_dict_serializes_json_ready_payload() -> None:
    cv_upload = SubscriberCvUpload(
        id=9,
        subscriber_id=1,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=120_000,
        extracted_text="""
Alice Example
Senior Backend Engineer

Technical Skills
Python, FastAPI, SQL
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-06T12:10:00Z",
        parsed_at="2026-04-06T12:11:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)
    payload = cv_profile_draft_snapshot_to_dict(snapshot)

    assert payload["generated_at"] == "2026-04-06T12:11:00Z"
    assert payload["source_upload_id"] == 9
    assert payload["source_filename"] == "alice_cv.pdf"
    assert payload["source_parse_status"] == CV_PARSE_STATUS_PARSED
    assert payload["parser_version"] == HEURISTIC_CV_PARSER_VERSION

    draft_payload = payload["draft"]
    assert draft_payload["headline"] == "Senior Backend Engineer"
    assert draft_payload["skills"] == ["Python", "FastAPI", "SQL"]
    assert draft_payload["experience_entries"] == []
    assert draft_payload["education_entries"] == []
    assert draft_payload["language_entries"] == []
    assert draft_payload["certification_entries"] == []


def test_cv_profile_draft_snapshot_json_roundtrip_restores_snapshot() -> None:
    cv_upload = SubscriberCvUpload(
        id=10,
        subscriber_id=1,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=120_000,
        extracted_text="""
Alice Example
Senior Backend Engineer

Technical Skills
Python, FastAPI, SQL
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-06T12:10:00Z",
        parsed_at="2026-04-06T12:11:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)
    restored = cv_profile_draft_snapshot_from_json(
        cv_profile_draft_snapshot_to_json(snapshot)
    )

    assert restored.generated_at == snapshot.generated_at
    assert restored.source_upload_id == snapshot.source_upload_id
    assert restored.source_filename == snapshot.source_filename
    assert restored.source_parse_status == snapshot.source_parse_status
    assert restored.parser_version == snapshot.parser_version
    assert restored.draft.headline == snapshot.draft.headline
    assert restored.draft.skills == snapshot.draft.skills
    assert restored.draft.certification_entries == snapshot.draft.certification_entries

def test_build_cv_profile_draft_snapshot_extracts_wrapped_certifications() -> None:
    cv_upload = SubscriberCvUpload(
        id=11,
        subscriber_id=1,
        original_filename="cert_cv.png",
        storage_path="uploads/cv/cert_cv.png",
        content_type="image/png",
        file_size_bytes=120_000,
        extracted_text="""
Cormac Turing
Mechanical Engineer
cormac@example.com

Experience
2014 Senior Mechanical Engineer
present XYZ Corp

Education
2008 BSc in Mechanical Engineering, MIT, Cambridge, MA

Certificates
2018 Geometric Dimensioning & Tolerancing Professional, American Society of
Mechanical Engineers International
2013 Certified Reliability Engineer, American Society for Quality

Skills
3D CAD
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-06T12:20:00Z",
        parsed_at="2026-04-06T12:21:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(
        cv_upload,
        ai_structuring_mode="off",
    )

    assert len(snapshot.draft.certification_entries) == 2
    first, second = snapshot.draft.certification_entries
    assert first.issued_year == 2018
    assert first.certificate_name == "Geometric Dimensioning & Tolerancing Professional"
    assert first.issuer_name == "American Society of Mechanical Engineers International"
    assert second.issued_year == 2013
    assert second.certificate_name == "Certified Reliability Engineer"
    assert second.issuer_name == "American Society for Quality"


def test_ollama_merge_preserves_deterministic_phone_and_filters_summary_skills(monkeypatch) -> None:
    from hiring_radar.services.cv_ocr_structuring import OcrStructuringResult
    from hiring_radar.services.cv_profile_draft import build_cv_profile_draft

    cv_upload = SubscriberCvUpload(
        id=12,
        subscriber_id=1,
        original_filename="leyla_cv.webp",
        storage_path="uploads/cv/leyla_cv.webp",
        content_type="image/webp",
        file_size_bytes=45_000,
        extracted_text="""
Leyla Aydin
Proje Mühendisi
0212 123 24 25
merhaba@harikasite.web.tr
PROFIL
QA/QC politikalarında deneyimli, karmaşık mühendislik projelerini kavramsallastırmadan
mühendisi. Standart Uyumluluk Ajansı tarafından akredite edilmiş lisanslı bir inşaat mühendisi.

İŞ DENEYİMİ
Proje Koordinatörü
Üst Düzey Mühendislik
2035-günümüz
+ Güvenlik ve performans standartlarına uyumu sağlar

EĞİTİM
Batı Eyalet Üniversitesi
Proje Mühendisliği Yüksek Lisansı
Haziran 2034
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-06T12:20:00Z",
        parsed_at="2026-04-06T12:21:00Z",
    )

    def fake_ollama_structuring(_text: str):
        return OcrStructuringResult(
            draft=build_cv_profile_draft(
                phone="+2121252425",
                skills=["Standart Uyumluluk Ajansı", "Lisanslı İnşaat Mühendisi"],
                target_roles=["Proje Mühendisi"],
            ),
            model="fake",
            response_time_ms=1,
        )

    monkeypatch.setattr(
        "hiring_radar.services.cv_ocr_structuring.extract_cv_structure_with_ollama",
        fake_ollama_structuring,
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(
        cv_upload,
        ai_structuring_mode="all",
    )

    assert snapshot.draft.phone == "0212 123 24 25"
    assert snapshot.draft.skills == ()


def test_cv_snapshot_reconciles_v2_bridge_with_heuristic_ocr_repairs() -> None:
    cv_upload = SubscriberCvUpload(
        id=13,
        subscriber_id=1,
        original_filename="bulut_cv.webp",
        storage_path="uploads/cv/bulut_cv.webp",
        content_type="image/webp",
        file_size_bytes=52_000,
        extracted_text="""
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
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-06T12:20:00Z",
        parsed_at="2026-04-06T12:21:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(
        cv_upload,
        ai_structuring_mode="off",
    )

    assert snapshot.draft.email == "bulutkarabulut@yandex.com"
    assert snapshot.draft.headline == "Project Coordinator"
    assert snapshot.draft.target_roles == ("Project Coordinator",)
    assert snapshot.draft.skills == ()
    assert snapshot.draft.preferred_locations == ()
    assert len(snapshot.draft.education_entries) == 2
    assert snapshot.draft.education_entries[0].school_name == "Istanbul Technical University"
    assert len(snapshot.draft.experience_entries) == 3
    assert snapshot.draft.experience_entries[1].company_name == "Ersan Kaucuk Sanayi Tic. Inc."


def test_pipeline_prefers_clean_heuristic_text_pdf_sections_over_contaminated_v2_lists() -> None:
    cv_upload = SubscriberCvUpload(
        id=31,
        subscriber_id=1,
        original_filename="sample_engineering_cv.pdf",
        storage_path="uploads/cv/sample_engineering_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=164_698,
        extracted_text="""
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
Final Year Project
Team project which investigated X. Used C++ and LINUX Operating System.
Other Projects
Wrote programs in C, C++ and in VHDL code for digital signal processing.
Leaving Certificate: 500 Points including an A1 in Honours Physics
1993 - 1999
RELEVANT EMPLOYMENT
Assistant Engineer - ABC Construction Contractors, Co. Galway
2003 - 2004
 Liaised with Engineers and reported to the Project Manager on all tasks.
Trainee Engineer - Robinson Electronic Design Services, Co. Cork
2002 - 2003
 Assisted with the designing and building of web pages.
OTHER EMPLOYMENT
Information Assistant - Aura Gym, Fermoy
1999 - 2002
 Checked membership cards at the information desk.
SKILLS
Technical:
Working knowledge of programming languages, C, C++. Highly
proficient at Access, Excel, Word & PowerPoint. Knowledge of
Matamatica and Electronics Workbench and experience of HTML,
VHDL and assembly code.
INTERESTS & ACHIEVEMENTS
Travel:
Widespread travel through Australia and Asia during 2003-2004.
REFERENCES
Available on request.
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-06T12:30:00Z",
        parsed_at="2026-04-06T12:31:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(
        cv_upload,
        ai_structuring_mode="auto",
    )

    draft = snapshot.draft
    assert draft.full_name == "Joe Bloggs"
    assert draft.headline == "Electrical Engineer"
    assert len(draft.education_entries) == 2
    assert len(draft.experience_entries) == 3
    assert draft.certification_entries == ()
    assert "INTERESTS & ACHIEVEMENTS" not in draft.skills
    assert "Available on request." not in draft.skills


def test_merge_prefers_heuristic_when_v2_text_pdf_lists_are_contaminated() -> None:
    from hiring_radar.services.cv_parse_pipeline import _merge_v2_and_heuristic_drafts
    from hiring_radar.services.cv_profile_draft import (
        build_cv_draft_certification_entry,
        build_cv_draft_education_entry,
        build_cv_draft_experience_entry,
        build_cv_profile_draft,
    )

    v2_draft = build_cv_profile_draft(
        full_name="Joe Bloggs",
        email="j.bloggs@yahoo.com",
        phone="086 1234567",
        headline="Electrical Engineer",
        skills=(
            "Working knowledge of programming languages, C, C++. Highly",
            "proficient at Access, Excel, Word & PowerPoint. Knowledge of",
            "Matamatica and Electronics Workbench and experience of HTML, VHDL and assembly code.",
            "Effective at time management and prioritising tasks to achieve",
            "deadlines.",
        ),
        education_entries=(
            build_cv_draft_education_entry(
                school_name="Bachelor of Electrical Engineering",
                start_year=1999,
                end_year=2003,
            ),
            build_cv_draft_education_entry(
                school_name="Leaving Certificate: 500 Points including an A1 in Honours Physics",
                start_year=1993,
                end_year=1999,
            ),
            build_cv_draft_education_entry(
                school_name="Leaving Certificate: 500 Points including an A1 in Honours Physics 1993 - 1999",
                start_year=1993,
                end_year=1999,
            ),
        ),
        experience_entries=(
            build_cv_draft_experience_entry(
                title=" Liaised with Engineers and reported to the Project Manager on all tasks.",
                company_name="Assistant Engineer - ABC Construction Contractors, Co. Galway 2003 - 2004",
                start_year=2003,
            ),
            build_cv_draft_experience_entry(
                title=" Reported to the Senior Engineer at the weekly team meeting.",
                company_name="Trainee Engineer - Robinson Electronic Design Services, Co. Cork 2002 - 2003",
                start_year=2002,
            ),
            build_cv_draft_experience_entry(
                title="Information Assistant - Aura Gym, Fermoy 1999 - 2002",
                company_name=" Checked membership cards at the information desk.",
                start_year=1999,
            ),
        ),
        certification_entries=(
            build_cv_draft_certification_entry(
                certificate_name="Leaving Certificate: 500 Points including an A1 in Honours Physics 1993 - 1999",
            ),
        ),
    )
    heuristic_draft = build_cv_profile_draft(
        full_name="Joe Bloggs",
        email="j.bloggs@yahoo.com",
        phone="086 1234567",
        headline="Electrical Engineer",
        skills=("C++", "C", "Access", "Excel", "Word", "PowerPoint", "Mathematica", "HTML", "VHDL"),
        education_entries=(
            build_cv_draft_education_entry(
                school_name="Cork Institute of Technology (1 st Class Honours)",
                degree_name="Bachelor",
                field_of_study="Electrical Engineering",
                start_year=1999,
                end_year=2003,
            ),
            build_cv_draft_education_entry(
                school_name="Leaving Certificate: 500 Points including an A1 in Honours Physics",
                start_year=1993,
                end_year=1999,
            ),
        ),
        experience_entries=(
            build_cv_draft_experience_entry(
                title="Assistant Engineer",
                company_name="ABC Construction Contractors, Co. Galway",
                start_year=2003,
                end_year=2004,
            ),
            build_cv_draft_experience_entry(
                title="Trainee Engineer",
                company_name="Robinson Electronic Design Services, Co. Cork",
                start_year=2002,
                end_year=2003,
            ),
            build_cv_draft_experience_entry(
                title="Information Assistant",
                company_name="Aura Gym, Fermoy",
                start_year=1999,
                end_year=2002,
            ),
        ),
    )

    merged = _merge_v2_and_heuristic_drafts(v2_draft, heuristic_draft)

    assert merged.skills == heuristic_draft.skills
    assert merged.education_entries == heuristic_draft.education_entries
    assert merged.experience_entries == heuristic_draft.experience_entries
    assert merged.certification_entries == ()
