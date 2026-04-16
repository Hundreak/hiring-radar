from __future__ import annotations

from hiring_radar.models import (
    Subscriber,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberProfile,
)
from hiring_radar.services.profile_completeness import (
    calculate_subscriber_profile_completeness,
)


def test_profile_completeness_returns_full_score_for_complete_profile() -> None:
    subscriber = Subscriber(
        id=1,
        email="alice@example.com",
        full_name="Alice Example",
        is_active=True,
        digest_enabled=True,
    )
    profile = SubscriberProfile(
        subscriber_id=1,
        phone="+90 555 000 00 00",
        headline="Backend Engineer",
        summary="Experienced backend engineer.",
        target_roles=("Backend Engineer",),
        skills=("Python", "FastAPI", "PostgreSQL"),
        preferred_locations=("Remote",),
        remote_preference="remote",
        cv_filename="alice_cv.pdf",
        cv_uploaded_at="2026-04-05T12:00:00Z",
    )
    education_entries = [
        SubscriberEducationEntry(
            school_name="Technical University",
            degree_name="BSc",
            field_of_study="Computer Engineering",
        )
    ]
    experience_entries = [
        SubscriberExperienceEntry(
            title="Backend Engineer",
            company_name="Acme",
            summary="API development",
        )
    ]

    completeness = calculate_subscriber_profile_completeness(
        subscriber=subscriber,
        profile=profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
    )

    assert completeness.score == 100
    assert completeness.missing_items == ()


def test_profile_completeness_identifies_missing_sections() -> None:
    subscriber = Subscriber(
        id=1,
        email="alice@example.com",
        full_name=None,
        is_active=True,
        digest_enabled=True,
    )
    profile = SubscriberProfile(subscriber_id=1)
    completeness = calculate_subscriber_profile_completeness(
        subscriber=subscriber,
        profile=profile,
        education_entries=[],
        experience_entries=[],
    )

    assert completeness.score == 0
    assert "full_name" in completeness.missing_items
    assert "skills" in completeness.missing_items
    assert "cv_upload" in completeness.missing_items
