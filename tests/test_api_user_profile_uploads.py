from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.routers import user_profile
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_PARSED,
    CvExtractionError,
    CvExtractionResult,
)
from hiring_radar.services.cv_profile_apply_execution import (
    CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED,
)
from hiring_radar.services.cv_profile_parser import HEURISTIC_CV_PARSER_VERSION
from hiring_radar.services.user_auth import UserSession


def _make_user_session(subscriber_id: int) -> UserSession:
    return UserSession(
        subscriber_id=subscriber_id,
        email="alice@example.com",
        issued_at="2026-04-05T10:00:00Z",
        expires_at="2026-04-05T12:00:00Z",
    )


def _resolve_upload_path(upload_root: Path, stored_path: str | None) -> Path:
    if not stored_path:
        raise AssertionError("Expected a stored file path, but none was saved.")

    path = Path(stored_path)
    if path.is_absolute():
        return path

    return upload_root / path


def _build_authed_client(
    tmp_path: Path,
    *,
    db_filename: str,
) -> tuple[TestClient, HiringRadarRepository, object, int]:
    connection = initialize_database(str(tmp_path / db_filename))
    repo = HiringRadarRepository(connection)
    subscriber, _ = repo.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-05T10:00:00Z",
    )
    subscriber_id = subscriber.id or 0

    app = create_app()
    app.dependency_overrides[get_current_user_session] = lambda: _make_user_session(
        subscriber_id
    )
    app.dependency_overrides[get_repository] = lambda: repo

    return TestClient(app), repo, connection, subscriber_id


def _assert_extraction_metadata(
    payload: dict[str, Any],
    *,
    file_format: str,
    extraction_method: str,
    uses_ocr: bool,
    parse_status_detail: str,
) -> None:
    extraction_metadata = payload["extraction_metadata"]
    assert extraction_metadata["file_format"] == file_format
    assert extraction_metadata["extraction_method"] == extraction_method
    assert extraction_metadata["uses_ocr"] is uses_ocr
    assert extraction_metadata["parse_status_detail"] == parse_status_detail



def _assert_extraction_operator_flags(
    payload: dict[str, Any],
    *,
    needs_manual_review: bool,
    is_safe_for_default_apply: bool,
    fallback_reason: str | None,
    recommended_next_action: str,
) -> None:
    extraction_metadata = payload["extraction_metadata"]
    assert extraction_metadata["needs_manual_review"] is needs_manual_review
    assert (
        extraction_metadata["is_safe_for_default_apply"]
        is is_safe_for_default_apply
    )
    assert extraction_metadata["fallback_reason"] == fallback_reason
    assert (
        extraction_metadata["recommended_next_action"]
        == recommended_next_action
    )



def _field_review_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["field_name"]: item for item in payload["field_review"]}


def test_upload_user_cv_persists_metadata_and_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads.db",
    )

    extracted_cv_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Professional Summary
Backend engineer with strong FastAPI and distributed systems experience.

