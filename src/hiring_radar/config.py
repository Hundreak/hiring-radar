from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hiring_radar.scrapers.base import ScraperSourceConfig


class ConfigError(Exception):
    """
    Raised when a configuration file is missing, malformed, or incomplete.
    """


def _read_yaml_file(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    if not config_path.is_file():
        raise ConfigError(f"Config path is not a file: {config_path}")

    try:
        raw_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file {config_path}: {exc}") from exc

    if raw_data is None:
        return {}

    if not isinstance(raw_data, dict):
        raise ConfigError(
            f"Top-level YAML structure must be a mapping/object in {config_path}"
        )

    return raw_data


def _require_non_empty_string(
    source_data: dict[str, Any],
    field_name: str,
    *,
    source_index: int,
) -> str:
    value = source_data.get(field_name)

    if not isinstance(value, str):
        raise ConfigError(
            f"Source entry at index {source_index} must define '{field_name}' as a string"
        )

    normalized_value = value.strip()
    if not normalized_value:
        raise ConfigError(
            f"Source entry at index {source_index} must define a non-empty '{field_name}'"
        )

    return normalized_value


def load_source_configs(path: str | Path) -> list[ScraperSourceConfig]:
    """
    Load source definitions from a YAML config file.

    Expected structure:

    sources:
      - source_name: demo-greenhouse
        company_name: Demo Company
        source_type: greenhouse
        url: https://boards.greenhouse.io/demo
    """
    raw_config = _read_yaml_file(path)
    raw_sources = raw_config.get("sources")

    if raw_sources is None:
        raise ConfigError("Config must contain a top-level 'sources' key")

    if not isinstance(raw_sources, list):
        raise ConfigError("Config field 'sources' must be a list")

    source_configs: list[ScraperSourceConfig] = []

    for index, item in enumerate(raw_sources):
        if not isinstance(item, dict):
            raise ConfigError(f"Source entry at index {index} must be a mapping/object")

        source_name = _require_non_empty_string(item, "source_name", source_index=index)
        company_name = _require_non_empty_string(item, "company_name", source_index=index)
        source_type = _require_non_empty_string(item, "source_type", source_index=index)
        url = _require_non_empty_string(item, "url", source_index=index)

        source_configs.append(
            ScraperSourceConfig(
                source_name=source_name,
                company_name=company_name,
                source_type=source_type,
                url=url,
            )
        )

    if not source_configs:
        raise ConfigError("Config field 'sources' must contain at least one source entry")

    return source_configs