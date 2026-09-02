from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserMeResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_active: bool
    digest_enabled: bool
    created_at: str | None
    updated_at: str | None


class UserPreferencesUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    is_active: bool | None = None
    digest_enabled: bool | None = None

    def provided_update_fields(self) -> dict[str, object]:
        return {field_name: getattr(self, field_name) for field_name in self.model_fields_set}


class UserFilterPolicyResponse(BaseModel):
    filter_enabled: bool
    apply_keyword_filter_to_digest: bool
    include_keywords: list[str]
    exclude_keywords: list[str]
    active_fields: list[str]

class UserNotificationPreferenceResponse(BaseModel):
    subscriber_id: int
    job_digest_enabled: bool
    product_updates_enabled: bool
    employer_messages_enabled: bool
    security_alerts_enabled: bool
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str
    timezone: str
    updated_at: str | None


class UserNotificationPreferenceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_digest_enabled: bool | None = None
    product_updates_enabled: bool | None = None
    employer_messages_enabled: bool | None = None
    security_alerts_enabled: bool | None = None
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None

    def provided_update_fields(self) -> dict[str, object]:
        return {field_name: getattr(self, field_name) for field_name in self.model_fields_set}