Technical Skills
Python, FastAPI, SQL
"""

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            lambda _file_path: CvExtractionResult(
                extracted_text=extracted_cv_text,
                parse_status=CV_PARSE_STATUS_PARSED,
                page_count=1,
            ),
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "alice_cv.pdf",
                    b"%PDF-1.4 example cv bytes",
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        payload = response.json()

        assert payload["original_filename"] == "alice_cv.pdf"
        assert payload["content_type"] == "application/pdf"
        assert payload["parse_status"] == "parsed"
        assert payload["parsed_at"] is not None

        _assert_extraction_metadata(
            payload,
            file_format="pdf",
            extraction_method="pdf_text",
            uses_ocr=False,
            parse_status_detail="pdf_text_extracted",
        )

        _assert_extraction_operator_flags(
            payload,
            needs_manual_review=False,
            is_safe_for_default_apply=True,
            fallback_reason=None,
            recommended_next_action="safe_to_apply",
        )

        assert payload["extraction_metadata"]["extraction_quality"] == "medium"
        assert payload["extraction_metadata"]["review_hints"] == [
            "medium_text_volume"
        ]

        uploads = repo.list_subscriber_cv_uploads(subscriber_id)
        assert len(uploads) == 1
        assert uploads[0].id is not None
        assert uploads[0].original_filename == "alice_cv.pdf"
        assert uploads[0].content_type == "application/pdf"
        assert uploads[0].parse_status == "parsed"
        assert uploads[0].parsed_at is not None
        assert uploads[0].extracted_text == extracted_cv_text

        parse_runs = repo.list_subscriber_cv_parse_runs_for_upload(uploads[0].id or 0)
        assert len(parse_runs) == 1
        assert parse_runs[0].parser_version == HEURISTIC_CV_PARSER_VERSION
        assert parse_runs[0].source_parse_status == "parsed"

        snapshot_payload = json.loads(parse_runs[0].snapshot_json)
        assert snapshot_payload["source_filename"] == "alice_cv.pdf"
        assert snapshot_payload["source_parse_status"] == "parsed"
        assert snapshot_payload["parser_version"] == HEURISTIC_CV_PARSER_VERSION
        assert snapshot_payload["draft"]["headline"] == "Senior Backend Engineer"
        assert snapshot_payload["draft"]["skills"] == ["Python", "FastAPI", "SQL"]

        stored_path = _resolve_upload_path(upload_root, uploads[0].storage_path)
        assert stored_path.exists()
        assert stored_path.read_bytes() == b"%PDF-1.4 example cv bytes"

        profile = repo.get_subscriber_profile(subscriber_id)
        assert profile.cv_filename == "alice_cv.pdf"
        assert profile.cv_uploaded_at is not None

        profile_response = client.get("/api/user/profile")
        assert profile_response.status_code == 200

        latest_cv_upload = profile_response.json()["latest_cv_upload"]
        assert latest_cv_upload["original_filename"] == "alice_cv.pdf"

        _assert_extraction_operator_flags(
            latest_cv_upload,
            needs_manual_review=False,
            is_safe_for_default_apply=True,
            fallback_reason=None,
            recommended_next_action="safe_to_apply",
        )

        assert latest_cv_upload["extraction_metadata"]["extraction_quality"] == "medium"
        assert latest_cv_upload["extraction_metadata"]["review_hints"] == [
            "medium_text_volume"
        ]

        _assert_extraction_metadata(
            latest_cv_upload,
            file_format="pdf",
            extraction_method="pdf_text",
            uses_ocr=False,
            parse_status_detail="pdf_text_extracted",
        )
    finally:
        close_connection(connection)


def test_upload_user_cv_accepts_png_and_persists_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads_png.db",
    )

    extracted_cv_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Technical Skills
Python, FastAPI, SQL
"""

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            lambda _file_path: CvExtractionResult(
                extracted_text=extracted_cv_text,
                parse_status=CV_PARSE_STATUS_PARSED,
                page_count=1,
            ),
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "alice_cv.png",
                    b"\x89PNG\r\n\x1a\nfake-image-bytes",
                    "image/png",
                )
            },
        )

        assert response.status_code == 200
        payload = response.json()

        assert payload["original_filename"] == "alice_cv.png"
        assert payload["content_type"] == "image/png"
        assert payload["parse_status"] == "parsed"

        _assert_extraction_metadata(
            payload,
            file_format="png",
            extraction_method="image_ocr",
            uses_ocr=True,
            parse_status_detail="ocr_text_extracted",
        )

        _assert_extraction_operator_flags(
            payload,
            needs_manual_review=True,
            is_safe_for_default_apply=False,
            fallback_reason="low_quality_ocr",
            recommended_next_action="reupload_as_document",
        )

        assert payload["extraction_metadata"]["extraction_quality"] == "low"
        assert payload["extraction_metadata"]["review_hints"] == [
            "ocr_source",
            "low_text_volume",
            "manual_review_recommended",
        ]

        uploads = repo.list_subscriber_cv_uploads(subscriber_id)
        assert len(uploads) == 1
        assert uploads[0].original_filename == "alice_cv.png"
        assert uploads[0].content_type == "image/png"
        assert uploads[0].parse_status == "parsed"
        assert uploads[0].extracted_text == extracted_cv_text

        parse_runs = repo.list_subscriber_cv_parse_runs_for_upload(uploads[0].id or 0)
        assert len(parse_runs) == 1
        snapshot_payload = json.loads(parse_runs[0].snapshot_json)
        assert snapshot_payload["source_filename"] == "alice_cv.png"
        assert snapshot_payload["draft"]["headline"] == "Senior Backend Engineer"

        stored_path = _resolve_upload_path(upload_root, uploads[0].storage_path)
        assert stored_path.exists()
        assert stored_path.read_bytes() == b"\x89PNG\r\n\x1a\nfake-image-bytes"

        profile_response = client.get("/api/user/profile")
        assert profile_response.status_code == 200

        latest_cv_upload = profile_response.json()["latest_cv_upload"]
        assert latest_cv_upload["original_filename"] == "alice_cv.png"

        _assert_extraction_operator_flags(
            latest_cv_upload,
            needs_manual_review=True,
            is_safe_for_default_apply=False,
            fallback_reason="low_quality_ocr",
            recommended_next_action="reupload_as_document",
        )

        assert latest_cv_upload["extraction_metadata"]["extraction_quality"] == "low"
        assert latest_cv_upload["extraction_metadata"]["review_hints"] == [
            "ocr_source",
            "low_text_volume",
            "manual_review_recommended",
        ]

        _assert_extraction_metadata(
            latest_cv_upload,
            file_format="png",
            extraction_method="image_ocr",
            uses_ocr=True,
            parse_status_detail="ocr_text_extracted",
        )
    finally:
        close_connection(connection)

