from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.config import ConfigError
from hiring_radar.settings import load_app_settings


def test_load_app_settings_defaults_notification_policy_to_false(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
keyword_filter:
  include_keywords: []
""".strip(),
        encoding="utf-8",
    )

    settings = load_app_settings(str(config_path))

    assert settings.notifications.apply_keyword_filter_to_digest is False


def test_load_app_settings_loads_notifications_block(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
keyword_filter:
  include_keywords:
    - engineer
notifications:
  apply_keyword_filter_to_digest: true
""".strip(),
        encoding="utf-8",
    )

    settings = load_app_settings(str(config_path))

    assert settings.keyword_filter.include_keywords == ("engineer",)
    assert settings.notifications.apply_keyword_filter_to_digest is True


def test_load_app_settings_rejects_non_mapping_notifications(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
notifications:
  - true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_app_settings(str(config_path))

    assert "'notifications' must be a mapping/object." in str(exc_info.value)


def test_load_app_settings_rejects_non_boolean_notification_policy(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
notifications:
  apply_keyword_filter_to_digest: "yes"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_app_settings(str(config_path))

    assert "'notifications.apply_keyword_filter_to_digest' must be a boolean." in str(
        exc_info.value
    )


def test_load_app_settings_rejects_unknown_notifications_keys(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
notifications:
  apply_keyword_filter_to_digest: true
  unknown_flag: true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_app_settings(str(config_path))

    assert "Unknown notifications setting(s): unknown_flag" in str(exc_info.value)
