from __future__ import annotations

import json
from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import SubscriberLanguageCertificate, SubscriberLanguageEntry


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "profile_assets_repository.db"))
    return HiringRadarRepository(connection), connection


def test_repository_can_replace_language_entries_and_certificates(
    tmp_path: Path,
) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-05T12:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        language_entries = repo.replace_subscriber_language_entries(
            subscriber_id,
            entries=[
                SubscriberLanguageEntry(
                    language_name="English",
                    proficiency_level="C1",
                    notes="Comfortable in technical interviews",
                ),
                SubscriberLanguageEntry(
                    language_name="German",
                    proficiency_level="B1",
                    notes="Improving for relocation",
                ),
            ],
            updated_at="2026-04-05T12:10:00Z",
        )

        certificates = repo.replace_subscriber_language_certificates(
            subscriber_id,
            certificates=[
                SubscriberLanguageCertificate(
                    language_entry_id=None,
                    certificate_name="IELTS Academic",
                    issuer_name="British Council",
                    file_name="ielts.pdf",
                    storage_path="uploads/certificates/ielts.pdf",
                    uploaded_at="2026-04-05T12:11:00Z",
                )
            ],
            updated_at="2026-04-05T12:12:00Z",
        )

        assert len(language_entries) == 2
        assert language_entries[0].language_name == "English"
        assert language_entries[0].display_order == 0
        assert language_entries[1].language_name == "German"
        assert language_entries[1].display_order == 1

        assert len(certificates) == 1
        assert certificates[0].certificate_name == "IELTS Academic"
        assert certificates[0].file_name == "ielts.pdf"
    finally:
        close_connection(connection)


