from __future__ import annotations

from pathlib import Path

from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.services.settings_store import serialize_app_settings, write_app_settings
from hiring_radar.settings import AppSettings, NotificationsSettings, load_app_settings


def test_serialize_app_settings_produces_expected_document() -> None:
    settings = AppSettings(
        keyword_filter=KeywordFilterSettings(
            include_keywords=("engineer",),
            exclude_keywords=("intern",),
            match_title=True,
            match_location=False,
            match_company_name=True,
        ),
        notifications=NotificationsSettings(
            apply_keyword_filter_to_digest=True,
        ),
    )

    document = serialize_app_settings(settings)

    assert document == {
        "keyword_filter": {
            "include_keywords": ["engineer"],
            "exclude_keywords": ["intern"],
            "match_title": True,
            "match_location": False,
            "match_company_name": True,
        },
        "notifications": {
            "apply_keyword_filter_to_digest": True,
        },
    }


def test_write_app_settings_roundtrips_to_loader(tmp_path: Path) -> None:
    config_path = tmp_path / "config" / "settings.local.yml"
    settings = AppSettings(
        keyword_filter=KeywordFilterSettings(
            include_keywords=("engineer",),
            exclude_keywords=("intern",),
            match_title=True,
            match_location=False,
            match_company_name=False,
        ),
        notifications=NotificationsSettings(
            apply_keyword_filter_to_digest=True,
        ),
    )

    write_app_settings(str(config_path), settings)

    loaded = load_app_settings(str(config_path))

    assert loaded.keyword_filter.include_keywords == ("engineer",)
    assert loaded.keyword_filter.exclude_keywords == ("intern",)
    assert loaded.keyword_filter.match_title is True
    assert loaded.keyword_filter.match_location is False
    assert loaded.keyword_filter.match_company_name is False
    assert loaded.notifications.apply_keyword_filter_to_digest is True
