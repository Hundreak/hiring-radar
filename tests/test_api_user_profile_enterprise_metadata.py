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


_PARSED_TEXT = """
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


def _seed_parsed_upload(
    repo: HiringRadarRepository,
    *,
    subscriber_id: int,
    original_filename: str,
    uploaded_at: str,
    parsed_at: str,
    extracted_text: str,
) -> int:
    upload = repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename=original_filename,
        storage_path=f"uploads/cv/{original_filename}",
        content_type="application/pdf",
        file_size_bytes=245760,
        extracted_text=extracted_text,
        parse_status="parsed",
        uploaded_at=uploaded_at,
        parsed_at=parsed_at,
    )
    upload_id = upload.id or 0
    repo.create_subscriber_cv_parse_run(
        subscriber_id,
        cv_upload_id=upload_id,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
        source_parse_status="parsed",
        snapshot_json=json.dumps(
            {
                "generated_at": parsed_at,
                "source_upload_id": upload_id,
                "source_filename": original_filename,
                "source_parse_status": "parsed",
                "parser_version": HEURISTIC_CV_PARSER_VERSION,
                "draft": {
                    "headline": "Senior Backend Engineer",
                    "summary": "Backend engineer with strong FastAPI and distributed systems experience.",
                    "skills": ["Python", "FastAPI", "SQL"],
                    "target_roles": ["Backend Engineer"],
                    "preferred_locations": ["Berlin"],
                    "remote_preference": "remote",
                    "education_entries": [],
                    "experience_entries": [
                        {
                            "title": "Senior Backend Engineer",
                            "company_name": "ACME",
                            "start_year": 2021,
                            "end_year": None,
                            "summary": "Built matching systems.",
                        }
                    ],
                    "language_entries": [],
                },
            }
        ),
        created_at=parsed_at,
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
        cv_filename=original_filename,
        cv_uploaded_at=uploaded_at,
        updated_at=uploaded_at,
    )
    return upload_id


def test_profile_latest_cv_upload_includes_enterprise_metadata(tmp_path: Path) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_enterprise_metadata.db",
    )

    try:
        _seed_parsed_upload(
            repo,
            subscriber_id=subscriber_id,
            original_filename="alice_cv.pdf",
            uploaded_at="2026-04-08T12:00:00Z",
            parsed_at="2026-04-08T12:01:00Z",
            extracted_text=_PARSED_TEXT,
        )
        response = client.get("/api/user/profile")

        assert response.status_code == 200
        latest_cv = response.json()["latest_cv_upload"]
        enterprise = latest_cv["enterprise_metadata"]

        assert enterprise["fingerprint"]["content_sha256"]
        assert enterprise["cache"]["cache_key"]
        assert enterprise["ats"]["score"] is not None
        assert enterprise["redaction"]["available"] is True
        assert enterprise["redaction"]["pii_findings_count"] >= 2
    finally:
        close_connection(connection)


def test_latest_parse_and_apply_plan_include_enterprise_metadata(tmp_path: Path) -> None:
    client, repo, connection, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_enterprise_metadata_parse.db",
    )

    try:
        _seed_parsed_upload(
            repo,
            subscriber_id=subscriber_id,
            original_filename="alice_cv_v1.pdf",
            uploaded_at="2026-04-08T13:00:00Z",
            parsed_at="2026-04-08T13:01:00Z",
            extracted_text=_PARSED_TEXT,
        )
        _seed_parsed_upload(
            repo,
            subscriber_id=subscriber_id,
            original_filename="alice_cv_v2.pdf",
            uploaded_at="2026-04-08T13:05:00Z",
            parsed_at="2026-04-08T13:06:00Z",
            extracted_text=_PARSED_TEXT,
        )

        parse_response = client.get("/api/user/profile/cv/latest-parse")
        assert parse_response.status_code == 200
        parse_payload = parse_response.json()
        assert parse_payload["enterprise_metadata"]["fingerprint"]["relation"] in {
            "exact_duplicate",
            "updated_version",
            "related_variant",
            "first_observed",
        }
        assert parse_payload["enterprise_metadata"]["ats"]["score"] is not None

        plan_response = client.get("/api/user/profile/cv/latest-apply-plan")
        assert plan_response.status_code == 200
        plan_payload = plan_response.json()
        assert plan_payload["enterprise_metadata"]["cache"]["cache_key"]
        assert plan_payload["enterprise_metadata"]["redaction"]["available"] is True
    finally:
        close_connection(connection)
