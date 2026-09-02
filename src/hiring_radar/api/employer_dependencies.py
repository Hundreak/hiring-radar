from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from hiring_radar.api.dependencies import get_db_path
from hiring_radar.db.employer_repository import EmployerRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.employer_auth import (
    EMPLOYER_SESSION_COOKIE_NAME,
    EmployerAuthError,
    EmployerSession,
    decode_employer_session_token,
    load_employer_auth_settings,
)

http_bearer = HTTPBearer(auto_error=False)

EmployerSessionCookie = Annotated[
    str | None,
    Cookie(alias=EMPLOYER_SESSION_COOKIE_NAME),
]


def get_employer_repository() -> Generator[EmployerRepository, None, None]:
    connection = initialize_database(get_db_path())
    repository = EmployerRepository(connection)
    try:
        yield repository
    finally:
        close_connection(connection)


def get_current_employer_session(
    session_cookie: EmployerSessionCookie = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> EmployerSession:
    token = session_cookie
    if credentials is not None and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        return decode_employer_session_token(token, settings=load_employer_auth_settings())
    except EmployerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
