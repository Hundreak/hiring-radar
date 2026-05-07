from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import (
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
    SubscriberSkillDetail,
)
from hiring_radar.services.matching.profile_features import refresh_subscriber_profile_features


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "matching_profile_features.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


def test_refresh_subscriber_profile_features_persists_normalized_profile_signals(
    repository: HiringRadarRepository,
) -> None:
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-18T09:00:00Z",
    )
    subscriber_id = subscriber.id or 0

    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Senior Backend Engineer",
        summary="Python, FastAPI and distributed systems engineer open to remote roles.",
        target_roles=("Backend Engineer", "Platform Engineer"),
        skills=("Python", "FastAPI", "Docker", "Kubernetes"),
        preferred_locations=("Istanbul", "Berlin"),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T09:01:00Z",
    )
    repository.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                title="Backend Engineer",
                company_name="Acme",
                start_year=2019,
                end_year=2022,
                summary="Built Python APIs, Dockerized services and CI/CD pipelines.",
            ),
            SubscriberExperienceEntry(
                title="Senior Platform Engineer",
                company_name="Beta",
                start_year=2022,
                end_year=None,
                summary="Owned Kubernetes platform reliability and cloud automation.",
            ),
        ],
        updated_at="2026-04-18T09:02:00Z",
    )
    repository.replace_subscriber_education_entries(
        subscriber_id,
        entries=[
            SubscriberEducationEntry(
                school_name="Example University",
                degree_name="Bachelor of Science",
                field_of_study="Computer Engineering",
                start_year=2014,
                end_year=2018,
            )
        ],
        updated_at="2026-04-18T09:03:00Z",
    )
    repository.replace_subscriber_language_entries(
        subscriber_id,
        entries=[
            SubscriberLanguageEntry(language_name="English", proficiency_level="C1"),
            SubscriberLanguageEntry(language_name="Turkish", proficiency_level="Native"),
        ],
        updated_at="2026-04-18T09:04:00Z",
    )
    repository.upsert_subscriber_skill_detail(
        subscriber_id,
        skill_name="Python",
        category="programming",
        proficiency_hint="advanced",
        years_hint=5,
        evidence_note="Built FastAPI services and data pipelines.",
        evidence_file_name=None,
        evidence_storage_path=None,
        uploaded_at="2026-04-18T09:05:00Z",
        updated_at="2026-04-18T09:05:00Z",
    )

    result = refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:10:00Z",
    )

    feature = result.profile_feature
    assert result.created is True
    assert "software_engineering" in feature.role_families
    assert any(discipline in feature.discipline_preferences for discipline in ("backend", "devops"))
    assert "python" in feature.skill_terms
    assert "fastapi" in feature.skill_terms
    assert "english" in feature.language_capabilities
    assert "istanbul" in feature.preferred_location_tokens
    assert feature.education_level == "bachelor"
    assert feature.years_experience_total is not None
    assert feature.years_experience_total >= 6
    assert feature.remote_preference == "remote"
    assert feature.profile_strength_score >= 0.6
    assert "python" in feature.experience_evidence_terms
    assert feature.responsibility_scope in {"senior-ic", "tech-lead", "architect"}
    assert feature.ownership_signals
    assert any(signal in feature.impact_signals for signal in ("delivery", "automation", "scale"))

    persisted = repository.get_subscriber_profile_feature(subscriber_id=subscriber_id)
    assert persisted is not None
    assert "python" in persisted.experience_evidence_terms
    assert persisted.responsibility_scope == feature.responsibility_scope
    assert persisted.ownership_signals == feature.ownership_signals
    assert persisted.impact_signals == feature.impact_signals
