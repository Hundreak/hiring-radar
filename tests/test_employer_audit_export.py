from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.db.employer_repository import EmployerRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.employer_auth import hash_password


def _register_owner(client: TestClient, *, company: str = "Audit Co") -> dict:
    response = client.post(
        "/api/employer/auth/register",
        json={
            "company_name": company,
            "company_email": f"owner@{company.lower().replace(' ', '')}.example",
            "password": "Admin12345!",
            "password_confirmation": "Admin12345!",
            "full_name": "Owner User",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_employer_audit_events_list_detail_and_export(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-audit-export.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())
    auth = _register_owner(client)

    connection = initialize_database(db_path)
    repository = EmployerRepository(connection)
    try:
        first_id = repository.create_audit_event(
            company_id=auth["company_id"],
            actor_user_id=auth["user_id"],
            event_type="employer.team.member.invited",
            resource_type="team_member",
            resource_id="42",
            before={},
            after={"role_key": "recruiter"},
            metadata={"reason": "test"},
        )
        repository.create_audit_event(
            company_id=auth["company_id"],
            actor_user_id=auth["user_id"],
            event_type="employer.candidate.note.created",
            resource_type="candidate_note",
            resource_id="88",
            before={},
            after={"note": "Strong React experience"},
            metadata={"candidate_id": 88},
        )
    finally:
        close_connection(connection)

    listed = client.get("/api/employer/compliance/audit-events?page_size=10")
    assert listed.status_code == 200, listed.text
    payload = listed.json()
    assert payload["ok"] is True
    assert payload["total_items"] >= 2
    assert payload["items"][0]["actor"]["email"] == auth["email"]
    assert any(item["event_type"] == "employer.team.member.invited" for item in payload["items"])

    filtered = client.get("/api/employer/compliance/audit-events?event_type=employer.candidate.note.created")
    assert filtered.status_code == 200, filtered.text
    assert filtered.json()["total_items"] == 1
    assert filtered.json()["items"][0]["sensitivity"] == "medium"

    detail = client.get(f"/api/employer/compliance/audit-events/{first_id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["item"]["id"] == first_id
    assert detail.json()["item"]["sensitivity"] == "high"

    exported_json = client.get("/api/employer/compliance/audit-events/export?format=json")
    assert exported_json.status_code == 200, exported_json.text
    assert exported_json.headers.get("X-Audit-Export-ID")
    assert exported_json.json()["format"] == "json"
    assert exported_json.json()["exported_items"] >= 2

    exported_csv = client.get("/api/employer/compliance/audit-events/export?format=csv")
    assert exported_csv.status_code == 200, exported_csv.text
    assert exported_csv.headers["content-type"].startswith("text/csv")
    assert "event_type" in exported_csv.text
    assert "employer.team.member.invited" in exported_csv.text

    after_export = client.get("/api/employer/compliance/audit-events?event_type=employer.audit.exported")
    assert after_export.status_code == 200, after_export.text
    assert after_export.json()["total_items"] >= 2


def test_employer_audit_events_require_owner_or_admin(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-audit-rbac.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    owner_client = TestClient(create_app())
    auth = _register_owner(owner_client, company="Audit RBAC")

    connection = initialize_database(db_path)
    repository = EmployerRepository(connection)
    try:
        viewer = repository.create_user(
            email="viewer@auditrbac.example",
            full_name="Viewer User",
            password_hash=hash_password("Viewer12345!"),
        )
        repository.add_team_member(
            company_id=auth["company_id"],
            user_id=viewer.id,
            role_key="viewer",
            status="active",
        )
        repository.create_audit_event(
            company_id=auth["company_id"],
            actor_user_id=auth["user_id"],
            event_type="employer.job.created",
            resource_type="job",
            resource_id="1",
        )
    finally:
        close_connection(connection)

    viewer_client = TestClient(create_app())
    login = viewer_client.post(
        "/api/employer/auth/login",
        json={"email": "viewer@auditrbac.example", "password": "Viewer12345!"},
    )
    assert login.status_code == 200, login.text

    denied = viewer_client.get("/api/employer/compliance/audit-events")
    assert denied.status_code == 403

    denied_export = viewer_client.get("/api/employer/compliance/audit-events/export?format=json")
    assert denied_export.status_code == 403
