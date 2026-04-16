from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.user_auth import UserSession


def _make_user_session(subscriber_id: int) -> UserSession:
    return UserSession(
        subscriber_id=subscriber_id,
        email="alice@example.com",
        issued_at="2026-04-11T10:00:00Z",
        expires_at="2026-04-11T12:00:00Z",
    )


def _build_authed_client(
    tmp_path: Path,
) -> tuple[TestClient, HiringRadarRepository, object, int]:
    connection = initialize_database(str(tmp_path / "profile_avatar.db"))
    repo = HiringRadarRepository(connection)
    subscriber, _ = repo.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-11T10:00:00Z",
    )
    subscriber_id = subscriber.id or 0

    app = create_app()
    app.dependency_overrides[get_current_user_session] = lambda: _make_user_session(
        subscriber_id
    )
    app.dependency_overrides[get_repository] = lambda: repo

    return TestClient(app), repo, connection, subscriber_id


def test_upload_avatar_persists_file_and_serves_current_avatar(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_root = tmp_path / "uploads"
    monkeypatch.setenv("HIRING_RADAR_UPLOAD_DIR", str(upload_root))

    client, repo, connection, subscriber_id = _build_authed_client(tmp_path)

    try:
        response = client.post(
            "/api/user/profile/upload/avatar",
            files={
                "file": (
                    "avatar.png",
                    b"\x89PNG\r\n\x1a\navatar-bytes",
                    "image/png",
                )
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["asset_id"]
        assert payload["url"].startswith("/api/user/profile/avatar?asset_id=")

        profile = repo.get_subscriber_profile(subscriber_id)
        assert profile.avatar_asset_id == payload["asset_id"]
        assert profile.avatar_content_type == "image/png"
        assert profile.avatar_storage_path is not None
        assert profile.avatar_url == payload["url"]

        stored_path = upload_root / Path(profile.avatar_storage_path)
        assert stored_path.exists()
        assert stored_path.read_bytes() == b"\x89PNG\r\n\x1a\navatar-bytes"

        image_response = client.get(payload["url"])
        assert image_response.status_code == 200
        assert image_response.headers["content-type"] == "image/png"
        assert image_response.content == b"\x89PNG\r\n\x1a\navatar-bytes"

        aggregate_response = client.get("/api/user/profile/aggregate")
        assert aggregate_response.status_code == 200
        aggregate_payload = aggregate_response.json()
        assert aggregate_payload["profile"]["avatar"]["asset_id"] == payload["asset_id"]
        assert aggregate_payload["profile"]["avatar"]["status"] == "ready"
    finally:
        close_connection(connection)
