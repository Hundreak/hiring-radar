from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from hiring_radar.db.employer_repository import EmployerRepository
from hiring_radar.db.sqlite import close_connection, initialize_database


def _csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token
    return {CSRF_HEADER_NAME: token}


def _register_employer(client: TestClient, *, company: str = "NoyTera Labs") -> dict:
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


def test_employer_dashboard_uses_company_scoped_real_data(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-dashboard-real.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())
    auth = _register_employer(client)

    connection = initialize_database(db_path)
    repository = EmployerRepository(connection)
    try:
        job = repository.create_job(
            company_id=auth["company_id"],
            title="Senior Platform Engineer",
            status="published",
            department="Engineering",
            location="İstanbul / Remote",
            work_model="remote",
            quality_score=88,
            required_skills=["Python", "FastAPI", "React"],
            created_by_user_id=auth["user_id"],
            published_at="2026-05-25T09:00:00+00:00",
        )
        repository.create_job(
            company_id=auth["company_id"],
            title="Draft Recruiter Role",
            status="draft",
            department="People",
            created_by_user_id=auth["user_id"],
        )
        candidate = repository.upsert_candidate(
            company_id=auth["company_id"],
            external_candidate_id="cand-real-1",
            full_name="Ada Lovelace",
            headline="Platform Engineer",
            location="İstanbul",
            years_experience=6,
            source="talent_radar",
            match_score=72,
            intent_score=84,
            skills=["Python", "FastAPI", "React"],
            profile={"education": "İTÜ", "summary": "Strong backend/platform profile."},
        )
        repository.create_candidate_job_match(
            company_id=auth["company_id"],
            job_id=job.id,
            candidate_id=candidate.id,
            stage_key="new",
            match_score=91,
            intent_score=84,
            explanation={"summary": "Strong overlap.", "breakdown": {"skills": 94, "experience": 88}},
        )
    finally:
        close_connection(connection)

    stats = client.get("/api/employer/dashboard/stats")
    assert stats.status_code == 200, stats.text
    assert stats.json()["stats"]["active_jobs"] == 1
    assert stats.json()["stats"]["total_jobs"] == 2
    assert stats.json()["stats"]["total_applications"] == 1
    assert stats.json()["stats"]["pending_reviews"] == 1
    assert stats.json()["stats"]["avg_match_score"] == 91.0

    recent_jobs = client.get("/api/employer/dashboard/recent-jobs")
    assert recent_jobs.status_code == 200, recent_jobs.text
    items = recent_jobs.json()["items"]
    assert any(item["title"] == "Senior Platform Engineer" and item["applicants"] == 1 for item in items)
    assert any(item["title"] == "Senior Platform Engineer" and item["status"] == "active" for item in items)

    candidates = client.get("/api/employer/dashboard/top-candidates")
    assert candidates.status_code == 200, candidates.text
    assert candidates.json()["items"][0]["name"] == "Ada Lovelace"
    assert candidates.json()["items"][0]["match_score"] == 91

    matches = client.get("/api/employer/matches")
    assert matches.status_code == 200, matches.text
    assert matches.json()["items"][0]["candidate_name"] == "Ada Lovelace"
    assert matches.json()["items"][0]["job_title"] == "Senior Platform Engineer"

    detail = client.get(f"/api/employer/candidates/{candidate.id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["candidate"]["name"] == "Ada Lovelace"
    assert detail.json()["candidate"]["match_breakdown"]["skills"] == 94

    analytics = client.get("/api/employer/analytics")
    assert analytics.status_code == 200, analytics.text
    assert analytics.json()["kpi"]["total_applicants"] == 1
    assert analytics.json()["match_distribution"] == [{"range": "90-100%", "count": 1}]


def test_employer_create_job_writes_real_db_job(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-dashboard-create-job.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    client = TestClient(create_app())
    _register_employer(client, company="Create Job Co")

    created = client.post(
        "/api/employer/jobs",
        json={
            "title": "Backend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "status": "active",
            "required_skills": ["Python", "PostgreSQL"],
            "quality_score": 82,
        },
        headers=_csrf_headers(client),
    )
    assert created.status_code == 200, created.text
    assert created.json()["job"]["title"] == "Backend Engineer"
    assert created.json()["job"]["status"] == "active"

    jobs = client.get("/api/employer/jobs?status=active")
    assert jobs.status_code == 200, jobs.text
    assert [item["title"] for item in jobs.json()["items"]] == ["Backend Engineer"]


def test_employer_dashboard_is_company_scoped(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "employer-dashboard-scoped.db"
    monkeypatch.setenv("HIRING_RADAR_DB_PATH", str(db_path))
    monkeypatch.setenv("HIRING_RADAR_EMPLOYER_SESSION_SECRET", "test-employer-secret")

    first = TestClient(create_app())
    first_auth = _register_employer(first, company="First Co")
    second = TestClient(create_app())
    second_auth = _register_employer(second, company="Second Co")

    connection = initialize_database(db_path)
    repository = EmployerRepository(connection)
    try:
        repository.create_job(
            company_id=first_auth["company_id"],
            title="Private First Job",
            status="published",
            created_by_user_id=first_auth["user_id"],
        )
        repository.create_job(
            company_id=second_auth["company_id"],
            title="Private Second Job",
            status="published",
            created_by_user_id=second_auth["user_id"],
        )
    finally:
        close_connection(connection)

    first_jobs = first.get("/api/employer/jobs")
    second_jobs = second.get("/api/employer/jobs")
    assert first_jobs.status_code == 200
    assert second_jobs.status_code == 200
    assert [item["title"] for item in first_jobs.json()["items"]] == ["Private First Job"]
    assert [item["title"] for item in second_jobs.json()["items"]] == ["Private Second Job"]