def test_upload_language_certificate_persists_metadata_and_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="language_certificate_uploads.db",
    )

    try:
        response = client.post(
            "/api/user/profile/upload/language-certificate",
            data={
                "certificate_name": "IELTS Academic",
                "issuer_name": "British Council",
            },
            files={
                "file": (
                    "ielts.pdf",
                    b"%PDF-1.4 example certificate bytes",
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["certificate_name"] == "IELTS Academic"
        assert payload["issuer_name"] == "British Council"
        assert payload["file_name"] == "ielts.pdf"

        certificates = repo.list_subscriber_language_certificates(subscriber_id)
        assert len(certificates) == 1
        assert certificates[0].certificate_name == "IELTS Academic"

        stored_path = _resolve_upload_path(upload_root, certificates[0].storage_path)
        assert stored_path.exists()
        assert stored_path.read_bytes() == b"%PDF-1.4 example certificate bytes"
    finally:
        close_connection(connection)



def test_upload_user_cv_marks_parse_failed_when_extraction_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads_failed.db",
    )

    try:
        def _raise_extraction_error(_file_path: Path) -> CvExtractionResult:
            raise CvExtractionError("unable to parse pdf")

        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            _raise_extraction_error,
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "alice_cv.pdf",
                    b"%PDF-1.4 broken cv bytes",
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["parse_status"] == "failed"
        assert payload["parsed_at"] is not None

        _assert_extraction_metadata(
            payload,
            file_format="pdf",
            extraction_method="pdf_text",
            uses_ocr=False,
            parse_status_detail="extraction_failed",
        )

        _assert_extraction_operator_flags(
            payload,
            needs_manual_review=True,
            is_safe_for_default_apply=False,
            fallback_reason="extraction_failed",
            recommended_next_action="reupload_or_edit_manually",
        )

        assert payload["extraction_metadata"]["extraction_quality"] == "low"
        assert payload["extraction_metadata"]["review_hints"] == ["extraction_failed"]

        uploads = repo.list_subscriber_cv_uploads(subscriber_id)
        assert len(uploads) == 1
        assert uploads[0].id is not None
        assert uploads[0].parse_status == "failed"
        assert uploads[0].parsed_at is not None
        assert uploads[0].extracted_text is None

        parse_runs = repo.list_subscriber_cv_parse_runs_for_upload(uploads[0].id or 0)
        assert len(parse_runs) == 1
        assert parse_runs[0].parser_version is None
        assert parse_runs[0].source_parse_status == "failed"

        snapshot_payload = json.loads(parse_runs[0].snapshot_json)
        assert snapshot_payload["source_filename"] == "alice_cv.pdf"
        assert snapshot_payload["source_parse_status"] == "failed"
        assert snapshot_payload["parser_version"] is None
        assert snapshot_payload["draft"]["headline"] is None
        assert snapshot_payload["draft"]["skills"] == []

        stored_path = _resolve_upload_path(upload_root, uploads[0].storage_path)
        assert stored_path.exists()

        profile_response = client.get("/api/user/profile")
        assert profile_response.status_code == 200

        latest_cv_upload = profile_response.json()["latest_cv_upload"]

        _assert_extraction_operator_flags(
            latest_cv_upload,
            needs_manual_review=True,
            is_safe_for_default_apply=False,
            fallback_reason="extraction_failed",
            recommended_next_action="reupload_or_edit_manually",
        )

        assert latest_cv_upload["extraction_metadata"]["extraction_quality"] == "low"
        assert latest_cv_upload["extraction_metadata"]["review_hints"] == [
            "extraction_failed"
        ]

        _assert_extraction_metadata(
            latest_cv_upload,
            file_format="pdf",
            extraction_method="pdf_text",
            uses_ocr=False,
            parse_status_detail="extraction_failed",
        )
    finally:
        close_connection(connection)



def test_get_latest_user_cv_parse_snapshot_returns_none_when_missing(
    tmp_path: Path,
) -> None:
    client, _repo, connection, _subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_parse_snapshot_none.db",
    )

    try:
        response = client.get("/api/user/profile/cv/latest-parse")

        assert response.status_code == 200
        assert response.json() is None
    finally:
        close_connection(connection)


def test_get_latest_user_cv_parse_snapshot_returns_latest_snapshot(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_parse_snapshot.db",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text="Alice Example\nSenior Backend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-06T14:21:00Z",
        parsed_at="2026-04-06T14:22:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    latest_parse_run = repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T14:22:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.pdf",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Senior Backend Engineer",
                    "summary": "Backend engineer with strong FastAPI experience.",
                    "skills": ["Python", "FastAPI", "SQL"],
                    "target_roles": ["Staff Backend Engineer"],
                    "preferred_locations": ["Berlin"],
                    "remote_preference": "remote",
                    "education_entries": [
                        {
                            "school_name": "METU",
                            "degree_name": "BSc Electrical Engineering",
                            "field_of_study": None,
                            "start_year": 2012,
                            "end_year": 2017,
                        }
                    ],
                    "experience_entries": [
                        {
                            "title": "Senior Backend Engineer",
                            "company_name": "ACME",
                            "start_year": 2021,
                            "end_year": None,
                            "summary": "Built matching systems.",
                        }
                    ],
                    "language_entries": [
                        {
                            "language_name": "English",
                            "proficiency_level": "C1",
                            "notes": None,
                        }
                    ],
                },
            }
        ),
        created_at="2026-04-06T14:22:00Z",
    )

    try:
        response = client.get("/api/user/profile/cv/latest-parse")

        assert response.status_code == 200
        payload = response.json()

        extraction_metadata = payload["extraction_metadata"]
        assert extraction_metadata["file_format"] == "pdf"
        assert extraction_metadata["extraction_method"] == "pdf_text"
        assert extraction_metadata["uses_ocr"] is False
        assert extraction_metadata["parse_status_detail"] == "pdf_text_extracted"
        assert extraction_metadata["extraction_quality"] == "medium"
        assert extraction_metadata["review_hints"] == ["medium_text_volume"]

        assert extraction_metadata["needs_manual_review"] is False
        assert extraction_metadata["is_safe_for_default_apply"] is True
        assert extraction_metadata["fallback_reason"] is None
        assert extraction_metadata["recommended_next_action"] == "safe_to_apply"

        review_summary = payload["review_summary"]
        assert review_summary == {
            "total_field_count": 9,
            "safe_field_count": 4,
            "review_recommended_count": 5,
            "review_required_count": 0,
            "highest_severity": "review_recommended",
            "focus_field_names": [
                "summary",
                "skills",
                "preferred_locations",
                "remote_preference",
                "language_entries",
            ],
            "manual_review_flow": False,
        }

        field_review = _field_review_by_name(payload)
        assert field_review["headline"]["severity"] == "safe"
        assert field_review["headline"]["reason_codes"] == [
            "high_confidence",
            "medium_text_volume",
        ]
        assert field_review["summary"]["severity"] == "review_recommended"
        assert field_review["summary"]["reason_codes"] == [
            "medium_confidence",
            "sparse_content",
            "medium_text_volume",
        ]
        assert field_review["language_entries"]["severity"] == "review_recommended"

        confidence = payload["confidence"]
        assert confidence["headline"]["field_name"] == "headline"
        assert confidence["headline"]["level"] == "high"
        assert confidence["headline"]["has_value"] is True

        assert confidence["skills"]["field_name"] == "skills"
        assert confidence["skills"]["level"] == "medium"
        assert confidence["skills"]["item_count"] == 3

        assert confidence["experience_entries"]["field_name"] == "experience_entries"
        assert confidence["experience_entries"]["level"] == "high"

        assert confidence["language_entries"]["field_name"] == "language_entries"
        assert confidence["language_entries"]["level"] == "medium"

        assert payload["parse_run_id"] == (latest_parse_run.id or 0)
        assert payload["generated_at"] == "2026-04-06T14:22:00Z"
        assert payload["source_upload_id"] == cv_upload_id
        assert payload["source_filename"] == "alice_cv.pdf"
        assert payload["source_parse_status"] == "parsed"
        assert payload["parser_version"] == HEURISTIC_CV_PARSER_VERSION

        draft = payload["draft"]
        assert draft["headline"] == "Senior Backend Engineer"
        assert draft["summary"] == "Backend engineer with strong FastAPI experience."
        assert draft["skills"] == ["Python", "FastAPI", "SQL"]
        assert draft["target_roles"] == ["Staff Backend Engineer"]
        assert draft["preferred_locations"] == ["Berlin"]
        assert draft["remote_preference"] == "remote"

        assert len(draft["education_entries"]) == 1
        assert draft["education_entries"][0]["school_name"] == "METU"

        assert len(draft["experience_entries"]) == 1
        assert draft["experience_entries"][0]["company_name"] == "ACME"

        assert len(draft["language_entries"]) == 1
        assert draft["language_entries"][0]["language_name"] == "English"
    finally:
        close_connection(connection)


def test_get_latest_user_cv_profile_apply_plan_returns_none_when_missing(
    tmp_path: Path,
) -> None:
    client, _repo, connection, _subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_apply_plan_none.db",
    )

    try:
        response = client.get("/api/user/profile/cv/latest-apply-plan")

        assert response.status_code == 200
        assert response.json() is None
    finally:
        close_connection(connection)


