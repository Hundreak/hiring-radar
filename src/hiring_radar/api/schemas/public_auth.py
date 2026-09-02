from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class PublicSignupVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=1, max_length=4096)
    password_confirmation: str = Field(min_length=1, max_length=4096)

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> PublicSignupVerificationRequest:
        if self.password != self.password_confirmation:
            raise ValueError("Password confirmation does not match.")
        return self


class PublicSignupVerificationResponse(BaseModel):
    ok: bool = True
    message: str


class PublicSignupConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    verification_code: str = Field(min_length=4, max_length=32)


class PublicSignupResponse(BaseModel):
    subscriber_id: int
    email: EmailStr
    full_name: str | None = None
    authenticated: bool = True
    message: str


# ---------------------------------------------------------------------------
# Backward-compatible aliases for older imports used elsewhere in the project
# ---------------------------------------------------------------------------

PublicSignupRequest = PublicSignupVerificationRequest
PublicSignupChallengeRequest = PublicSignupVerificationRequest
PublicSignupChallengeResponse = PublicSignupVerificationResponse
PublicCompleteSignupRequest = PublicSignupConfirmRequest
PublicCompleteSignupResponse = PublicSignupResponse

__all__ = [
    "PublicSignupVerificationRequest",
    "PublicSignupVerificationResponse",
    "PublicSignupConfirmRequest",
    "PublicSignupResponse",
    "PublicSignupRequest",
    "PublicSignupChallengeRequest",
    "PublicSignupChallengeResponse",
    "PublicCompleteSignupRequest",
    "PublicCompleteSignupResponse",
]