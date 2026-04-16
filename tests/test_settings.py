from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from hiring_radar.config import ConfigError
from hiring_radar.filtering.models import KeywordFilterSettings

_KEYWORD_FILTER_ALLOWED_KEYS = frozenset(
    {
        "include_keywords",
        "exclude_keywords",
        "match_title",
        "match_location",
        "match_company_name",
    }
)


@dataclass(slots=True, frozen=True)
class AppSettings:
    keyword_filter: KeywordFilterSettings = field(default_factory=KeywordFilterSettings)


def _read_settings_document(config_path: str) -> dict[str, Any]:
    path = Path(config_path)

    if not path.exists():
        raise ConfigError(f"Settings config file does not exist: {config_path}")

    if not path.is_file():
        raise ConfigError(f"Settings config path is not a file: {config_path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in settings config ({config_path}): {exc}") from exc

    if raw is None:
        return {}

    if not isinstance(raw, dict):
        raise ConfigError(f"Settings config must contain a top-level mapping: {config_path}")

    return raw


def _require_mapping(
    *,
    section_name: str,
    value: Any,
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise ConfigError(f"'{section_name}' must be a mapping/object.")

    return value


def _coerce_string_tuple(
    *,
    field_name: str,
    value: Any,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(value, list):
        raise ConfigError(f"'{field_name}' must be a list of strings.")

    result: list[str] = []

    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ConfigError(
                f"'{field_name}[{index}]' must be a string, got {type(item).__name__}."
            )
        result.append(item)

    return tuple(result)


def _coerce_bool(
    *,
    field_name: str,
    value: Any,
    default: bool,
) -> bool:
    if value is None:
        return default

    if not isinstance(value, bool):
        raise ConfigError(f"'{field_name}' must be a boolean.")

    return value


def _load_keyword_filter_settings(raw_section: dict[str, Any]) -> KeywordFilterSettings:
    unknown_keys = sorted(set(raw_section) - _KEYWORD_FILTER_ALLOWED_KEYS)
    if unknown_keys:
        joined = ", ".join(unknown_keys)
        raise ConfigError(f"Unknown keyword_filter setting(s): {joined}")

    try:
        return KeywordFilterSettings(
            include_keywords=_coerce_string_tuple(
                field_name="keyword_filter.include_keywords",
                value=raw_section.get("include_keywords"),
            ),
            exclude_keywords=_coerce_string_tuple(
                field_name="keyword_filter.exclude_keywords",
                value=raw_section.get("exclude_keywords"),
            ),
            match_title=_coerce_bool(
                field_name="keyword_filter.match_title",
                value=raw_section.get("match_title"),
                default=True,
            ),
            match_location=_coerce_bool(
                field_name="keyword_filter.match_location",
                value=raw_section.get("match_location"),
                default=True,
            ),
            match_company_name=_coerce_bool(
                field_name="keyword_filter.match_company_name",
                value=raw_section.get("match_company_name"),
                default=True,
            ),
        )
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def load_app_settings(config_path: str) -> AppSettings:
    raw = _read_settings_document(config_path)

    raw_keyword_filter = _require_mapping(
        section_name="keyword_filter",
        value=raw.get("keyword_filter"),
    )

    return AppSettings(
        keyword_filter=_load_keyword_filter_settings(raw_keyword_filter),
    )
