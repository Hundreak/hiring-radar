from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "subscriber_keyword_preferences.db"))
    return HiringRadarRepository(connection), connection


def test_repository_returns_default_keyword_preference_when_missing(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice",
            updated_at="2026-04-04T10:00:00Z",
        )

        preference = repo.get_subscriber_keyword_preference(subscriber.id or 0)

        assert preference.subscriber_id == (subscriber.id or 0)
        assert preference.include_keywords == ()
        assert preference.exclude_keywords == ()
        assert preference.match_title is True
        assert preference.match_location is True
        assert preference.match_company_name is True
        assert preference.updated_at is None
    finally:
        close_connection(connection)


def test_repository_can_upsert_keyword_preference(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice",
            updated_at="2026-04-04T10:00:00Z",
        )

        preference = repo.upsert_subscriber_keyword_preference(
            subscriber.id or 0,
            include_keywords=("engineer", "python"),
            exclude_keywords=("intern",),
            match_title=True,
            match_location=False,
            match_company_name=False,
            updated_at="2026-04-04T11:00:00Z",
        )

        assert preference.subscriber_id == (subscriber.id or 0)
        assert preference.include_keywords == ("engineer", "python")
        assert preference.exclude_keywords == ("intern",)
        assert preference.match_title is True
        assert preference.match_location is False
        assert preference.match_company_name is False
        assert preference.updated_at == "2026-04-04T11:00:00Z"
    finally:
        close_connection(connection)
