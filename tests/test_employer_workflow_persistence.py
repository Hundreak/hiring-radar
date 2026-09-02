from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from hiring_radar.db.employer_repository import EmployerRepository
from hiring_radar.db.sqlite import close_connection, initialize_database


def _register(client: TestClient) -> None:
    response = client.post(
        "/api/employer/auth/register",
        json={
            "company_name": "Workflow Labs",
            "company_email": "owner@workflowlabs.com",
            "password": "Admin12345!",
            "password_confirmation": "Admin12345!",
            "full_name": "Workflow Owner",
        },
    )
    assert response.status_code == 200, response.text


def _csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token
    return {CSRF_HEADER_NAME: token}


def test_candidate_workflow_tags_notes_and_stage_are_persisted_in_db(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "workflow.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())
    _register(client)

    tagged = client.post(
        "/api/employer/talent/workflow/bulk-tags",
        json={"candidate_ids": [1, 2], "tag": "Sıcak aday"},
        headers=_csrf_headers(client),
    )
    assert tagged.status_code == 200, tagged.text
    workflow = tagged.json()["workflow"]
    assert workflow["1"]["tags"] == ["Sıcak aday"]
    assert workflow["2"]["tags"] == ["Sıcak aday"]

    noted = client.post(
        "/api/employer/talent/workflow/bulk-notes",
        json={"candidate_ids": [1], "note": "Hiring manager teknik görüşme istiyor.", "tone": "ai"},
        headers=_csrf_headers(client),
    )
    assert noted.status_code == 200, noted.text
    assert noted.json()["workflow"]["1"]["notes"][0]["body"] == "Hiring manager teknik görüşme istiyor."

    staged = client.patch(
        "/api/employer/talent/workflow/stage",
        json={"candidate_id": 1, "stage_key": "shortlist", "note": "Ön eleme geçti."},
        headers=_csrf_headers(client),
    )
    assert staged.status_code == 200, staged.text
    assert staged.json()["workflow"]["1"]["stage"] == "shortlist"

    reloaded = client.get("/api/employer/talent/workflow")
    assert reloaded.status_code == 200, reloaded.text
    reloaded_workflow = reloaded.json()["workflow"]
    assert reloaded_workflow["1"]["tags"] == ["Sıcak aday"]
    assert reloaded_workflow["1"]["notes"][0]["tone"] == "ai"
    assert reloaded_workflow["1"]["stage"] == "shortlist"

    connection = initialize_database(str(db_path))
    try:
        repo = EmployerRepository(connection)
        candidates = repo.list_candidates(1)
        assert {candidate.id for candidate in candidates} >= {1, 2}
        assert repo.list_candidate_tags(company_id=1, candidate_id=1) == ["Sıcak aday"]
        audit_count = connection.execute("SELECT COUNT(*) AS count FROM employer_audit_events").fetchone()["count"]
        assert audit_count >= 3
    finally:
        close_connection(connection)


def test_candidate_workflow_tag_delete_and_campaign_side_effects_use_db(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "workflow-campaign.db"
    store_path = tmp_path / "outreach-store.json"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_OUTREACH_STORE_PATH", str(store_path))

    client = TestClient(create_app())
    _register(client)

    created = client.post(
        "/api/employer/outreach/campaigns",
        json={
            "candidate_ids": [3],
            "channel": "email",
            "tone": "warm",
            "template": "role-fit",
            "message_preview": "Profiliniz rol için güçlü görünüyor.",
            "response_rate": 72,
        },
        headers=_csrf_headers(client),
    )
    assert created.status_code == 200, created.text
    workflow = created.json()["workflow"]
    assert "Davet gönderilecek" in workflow["3"]["tags"]
    assert workflow["3"]["notes"][0]["tone"] == "ai"

    deleted = client.delete("/api/employer/talent/workflow/candidates/3/tags/Davet%20g%C3%B6nderilecek", headers=_csrf_headers(client))
    assert deleted.status_code == 200, deleted.text
    assert "Davet gönderilecek" not in deleted.json()["workflow"]["3"]["tags"]

    reloaded = client.get("/api/employer/talent/workflow")
    assert "Davet gönderilecek" not in reloaded.json()["workflow"]["3"]["tags"]
    assert reloaded.json()["workflow"]["3"]["notes"][0]["tone"] == "ai"



def test_outreach_campaigns_and_send_queue_are_persisted_in_db(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "outreach-db.db"
    legacy_store_path = tmp_path / "legacy-store-should-not-be-created.json"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_OUTREACH_STORE_PATH", str(legacy_store_path))

    client = TestClient(create_app())
    _register(client)

    created = client.post(
        "/api/employer/outreach/campaigns",
        json={
            "name": "Senior radar daveti",
            "candidate_ids": [7, 8],
            "channel": "email",
            "tone": "premium",
            "template": "salary-transparent",
            "include_salary": True,
            "include_calendar": False,
            "message_preview": "Profiliniz senior rol için güçlü görünüyor.",
            "response_rate": 81,
            "metadata": {"quality_score": 88},
        },
        headers=_csrf_headers(client),
    )
    assert created.status_code == 200, created.text
    campaign = created.json()["campaign"]
    assert campaign["candidate_ids"] == [7, 8]
    assert campaign["template"] == "salary-transparent"
    assert campaign["include_calendar"] is False

    listed = client.get("/api/employer/outreach/campaigns")
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()["items"]] == [campaign["id"]]

    before_queue = client.get(f"/api/employer/outreach/campaigns/{campaign['id']}/send-queue")
    assert before_queue.status_code == 200, before_queue.text
    assert before_queue.json()["queue"] is None

    prepared = client.post(
        f"/api/employer/outreach/campaigns/{campaign['id']}/send-queue/prepare",
        json={
            "actor": "Workflow Owner",
            "note": "İlk gönderim kuyruğu hazırlandı.",
            "items": [
                {
                    "candidate_id": 7,
                    "subject": "Senior rol için tanışalım",
                    "message": "Merhaba, profiliniz rol için çok güçlü görünüyor.",
                    "response_score": 92,
                    "status": "ready",
                    "checks": [],
                },
                {
                    "candidate_id": 8,
                    "subject": "Teknik liderlik fırsatı",
                    "message": "Rol detaylarını birlikte değerlendirmek isteriz.",
                    "response_score": 61,
                    "status": "review",
                    "checks": ["Takvim linki eksik"],
                },
            ],
        },
        headers=_csrf_headers(client),
    )
    assert prepared.status_code == 200, prepared.text
    queue = prepared.json()["queue"]
    assert queue["ready_count"] == 1
    assert queue["review_count"] == 1
    assert queue["blocked_count"] == 0
    assert queue["audit"][0]["action"] == "queue_prepared"
    assert {item["candidate_id"] for item in queue["items"]} == {7, 8}

    item_id = next(item["id"] for item in queue["items"] if item["candidate_id"] == 8)
    updated = client.patch(
        f"/api/employer/outreach/campaigns/{campaign['id']}/send-queue/items/{item_id}",
        json={"status": "blocked", "checks": ["Onay gerekiyor"], "note": "Hukuk onayı bekleniyor."},
        headers=_csrf_headers(client),
    )
    assert updated.status_code == 200, updated.text
    updated_queue = updated.json()["queue"]
    assert updated_queue["status"] == "blocked"
    assert updated_queue["blocked_count"] == 1
    assert updated_queue["audit"][0]["action"] == "queue_item_updated"

    reloaded = client.get(f"/api/employer/outreach/campaigns/{campaign['id']}/send-queue")
    assert reloaded.status_code == 200, reloaded.text
    assert reloaded.json()["queue"]["blocked_count"] == 1

    connection = initialize_database(str(db_path))
    try:
        campaign_rows = connection.execute("SELECT COUNT(*) AS count FROM employer_outreach_campaigns").fetchone()["count"]
        queue_rows = connection.execute("SELECT COUNT(*) AS count FROM employer_send_queue_items").fetchone()["count"]
        audit_rows = connection.execute("SELECT COUNT(*) AS count FROM employer_audit_events WHERE event_type LIKE 'send_queue%'").fetchone()["count"]
        assert campaign_rows == 1
        assert queue_rows == 2
        assert audit_rows >= 2
    finally:
        close_connection(connection)

    assert not legacy_store_path.exists()
