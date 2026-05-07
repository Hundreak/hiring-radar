from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import (
    SubscriberCertificationEntry,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
)


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "subscriber_profile.db"))
    return HiringRadarRepository(connection), connection


def test_repository_returns_default_subscriber_profile(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-05T12:00:00Z",
        )

        profile = repo.get_subscriber_profile(subscriber.id or 0)

        assert profile.subscriber_id == (subscriber.id or 0)
        assert profile.phone is None
        assert profile.target_roles == ()
        assert profile.skills == ()
        assert profile.preferred_locations == ()
        assert profile.created_at is None
        assert profile.updated_at is None
    finally:
        close_connection(connection)


def test_repository_can_upsert_subscriber_profile(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-05T12:00:00Z",
        )

        profile = repo.upsert_subscriber_profile(
            subscriber.id or 0,
            phone="+90 555 000 00 00",
            headline="Backend Engineer",
            summary="Python, FastAPI and platform engineering background.",
            target_roles=("Backend Engineer", "Platform Engineer"),
            skills=("Python", "FastAPI", "PostgreSQL"),
            preferred_locations=("Remote", "Berlin"),
            remote_preference="remote",
            cv_filename=None,
            cv_uploaded_at=None,
            updated_at="2026-04-05T12:05:00Z",
        )

        assert profile.phone == "+90 555 000 00 00"
        assert profile.headline == "Backend Engineer"
        assert profile.target_roles == ("Backend Engineer", "Platform Engineer")
        assert profile.skills == ("Python", "FastAPI", "PostgreSQL")
        assert profile.preferred_locations == ("Remote", "Berlin")
        assert profile.remote_preference == "remote"
        assert profile.created_at == "2026-04-05T12:05:00Z"
        assert profile.updated_at == "2026-04-05T12:05:00Z"
    finally:
        close_connection(connection)


def test_repository_can_replace_education_and_experience_entries(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-05T12:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        education_entries = repo.replace_subscriber_education_entries(
            subscriber_id,
            entries=[
                SubscriberEducationEntry(
                    school_name="Technical University",
                    degree_name="BSc",
                    field_of_study="Computer Engineering",
                    start_year=2018,
                    end_year=2022,
                )
            ],
            updated_at="2026-04-05T12:10:00Z",
        )

        experience_entries = repo.replace_subscriber_experience_entries(
            subscriber_id,
            entries=[
                SubscriberExperienceEntry(
                    title="Backend Engineer",
                    company_name="Acme",
                    start_year=2022,
                    end_year=2025,
                    summary="Worked on APIs and data pipelines.",
                )
            ],
            updated_at="2026-04-05T12:12:00Z",
        )

        assert len(education_entries) == 1
        assert education_entries[0].school_name == "Technical University"
        assert education_entries[0].display_order == 0

        assert len(experience_entries) == 1
        assert experience_entries[0].title == "Backend Engineer"
        assert experience_entries[0].display_order == 0
    finally:
        close_connection(connection)


def test_repository_can_replace_generic_certification_entries(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-05T12:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        certifications = repo.replace_subscriber_certification_entries(
            subscriber_id,
            entries=[
                SubscriberCertificationEntry(
                    certificate_name="Certified Reliability Engineer",
                    issuer_name="American Society for Quality",
                    issued_year=2013,
                ),
                SubscriberCertificationEntry(
                    certificate_name="GD&T Professional",
                    issuer_name="ASME International",
                    issued_year=2018,
                ),
            ],
            updated_at="2026-04-05T12:20:00Z",
        )

        assert [item.certificate_name for item in certifications] == [
            "Certified Reliability Engineer",
            "GD&T Professional",
        ]
        assert certifications[0].issuer_name == "American Society for Quality"
        assert certifications[0].issued_year == 2013
        assert certifications[0].display_order == 0
        assert certifications[1].display_order == 1
    finally:
        close_connection(connection)
