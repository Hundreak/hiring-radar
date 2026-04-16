from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class KeywordPreferenceFieldMatchResponse(BaseModel):
    field_name: str
    keyword: str
    field_value: str


class KeywordPreferenceSampleResponse(BaseModel):
    job_id: int | None
    title: str
    company_name: str
    location: str | None
    canonical_url: str
    include_matches: list[KeywordPreferenceFieldMatchResponse]
    exclude_matches: list[KeywordPreferenceFieldMatchResponse]


class SubscriberKeywordPreferenceResponse(BaseModel):
    subscriber_id: int
    include_keywords: list[str]
    exclude_keywords: list[str]
    match_title: bool
    match_location: bool
    match_company_name: bool
    enabled: bool
    active_fields: list[str]
    updated_at: str | None


class SubscriberKeywordPreferenceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    match_title: bool = True
    match_location: bool = True
    match_company_name: bool = True


class SubscriberKeywordPreferencePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keyword_preference: SubscriberKeywordPreferenceUpdateRequest
    active_only: bool = True
    sample_limit: int = Field(default=5, ge=1, le=50)


class SubscriberKeywordPreferencePreviewResponse(BaseModel):
    jobs_scope: str
    filter_enabled: bool
    include_keywords: list[str]
    exclude_keywords: list[str]
    active_fields: list[str]
    total_jobs: int
    passed_jobs: int
    rejected_jobs: int
    sample_limit: int
    passed_samples: list[KeywordPreferenceSampleResponse]
    rejected_samples: list[KeywordPreferenceSampleResponse]