def test_get_latest_user_cv_profile_apply_plan_returns_typed_apply_plan(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_apply_plan.db",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text="Alice Example\nSenior Backend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-06T15:31:00Z",
        parsed_at="2026-04-06T15:32:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T15:32:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.pdf",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Senior Backend Engineer",
                    "summary": "Built reliable FastAPI platforms.",
                    "skills": ["Python", "FastAPI", "SQL"],
                    "target_roles": ["Staff Backend Engineer"],
                    "preferred_locations": ["Berlin"],
                    "remote_preference": "remote",
                    "education_entries": [
                        {
                            "school_name": "METU",
                            "degree_name": "BSc Electrical Engineering",
                            "field_of_study": None,
                            "start_year": 2012,
                            "end_year": 2017,
                        }
                    ],
                    "experience_entries": [
                        {
                            "title": "Senior Backend Engineer",
                            "company_name": "ACME",
                            "start_year": 2021,
                            "end_year": None,
                            "summary": "Built matching systems.",
                        }
                    ],
                    "language_entries": [
                        {
                            "language_name": "English",
                            "proficiency_level": "C1",
                            "notes": None,
                        }
                    ],
                },
            }
        ),
        created_at="2026-04-06T15:32:00Z",
    )

    try:
        response = client.get("/api/user/profile/cv/latest-apply-plan")

        assert response.status_code == 200
        payload = response.json()

        extraction_metadata = payload["extraction_metadata"]
        assert extraction_metadata["file_format"] == "pdf"
        assert extraction_metadata["extraction_method"] == "pdf_text"
        assert extraction_metadata["uses_ocr"] is False
        assert extraction_metadata["parse_status_detail"] == "pdf_text_extracted"
        assert extraction_metadata["extraction_quality"] == "medium"
        assert extraction_metadata["review_hints"] == ["medium_text_volume"]
        assert extraction_metadata["needs_manual_review"] is False
        assert extraction_metadata["is_safe_for_default_apply"] is True
        assert extraction_metadata["fallback_reason"] is None
        assert extraction_metadata["recommended_next_action"] == "safe_to_apply"

        confidence = payload["confidence"]
        assert confidence["headline"]["field_name"] == "headline"
        assert confidence["headline"]["level"] == "high"

        assert confidence["summary"]["field_name"] == "summary"
        assert confidence["summary"]["level"] == "medium"

        assert confidence["skills"]["field_name"] == "skills"
        assert confidence["skills"]["level"] == "medium"

        assert confidence["experience_entries"]["field_name"] == "experience_entries"
        assert confidence["experience_entries"]["level"] == "high"

        assert payload["source_filename"] == "alice_cv.pdf"
        assert payload["source_parse_status"] == "parsed"
        assert payload["parser_version"] == HEURISTIC_CV_PARSER_VERSION
        assert payload["has_actionable_changes"] is True
        assert payload["default_selected_change_count"] == 9

        assert payload["headline"]["action"] == "fill_missing"
        assert payload["headline"]["default_selected"] is True
        assert payload["headline"]["suggested_value"] == "Senior Backend Engineer"

        assert payload["summary"]["action"] == "fill_missing"
        assert payload["remote_preference"]["action"] == "fill_missing"

        assert payload["skills"]["action"] == "add_unique"
        assert payload["skills"]["items_to_add"] == ["Python", "FastAPI", "SQL"]

        assert payload["target_roles"]["action"] == "add_unique"
        assert payload["target_roles"]["items_to_add"] == ["Staff Backend Engineer"]

        assert payload["preferred_locations"]["action"] == "add_unique"
        assert payload["preferred_locations"]["items_to_add"] == ["Berlin"]

        assert len(payload["education_entries"]) == 1
        assert payload["education_entries"][0]["action"] == "add_unique"

        assert len(payload["experience_entries"]) == 1
        assert payload["experience_entries"][0]["action"] == "add_unique"

        assert len(payload["language_entries"]) == 1
        assert payload["language_entries"][0]["action"] == "add_unique"
    finally:
        close_connection(connection)


