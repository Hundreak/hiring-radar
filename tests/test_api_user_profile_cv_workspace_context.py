from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import SubscriberLanguageCertificate
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
) -> tuple[TestClient, HiringRadarRepository, int]:
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

    return TestClient(app), repo, subscriber_id


def test_get_user_cv_workspace_context_returns_latest_upload_and_certificates(
    tmp_path: Path,
) -> None:
    client, repo, subscriber_id = _build_authed_client(
        tmp_path,
        db_filename="profile_cv_workspace_context.db",
    )

    repo.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="alice_cv.pdf",
        content_type="application/pdf",
        file_size_bytes=4096,
        storage_path="user_uploads/cv/alice_cv.pdf",
        parse_status="parsed",
        extracted_text="Alice Example\nSenior Engineer\nPython",
        uploaded_at="2026-04-05T10:00:00Z",
        parsed_at="2026-04-05T10:00:05Z",
    )

    repo.replace_subscriber_language_certificates(
        subscriber_id,
        certificates=[
            SubscriberLanguageCertificate(
                language_entry_id=None,
                certificate_name="IELTS Academic",
                issuer_name="British Council",
                file_name="ielts.pdf",
                storage_path="user_uploads/language_certificates/ielts.pdf",
                uploaded_at="2026-04-05T10:05:00Z",
            )
        ],
        updated_at="2026-04-05T10:05:00Z",
    )

    response = client.get("/api/user/profile/cv/workspace-context")

    assert response.status_code == 200
    payload = response.json()

    assert payload["latest_cv_upload"] is not None
    assert payload["latest_cv_upload"]["original_filename"] == "alice_cv.pdf"
    assert payload["latest_cv_upload"]["parse_status"] == "parsed"
    assert payload["latest_cv_upload"]["enterprise_metadata"] is not None

    assert len(payload["language_certificates"]) == 1
    assert payload["language_certificates"][0]["certificate_name"] == "IELTS Academic"
    assert payload["language_certificates"][0]["issuer_name"] == "British Council"

    uploads = repo.list_subscriber_cv_uploads(subscriber_id)
    assert len(uploads) == 1
