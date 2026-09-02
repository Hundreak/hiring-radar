from __future__ import annotations

from hiring_radar.db.employer_repository import EmployerRepository
from hiring_radar.db.sqlite import close_connection, initialize_database


def _table_names(connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name LIKE 'employer_%'
        """
    ).fetchall()
    return {row["name"] for row in rows}


def test_employer_schema_is_initialized_with_application_database(tmp_path):
    db_path = tmp_path / "hiring_radar.db"
    connection = initialize_database(str(db_path))
    try:
        tables = _table_names(connection)
    finally:
        close_connection(connection)

    assert {
        "employer_companies",
        "employer_users",
        "employer_team_members",
        "employer_roles",
        "employer_jobs",
        "employer_candidates",
        "employer_candidate_job_matches",
        "employer_pipeline_stages",
        "employer_candidate_stage_history",
        "employer_candidate_notes",
        "employer_candidate_tags",
        "employer_outreach_campaigns",
        "employer_outreach_messages",
        "employer_send_queue_items",
        "employer_audit_events",
    }.issubset(tables)


def test_employer_repository_creates_workspace_roles_pipeline_and_core_records(tmp_path):
    db_path = tmp_path / "hiring_radar.db"
    connection = initialize_database(str(db_path))
    repo = EmployerRepository(connection)

    try:
        company = repo.create_company(
            name="NoyTera Teknoloji",
            slug="noytera",
            plan_tier="growth",
            brand_profile={"promise": "24 saat içinde dönüş"},
        )
        owner = repo.create_user(
            email="owner@noytera.com",
            full_name="NoyTera Owner",
            password_hash="hashed-password",
            title="Founder",
        )
        member = repo.add_team_member(company_id=company.id, user_id=owner.id, role_key="owner")

        roles = repo.list_roles(company.id)
        stages = repo.list_pipeline_stages(company.id)

        job = repo.create_job(
            company_id=company.id,
            title="Senior Frontend Engineer",
            status="published",
            location="İstanbul",
            work_model="hybrid",
            salary_min=120000,
            salary_max=170000,
            required_skills=["React", "TypeScript"],
            preferred_skills=["Design Systems"],
            quality_score=84,
            quality_factors={"salary_transparency": "strong"},
            risk_flags=["domain_depth_check"],
            created_by_user_id=owner.id,
        )
        candidate = repo.upsert_candidate(
            company_id=company.id,
            external_candidate_id="cand-1",
            full_name="Ada Lovelace",
            headline="Frontend Platform Engineer",
            email="ada@example.com",
            location="İstanbul",
            source="talent_radar",
            availability="immediate",
            match_score=94,
            intent_score=88,
            skills=["React", "TypeScript", "Design Systems"],
            profile={"summary": "Owns design system migrations."},
        )
        match_id = repo.create_candidate_job_match(
            company_id=company.id,
            job_id=job.id,
            candidate_id=candidate.id,
            stage_key="shortlist",
            match_score=94,
            intent_score=88,
            explanation={"must_have": ["React", "TypeScript"]},
        )
        repo.add_candidate_tag(company_id=company.id, candidate_id=candidate.id, tag="Sıcak aday")
        note_id = repo.add_candidate_note(
            company_id=company.id,
            candidate_id=candidate.id,
            author_user_id=owner.id,
            body="Hiring manager teknik görüşme istiyor.",
        )
        campaign = repo.create_outreach_campaign(
            company_id=company.id,
            created_by_user_id=owner.id,
            name="Frontend kısa liste daveti",
            channel="email",
            candidate_ids=[candidate.id],
            subject_preview="Senior Frontend rolü için tanışalım",
            message_preview="Profiliniz rol için güçlü görünüyor.",
            response_rate=72,
            metadata={"composer_version": "v2"},
        )
        audit_id = repo.create_audit_event(
            company_id=company.id,
            actor_user_id=owner.id,
            event_type="campaign.created",
            resource_type="outreach_campaign",
            resource_id=campaign.id,
            after={"status": campaign.status},
        )

        assert company.brand_profile["promise"] == "24 saat içinde dönüş"
        assert member.email == "owner@noytera.com"
        assert {role["role_key"] for role in roles} >= {"owner", "admin", "recruiter", "hiring_manager", "viewer"}
        assert [stage["stage_key"] for stage in stages][:3] == ["new", "reviewed", "shortlist"]
        assert repo.list_jobs(company.id)[0].required_skills == ["React", "TypeScript"]
        assert repo.list_candidates(company.id)[0].skills == ["React", "TypeScript", "Design Systems"]
        assert match_id >= 0
        assert repo.list_candidate_tags(company_id=company.id, candidate_id=candidate.id) == ["Sıcak aday"]
        assert note_id > 0
        assert repo.list_outreach_campaigns(company.id)[0].metadata["composer_version"] == "v2"
        assert audit_id > 0
    finally:
        close_connection(connection)


def test_employer_candidate_upsert_updates_existing_external_candidate(tmp_path):
    db_path = tmp_path / "hiring_radar.db"
    connection = initialize_database(str(db_path))
    repo = EmployerRepository(connection)

    try:
        company = repo.create_company(name="Acme", slug="acme")
        first = repo.upsert_candidate(
            company_id=company.id,
            external_candidate_id="same-candidate",
            full_name="First Name",
            match_score=70,
            skills=["React"],
        )
        second = repo.upsert_candidate(
            company_id=company.id,
            external_candidate_id="same-candidate",
            full_name="Updated Name",
            match_score=91,
            skills=["React", "TypeScript"],
        )

        assert second.id == first.id
        assert second.full_name == "Updated Name"
        assert second.match_score == 91
        assert second.skills == ["React", "TypeScript"]
        assert len(repo.list_candidates(company.id)) == 1
    finally:
        close_connection(connection)