def test_apply_selected_user_cv_profile_operations_updates_profile_and_entries(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_apply_selected.db",
    )

    repo.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline=None,
        summary="Existing summary to be explicitly replaced.",
        target_roles=(),
        skills=("Python",),
        preferred_locations=(),
        remote_preference=None,
        cv_filename="alice_cv.pdf",
        cv_uploaded_at="2026-04-06T16:21:00Z",
        updated_at="2026-04-06T16:21:00Z",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text="Alice Example\nSenior Backend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-06T16:21:00Z",
        parsed_at="2026-04-06T16:22:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    parse_run = repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T16:22:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.pdf",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Senior Backend Engineer",
                    "summary": "Built reliable FastAPI platforms.",
                    "skills": ["Python", "FastAPI", "SQL"],
                    "target_roles": ["Staff Backend Engineer"],
                    "preferred_locations": ["Berlin"],
                    "remote_preference": "remote",
                    "education_entries": [
                        {
                            "school_name": "METU",
                            "degree_name": "BSc Electrical Engineering",
                            "field_of_study": None,
                            "start_year": 2012,
                            "end_year": 2017,
                        }
                    ],
                    "experience_entries": [
                        {
                            "title": "Senior Backend Engineer",
                            "company_name": "ACME",
                            "start_year": 2021,
                            "end_year": None,
                            "summary": "Built matching systems.",
                        }
                    ],
                    "language_entries": [
                        {
                            "language_name": "English",
                            "proficiency_level": "C1",
                            "notes": None,
                        }
                    ],
                },
            }
        ),
        created_at="2026-04-06T16:22:00Z",
    )

    try:
        response = client.post(
            "/api/user/profile/cv/apply-selected",
            json={
                "parse_run_id": parse_run.id,
                "scalar_fields": ["headline", "summary", "remote_preference"],
                "list_fields": ["skills", "target_roles", "preferred_locations"],
                "education_entry_indexes": [0],
                "experience_entry_indexes": [0],
                "language_entry_indexes": [0],
                "manual_review_acknowledged": True,
            },
        )

        assert response.status_code == 200
        payload = response.json()

        assert payload["parse_run_id"] == (parse_run.id or 0)
        assert payload["applied_change_count"] == 9
        assert payload["applied_scalar_fields"] == [
            "headline",
            "summary",
            "remote_preference",
        ]
        assert payload["applied_list_fields"] == [
            "skills",
            "target_roles",
            "preferred_locations",
        ]
        assert payload["applied_education_entry_indexes"] == [0]
        assert payload["applied_experience_entry_indexes"] == [0]
        assert payload["applied_language_entry_indexes"] == [0]

        assert payload["workspace_refresh_required"] is True
        assert "profile" not in payload

        persisted_profile = repo.get_subscriber_profile(subscriber_id)
        assert persisted_profile.headline == "Senior Backend Engineer"
        assert persisted_profile.summary == "Built reliable FastAPI platforms."
        assert persisted_profile.remote_preference == "remote"
        assert persisted_profile.skills == ("Python", "FastAPI", "SQL")
        assert persisted_profile.target_roles == ("Staff Backend Engineer",)
        assert persisted_profile.preferred_locations == ("Berlin",)

        persisted_education = repo.list_subscriber_education_entries(subscriber_id)
        persisted_experience = repo.list_subscriber_experience_entries(subscriber_id)
        persisted_languages = repo.list_subscriber_language_entries(subscriber_id)

        assert len(persisted_education) == 1
        assert persisted_education[0].school_name == "METU"

        assert len(persisted_experience) == 1
        assert persisted_experience[0].company_name == "ACME"

        assert len(persisted_languages) == 1
        assert persisted_languages[0].language_name == "English"

        assert payload["apply_audit_id"] > 0
        assert (
            payload["resulting_parse_run_apply_status"]
            == CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED
        )
        assert payload["remaining_actionable_change_count"] == 0

        updated_parse_run = repo.get_subscriber_cv_parse_run_by_id(parse_run.id or 0)
        assert updated_parse_run is not None
        assert updated_parse_run.apply_status == CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED
        assert updated_parse_run.applied_change_count == 9
        assert updated_parse_run.applied_at is not None

        apply_audits = repo.list_subscriber_cv_apply_audits_for_parse_run(
            parse_run.id or 0
        )
        assert len(apply_audits) == 1
        assert apply_audits[0].applied_change_count == 9
        assert (
            apply_audits[0].resulting_apply_status
            == CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED
        )
        assert apply_audits[0].remaining_actionable_change_count == 0

        selected_operations_payload = json.loads(
            apply_audits[0].selected_operations_json
        )
        assert selected_operations_payload["selection"]["scalar_fields"] == [
            "headline",
            "summary",
            "remote_preference",
        ]
        assert selected_operations_payload["operator_context"] == {
            "source_upload_id": cv_upload_id,
            "source_filename": "alice_cv.pdf",
            "source_parse_status": "parsed",
            "needs_manual_review": True,
            "manual_review_acknowledged": True,
            "is_safe_for_default_apply": False,
            "fallback_reason": "low_text_volume",
            "recommended_next_action": "review_before_apply",
        }

        applied_operations_payload = json.loads(
            apply_audits[0].applied_operations_json
        )
        assert (
            applied_operations_payload["operator_context"]
            == selected_operations_payload["operator_context"]
        )
        assert applied_operations_payload["post_apply_summary"] == {
            "resulting_parse_run_apply_status": (
                CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED
            ),
            "remaining_actionable_change_count": 0,
        }
    finally:
        close_connection(connection)


def test_apply_selected_user_cv_profile_operations_allows_safe_apply_without_acknowledgement(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_apply_selected_safe_without_ack.db",
    )

    repo.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline=None,
        summary=None,
        target_roles=(),
        skills=(),
        preferred_locations=(),
        remote_preference=None,
        cv_filename="alice_cv.pdf",
        cv_uploaded_at="2026-04-06T16:40:00Z",
        updated_at="2026-04-06T16:40:00Z",
    )

    safe_extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote

Professional Summary
Backend engineer with strong FastAPI and distributed systems experience.

