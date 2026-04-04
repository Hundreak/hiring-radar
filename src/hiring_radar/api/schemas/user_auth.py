from __future__ import annotations

from pydantic import BaseModel


class UserRequestMagicLinkRequest(BaseModel):
    email: str


class UserRequestMagicLinkResponse(BaseModel):
    ok: bool = True
    message: str


class UserConsumeMagicLinkRequest(BaseModel):
    token: str


class UserAuthMeResponse(BaseModel):
    subscriber_id: int
    email: str
    authenticated: bool = True