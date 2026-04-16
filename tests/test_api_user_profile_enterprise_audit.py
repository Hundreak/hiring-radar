from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
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


def test_apply_selected_persists_enterprise_audit_metadata_json(
    tmp_path: Path,
) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="enterprise_apply_audit.db",
    )

    repo.upsert_subscriber_profile(
        subscriber_id,
        phone="+49 151 23456789",
        headline=None,
        summary=None,
        target_roles=(),
        skills=(),
        preferred_locations=(),
        remote_preference=None,
        cv_filename="alice_cv.pdf",
        cv_uploaded_at="2026-04-09T11:00:00Z",
        updated_at="2026-04-09T11:00:00Z",
    )

    cv_upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        storage_path="uploads/cv/alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text="Alice Example\nSenior Backend Engineer",
        parse_status="parsed",
        uploaded_at="2026-04-09T11:00:00Z",
        parsed_at="2026-04-09T11:01:00Z",
    )
    upload_id = cv_upload.id or 0

    parse_run = repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": "2026-04-09T11:01:00Z",
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
        created_at="2026-04-09T11:01:00Z",
        metadata_json=json.dumps(
            {
                "schema_version": 1,
                "parse": {
                    "parser_version": HEURISTIC_CV_PARSER_VERSION,
                    "source_upload_id": upload_id,
                    "source_filename": "alice_cv.pdf",
                    "source_parse_status": "parsed",
                    "generated_at": "2026-04-09T11:01:00Z",
                },
                "enterprise": {
                    "fingerprint": {
                        "document_sha256": "doc",
                        "content_sha256": "content",
                        "person_fingerprint_available": True,
                        "relation": "first_observed",
                        "similarity": None,
                        "reason_codes": [],
                    },
                    "cache": {
                        "cache_key": "cache-key",
                        "status": "miss",
                        "exact_reusable": False,
                        "partial_reusable": False,
                        "reusable_section_names": [],
                        "changed_section_names": [],
                        "reason_codes": [],
                    },
                    "ats": {
                        "score": 78,
                        "level": "medium",
                        "issue_codes": ["missing_contact_details"],
                        "recommendations": ["add_contact_bundle"],
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
        ),
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

        audits = repo.list_subscriber_cv_apply_audits_for_parse_run(parse_run.id or 0)
        assert len(audits) == 1

        metadata = json.loads(audits[0].metadata_json)
        assert metadata["schema_version"] == 1
        assert metadata["enterprise"]["ats"]["score"] == 78
        assert metadata["operator_context"]["source_filename"] == "alice_cv.pdf"
        assert metadata["apply_summary"]["selected_operation_count"] == 2
        assert metadata["apply_summary"]["applied_change_count"] == 2
    finally:
        close_connection(connection)