Technical Skills
Python, FastAPI, SQL
"""

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text=safe_extracted_text,
        parse_status="parsed",
        uploaded_at="2026-04-06T16:40:00Z",
        parsed_at="2026-04-06T16:41:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    parse_run = repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T16:41:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.pdf",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Senior Backend Engineer",
                    "summary": (
                        "Backend engineer with strong FastAPI and distributed "
                        "systems experience."
                    ),
                    "skills": ["Python", "FastAPI", "SQL"],
                    "target_roles": ["Staff Backend Engineer"],
                    "preferred_locations": ["Berlin"],
                    "remote_preference": "remote",
                    "education_entries": [],
                    "experience_entries": [],
                    "language_entries": [],
                },
            }
        ),
        created_at="2026-04-06T16:41:00Z",
    )

    try:
        response = client.post(
            "/api/user/profile/cv/apply-selected",
            json={
                "parse_run_id": parse_run.id,
                "scalar_fields": ["headline", "summary", "remote_preference"],
                "list_fields": [
                    "skills",
                    "target_roles",
                    "preferred_locations",
                ],
                "education_entry_indexes": [],
                "experience_entry_indexes": [],
                "language_entry_indexes": [],
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["applied_change_count"] == 6
        assert payload["workspace_refresh_required"] is True
        assert "profile" not in payload

        apply_audits = repo.list_subscriber_cv_apply_audits_for_parse_run(
            parse_run.id or 0
        )
        assert len(apply_audits) == 1

        selected_operations_payload = json.loads(
            apply_audits[0].selected_operations_json
        )
        assert selected_operations_payload["operator_context"] == {
            "source_upload_id": cv_upload_id,
            "source_filename": "alice_cv.pdf",
            "source_parse_status": "parsed",
            "needs_manual_review": False,
            "manual_review_acknowledged": False,
            "is_safe_for_default_apply": True,
            "fallback_reason": None,
            "recommended_next_action": "safe_to_apply",
        }
    finally:
        close_connection(connection)


def test_apply_selected_user_cv_profile_operations_rejects_empty_selection(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_apply_selected_empty.db",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text="Alice Example\nSenior Backend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-06T16:31:00Z",
        parsed_at="2026-04-06T16:32:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    parse_run = repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T16:32:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.pdf",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Senior Backend Engineer",
                    "summary": None,
                    "skills": ["Python"],
                    "target_roles": [],
                    "preferred_locations": [],
                    "remote_preference": None,
                    "education_entries": [],
                    "experience_entries": [],
                    "language_entries": [],
                },
            }
        ),
        created_at="2026-04-06T16:32:00Z",
    )

    try:
        response = client.post(
            "/api/user/profile/cv/apply-selected",
            json={"parse_run_id": parse_run.id},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "At least one CV apply operation must be selected."
        )
    finally:
        close_connection(connection)


def test_get_latest_user_cv_parse_snapshot_surfaces_manual_review_field_risks(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_parse_snapshot_manual_review.db",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.png",
        storage_path="uploads/cv/alice_cv.png",
        content_type="image/png",
        file_size_bytes=16384,
        extracted_text="Alice Example\nBackend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-06T17:45:00Z",
        parsed_at="2026-04-06T17:46:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T17:46:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.png",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Backend Engineer",
                    "summary": None,
                    "skills": ["Python"],
                    "target_roles": [],
                    "preferred_locations": [],
                    "remote_preference": None,
                    "education_entries": [],
                    "experience_entries": [],
                    "language_entries": [],
                },
            }
        ),
        created_at="2026-04-06T17:46:00Z",
    )

    try:
        response = client.get("/api/user/profile/cv/latest-parse")

        assert response.status_code == 200
        payload = response.json()

        review_summary = payload["review_summary"]
        assert review_summary == {
            "total_field_count": 9,
            "safe_field_count": 0,
            "review_recommended_count": 1,
            "review_required_count": 8,
            "highest_severity": "review_required",
            "focus_field_names": [
                "headline",
                "summary",
                "skills",
                "target_roles",
                "preferred_locations",
                "remote_preference",
                "education_entries",
                "experience_entries",
                "language_entries",
            ],
            "manual_review_flow": True,
        }

        field_review = _field_review_by_name(payload)
        assert field_review["headline"]["severity"] == "review_recommended"
        assert field_review["headline"]["reason_codes"] == [
            "high_confidence",
            "ocr_source",
            "manual_review_flow",
            "low_text_volume",
            "extraction_review_hint",
        ]
        assert field_review["summary"]["severity"] == "review_required"
    finally:
        close_connection(connection)


def test_apply_selected_user_cv_profile_operations_requires_manual_review_acknowledgement(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_apply_selected_manual_review_required.db",
    )

    repo.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline=None,
        summary=None,
        target_roles=(),
        skills=(),
        preferred_locations=(),
        remote_preference=None,
        cv_filename="alice_cv.png",
        cv_uploaded_at="2026-04-06T18:00:00Z",
        updated_at="2026-04-06T18:00:00Z",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.png",
        storage_path="uploads/cv/alice_cv.png",
        content_type="image/png",
        file_size_bytes=16384,
        extracted_text="Alice Example\nBackend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-06T18:00:00Z",
        parsed_at="2026-04-06T18:01:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    parse_run = repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T18:01:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.png",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Backend Engineer",
                    "summary": None,
                    "skills": ["Python"],
                    "target_roles": [],
                    "preferred_locations": [],
                    "remote_preference": None,
                    "education_entries": [],
                    "experience_entries": [],
                    "language_entries": [],
                },
            }
        ),
        created_at="2026-04-06T18:01:00Z",
    )

    try:
        response = client.post(
            "/api/user/profile/cv/apply-selected",
            json={
                "parse_run_id": parse_run.id,
                "scalar_fields": ["headline"],
                "list_fields": ["skills"],
                "education_entry_indexes": [],
                "experience_entry_indexes": [],
                "language_entry_indexes": [],
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Manual review acknowledgement is required before applying "
            "CV changes for this extraction result."
        )
    finally:
        close_connection(connection)



def test_apply_selected_user_cv_profile_operations_allows_manual_review_apply_when_acknowledged(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_apply_selected_manual_review_acknowledged.db",
    )

    repo.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline=None,
        summary=None,
        target_roles=(),
        skills=(),
        preferred_locations=(),
        remote_preference=None,
        cv_filename="alice_cv.png",
        cv_uploaded_at="2026-04-06T18:10:00Z",
        updated_at="2026-04-06T18:10:00Z",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.png",
        storage_path="uploads/cv/alice_cv.png",
        content_type="image/png",
        file_size_bytes=16384,
        extracted_text="Alice Example\nBackend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-06T18:10:00Z",
        parsed_at="2026-04-06T18:11:00Z",
    )
    cv_upload_id = cv_upload.id or 0

    parse_run = repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=cv_upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-06T18:11:00Z",
                "source_upload_id": cv_upload_id,
                "source_filename": "alice_cv.png",
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Backend Engineer",
                    "summary": None,
                    "skills": ["Python"],
                    "target_roles": [],
                    "preferred_locations": [],
                    "remote_preference": None,
                    "education_entries": [],
                    "experience_entries": [],
                    "language_entries": [],
                },
            }
        ),
        created_at="2026-04-06T18:11:00Z",
    )

    try:
        response = client.post(
            "/api/user/profile/cv/apply-selected",
            json={
                "parse_run_id": parse_run.id,
                "scalar_fields": ["headline"],
                "list_fields": ["skills"],
                "education_entry_indexes": [],
                "experience_entry_indexes": [],
                "language_entry_indexes": [],
                "manual_review_acknowledged": True,
            },
        )

        assert response.status_code == 200
        payload = response.json()

        assert payload["parse_run_id"] == (parse_run.id or 0)
        assert payload["applied_change_count"] == 2
        assert payload["workspace_refresh_required"] is True
        assert "profile" not in payload
    finally:
        close_connection(connection)

def test_upload_user_cv_auto_applies_safe_additive_changes_end_to_end(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads_auto_apply.db",
    )

    extracted_cv_text = """
Olivia Campos
Senior Software Engineer
olivia@example.com | +1 415 555 0123 | San Francisco, CA

Summary
Seasoned backend engineer with 6+ years shipping distributed systems.

Experience
Senior Software Engineer | Wish | Remote
Jan 2020 - Present
- Led backend platform overhaul.
- Designed scalable REST APIs.

Software Engineer | PostMates | San Francisco
2018 - 2020
- Built logistics services.

Software Engineering Intern | Mosaic | New York
2016 - 2017
- Prototyped data pipelines.

