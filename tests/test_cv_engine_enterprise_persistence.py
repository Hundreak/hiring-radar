from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.routers import user_profile
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_PARSED,
    CvExtractionResult,
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


def test_upload_user_cv_persists_parse_run_metadata_json(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="enterprise_parse_metadata.db",
    )

    extracted_text = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote
+49 151 23456789

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
                extracted_text=extracted_text,
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

        uploads = repo.list_subscriber_cv_uploads(subscriber_id)
        parse_runs = repo.list_subscriber_cv_parse_runs_for_upload(uploads[0].id or 0)
        assert len(parse_runs) == 1

        metadata = json.loads(parse_runs[0].metadata_json)
        assert metadata["schema_version"] == 1
        assert metadata["parse"]["source_filename"] == "alice_cv.pdf"
        assert metadata["enterprise"]["fingerprint"]["content_sha256"]
        assert metadata["enterprise"]["ats"]["score"] is not None
        assert metadata["enterprise"]["redaction"]["available"] is True
    finally:
        close_connection(connection)


def test_latest_parse_prefers_persisted_enterprise_metadata(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="enterprise_metadata_preferred.db",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text="Alice Example\nSenior Backend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-09T10:00:00Z",
        parsed_at="2026-04-09T10:01:00Z",
    )
    upload_id = cv_upload.id or 0

    metadata_json = json.dumps(
        {
            "schema_version": 1,
            "parse": {
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "source_upload_id": upload_id,
                "source_filename": "alice_cv.pdf",
                "source_parse_status": "parsed",
                "generated_at": "2026-04-09T10:01:00Z",
            },
            "enterprise": {
                "fingerprint": {
                    "document_sha256": "doc",
                    "content_sha256": "content",
                    "person_fingerprint_available": True,
                    "relation": "exact_duplicate",
                    "similarity": 1.0,
                    "reason_codes": ["exact_hash"],
                },
                "cache": {
                    "cache_key": "cache-key",
                    "status": "exact_hit",
                    "exact_reusable": True,
                    "partial_reusable": False,
                    "reusable_section_names": ["summary"],
                    "changed_section_names": [],
                    "reason_codes": ["exact_hash"],
                },
                "ats": {
                    "score": 91,
                    "level": "high",
                    "issue_codes": [],
                    "recommendations": ["keep_format"],
                },
                "redaction": {
                    "available": True,
                    "pii_findings_count": 2,
                    "pii_types": ["email", "phone"],
                    "warnings": [],
                },
            },
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

    repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-09T10:01:00Z",
                "source_upload_id": upload_id,
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
        created_at="2026-04-09T10:01:00Z",
        metadata_json=metadata_json,
    )

    try:
        response = client.get("/api/user/profile/cv/latest-parse")

        assert response.status_code == 200
        payload = response.json()
        assert payload["enterprise_metadata"]["ats"]["score"] == 91
        assert payload["enterprise_metadata"]["cache"]["status"] == "exact_hit"
        assert payload["enterprise_metadata"]["fingerprint"]["relation"] == "exact_duplicate"
    finally:
        close_connection(connection)
