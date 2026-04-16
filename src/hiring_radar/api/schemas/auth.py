from __future__ import annotations

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminAuthMeResponse(BaseModel):
    email: str
    authenticated: bool = True