def test_repository_can_create_and_fetch_cv_uploads(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-05T12:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        created = repo.create_subscriber_cv_upload(
            subscriber_id,
            original_filename="alice_cv.pdf",
            storage_path="uploads/cv/alice_cv.pdf",
            content_type="application/pdf",
            file_size_bytes=245760,
            extracted_text="Alice Example Backend Engineer Python FastAPI",
            parse_status="pending",
            uploaded_at="2026-04-05T12:20:00Z",
            parsed_at=None,
        )

        listed = repo.list_subscriber_cv_uploads(subscriber_id)
        latest = repo.get_latest_subscriber_cv_upload(subscriber_id)

        assert created.original_filename == "alice_cv.pdf"
        assert created.storage_path == "uploads/cv/alice_cv.pdf"
        assert created.content_type == "application/pdf"
        assert created.file_size_bytes == 245760
        assert len(listed) == 1
        assert latest is not None
        assert latest.original_filename == "alice_cv.pdf"
        assert latest.parse_status == "pending"
    finally:
        close_connection(connection)



def test_repository_can_update_cv_upload_parse_result(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-05T12:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        created = repo.create_subscriber_cv_upload(
            subscriber_id,
            original_filename="alice_cv.pdf",
            storage_path="uploads/cv/alice_cv.pdf",
            content_type="application/pdf",
            file_size_bytes=245760,
            extracted_text=None,
            parse_status="pending",
            uploaded_at="2026-04-05T12:20:00Z",
            parsed_at=None,
        )

        upload_id = created.id
        assert upload_id is not None

        updated = repo.update_subscriber_cv_upload_parse_result(
            upload_id,
            extracted_text="Alice Example Python FastAPI",
            parse_status="parsed",
            parsed_at="2026-04-05T12:21:00Z",
            updated_at="2026-04-05T12:21:00Z",
        )

        assert updated is not None
        assert updated.extracted_text == "Alice Example Python FastAPI"
        assert updated.parse_status == "parsed"
        assert updated.parsed_at == "2026-04-05T12:21:00Z"
    finally:
        close_connection(connection)


def test_repository_can_get_latest_cv_parse_run_for_subscriber(
    tmp_path: Path,
) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-06T14:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        cv_upload = repo.create_subscriber_cv_upload(
            subscriber_id,
            original_filename="alice_cv.pdf",
            storage_path="uploads/cv/alice_cv.pdf",
            content_type="application/pdf",
            file_size_bytes=245760,
            extracted_text="Alice Example\nSenior Backend Engineer",
            parse_status="parsed",
            uploaded_at="2026-04-06T14:01:00Z",
            parsed_at="2026-04-06T14:02:00Z",
        )
        cv_upload_id = cv_upload.id or 0

        old_snapshot_json = json.dumps(
            {
                "generated_at": "2026-04-06T14:02:00Z",
                "draft": {
                    "headline": "Old Snapshot",
                    "skills": [],
                    "target_roles": [],
                    "preferred_locations": [],
                    "remote_preference": None,
                    "education_entries": [],
                    "experience_entries": [],
                    "language_entries": [],
                },
            }
        )
        latest_snapshot_json = json.dumps(
            {
                "generated_at": "2026-04-06T14:03:00Z",
                "draft": {
                    "headline": "Latest Snapshot",
                    "skills": [],
                    "target_roles": [],
                    "preferred_locations": [],
                    "remote_preference": None,
                    "education_entries": [],
                    "experience_entries": [],
                    "language_entries": [],
                },
            }
        )

        repo.create_subscriber_cv_parse_run(
            subscriber_id,
            cv_upload_id=cv_upload_id,
            parser_version="heuristic-v0",
            source_parse_status="parsed",
            snapshot_json=old_snapshot_json,
            created_at="2026-04-06T14:02:00Z",
        )
        latest = repo.create_subscriber_cv_parse_run(
            subscriber_id,
            cv_upload_id=cv_upload_id,
            parser_version="heuristic-v1",
            source_parse_status="parsed",
            snapshot_json=latest_snapshot_json,
            created_at="2026-04-06T14:03:00Z",
        )

        fetched = repo.get_latest_subscriber_cv_parse_run(subscriber_id)

        assert fetched is not None
        assert fetched.id == latest.id
        assert fetched.parser_version == "heuristic-v1"
    finally:
        close_connection(connection)


def test_repository_can_create_apply_audit_and_update_parse_run_state(
    tmp_path: Path,
) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-06T17:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        cv_upload = repo.create_subscriber_cv_upload(
            subscriber_id,
            original_filename="alice_cv.pdf",
            storage_path="uploads/cv/alice_cv.pdf",
            content_type="application/pdf",
            file_size_bytes=245760,
            extracted_text="Alice Example\nSenior Backend Engineer",
            parse_status="parsed",
            uploaded_at="2026-04-06T17:01:00Z",
            parsed_at="2026-04-06T17:02:00Z",
        )
        
        parse_run = repo.create_subscriber_cv_parse_run(
            subscriber_id,
            cv_upload_id=cv_upload.id or 0,
            parser_version="heuristic-v0",
            source_parse_status="parsed",
            snapshot_json=json.dumps(
                {
                    "generated_at": "2026-04-06T17:02:00Z",
                    "draft": {
                        "headline": "Senior Backend Engineer",
                        "skills": [],
                        "target_roles": [],
                        "preferred_locations": [],
                        "remote_preference": None,
                        "education_entries": [],
                        "experience_entries": [],
                        "language_entries": [],
                    },
                }
            ),
            created_at="2026-04-06T17:02:00Z",
        )

        updated_parse_run = repo.update_subscriber_cv_parse_run_apply_state(
            parse_run.id or 0,
            apply_status="fully_applied",
            applied_change_count=3,
            applied_at="2026-04-06T17:05:00Z",
            updated_at="2026-04-06T17:05:00Z",
        )
        audit = repo.create_subscriber_cv_apply_audit(
            subscriber_id,
            parse_run_id=parse_run.id or 0,
            selected_operations_json='{"scalar_fields":["headline"]}',
            applied_operations_json='{"applied_scalar_fields":["headline"]}',
            applied_change_count=1,
            resulting_apply_status="fully_applied",
            remaining_actionable_change_count=0,
            created_at="2026-04-06T17:05:00Z",
        )
        audits = repo.list_subscriber_cv_apply_audits_for_parse_run(parse_run.id or 0)

        assert updated_parse_run is not None
        assert updated_parse_run.apply_status == "fully_applied"
        assert updated_parse_run.applied_change_count == 3
        assert updated_parse_run.applied_at == "2026-04-06T17:05:00Z"

        assert audit.parse_run_id == (parse_run.id or 0)
        assert audit.applied_change_count == 1
        assert audit.resulting_apply_status == "fully_applied"
        assert audit.remaining_actionable_change_count == 0

        assert len(audits) == 1
        assert audits[0].id == audit.id
    finally:
        close_connection(connection)