from __future__ import annotations

from hiring_radar.models import SubscriberCvUpload
from hiring_radar.services.cv_extraction import CV_PARSE_STATUS_PARSED
from hiring_radar.services.cv_parse_pipeline import (
    build_cv_profile_draft_snapshot_from_cv_upload,
)
from hiring_radar.services.cv_profile_parser import HEURISTIC_CV_PARSER_VERSION


def test_build_cv_profile_draft_snapshot_from_cv_upload_uses_v2_bridge_contract() -> None:
    cv_upload = SubscriberCvUpload(
        id=21,
        subscriber_id=4,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=128_000,
        extracted_text="""
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Professional Summary
Backend engineer with strong FastAPI and distributed systems experience.

Technical Skills
Python, FastAPI, SQL

Work Experience
Senior Backend Engineer | ACME | 2021 - Present
Built matching systems.
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-07T10:00:00Z",
        parsed_at="2026-04-07T10:01:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)

    assert snapshot.source_upload_id == 21
    assert snapshot.source_filename == "alice_cv.pdf"
    assert snapshot.source_parse_status == CV_PARSE_STATUS_PARSED
    assert snapshot.generated_at == "2026-04-07T10:01:00Z"
    assert snapshot.parser_version == HEURISTIC_CV_PARSER_VERSION
    assert snapshot.draft.headline == "Senior Backend Engineer"
    assert snapshot.draft.skills == ("Python", "FastAPI", "SQL")
    assert len(snapshot.draft.experience_entries) == 1


def test_build_cv_profile_draft_snapshot_from_cv_upload_falls_back_when_bridge_fails(
    monkeypatch,
) -> None:
    cv_upload = SubscriberCvUpload(
        id=22,
        subscriber_id=4,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=128_000,
        extracted_text="""
Alice Example
Senior Backend Engineer

Technical Skills
Python, FastAPI, SQL
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-07T10:10:00Z",
        parsed_at="2026-04-07T10:11:00Z",
    )

    monkeypatch.setattr(
        "hiring_radar.services.cv_parse_pipeline.build_foundation_parser_result_from_text",
        lambda **_: (_ for _ in ()).throw(RuntimeError("bridge failed")),
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)

    assert snapshot.parser_version == HEURISTIC_CV_PARSER_VERSION
    assert snapshot.generated_at == "2026-04-07T10:11:00Z"
    assert snapshot.draft.headline == "Senior Backend Engineer"
    assert snapshot.draft.skills == ("Python", "FastAPI", "SQL")



def test_build_cv_profile_draft_snapshot_from_cv_upload_handles_german_dates_via_v2_bridge() -> None:
    cv_upload = SubscriberCvUpload(
        id=23,
        subscriber_id=4,
        original_filename="anna_cv.pdf",
        storage_path="uploads/cv/anna_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=128_000,
        extracted_text="""
Anna Beispiel
Senior Software Engineer
anna@example.com | Berlin | Hybrid

Berufserfahrung
Senior Software Engineer
Beispiel GmbH
Januar 2020 - Heute
Verantwortlich für APIs.

Fähigkeiten
Python, FastAPI
""",
        parse_status=CV_PARSE_STATUS_PARSED,
        uploaded_at="2026-04-07T10:20:00Z",
        parsed_at="2026-04-07T10:21:00Z",
    )

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)

    assert snapshot.draft.headline == "Senior Software Engineer"
    assert snapshot.draft.skills == ("Python", "FastAPI")
    assert len(snapshot.draft.experience_entries) == 1
    assert snapshot.draft.experience_entries[0].company_name == "Beispiel GmbH"
    assert snapshot.draft.experience_entries[0].start_year == 2020
    assert snapshot.draft.experience_entries[0].end_year is None
