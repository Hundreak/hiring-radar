from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import yaml

from hiring_radar.settings import AppSettings, load_app_settings


def serialize_app_settings(settings: AppSettings) -> dict[str, Any]:
    keyword_filter = settings.keyword_filter

    return {
        "keyword_filter": {
            "include_keywords": list(keyword_filter.include_keywords),
            "exclude_keywords": list(keyword_filter.exclude_keywords),
            "match_title": keyword_filter.match_title,
            "match_location": keyword_filter.match_location,
            "match_company_name": keyword_filter.match_company_name,
        },
        "notifications": {
            "apply_keyword_filter_to_digest": (
                settings.notifications.apply_keyword_filter_to_digest
            ),
        },
    }


def write_app_settings(config_path: str, settings: AppSettings) -> None:
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    document = serialize_app_settings(settings)
    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            yaml.safe_dump(
                document,
                handle,
                sort_keys=False,
                allow_unicode=True,
            )
            temporary_path = Path(handle.name)

        # Validate roundtrip before replacing the live file.
        load_app_settings(str(temporary_path))

        os.replace(temporary_path, path)

    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass