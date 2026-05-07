from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import (
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
    SubscriberProfileFeature,
    SubscriberSkillDetail,
)
from hiring_radar.services.matching.contracts import ProfileFeatureRefreshResult
from hiring_radar.services.jobs.normalization import (
    extract_domain_signals,
    extract_impact_signals,
    extract_language_requirements,
    extract_ownership_signals,
    extract_skill_terms,
    infer_education_level_hint,
    infer_job_discipline,
    infer_management_track,
    infer_profile_responsibility_scope,
    infer_profile_seniority,
    infer_role_category,
    normalize_location_text,
    normalize_text,
    tokenize_keywords,
)

_FEATURE_VERSION = "v6"
_EDUCATION_RANK = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "doctorate": 5,
}


def _dedupe_preserve_order(values: Iterable[str | None], *, limit: int | None = None) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw_value in values:
        normalized = normalize_text(raw_value).casefold()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
        if limit is not None and len(ordered) >= limit:
            break
    return tuple(ordered)


def _collect_role_preferences(*texts: str | None) -> tuple[str, ...]:
    collected: list[str] = []
    for text in texts:
        inferred = infer_role_category(text, None)
        if inferred is not None:
            collected.append(inferred)
    return _dedupe_preserve_order(collected, limit=8)


def _collect_domain_signals(*texts: str | None) -> tuple[str, ...]:
    collected: list[str] = []
    for text in texts:
        for signal in extract_domain_signals(text):
            collected.append(signal)
    return _dedupe_preserve_order(collected, limit=10)


def _collect_profile_keyword_signals(*texts: str | None, extractor) -> tuple[str, ...]:
    collected: list[str] = []
    for text in texts:
        for signal in extractor(text):
            collected.append(signal)
    return _dedupe_preserve_order(collected, limit=10)


def _collect_discipline_preferences(*texts: str | None) -> tuple[str, ...]:
    collected: list[str] = []
    for text in texts:
        inferred = infer_job_discipline(text, None)
        if inferred is not None:
            collected.append(inferred)
    return _dedupe_preserve_order(collected, limit=8)


def _normalize_profile_skill_terms(
    profile_skills: Iterable[str],
    skill_details: Iterable[SubscriberSkillDetail],
    experience_entries: Iterable[SubscriberExperienceEntry],
) -> tuple[str, ...]:
    explicit_terms: list[str] = []
    for raw_skill in profile_skills:
        normalized = normalize_text(raw_skill).casefold()
        if normalized:
            explicit_terms.append(normalized)
        explicit_terms.extend(extract_skill_terms(raw_skill))

    for detail in skill_details:
        normalized = normalize_text(detail.skill_name_normalized or detail.skill_name).casefold()
        if normalized:
            explicit_terms.append(normalized)
        explicit_terms.extend(extract_skill_terms(detail.skill_name, detail.evidence_note))

    for entry in experience_entries:
        explicit_terms.extend(extract_skill_terms(entry.title, entry.summary))

    return _dedupe_preserve_order(explicit_terms, limit=48)


def _normalize_experience_evidence_terms(
    profile_headline: str | None,
    profile_summary: str | None,
    experience_entries: Iterable[SubscriberExperienceEntry],
) -> tuple[str, ...]:
    extracted: list[str] = []
    extracted.extend(extract_skill_terms(profile_headline, profile_summary, limit=24))
    for entry in experience_entries:
        extracted.extend(extract_skill_terms(entry.title, entry.summary, limit=16))
    return _dedupe_preserve_order(extracted, limit=40)


def _normalize_language_capabilities(entries: Iterable[SubscriberLanguageEntry]) -> tuple[str, ...]:
    languages: list[str] = []
    for entry in entries:
        normalized_name = normalize_text(entry.language_name).casefold()
        if normalized_name:
            languages.append(normalized_name)
        languages.extend(extract_language_requirements(entry.language_name, entry.notes))
    return _dedupe_preserve_order(languages, limit=12)


def _infer_highest_education_level(entries: Iterable[SubscriberEducationEntry]) -> str | None:
    best_level: str | None = None
    best_rank = 0
    for entry in entries:
        inferred = infer_education_level_hint(entry.degree_name, entry.field_of_study)
        if inferred is None:
            continue
        rank = _EDUCATION_RANK.get(inferred, 0)
        if rank > best_rank:
            best_level = inferred
            best_rank = rank
    return best_level


