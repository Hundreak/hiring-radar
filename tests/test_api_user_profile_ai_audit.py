from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.user_auth import UserSession


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=1,
        email="audit@example.com",
        issued_at="2026-04-13T10:00:00Z",
        expires_at="2026-04-13T12:00:00Z",
    )


def _seed_repository(repository: HiringRadarRepository) -> None:
    repository.upsert_subscriber(
        email="audit@example.com",
        full_name="Audit User",
        updated_at="2026-04-13T10:00:00Z",
    )
    repository.upsert_subscriber_profile(
        1,
        phone=None,
        headline="Existing headline",
        summary="Existing summary",
        target_roles=("Embedded Engineer",),
        skills=("Python",),
        preferred_locations=("Istanbul",),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-13T10:00:00Z",
    )
    repository.upsert_subscriber_skill_detail(
        1,
        skill_name="Python",
        category="Programming",
        proficiency_hint="Intermediate",
        years_hint=4,
        evidence_note="Automation scripts",
        updated_at="2026-04-13T10:00:00Z",
    )


class RepositoryProvider:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def __call__(self):
        connection = initialize_database(str(self.db_path))
        repository = HiringRadarRepository(connection)
        try:
            yield repository
        finally:
            close_connection(connection)


def test_ai_audit_create_finalize_and_export_json(tmp_path: Path) -> None:
    db_path = tmp_path / "audit.db"
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)
    _seed_repository(repository)
    close_connection(connection)

    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = RepositoryProvider(db_path)
    client = TestClient(app)

    create_response = client.post(
        "/api/user/profile/ai-audit/events",
        json={
            "telemetry_ref": "ai_test_ref",
            "target_field": "headline",
            "action_type": "replace",
            "source_panel": "headline-summary",
            "before_snapshot": "Existing headline",
            "after_snapshot": "Updated by AI",
            "persistence_status": "unsaved",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["target_field"] == "headline"
    assert created["persistence_status"] == "unsaved"

    finalize_response = client.patch(
        f"/api/user/profile/ai-audit/events/{created['id']}",
        json={
            "persistence_status": "saved",
            "saved_snapshot": "Updated by AI",
        },
    )
    assert finalize_response.status_code == 200
    finalized = finalize_response.json()
    assert finalized["persistence_status"] == "saved"
    assert finalized["evaluation_status"] == "accepted"
    assert finalized["evaluation_score"] == 1.0

    export_response = client.get("/api/user/profile/ai-audit/export?format=json")
    assert export_response.status_code == 200
    payload = json.loads(export_response.text)
    assert payload[0]["telemetry_ref"] == "ai_test_ref"


def test_ai_audit_revert_restores_saved_headline(tmp_path: Path) -> None:
    db_path = tmp_path / "audit-revert.db"
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)
    _seed_repository(repository)
    close_connection(connection)

    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = RepositoryProvider(db_path)
    client = TestClient(app)

    create_response = client.post(
        "/api/user/profile/ai-audit/events",
        json={
            "telemetry_ref": "ai_revert_ref",
            "target_field": "headline",
            "action_type": "replace",
            "source_panel": "headline-summary",
            "before_snapshot": "Existing headline",
            "after_snapshot": "AI headline",
            "persistence_status": "saved",
        },
    )
    audit_id = create_response.json()["id"]

    patch_response = client.patch(
        "/api/user/profile/basic-info",
        json={"headline": "AI headline"},
    )
    assert patch_response.status_code == 200

    revert_response = client.post(f"/api/user/profile/ai-audit/events/{audit_id}/revert")
    assert revert_response.status_code == 200
    reverted = revert_response.json()
    assert reverted["audit_log"]["evaluation_status"] == "reverted"
    assert reverted["aggregate"]["profile"]["headline"]["value"] == "Existing headline"


def test_system_health_reports_database_and_ai_runtime(tmp_path: Path) -> None:
    db_path = tmp_path / "audit-health.db"
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)
    _seed_repository(repository)
    close_connection(connection)

    app = create_app()
    app.dependency_overrides[get_repository] = RepositoryProvider(db_path)
    client = TestClient(app)

    response = client.get("/api/health/system")
    assert response.status_code == 200
    payload = response.json()
    assert payload["database"]["status"] == "ok"
    assert payload["ai_runtime"]["runtime_status"] in {"disabled", "ready", "unreachable", "misconfigured", "error"}
