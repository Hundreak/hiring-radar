from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

EmployerRoleKey = Literal["owner", "admin", "recruiter", "hiring_manager", "viewer"]
TeamMemberStatus = Literal["active", "invited", "disabled"]


class EmployerRegisterRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    company_email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    password_confirmation: str = Field(min_length=8, max_length=256)
    full_name: str | None = Field(default=None, max_length=160)
    website_url: str | None = Field(default=None, max_length=240)
    default_locale: Literal["tr", "en"] = "tr"


class EmployerLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class EmployerRefreshRequest(BaseModel):
    refresh_token: str | None = None


class EmployerTeamInvitationRequest(BaseModel):
    email: EmailStr
    role_key: EmployerRoleKey = "recruiter"


class EmployerTeamMemberUpdateRequest(BaseModel):
    role_key: EmployerRoleKey | None = None
    status: TeamMemberStatus | None = None


class EmployerAuthResponse(BaseModel):
    ok: bool = True
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    company_id: int
    member_id: int | None = None
    email: str
    full_name: str
    company_name: str
    role: str
    role_key: str
