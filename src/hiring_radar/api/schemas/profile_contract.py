from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")




class AiAuditFinalizeContext(StrictSchema):
    audit_event_ids: list[str] = Field(default_factory=list)

class ProfileValueSource(str, Enum):
    EXTRACTED = "extracted"
    USER = "user"
    MERGED = "merged"


class CompletionSectionStatus(str, Enum):
    DONE = "done"
    PARTIAL = "partial"
    MISSING = "missing"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    OTHER = "other"


class WorkMode(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


class LanguageProficiency(str, Enum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    PROFESSIONAL_WORKING = "professional_working"
    FULL_PROFESSIONAL = "full_professional"
    NATIVE_OR_BILINGUAL = "native_or_bilingual"


class SuggestionImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProfileTextField(StrictSchema):
    value: str | None = None
    source_type: ProfileValueSource = ProfileValueSource.EXTRACTED
    source_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_user_edited: bool = False
    raw_origin_ref: str | None = None
    last_confirmed_at: str | None = None


class ProfileAvatarSummary(StrictSchema):
    asset_id: str | None = None
    url: str | None = None
    status: str = "missing"


class ProfileCompletionSection(StrictSchema):
    key: str
    label: str
    status: CompletionSectionStatus


class ProfileCompletenessSummary(StrictSchema):
    score: int = Field(ge=0, le=100)
    sections: list[ProfileCompletionSection] = Field(default_factory=list)


class LastCvParseSummary(StrictSchema):
    parse_run_id: str | None = None
    parsed_at: str | None = None
    source_file_name: str | None = None


class ProfileExperienceRecord(StrictSchema):
    id: str | None = None
    title: str
    company_name: str
    location: str | None = None
    employment_type: EmploymentType | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    skills_used: list[str] = Field(default_factory=list)
    display_order: int = 0
    source_type: ProfileValueSource = ProfileValueSource.EXTRACTED
    source_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_user_edited: bool = False
    is_suppressed: bool = False


class ProfileEducationRecord(StrictSchema):
    id: str | None = None
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    description: str | None = None
    display_order: int = 0
    source_type: ProfileValueSource = ProfileValueSource.EXTRACTED
    source_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_user_edited: bool = False
    is_suppressed: bool = False


class ProfileLanguageRecord(StrictSchema):
    id: str | None = None
    language_name: str
    proficiency_level: LanguageProficiency | None = None
    certificate_name: str | None = None
    display_order: int = 0
    source_type: ProfileValueSource = ProfileValueSource.EXTRACTED
    source_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_user_edited: bool = False
    is_suppressed: bool = False


class ProfileSkillRecord(StrictSchema):
    id: str | None = None
    skill_name: str
    category: str | None = None
    proficiency_hint: str | None = None
    years_hint: int | None = Field(default=None, ge=0)
    display_order: int = 0
    source_type: ProfileValueSource = ProfileValueSource.EXTRACTED
    source_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_user_edited: bool = False
    is_suppressed: bool = False


class ProfilePreferencesRecord(StrictSchema):
    preferred_locations: list[str] = Field(default_factory=list)
    work_modes: list[WorkMode] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    salary_expectation: str | None = None
    relocation: bool | None = None


class CandidateProfileAggregate(StrictSchema):
    id: str
    user_id: str
    full_name: ProfileTextField
    headline: ProfileTextField
    summary: ProfileTextField
    primary_email: ProfileTextField
    phone: ProfileTextField
    avatar: ProfileAvatarSummary = Field(default_factory=ProfileAvatarSummary)
    preferences: ProfilePreferencesRecord = Field(default_factory=ProfilePreferencesRecord)
    completeness: ProfileCompletenessSummary
    experiences: list[ProfileExperienceRecord] = Field(default_factory=list)
    education: list[ProfileEducationRecord] = Field(default_factory=list)
    languages: list[ProfileLanguageRecord] = Field(default_factory=list)
    skills: list[ProfileSkillRecord] = Field(default_factory=list)
    last_cv_parse: LastCvParseSummary | None = None
    created_at: str
    updated_at: str


class ProfileSuggestionItem(StrictSchema):
    id: str
    title: str
    description: str
    impact_level: SuggestionImpactLevel = SuggestionImpactLevel.LOW
    action_type: str | None = None
    target_section: str | None = None


class ProfileSuggestionsBundle(StrictSchema):
    highlights: list[ProfileSuggestionItem] = Field(default_factory=list)
    critical_gaps: list[ProfileSuggestionItem] = Field(default_factory=list)
    quick_wins: list[ProfileSuggestionItem] = Field(default_factory=list)


class UserProfileAggregateResponse(StrictSchema):
    profile: CandidateProfileAggregate
    suggestions: ProfileSuggestionsBundle


class UpdateBasicInfoRequest(StrictSchema):
    full_name: str | None = None
    headline: str | None = None
    primary_email: str | None = None
    phone: str | None = None
    summary: str | None = None
    ai_audit_context: AiAuditFinalizeContext | None = None


class UpdatePreferencesRequest(StrictSchema):
    preferred_locations: list[str] = Field(default_factory=list)
    work_modes: list[WorkMode] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    salary_expectation: str | None = None
    relocation: bool | None = None
    ai_audit_context: AiAuditFinalizeContext | None = None


class CreateExperienceRequest(StrictSchema):
    title: str
    company_name: str
    location: str | None = None
    employment_type: EmploymentType | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    skills_used: list[str] = Field(default_factory=list)


class UpdateExperienceRequest(StrictSchema):
    title: str | None = None
    company_name: str | None = None
    location: str | None = None
    employment_type: EmploymentType | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None
    description: str | None = None
    skills_used: list[str] | None = None
    display_order: int | None = Field(default=None, ge=0)


class CreateEducationRequest(StrictSchema):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    description: str | None = None


class UpdateEducationRequest(StrictSchema):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    description: str | None = None
    display_order: int | None = Field(default=None, ge=0)


class CreateLanguageRequest(StrictSchema):
    language_name: str
    proficiency_level: LanguageProficiency | None = None
    certificate_name: str | None = None


class UpdateLanguageRequest(StrictSchema):
    language_name: str | None = None
    proficiency_level: LanguageProficiency | None = None
    certificate_name: str | None = None
    display_order: int | None = Field(default=None, ge=0)


class CreateSkillRequest(StrictSchema):
    skill_name: str
    category: str | None = None
    proficiency_hint: str | None = None
    years_hint: int | None = Field(default=None, ge=0)


class UpdateSkillRequest(StrictSchema):
    skill_name: str | None = None
    category: str | None = None
    proficiency_hint: str | None = None
    years_hint: int | None = Field(default=None, ge=0)
    display_order: int | None = Field(default=None, ge=0)


class ProfileAvatarUploadResponse(StrictSchema):
    asset_id: str
    url: str
    status: str = "ready"