Education
B.S. Computer Science | University of California, Los Angeles (UCLA) | 2016 - 2020

Technical Skills
Programming Languages: Python, JavaScript
Frameworks: Django, Angular
Tools: AWS, Git, SQL
Concepts: REST, HTML, CSS

Languages
English - Native
Spanish - Fluent
"""

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            lambda _file_path: CvExtractionResult(
                extracted_text=extracted_cv_text,
                parse_status=CV_PARSE_STATUS_PARSED,
                page_count=1,
            ),
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "olivia_cv.pdf",
                    b"%PDF-1.4 example cv bytes",
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["parse_status"] == "parsed"

        profile = repo.get_subscriber_profile(subscriber_id)
        assert profile.headline == "Senior Software Engineer"
        assert profile.summary and profile.summary.startswith("Seasoned backend engineer")
        assert profile.phone == "+1 415 555 0123"

        skill_set = set(profile.skills)
        for expected_skill in (
            "Python",
            "JavaScript",
            "Django",
            "Angular",
            "AWS",
            "Git",
            "SQL",
        ):
            assert expected_skill in skill_set, f"missing skill: {expected_skill}"

        experiences = repo.list_subscriber_experience_entries(subscriber_id)
        exp_titles = {e.title for e in experiences}
        assert "Senior Software Engineer" in exp_titles
        assert "Software Engineer" in exp_titles
        assert "Software Engineering Intern" in exp_titles

        wish_entry = next(e for e in experiences if e.title == "Senior Software Engineer")
        assert wish_entry.company_name == "Wish"
        assert wish_entry.start_year == 2020

        education = repo.list_subscriber_education_entries(subscriber_id)
        assert len(education) == 1
        assert education[0].school_name == "University of California, Los Angeles (UCLA)"
        assert education[0].degree_name == "B.S. Computer Science"
        assert education[0].start_year == 2016
        assert education[0].end_year == 2020

        languages = repo.list_subscriber_language_entries(subscriber_id)
        lang_names = {entry.language_name for entry in languages}
        assert "English" in lang_names
        assert "Spanish" in lang_names
    finally:
        close_connection(connection)


def test_upload_user_cv_replaces_stale_profile_with_new_cv_as_source_of_truth(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A new CV upload must make the freshly uploaded CV the active profile source.

    When the profile already holds stale scalar fields and prior structured
    entries from an earlier CV, uploading a new CV should overwrite scalar
    fields and replace the structured sections with entries derived from
    the new CV — not append to the stale sections or leave stale scalars
    in place.
    """
    from hiring_radar.models import (
        SubscriberEducationEntry,
        SubscriberExperienceEntry,
        SubscriberLanguageEntry,
    )

    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads_replace_semantics.db",
    )

    seed_updated_at = "2026-04-04T09:00:00Z"
    repo.upsert_subscriber_profile(
        subscriber_id,
        phone="+90 555 000 0000",
        headline="Stale Headline From Old CV",
        summary="Outdated summary left over from a previous CV upload.",
        target_roles=("Frontend Developer",),
        skills=("COBOL", "Fortran"),
        preferred_locations=("Istanbul",),
        remote_preference="onsite",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at=seed_updated_at,
    )
    repo.replace_subscriber_education_entries(
        subscriber_id,
        entries=[
            SubscriberEducationEntry(
                subscriber_id=subscriber_id,
                school_name="Old University",
                degree_name="B.A.",
                field_of_study="History",
                start_year=2005,
                end_year=2009,
            )
        ],
        updated_at=seed_updated_at,
    )
    repo.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                subscriber_id=subscriber_id,
                title="Old Title",
                company_name="Legacy Corp",
                start_year=2010,
                end_year=2015,
                summary="Did old things at a legacy company.",
            )
        ],
        updated_at=seed_updated_at,
    )
    repo.replace_subscriber_language_entries(
        subscriber_id,
        entries=[
            SubscriberLanguageEntry(
                subscriber_id=subscriber_id,
                language_name="Turkish",
                proficiency_level="Native",
                notes=None,
            )
        ],
        updated_at=seed_updated_at,
    )

    extracted_cv_text = """
Olivia Campos
Senior Software Engineer
olivia@example.com | +1 415 555 0123 | San Francisco, CA

Summary
Seasoned backend engineer with 6+ years shipping distributed systems.

Experience
Senior Software Engineer | Wish | Remote
Jan 2020 - Present
- Led backend platform overhaul.

Software Engineer | PostMates | San Francisco
2018 - 2020
- Built logistics services.

Education
B.S. Computer Science | University of California, Los Angeles (UCLA) | 2016 - 2020

Technical Skills
Programming Languages: Python, JavaScript
Frameworks: Django, Angular

Languages
English - Native
Spanish - Fluent
"""

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            lambda _file_path: CvExtractionResult(
                extracted_text=extracted_cv_text,
                parse_status=CV_PARSE_STATUS_PARSED,
                page_count=1,
            ),
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "olivia_cv.pdf",
                    b"%PDF-1.4 replacement cv bytes",
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 200, response.text

        profile = repo.get_subscriber_profile(subscriber_id)
        assert profile.headline == "Senior Software Engineer"
        assert profile.summary and profile.summary.startswith("Seasoned backend engineer")
        assert profile.phone == "+1 415 555 0123"
        assert "COBOL" not in profile.skills
        assert "Fortran" not in profile.skills
        assert "Python" in profile.skills
        assert "Django" in profile.skills

        experiences = repo.list_subscriber_experience_entries(subscriber_id)
        exp_titles = {e.title for e in experiences}
        assert "Old Title" not in exp_titles, "stale experience entry was not removed"
        assert "Senior Software Engineer" in exp_titles
        assert "Software Engineer" in exp_titles

        education = repo.list_subscriber_education_entries(subscriber_id)
        schools = {e.school_name for e in education}
        assert "Old University" not in schools, "stale education entry was not removed"
        assert any("UCLA" in name for name in schools)

        languages = repo.list_subscriber_language_entries(subscriber_id)
        lang_names = {entry.language_name for entry in languages}
        assert "Turkish" not in lang_names, "stale language entry was not removed"
        assert "English" in lang_names
        assert "Spanish" in lang_names
    finally:
        close_connection(connection)