def _merge_year_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged: list[list[int]] = [[ordered[0][0], ordered[0][1]]]
    for start, end in ordered[1:]:
        current = merged[-1]
        if start <= current[1]:
            current[1] = max(current[1], end)
            continue
        merged.append([start, end])
    return [(start, end) for start, end in merged]


def _estimate_total_experience_years(entries: Iterable[SubscriberExperienceEntry]) -> int | None:
    current_year = date.today().year
    ranges: list[tuple[int, int]] = []
    for entry in entries:
        if entry.start_year is None:
            continue
        end_year = entry.end_year or current_year
        if end_year < entry.start_year:
            continue
        normalized_end = max(entry.start_year + 1, end_year)
        ranges.append((entry.start_year, normalized_end))
    if not ranges:
        return None
    merged = _merge_year_ranges(ranges)
    total_years = sum(max(1, end - start) for start, end in merged)
    return max(0, total_years)


def _infer_management_preference(
    profile_texts: Iterable[str | None],
    experience_entries: Iterable[SubscriberExperienceEntry],
) -> bool | None:
    signals: list[bool] = []
    for text in profile_texts:
        normalized = normalize_text(text)
        if normalized:
            signals.append(infer_management_track(normalized, None))
    for entry in experience_entries:
        signals.append(infer_management_track(entry.title, entry.summary))
    if not signals:
        return None
    positive = sum(1 for signal in signals if signal)
    if positive == 0:
        return False
    return positive >= max(1, len(signals) // 2)


def _compute_profile_strength_score(
    *,
    target_roles: tuple[str, ...],
    title_tokens: tuple[str, ...],
    skill_terms: tuple[str, ...],
    preferred_location_tokens: tuple[str, ...],
    language_capabilities: tuple[str, ...],
    education_level: str | None,
    years_experience_total: int | None,
) -> float:
    score = 0.0
    if target_roles:
        score += min(0.18, len(target_roles) * 0.06)
    if title_tokens:
        score += min(0.16, len(title_tokens) * 0.01)
    if skill_terms:
        score += min(0.28, len(skill_terms) * 0.015)
    if preferred_location_tokens:
        score += min(0.08, len(preferred_location_tokens) * 0.03)
    if language_capabilities:
        score += min(0.10, len(language_capabilities) * 0.04)
    if education_level:
        score += 0.08
    if years_experience_total is not None:
        score += 0.12
    return round(min(1.0, max(0.2, score)), 4)


def build_subscriber_profile_features(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    refreshed_at: str,
) -> SubscriberProfileFeature:
    profile = repository.get_subscriber_profile(subscriber_id)
    experience_entries = repository.list_subscriber_experience_entries(subscriber_id)
    education_entries = repository.list_subscriber_education_entries(subscriber_id)
    language_entries = repository.list_subscriber_language_entries(subscriber_id)
    skill_details = repository.list_subscriber_skill_details(subscriber_id)

    skill_signal_texts = [
        *profile.skills,
        *(detail.skill_name for detail in skill_details),
        *(detail.evidence_note for detail in skill_details if detail.evidence_note),
    ]
    role_source_texts = [
        profile.headline,
        profile.summary,
        *profile.target_roles,
        *skill_signal_texts,
        *(entry.title for entry in experience_entries),
        *(entry.summary for entry in experience_entries if entry.summary),
    ]
    discipline_source_texts = [
        profile.headline,
        profile.summary,
        *profile.target_roles,
        *skill_signal_texts,
        *(entry.title for entry in experience_entries),
        *(entry.summary for entry in experience_entries if entry.summary),
    ]
    domain_source_texts = [
        profile.headline,
        profile.summary,
        *skill_signal_texts,
        *(entry.summary for entry in experience_entries if entry.summary),
        *(entry.title for entry in experience_entries),
    ]

    role_families = _collect_role_preferences(*role_source_texts)
    discipline_preferences = _collect_discipline_preferences(*discipline_source_texts)
    domain_signals = _collect_domain_signals(*domain_source_texts)
    ownership_signals = _collect_profile_keyword_signals(*domain_source_texts, extractor=extract_ownership_signals)
    impact_signals = _collect_profile_keyword_signals(*domain_source_texts, extractor=extract_impact_signals)
    title_tokens = tokenize_keywords(
        profile.headline,
        profile.summary,
        *profile.target_roles,
        *(entry.title for entry in experience_entries),
        limit=40,
    )
    skill_terms = _normalize_profile_skill_terms(profile.skills, skill_details, experience_entries)
    experience_evidence_terms = _normalize_experience_evidence_terms(
        profile.headline,
        profile.summary,
        experience_entries,
    )

    location_values = [normalize_location_text(value) for value in profile.preferred_locations]
    if profile.remote_preference and profile.remote_preference.casefold() in {"remote", "hybrid"}:
        location_values.append(profile.remote_preference)
    preferred_location_tokens = tokenize_keywords(*location_values, limit=16)

    language_capabilities = _normalize_language_capabilities(language_entries)
    education_level = _infer_highest_education_level(education_entries)
    years_experience_total = _estimate_total_experience_years(experience_entries)
    management_preference = _infer_management_preference(
        [profile.headline, profile.summary, *profile.target_roles],
        experience_entries,
    )

    seniority_level = infer_profile_seniority(
        experience_titles=[entry.title for entry in experience_entries if entry.title],
        experience_summaries=[entry.summary for entry in experience_entries if entry.summary],
        years_experience_total=years_experience_total,
    )
    responsibility_scope = infer_profile_responsibility_scope(
        [entry.title for entry in experience_entries if entry.title],
        [entry.summary for entry in experience_entries if entry.summary],
        management_preference=management_preference,
        seniority_level=seniority_level,
    )

    profile_strength_score = _compute_profile_strength_score(
        target_roles=profile.target_roles,
        title_tokens=title_tokens,
        skill_terms=skill_terms,
        preferred_location_tokens=preferred_location_tokens,
        language_capabilities=language_capabilities,
        education_level=education_level,
        years_experience_total=years_experience_total,
    )

    return SubscriberProfileFeature(
        subscriber_id=subscriber_id,
        feature_version=_FEATURE_VERSION,
        role_families=role_families,
        discipline_preferences=discipline_preferences,
        title_tokens=title_tokens,
        skill_terms=skill_terms,
        experience_evidence_terms=experience_evidence_terms,
        preferred_location_tokens=preferred_location_tokens,
        language_capabilities=language_capabilities,
        education_level=education_level,
        years_experience_total=years_experience_total,
        remote_preference=profile.remote_preference,
        management_preference=management_preference,
        profile_strength_score=profile_strength_score,
        seniority_level=seniority_level,
        domain_signals=domain_signals,
        responsibility_scope=responsibility_scope,
        ownership_signals=ownership_signals,
        impact_signals=impact_signals,
        created_at=refreshed_at,
        updated_at=refreshed_at,
    )


def refresh_subscriber_profile_features(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    refreshed_at: str,
) -> ProfileFeatureRefreshResult:
    existing = repository.get_subscriber_profile_feature(subscriber_id=subscriber_id)
    feature = build_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=refreshed_at,
    )
    if existing is not None:
        feature = SubscriberProfileFeature(
            id=existing.id,
            subscriber_id=feature.subscriber_id,
            feature_version=feature.feature_version,
            role_families=feature.role_families,
            discipline_preferences=feature.discipline_preferences,
            title_tokens=feature.title_tokens,
            skill_terms=feature.skill_terms,
            experience_evidence_terms=feature.experience_evidence_terms,
            preferred_location_tokens=feature.preferred_location_tokens,
            language_capabilities=feature.language_capabilities,
            education_level=feature.education_level,
            years_experience_total=feature.years_experience_total,
            remote_preference=feature.remote_preference,
            management_preference=feature.management_preference,
            profile_strength_score=feature.profile_strength_score,
            seniority_level=feature.seniority_level,
            domain_signals=feature.domain_signals,
            responsibility_scope=feature.responsibility_scope,
            ownership_signals=feature.ownership_signals,
            impact_signals=feature.impact_signals,
            created_at=existing.created_at or refreshed_at,
            updated_at=refreshed_at,
        )
    stored = repository.upsert_subscriber_profile_feature(feature)
    return ProfileFeatureRefreshResult(
        subscriber_id=subscriber_id,
        created=existing is None,
        profile_feature=stored,
    )
