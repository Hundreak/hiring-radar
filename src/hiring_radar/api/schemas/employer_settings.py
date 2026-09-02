from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

EmployerNotificationRoute = Literal["owner", "admin", "recruiter", "hiring_manager"]
EmployerNotificationChannel = Literal["email", "in_app", "email_and_in_app"]

_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class EmployerCommunicationPreferences(BaseModel):
    candidate_alerts_enabled: bool = True
    campaign_review_enabled: bool = True
    weekly_leadership_digest_enabled: bool = False
    product_updates_enabled: bool = False
    security_alerts_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    timezone: str = Field(default="Europe/Istanbul", min_length=2, max_length=80)
    default_channel: EmployerNotificationChannel = "email"
    notification_emails: list[EmailStr] = Field(default_factory=list, max_length=10)
    route_overdue_candidates_to: EmployerNotificationRoute = "owner"
    route_hot_candidates_to: EmployerNotificationRoute = "recruiter"
    route_campaign_review_to: EmployerNotificationRoute = "recruiter"
    route_weekly_digest_to: EmployerNotificationRoute = "owner"

    @field_validator("quiet_hours_start", "quiet_hours_end")
    @classmethod
    def validate_time(cls, value: str) -> str:
        normalized = value.strip()
        if not _TIME_PATTERN.match(normalized):
            raise ValueError("time_must_be_hh_mm")
        return normalized

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        normalized = value.strip()
        if "/" not in normalized or any(char.isspace() for char in normalized):
            raise ValueError("timezone_must_be_iana_like")
        return normalized


class EmployerCommunicationPreferencesUpdate(BaseModel):
    candidate_alerts_enabled: bool | None = None
    campaign_review_enabled: bool | None = None
    weekly_leadership_digest_enabled: bool | None = None
    product_updates_enabled: bool | None = None
    security_alerts_enabled: bool | None = None
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = Field(default=None, min_length=2, max_length=80)
    default_channel: EmployerNotificationChannel | None = None
    notification_emails: list[EmailStr] | None = Field(default=None, max_length=10)
    route_overdue_candidates_to: EmployerNotificationRoute | None = None
    route_hot_candidates_to: EmployerNotificationRoute | None = None
    route_campaign_review_to: EmployerNotificationRoute | None = None
    route_weekly_digest_to: EmployerNotificationRoute | None = None

    @field_validator("quiet_hours_start", "quiet_hours_end")
    @classmethod
    def validate_optional_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not _TIME_PATTERN.match(normalized):
            raise ValueError("time_must_be_hh_mm")
        return normalized

    @field_validator("timezone")
    @classmethod
    def validate_optional_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if "/" not in normalized or any(char.isspace() for char in normalized):
            raise ValueError("timezone_must_be_iana_like")
        return normalized


class EmployerCommunicationTeamSummary(BaseModel):
    active_members: int
    invited_members: int
    roles: dict[str, int]


class EmployerCommunicationPreferencesResponse(BaseModel):
    ok: bool = True
    company_id: int
    preferences: EmployerCommunicationPreferences
    team_summary: EmployerCommunicationTeamSummary
    updated_at: str | None = None
