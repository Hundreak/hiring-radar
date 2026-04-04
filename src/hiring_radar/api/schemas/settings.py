from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AdminSettingsKeywordFilterResponse(BaseModel):
    include_keywords: list[str]
    exclude_keywords: list[str]
    match_title: bool
    match_location: bool
    match_company_name: bool
    enabled: bool
    active_fields: list[str]


class AdminSettingsNotificationsResponse(BaseModel):
    apply_keyword_filter_to_digest: bool


class AdminSettingsResponse(BaseModel):
    settings_path: str
    keyword_filter: AdminSettingsKeywordFilterResponse
    notifications: AdminSettingsNotificationsResponse


class AdminSettingsKeywordFilterUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    match_title: bool = True
    match_location: bool = True
    match_company_name: bool = True


class AdminSettingsNotificationsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    apply_keyword_filter_to_digest: bool = False


class AdminSettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keyword_filter: AdminSettingsKeywordFilterUpdate
    notifications: AdminSettingsNotificationsUpdate


class AdminFilterPreviewFieldMatchResponse(BaseModel):
    field_name: str
    keyword: str
    field_value: str


class AdminFilterPreviewSampleResponse(BaseModel):
    job_id: int | None
    title: str
    company_name: str
    location: str | None
    canonical_url: str
    include_matches: list[AdminFilterPreviewFieldMatchResponse]
    exclude_matches: list[AdminFilterPreviewFieldMatchResponse]


class AdminSettingsFilterPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keyword_filter: AdminSettingsKeywordFilterUpdate
    active_only: bool = True
    sample_limit: int = Field(default=5, ge=1, le=50)


class AdminSettingsFilterPreviewResponse(BaseModel):
    jobs_scope: str
    filter_enabled: bool
    include_keywords: list[str]
    exclude_keywords: list[str]
    active_fields: list[str]
    total_jobs: int
    passed_jobs: int
    rejected_jobs: int
    sample_limit: int
    passed_samples: list[AdminFilterPreviewSampleResponse]
    rejected_samples: list[AdminFilterPreviewSampleResponse]