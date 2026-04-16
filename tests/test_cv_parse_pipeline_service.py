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