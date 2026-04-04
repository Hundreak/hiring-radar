from __future__ import annotations

import os
from collections.abc import Generator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException

from hiring_radar.api.security import (
    ADMIN_SESSION_COOKIE_NAME,
    AdminAuthError,
    AdminAuthSettings,
    AdminSession,
    decode_admin_session_token,
    load_admin_auth_settings,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.settings import AppSettings, load_app_settings


def get_db_path() -> str:
    return os.environ.get("HIRING_RADAR_DB_PATH", "data/hiring_radar.db")


def get_settings_path() -> str:
    return os.environ.get("HIRING_RADAR_SETTINGS_PATH", "config/settings.example.yml")


def get_env_path() -> str:
    return os.environ.get("HIRING_RADAR_ENV_PATH", ".env")


def get_repository() -> Generator[HiringRadarRepository, None, None]:
    connection = initialize_database(get_db_path())
    repository = HiringRadarRepository(connection)

    try:
        yield repository
    finally:
        close_connection(connection)


def get_app_settings() -> AppSettings:
    return load_app_settings(get_settings_path())


def get_admin_auth_settings() -> AdminAuthSettings:
    return load_admin_auth_settings(get_env_path())


AdminSessionCookie = Annotated[
    str | None,
    Cookie(alias=ADMIN_SESSION_COOKIE_NAME),
]

AdminAuthSettingsDep = Annotated[
    AdminAuthSettings,
    Depends(get_admin_auth_settings),
]


def get_current_admin_session(
    admin_session_cookie: AdminSessionCookie = None,
    auth_settings: AdminAuthSettingsDep = None,
) -> AdminSession:
    if auth_settings is None:
        raise HTTPException(status_code=500, detail="Admin auth settings are unavailable.")

    if not admin_session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    try:
        return decode_admin_session_token(
            token=admin_session_cookie,
            settings=auth_settings,
        )
    except AdminAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc