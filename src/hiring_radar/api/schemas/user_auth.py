from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserRequestMagicLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    redirect_path: str | None = Field(default=None, max_length=2048)


class UserRequestMagicLinkResponse(BaseModel):
    ok: bool = True
    message: str


class UserConsumeMagicLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=8, max_length=512)


class UserPasswordLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=1, max_length=4096)


class UserPasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class UserPasswordResetRequestResponse(BaseModel):
    ok: bool = True
    message: str


class UserConfirmPasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=8, max_length=512)
    password: str = Field(min_length=1, max_length=4096)
    password_confirmation: str = Field(min_length=1, max_length=4096)

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> UserConfirmPasswordResetRequest:
        if self.password != self.password_confirmation:
            raise ValueError("Password confirmation does not match.")
        return self


class UserConfirmPasswordResetResponse(BaseModel):
    ok: bool = True
    message: str


class UserAuthMeResponse(BaseModel):
    subscriber_id: int
    email: EmailStr
    authenticated: bool = True


class UserPasswordLoginResponse(UserAuthMeResponse):
    pass
