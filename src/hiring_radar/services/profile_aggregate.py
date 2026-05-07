from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hiring_radar.services.cv_profile_parser import is_valid_spoken_language
from hiring_radar.api.schemas.profile_contract import (
    CandidateProfileAggregate,
    CompletionSectionStatus,
    LastCvParseSummary,
    ProfileAvatarSummary,
    ProfileCompletenessSummary,
    ProfileCompletionSection,
    ProfileEducationRecord,
    ProfileExperienceRecord,
    ProfileLanguageRecord,
    ProfilePreferencesRecord,
    ProfileSkillRecord,
    ProfileSuggestionItem,
    ProfileSuggestionsBundle,
    ProfileTextField,
    ProfileValueSource,
    SuggestionImpactLevel,
    UserProfileAggregateResponse,
    WorkMode,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _to_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [item.strip() for item in value.split(",")]
        return [item for item in parts if item]
    return []


def _to_work_modes(value: Any) -> list[WorkMode]:
    result: list[WorkMode] = []
    for item in _to_str_list(value):
        lowered = item.lower()
        if lowered in {"onsite", "on_site", "office"}:
            result.append(WorkMode.ONSITE)
        elif lowered in {"hybrid"}:
            result.append(WorkMode.HYBRID)
        elif lowered in {"remote"}:
            result.append(WorkMode.REMOTE)
    return result


def _source_from_flags(
    is_user_edited: bool,
    has_extracted_value: bool = True,
) -> ProfileValueSource:
    if is_user_edited and has_extracted_value:
        return ProfileValueSource.MERGED
    if is_user_edited:
        return ProfileValueSource.USER
    return ProfileValueSource.EXTRACTED


def _text_field(
    value: Any,
    *,
    is_user_edited: bool = False,
    confidence: float | None = None,
    raw_origin_ref: str | None = None,
) -> ProfileTextField:
    normalized = None
    if value is not None:
        text = str(value).strip()
        normalized = text or None

    return ProfileTextField(
        value=normalized,
        source_type=_source_from_flags(
            is_user_edited,
            has_extracted_value=normalized is not None,
        ),
        source_confidence=confidence,
        is_user_edited=is_user_edited,
        raw_origin_ref=raw_origin_ref,
        last_confirmed_at=None,
    )


def _build_experiences(raw_items: Any) -> list[ProfileExperienceRecord]:
    if not isinstance(raw_items, list):
        return []

    result: list[ProfileExperienceRecord] = []
    for index, item in enumerate(raw_items):
        start_date = _read(item, "start_date")
        if start_date is None:
            start_year = _read(item, "start_year")
            start_date = str(start_year) if start_year is not None else None

        end_date = _read(item, "end_date")
        if end_date is None:
            end_year = _read(item, "end_year")
            end_date = str(end_year) if end_year is not None else None

        description = _read(item, "description")
        if description is None:
            description = _read(item, "summary")

        result.append(
            ProfileExperienceRecord(
                id=str(_read(item, "id", f"exp_{index}")),
                title=str(_read(item, "title", "")).strip(),
                company_name=str(
                    _read(item, "company_name", _read(item, "company", ""))
                ).strip(),
                location=_read(item, "location"),
                employment_type=_read(item, "employment_type"),
                start_date=start_date,
                end_date=end_date,
                is_current=bool(_read(item, "is_current", False)),
                description=description,
                skills_used=_to_str_list(_read(item, "skills_used", [])),
                display_order=int(_read(item, "display_order", index)),
                source_type=ProfileValueSource(
                    _read(item, "source_type", "extracted")
                ),
                source_confidence=_read(item, "source_confidence"),
                is_user_edited=bool(_read(item, "is_user_edited", False)),
                is_suppressed=bool(_read(item, "is_suppressed", False)),
            )
        )
    return result


def _build_education(raw_items: Any) -> list[ProfileEducationRecord]:
    if not isinstance(raw_items, list):
        return []

    result: list[ProfileEducationRecord] = []
    for index, item in enumerate(raw_items):
        start_date = _read(item, "start_date")
        if start_date is None:
            start_year = _read(item, "start_year")
            start_date = str(start_year) if start_year is not None else None

        end_date = _read(item, "end_date")
        if end_date is None:
            end_year = _read(item, "end_year")
            end_date = str(end_year) if end_year is not None else None

        result.append(
            ProfileEducationRecord(
                id=str(_read(item, "id", f"edu_{index}")),
                institution=str(
                    _read(item, "institution", _read(item, "school_name", ""))
                ).strip(),
                degree=_read(item, "degree", _read(item, "degree_name")),
                field_of_study=_read(item, "field_of_study"),
                start_date=start_date,
                end_date=end_date,
                grade=_read(item, "grade"),
                description=_read(item, "description"),
                display_order=int(_read(item, "display_order", index)),
                source_type=ProfileValueSource(
                    _read(item, "source_type", "extracted")
                ),
                source_confidence=_read(item, "source_confidence"),
                is_user_edited=bool(_read(item, "is_user_edited", False)),
                is_suppressed=bool(_read(item, "is_suppressed", False)),
            )
        )
    return result


_LEGACY_PROFICIENCY_MAP: dict[str, str] = {
    "native": "native_or_bilingual",
    "bilingual": "native_or_bilingual",
    "native or bilingual": "native_or_bilingual",
    "fluent": "full_professional",
    "full professional": "full_professional",
    "professional": "professional_working",
    "professional working": "professional_working",
    "upper intermediate": "upper_intermediate",
    "upperintermediate": "upper_intermediate",
    "advanced": "advanced",
    "intermediate": "intermediate",
    "elementary": "elementary",
    "beginner": "beginner",
    "basic": "beginner",
}


def _normalize_proficiency(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    normalized = _LEGACY_PROFICIENCY_MAP.get(value.lower().strip())
    return normalized if normalized is not None else value


def _build_languages(raw_items: Any) -> list[ProfileLanguageRecord]:
    if not isinstance(raw_items, list):
        return []

    result: list[ProfileLanguageRecord] = []
    for index, item in enumerate(raw_items):
        language_name = str(
            _read(item, "language_name", _read(item, "name", ""))
        ).strip()
        if not is_valid_spoken_language(language_name):
            continue
        result.append(
            ProfileLanguageRecord(
                id=str(_read(item, "id", f"lang_{index}")),
                language_name=language_name,
                proficiency_level=_normalize_proficiency(_read(item, "proficiency_level")),
                certificate_name=_read(item, "certificate_name"),
                display_order=int(_read(item, "display_order", index)),
                source_type=ProfileValueSource(
                    _read(item, "source_type", "extracted")
                ),
                source_confidence=_read(item, "source_confidence"),
                is_user_edited=bool(_read(item, "is_user_edited", False)),
                is_suppressed=bool(_read(item, "is_suppressed", False)),
            )
        )
    return result


def _build_skills(raw_items: Any) -> list[ProfileSkillRecord]:
    if isinstance(raw_items, str):
        raw_items = _to_str_list(raw_items)
    elif isinstance(raw_items, tuple):
        raw_items = list(raw_items)

    if not isinstance(raw_items, list):
        return []

    result: list[ProfileSkillRecord] = []
    for index, item in enumerate(raw_items):
        if isinstance(item, str):
            skill_name = item.strip()
            category = None
            proficiency_hint = None
            years_hint = None
            source_type = ProfileValueSource.EXTRACTED
            source_confidence = None
            is_user_edited = False
            is_suppressed = False
            skill_id = f"skill_{index}"
        else:
            skill_name = str(
                _read(item, "skill_name", _read(item, "name", ""))
            ).strip()
            category = _read(item, "category")
            proficiency_hint = _read(item, "proficiency_hint")
            years_hint = _read(item, "years_hint")
            source_type = ProfileValueSource(
                _read(item, "source_type", "extracted")
            )
            source_confidence = _read(item, "source_confidence")
            is_user_edited = bool(_read(item, "is_user_edited", False))
            is_suppressed = bool(_read(item, "is_suppressed", False))
            skill_id = str(_read(item, "id", f"skill_{index}"))

        result.append(
            ProfileSkillRecord(
                id=skill_id,
                skill_name=skill_name,
                category=category,
                proficiency_hint=proficiency_hint,
                years_hint=years_hint,
                display_order=index,
                source_type=source_type,
                source_confidence=source_confidence,
                is_user_edited=is_user_edited,
                is_suppressed=is_suppressed,
            )
        )
    return result


def _completion_status(has_value: bool) -> CompletionSectionStatus:
    return (
        CompletionSectionStatus.DONE
        if has_value
        else CompletionSectionStatus.MISSING
    )


def _build_completeness(
    *,
    headline: str | None,
    summary: str | None,
    experiences: list[ProfileExperienceRecord],
    education: list[ProfileEducationRecord],
    languages: list[ProfileLanguageRecord],
    skills: list[ProfileSkillRecord],
    target_roles: list[str],
) -> ProfileCompletenessSummary:
    sections = [
        ProfileCompletionSection(
            key="basic_info",
            label="Temel bilgiler",
            status=_completion_status(bool(headline)),
        ),
        ProfileCompletionSection(
            key="summary",
            label="Kısa özet",
            status=_completion_status(bool(summary)),
        ),
        ProfileCompletionSection(
            key="experiences",
            label="Deneyimler",
            status=_completion_status(bool(experiences)),
        ),
        ProfileCompletionSection(
            key="education",
            label="Eğitim",
            status=_completion_status(bool(education)),
        ),
        ProfileCompletionSection(
            key="languages",
            label="Diller",
            status=_completion_status(bool(languages)),
        ),
        ProfileCompletionSection(
            key="skills",
            label="Beceriler",
            status=_completion_status(bool(skills)),
        ),
        ProfileCompletionSection(
            key="preferences",
            label="Hedef roller",
            status=_completion_status(bool(target_roles)),
        ),
    ]

    total = len(sections)
    done = sum(
        1 for item in sections if item.status == CompletionSectionStatus.DONE
    )
    score = int(round((done / total) * 100)) if total else 0

    return ProfileCompletenessSummary(score=score, sections=sections)


def _build_suggestions(
    *,
    headline: str | None,
    summary: str | None,
    experiences: list[ProfileExperienceRecord],
    languages: list[ProfileLanguageRecord],
    skills: list[ProfileSkillRecord],
    target_roles: list[str],
) -> ProfileSuggestionsBundle:
    highlights: list[ProfileSuggestionItem] = []
    critical_gaps: list[ProfileSuggestionItem] = []
    quick_wins: list[ProfileSuggestionItem] = []

    if headline:
        highlights.append(
            ProfileSuggestionItem(
                id="headline_present",
                title="Profil başlığı görünüyor",
                description="Başlık alanın dolu olduğu için profilin daha anlaşılır görünüyor.",
                impact_level=SuggestionImpactLevel.LOW,
                action_type=None,
                target_section="basic_info",
            )
        )

    if len(skills) >= 5:
        highlights.append(
            ProfileSuggestionItem(
                id="skills_visible",
                title="Beceri alanı güçlü duruyor",
                description=f"{len(skills)} beceri alanı görünüyor durumda.",
                impact_level=SuggestionImpactLevel.LOW,
                action_type=None,
                target_section="skills",
            )
        )

    if not experiences:
        critical_gaps.append(
            ProfileSuggestionItem(
                id="missing_experience",
                title="Deneyim alanı eksik",
                description="En az bir deneyim kaydı eklemek eşleşme kalitesini ciddi biçimde artırır.",
                impact_level=SuggestionImpactLevel.HIGH,
                action_type="navigate_section",
                target_section="experiences",
            )
        )

    if not languages:
        quick_wins.append(
            ProfileSuggestionItem(
                id="missing_languages",
                title="Dil bilgisi ekle",
                description="Dil seviyelerini belirtmek teknik ve uluslararası roller için görünürlüğünü artırabilir.",
                impact_level=SuggestionImpactLevel.MEDIUM,
                action_type="navigate_section",
                target_section="languages",
            )
        )

    if not summary:
        quick_wins.append(
            ProfileSuggestionItem(
                id="missing_summary",
                title="Kısa özet ekle",
                description="Kısa özet alanı, profilin dışarıdan daha güçlü görünmesini sağlar.",
                impact_level=SuggestionImpactLevel.MEDIUM,
                action_type="navigate_section",
                target_section="summary",
            )
        )

    if not target_roles:
        quick_wins.append(
            ProfileSuggestionItem(
                id="missing_target_roles",
                title="Hedef rollerini belirt",
                description="Hedef rol belirtmek sana daha alakalı eşleşmeler sunulmasına yardımcı olur.",
                impact_level=SuggestionImpactLevel.MEDIUM,
                action_type="navigate_section",
                target_section="preferences",
            )
        )

    return ProfileSuggestionsBundle(
        highlights=highlights,
        critical_gaps=critical_gaps,
        quick_wins=quick_wins,
    )


def build_user_profile_aggregate_response(
    *,
    user_id: str,
    email: str,
    full_name: str | None,
    legacy_profile: Any,
    experience_entries: Any | None = None,
    education_entries: Any | None = None,
    language_entries: Any | None = None,
) -> UserProfileAggregateResponse:
    headline_value = _read(legacy_profile, "headline") or _read(
        legacy_profile, "profile_title"
    )
    summary_value = _read(legacy_profile, "summary") or _read(
        legacy_profile, "short_summary"
    )
    phone_value = _read(legacy_profile, "phone")
    preferred_locations = _to_str_list(
        _read(legacy_profile, "preferred_locations", _read(legacy_profile, "locations"))
    )
    target_roles = _to_str_list(
        _read(legacy_profile, "target_roles", _read(legacy_profile, "desired_roles"))
    )

    experiences = _build_experiences(
        experience_entries
        if experience_entries is not None
        else _read(legacy_profile, "experiences", [])
    )
    education = _build_education(
        education_entries
        if education_entries is not None
        else _read(legacy_profile, "education", [])
    )
    languages = _build_languages(
        language_entries
        if language_entries is not None
        else _read(legacy_profile, "languages", [])
    )
    skills = _build_skills(_read(legacy_profile, "skills", []))

    completeness = _build_completeness(
        headline=headline_value,
        summary=summary_value,
        experiences=experiences,
        education=education,
        languages=languages,
        skills=skills,
        target_roles=target_roles,
    )

    suggestions = _build_suggestions(
        headline=headline_value,
        summary=summary_value,
        experiences=experiences,
        languages=languages,
        skills=skills,
        target_roles=target_roles,
    )

    now_iso = _utc_now_iso()

    profile = CandidateProfileAggregate(
        id=str(_read(legacy_profile, "id", f"profile_{user_id}")),
        user_id=user_id,
        full_name=_text_field(full_name, is_user_edited=True, confidence=1.0),
        headline=_text_field(
            headline_value,
            is_user_edited=bool(headline_value),
            confidence=0.8,
        ),
        summary=_text_field(
            summary_value,
            is_user_edited=bool(summary_value),
            confidence=0.75,
        ),
        primary_email=_text_field(email, is_user_edited=True, confidence=1.0),
        phone=_text_field(
            phone_value,
            is_user_edited=bool(phone_value),
            confidence=0.95,
        ),
        avatar=ProfileAvatarSummary(
            asset_id=_read(legacy_profile, "avatar_asset_id"),
            url=_read(legacy_profile, "avatar_url"),
            status="ready" if _read(legacy_profile, "avatar_url") else "missing",
        ),
        preferences=ProfilePreferencesRecord(
            preferred_locations=preferred_locations,
            work_modes=_to_work_modes(
                _read(
                    legacy_profile,
                    "work_modes",
                    _read(legacy_profile, "work_mode", _read(legacy_profile, "remote_preference")),
                )
            ),
            target_roles=target_roles,
            salary_expectation=_read(legacy_profile, "salary_expectation"),
            relocation=_read(legacy_profile, "relocation"),
        ),
        completeness=completeness,
        experiences=experiences,
        education=education,
        languages=languages,
        skills=skills,
        last_cv_parse=LastCvParseSummary(
            parse_run_id=_read(legacy_profile, "last_cv_parse_run_id"),
            parsed_at=_read(legacy_profile, "last_cv_parsed_at"),
            source_file_name=_read(legacy_profile, "last_cv_file_name"),
        ),
        created_at=str(_read(legacy_profile, "created_at", now_iso)),
        updated_at=str(_read(legacy_profile, "updated_at", now_iso)),
    )

    return UserProfileAggregateResponse(
        profile=profile,
        suggestions=suggestions,
    )