from __future__ import annotations

import os

import uvicorn


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    return default


def main() -> None:
    host = os.environ.get("HIRING_RADAR_API_HOST", "127.0.0.1")
    port = int(os.environ.get("HIRING_RADAR_API_PORT", "8000"))
    reload_enabled = _parse_bool(
        os.environ.get("HIRING_RADAR_API_RELOAD"),
        default=os.environ.get("HIRING_RADAR_ENV", "development") == "development",
    )

    uvicorn.run(
        "hiring_radar.api.app:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )