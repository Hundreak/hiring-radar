from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database


def test_repository_notification_preferences_default_and_upsert(tmp_path: Path) -> None:
    connection = initialize_database(str(tmp_path / "notifications.db"))
    repository = HiringRadarRepository(connection)
    try:
        subscriber, _ = repository.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-04T09:00:00Z",
        )
        assert subscriber.id is not None

        default_preference = repository.get_subscriber_notification_preference(subscriber.id)
        assert default_preference is not None
        assert default_preference.job_digest_enabled is True
        assert default_preference.product_updates_enabled is False
        assert default_preference.employer_messages_enabled is True

        updated = repository.upsert_subscriber_notification_preference(
            subscriber.id,
            product_updates_enabled=True,
            employer_messages_enabled=False,
            quiet_hours_enabled=True,
            quiet_hours_start="21:00",
            quiet_hours_end="06:30",
            timezone="Europe/Istanbul",
            updated_at="2026-04-04T10:00:00Z",
        )

        assert updated is not None
        assert updated.product_updates_enabled is True
        assert updated.employer_messages_enabled is False
        assert updated.quiet_hours_enabled is True
        assert updated.quiet_hours_start == "21:00"
    finally:
        repository.close()
