from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.routers import user_profile
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.cv_extraction import CV_PARSE_STATUS_PARSED, CvExtractionResult
from hiring_radar.services.user_auth import UserSession


SAFE_EXTRACTED_TEXT = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin | Remote
+49 151 23456789

Professional Summary
Backend engineer with strong FastAPI and distributed systems experience.

Technical Skills
Python, FastAPI, SQL

Work Experience
Senior Backend Engineer | ACME | 2021 - Present
Built matching systems.
"""


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


def test_upload_parse_plan_apply_flow_exposes_consistent_enterprise_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="enterprise_end_to_end.db",
    )

    try:
        monkeypatch.setattr(
            user_profile,
            "extract_text_from_cv_file",
            lambda _file_path: CvExtractionResult(
                extracted_text=SAFE_EXTRACTED_TEXT,
                parse_status=CV_PARSE_STATUS_PARSED,
                page_count=1,
            ),
        )

        upload_response = client.post(
            "/api/user/profile/upload/cv",
            files={
                "file": (
                    "alice_cv.pdf",
                    b"%PDF-1.4 enterprise e2e bytes",
                    "application/pdf",
                )
            },
        )
        assert upload_response.status_code == 200
        upload_payload = upload_response.json()
        upload_enterprise = upload_payload["enterprise_metadata"]
        assert upload_enterprise["fingerprint"]["content_sha256"]
        assert upload_enterprise["cache"]["cache_key"]
        assert upload_enterprise["ats"]["score"] is not None
        assert upload_enterprise["redaction"]["available"] is True
        assert upload_enterprise["redaction"]["pii_findings_count"] >= 2

        profile_response = client.get("/api/user/profile")
        assert profile_response.status_code == 200
        latest_cv_upload = profile_response.json()["latest_cv_upload"]
        assert latest_cv_upload["enterprise_metadata"]["cache"]["cache_key"]

        latest_parse_response = client.get("/api/user/profile/cv/latest-parse")
        assert latest_parse_response.status_code == 200
        latest_parse_payload = latest_parse_response.json()
        parse_run_id = latest_parse_payload["parse_run_id"]
        parse_enterprise = latest_parse_payload["enterprise_metadata"]
        assert parse_enterprise["fingerprint"]["content_sha256"]
        assert parse_enterprise["ats"]["score"] is not None
        assert parse_enterprise["redaction"]["available"] is True

        latest_apply_plan_response = client.get(
            "/api/user/profile/cv/latest-apply-plan"
        )
        assert latest_apply_plan_response.status_code == 200
        latest_apply_plan_payload = latest_apply_plan_response.json()
        plan_enterprise = latest_apply_plan_payload["enterprise_metadata"]
        assert plan_enterprise["cache"]["cache_key"] == parse_enterprise["cache"][
            "cache_key"
        ]
        assert plan_enterprise["fingerprint"][
            "content_sha256"
        ] == parse_enterprise["fingerprint"]["content_sha256"]
        assert plan_enterprise["redaction"]["pii_types"]

        apply_response = client.post(
            "/api/user/profile/cv/apply-selected",
            json={
                "parse_run_id": parse_run_id,
                "scalar_fields": ["headline", "summary", "remote_preference"],
                "list_fields": [
                    "skills",
                    "target_roles",
                    "preferred_locations",
                ],
                "education_entry_indexes": [],
                "experience_entry_indexes": [0],
                "language_entry_indexes": [],
            },
        )
        assert apply_response.status_code == 200
        apply_payload = apply_response.json()
        assert apply_payload["applied_change_count"] >= 5

        parse_run = repo.get_subscriber_cv_parse_run_by_id(parse_run_id)
        assert parse_run is not None
        parse_run_metadata = json.loads(parse_run.metadata_json)
        assert parse_run_metadata["enterprise"]["ats"]["score"] is not None
        assert parse_run_metadata["enterprise"]["redaction"]["available"] is True

        audits = repo.list_subscriber_cv_apply_audits_for_parse_run(parse_run_id)
        assert len(audits) == 1
        audit_metadata = json.loads(audits[0].metadata_json)
        assert audit_metadata["enterprise"]["fingerprint"]["content_sha256"]
        assert audit_metadata["enterprise"]["cache"]["cache_key"]
        assert audit_metadata["enterprise"]["ats"]["score"] is not None
        assert audit_metadata["enterprise"]["redaction"]["available"] is True
        assert audit_metadata["operator_context"]["manual_review_acknowledged"] is False

        persisted_profile = repo.get_subscriber_profile(subscriber_id)
        assert persisted_profile.headline == "Senior Backend Engineer"
        assert persisted_profile.skills == ("Python", "FastAPI", "SQL")
    finally:
        close_connection(connection)
