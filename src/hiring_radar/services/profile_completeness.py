from __future__ import annotations

from hiring_radar.models import (
    Subscriber,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberProfile,
    SubscriberProfileCompleteness,
)


def calculate_subscriber_profile_completeness(
    *,
    subscriber: Subscriber,
    profile: SubscriberProfile,
    education_entries: list[SubscriberEducationEntry],
    experience_entries: list[SubscriberExperienceEntry],
) -> SubscriberProfileCompleteness:
    checks: list[tuple[str, bool]] = [
        ("full_name", bool(subscriber.full_name and subscriber.full_name.strip())),
        ("phone", bool(profile.phone and profile.phone.strip())),
        ("headline", bool(profile.headline and profile.headline.strip())),
        ("summary", bool(profile.summary and profile.summary.strip())),
        ("target_roles", len(profile.target_roles) >= 1),
        ("skills", len(profile.skills) >= 3),
        ("preferred_locations", len(profile.preferred_locations) >= 1),
        ("education", len(education_entries) >= 1),
        ("experience", len(experience_entries) >= 1),
        ("cv_upload", bool(profile.cv_filename and profile.cv_filename.strip())),
    ]

    completed_items = tuple(item_id for item_id, complete in checks if complete)
    missing_items = tuple(item_id for item_id, complete in checks if not complete)

    score = round((len(completed_items) / len(checks)) * 100) if checks else 0

    return SubscriberProfileCompleteness(
        score=score,
        completed_items=completed_items,
        missing_items=missing_items,
    )