def test_upload_user_cv_preserves_existing_profile_when_draft_has_no_signal(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """An unsubstantive draft must not pivot (and therefore wipe) the profile.

    Pivoting is gated on a substantive draft — a draft with at least one
    CV-derived scalar, list item, or structured entry. When the draft has
    no signal at all (e.g. parse status ``empty``), the helper must
    preserve the user's existing structured sections rather than
    replacing them with empty lists.
    """
    from hiring_radar.models import (
        SubscriberEducationEntry,
        SubscriberExperienceEntry,
        SubscriberLanguageEntry,
    )
    from hiring_radar.services.cv_extraction import CV_PARSE_STATUS_EMPTY

    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads_preserve_when_empty.db",
    )

    seed_updated_at = "2026-04-04T09:00:00Z"
    repo.replace_subscriber_education_entries(
        subscriber_id,
        entries=[
            SubscriberEducationEntry(
                subscriber_id=subscriber_id,
                school_name="Existing University",
                degree_name="M.S.",
                field_of_study="Computer Science",
                start_year=2018,
                end_year=2020,
            )
        ],
        updated_at=seed_updated_at,
    )
    repo.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                subscriber_id=subscriber_id,
                title="Existing Engineer",
                company_name="Existing Co",
                start_year=2020,
                end_year=None,
                summary=None,
            )
        ],
        updated_at=seed_updated_at,
    )
    repo.replace_subscriber_language_entries(
        subscriber_id,
        entries=[
            SubscriberLanguageEntry(
                subscriber_id=subscriber_id,
                language_name="German",
                proficiency_level="B2",
                notes=None,
            )
        ],
        updated_at=seed_updated_at,
    )

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            lambda _file_path: CvExtractionResult(
                extracted_text="",
                parse_status=CV_PARSE_STATUS_EMPTY,
                page_count=1,
            ),
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "sparse_cv.pdf",
                    b"%PDF-1.4 sparse cv bytes",
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 200, response.text

        education = repo.list_subscriber_education_entries(subscriber_id)
        assert len(education) == 1
        assert education[0].school_name == "Existing University"

        experiences = repo.list_subscriber_experience_entries(subscriber_id)
        assert len(experiences) == 1
        assert experiences[0].title == "Existing Engineer"

        languages = repo.list_subscriber_language_entries(subscriber_id)
        assert len(languages) == 1
        assert languages[0].language_name == "German"
    finally:
        close_connection(connection)


def test_upload_user_cv_pivots_profile_and_clears_stale_scalars_from_prior_cv(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A substantive new CV must clear stale scalars left by a prior CV.

    The prior CV left Turkish scalars on the profile (headline, summary,
    target_roles). The new CV is substantive (has structured sections
    and other scalars) but does not carry those specific fields. After
    the upload the stale scalars must be gone — the new CV is now the
    authoritative CV-derived source for the profile, not the old one.
    """
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads_pivot.db",
    )

    seed_updated_at = "2026-04-04T09:00:00Z"
    repo.upsert_subscriber_profile(
        subscriber_id,
        phone="+90 555 000 0000",
        headline="Mühendis",
        summary=(
            "Mühendislik sektöründe uzun yıllardır aktif olarak görev alan bir uzman. "
            "Elektronik sistemler geliştirme, ürün tasarımı ve proje yönetimi konularında deneyimli."
        ),
        target_roles=("Elektrik Elektronik Mühendisliği", "Proje Yönetimi Uzmanı"),
        skills=(),
        preferred_locations=(),
        remote_preference=None,
        cv_filename="old-turkish-cv.pdf",
        cv_uploaded_at=seed_updated_at,
        updated_at=seed_updated_at,
    )

    extracted_cv_text = """
Olivia Campos
Software Developer
olivia@example.com

Experience
Software Developer | Acme Corp
2022 - Present
- Built services.

Education
B.S. Computer Science | State University | 2018 - 2022

Technical Skills
Python, JavaScript
"""

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            lambda _file_path: CvExtractionResult(
                extracted_text=extracted_cv_text,
                parse_status=CV_PARSE_STATUS_PARSED,
                page_count=1,
            ),
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "olivia_cv.pdf",
                    b"%PDF-1.4 pivot cv bytes",
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 200, response.text

        profile = repo.get_subscriber_profile(subscriber_id)
        assert profile.headline != "Mühendis", "stale Turkish headline was not cleared"
        assert profile.headline == "Software Developer"
        assert profile.summary is None or "Mühendislik" not in (profile.summary or "")
        assert "Elektrik Elektronik Mühendisliği" not in profile.target_roles
        assert "Proje Yönetimi Uzmanı" not in profile.target_roles

        experiences = repo.list_subscriber_experience_entries(subscriber_id)
        assert any(e.company_name == "Acme Corp" for e in experiences)

        education = repo.list_subscriber_education_entries(subscriber_id)
        assert any("State University" in (e.school_name or "") for e in education)
    finally:
        close_connection(connection)


def test_upload_user_cv_with_failed_extraction_preserves_existing_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A failed extraction must never wipe a populated profile.

    When OCR / extraction fails (e.g. tesseract unavailable, corrupt
    image), the profile keeps whatever data it had — the pivot helper
    is gated on a substantive draft so the failed upload cannot
    destroy the user's existing profile content.
    """
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_uploads_pivot_failed.db",
    )

    seed_updated_at = "2026-04-04T09:00:00Z"
    repo.upsert_subscriber_profile(
        subscriber_id,
        phone="+90 555 000 0000",
        headline="Mühendis",
        summary="Some existing summary.",
        target_roles=("Existing Role",),
        skills=("Python",),
        preferred_locations=(),
        remote_preference=None,
        cv_filename="old-cv.pdf",
        cv_uploaded_at=seed_updated_at,
        updated_at=seed_updated_at,
    )

    def _fail_extraction(_file_path):
        raise CvExtractionError("OCR engine unavailable in this environment.")

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            _fail_extraction,
        )

        response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "broken.png",
                    b"\x89PNG not-a-real-image",
                    "image/png",
                )
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["parse_status"] == "failed"

        profile = repo.get_subscriber_profile(subscriber_id)
        assert profile.headline == "Mühendis"
        assert profile.summary == "Some existing summary."
        assert profile.target_roles == ("Existing Role",)
        assert profile.skills == ("Python",)
    finally:
        close_connection(connection)
