from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CanonicalJob, CanonicalJobFeature
from hiring_radar.services.jobs.contracts import JobFeatureRefreshResult
from hiring_radar.services.jobs.normalization import (
    compute_match_readiness_score,
    extract_domain_signals,
    extract_language_requirements,
    extract_required_preferred_skill_terms,
    extract_skill_terms,
    infer_department_family,
    infer_education_level_hint,
    infer_job_discipline,
    infer_management_track,
    infer_responsibility_scope,
    infer_role_category,
    infer_years_experience_min,
    normalize_company_name,
    normalize_job_title,
    normalize_location_text,
    normalize_url_for_dedup,
    tokenize_keywords,
)

_FEATURE_VERSION = "v4"


def _merge_unique_terms(*groups: tuple[str, ...] | list[str], limit: int) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for group in groups:
        for value in group:
            normalized = value.strip().casefold()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
            if len(ordered) >= limit:
                return tuple(ordered)
    return tuple(ordered)


def _coerce_string_tuple(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return ()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip().casefold()
        if normalized and normalized not in result:
            result.append(normalized)
    return tuple(result)


def _load_quantitative_signals(snapshot: object) -> dict[str, object]:
    metadata = getattr(snapshot, "source_metadata_json", {}) or {}
    if not isinstance(metadata, dict):
        return {}
    raw_capture = metadata.get("raw_capture_metadata")
    if not isinstance(raw_capture, dict):
        return {}
    quantitative = raw_capture.get("quantitative_signals")
    if not isinstance(quantitative, dict):
        return {}
    return quantitative


def _get_snapshot_by_candidate_url(repository: HiringRadarRepository, candidate_url: str | None):
    normalized_candidate = normalize_url_for_dedup(candidate_url)
    if not normalized_candidate:
        return None
    snapshot = repository.get_job_external_context_snapshot_by_url(candidate_url or "")
    if snapshot is not None:
        return snapshot
    if normalized_candidate != (candidate_url or "").strip():
        snapshot = repository.get_job_external_context_snapshot_by_url(normalized_candidate)
        if snapshot is not None:
            return snapshot
    return None


def _iter_source_records(repository: HiringRadarRepository) -> tuple[object, ...]:
    records: list[object] = []
    for source in repository.list_job_sources(active_only=False):
        if source.id is None:
            continue
        records.extend(repository.list_job_source_records(source_id=source.id, active_only=False))
    return tuple(records)


def _find_external_snapshot_for_job(repository: HiringRadarRepository, *, job: CanonicalJob):
    snapshot = _get_snapshot_by_candidate_url(repository, job.apply_url)
    if snapshot is not None:
        return snapshot

    source_records = _iter_source_records(repository)
    if job.id is not None:
        linked_ids = {link.source_job_id for link in repository.list_canonical_job_links(canonical_job_id=job.id)}
        for record in source_records:
            if getattr(record, "id", None) not in linked_ids:
                continue
            snapshot = _get_snapshot_by_candidate_url(repository, getattr(record, "apply_url", None) or getattr(record, "canonical_url", None))
            if snapshot is not None:
                return snapshot

    # Do not fall back to title/company-only matching here. Multiple active jobs from the
    # same company can legitimately share a title, and leaking one posting's external
    # context into its sibling makes catalog confidence indistinguishable and misleading.
    # External snapshots should be attached only by the canonical job URL or by explicit
    # canonical-job links to source records.
    return None


def _load_external_context_terms(
    repository: HiringRadarRepository,
    *,
    source_url: str | None,
    job: CanonicalJob | None = None,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    str | None,
    str | None,
    dict[str, object],
]:
    snapshot = None
    normalized_source_url = (source_url or '').strip()
    if normalized_source_url:
        snapshot = _get_snapshot_by_candidate_url(repository, normalized_source_url)
    if snapshot is None and job is not None:
        snapshot = _find_external_snapshot_for_job(repository, job=job)
    if snapshot is None:
        return (), (), (), (), None, None, {}

    quantitative_signals = _load_quantitative_signals(snapshot)
    requirement_text = ' '.join(snapshot.site_specific_requirements)
    responsibility_text = ' '.join(snapshot.responsibility_clues)
    technology_text = ' '.join(snapshot.technology_stack_terms)

    quantitative_required = _merge_unique_terms(
        _coerce_string_tuple(quantitative_signals.get('required_scripting_languages')),
        ('linux',) if bool(quantitative_signals.get('requires_linux')) else (),
        _coerce_string_tuple(quantitative_signals.get('support_model_terms')),
        limit=16,
    )
    quantitative_preferred = _merge_unique_terms(
        _coerce_string_tuple(quantitative_signals.get('preferred_cloud_platforms')),
        _coerce_string_tuple(quantitative_signals.get('preferred_virtualization_terms')),
        limit=12,
    )

    requirement_terms = _merge_unique_terms(
        extract_skill_terms(None, requirement_text, limit=16),
        quantitative_required,
        limit=18,
    )
    technology_terms = _merge_unique_terms(
        tuple(term.casefold() for term in snapshot.technology_stack_terms),
        extract_skill_terms(None, technology_text, limit=16),
        quantitative_preferred,
        limit=18,
    )
    responsibility_terms = _merge_unique_terms(
        extract_skill_terms(None, responsibility_text, limit=16),
        _coerce_string_tuple(quantitative_signals.get('support_model_terms')),
        limit=18,
    )
    domain_signals = extract_domain_signals(
        ' '.join((requirement_text, responsibility_text, technology_text, ' '.join(snapshot.company_culture_clues))),
        snapshot.page_title,
    )
    return (
        requirement_terms,
        technology_terms,
        responsibility_terms,
        domain_signals,
        snapshot.fetch_status,
        snapshot.updated_at or snapshot.fetched_at,
        quantitative_signals,
    )




def build_matching_readiness_features(
    repository: HiringRadarRepository,
    job: CanonicalJob,
    *,
    refreshed_at: str,
) -> CanonicalJobFeature:
    if job.id is None:
        raise ValueError("Canonical job must have a persisted identifier before features can be built.")

    title_tokens = tokenize_keywords(job.display_title, job.normalized_title, limit=16)
    location_tokens = tokenize_keywords(job.location_city, job.country, job.workplace_type, limit=8)
    external_requirement_terms, external_technology_terms, external_responsibility_terms, external_domain_signals, external_context_status, external_context_updated_at, quantitative_signals = _load_external_context_terms(
        repository,
        source_url=job.apply_url,
        job=job,
    )
    external_snapshot = _find_external_snapshot_for_job(repository, job=job)
    external_responsibility_text = " ".join(external_snapshot.responsibility_clues) if external_snapshot is not None else ""
    enriched_description_text = " ".join(
        part
        for part in (
            job.description_text,
            " ".join(external_requirement_terms),
            " ".join(external_technology_terms),
            external_responsibility_text,
            " ".join(external_responsibility_terms),
        )
        if part
    )
    # Increase skill extraction limit — wider vocabulary means more differentiation
    skill_terms = _merge_unique_terms(
        extract_skill_terms(job.display_title, job.description_text, limit=32),
        external_requirement_terms,
        external_technology_terms,
        external_responsibility_terms,
        limit=40,
    )
    parsed_required_skill_terms, parsed_preferred_skill_terms = extract_required_preferred_skill_terms(job.description_text)
    quantitative_required_terms = _merge_unique_terms(
        _coerce_string_tuple(quantitative_signals.get('required_scripting_languages')),
        ('linux',) if bool(quantitative_signals.get('requires_linux')) else (),
        _coerce_string_tuple(quantitative_signals.get('support_model_terms')),
        limit=10,
    )
    quantitative_preferred_terms = _merge_unique_terms(
        _coerce_string_tuple(quantitative_signals.get('preferred_cloud_platforms')),
        _coerce_string_tuple(quantitative_signals.get('preferred_virtualization_terms')),
        limit=10,
    )
    required_skill_terms = _merge_unique_terms(parsed_required_skill_terms, external_requirement_terms, quantitative_required_terms, limit=22)
    preferred_skill_terms = tuple(
        term
        for term in _merge_unique_terms(parsed_preferred_skill_terms, external_technology_terms, quantitative_preferred_terms, limit=18)
        if term not in set(required_skill_terms)
    )
    language_requirements = extract_language_requirements(enriched_description_text, job.display_title)
    role_family = job.category or infer_role_category(job.display_title, job.description_text)
    department_family = job.department or infer_department_family(job.display_title, job.description_text)
    job_discipline = infer_job_discipline(job.display_title, enriched_description_text)
    education_level_hint = infer_education_level_hint(enriched_description_text, job.display_title)
    quantitative_years = quantitative_signals.get('min_experience_years')
    years_experience_min = int(quantitative_years) if isinstance(quantitative_years, int) else infer_years_experience_min(enriched_description_text)
    management_track = infer_management_track(job.display_title, enriched_description_text)
    individual_contributor = not management_track
    quantitative_domain_terms = _merge_unique_terms(
        ('cloud',) if _coerce_string_tuple(quantitative_signals.get('preferred_cloud_platforms')) else (),
        ('virtualization',) if _coerce_string_tuple(quantitative_signals.get('preferred_virtualization_terms')) else (),
        ('support',) if _coerce_string_tuple(quantitative_signals.get('support_model_terms')) else (),
        ('distributed_systems',) if isinstance(quantitative_signals.get('minimum_stack_match_count'), int) else (),
        limit=8,
    )
    domain_signals = _merge_unique_terms(
        extract_domain_signals(job.description_text, job.display_title),
        external_domain_signals,
        quantitative_domain_terms,
        limit=12,
    )
    responsibility_scope = infer_responsibility_scope(
        " ".join((enriched_description_text, external_responsibility_text, " ".join(external_responsibility_terms))).strip(),
        job.display_title,
    )

    match_readiness_score = compute_match_readiness_score(
        role_family=role_family,
        job_discipline=job_discipline,
        title_tokens=title_tokens,
        skill_terms=skill_terms,
        location_tokens=location_tokens,
        language_requirements=language_requirements,
        education_level_hint=education_level_hint,
        years_experience_min=years_experience_min,
        workplace_type=job.workplace_type,
        employment_type=job.employment_type,
        seniority=job.seniority,
        description_text=enriched_description_text,
    )

    return CanonicalJobFeature(
        canonical_job_id=job.id,
        feature_version=_FEATURE_VERSION,
        role_family=role_family,
        job_discipline=job_discipline,
        department_family=department_family,
        title_tokens=title_tokens,
        skill_terms=skill_terms,
        required_skill_terms=required_skill_terms,
        preferred_skill_terms=preferred_skill_terms,
        external_requirement_terms=external_requirement_terms,
        external_technology_terms=external_technology_terms,
        external_responsibility_terms=external_responsibility_terms,
        location_tokens=location_tokens,
        language_requirements=language_requirements,
        education_level_hint=education_level_hint,
        years_experience_min=years_experience_min,
        management_track=management_track,
        individual_contributor=individual_contributor,
        domain_signals=domain_signals,
        responsibility_scope=responsibility_scope,
        external_context_status=external_context_status,
        external_context_updated_at=external_context_updated_at,
        match_readiness_score=match_readiness_score,
        created_at=refreshed_at,
        updated_at=refreshed_at,
    )


def _iter_jobs(
    repository: HiringRadarRepository,
    *,
    canonical_job_ids: Iterable[int] | None,
) -> list[CanonicalJob]:
    if canonical_job_ids is None:
        return repository.list_canonical_jobs(active_only=True)

    jobs: list[CanonicalJob] = []
    for canonical_job_id in canonical_job_ids:
        job = repository.get_canonical_job_by_id(canonical_job_id)
        if job is None or not job.is_active:
            continue
        jobs.append(job)
    return jobs


def refresh_matching_readiness_features(
    repository: HiringRadarRepository,
    *,
    refreshed_at: str,
    canonical_job_ids: Iterable[int] | None = None,
) -> JobFeatureRefreshResult:
    jobs = _iter_jobs(repository, canonical_job_ids=canonical_job_ids)
    stored_features: list[CanonicalJobFeature] = []

    for job in jobs:
        feature_candidate = build_matching_readiness_features(repository, job, refreshed_at=refreshed_at)
        existing = repository.get_canonical_job_feature(canonical_job_id=feature_candidate.canonical_job_id)
        if existing is not None:
            feature_candidate = replace(feature_candidate, created_at=existing.created_at or refreshed_at)
        stored_features.append(repository.upsert_canonical_job_feature(feature_candidate))

    pruned_features = repository.prune_canonical_job_features_for_inactive_jobs()

    return JobFeatureRefreshResult(
        total_jobs_considered=len(jobs),
        refreshed_features=len(stored_features),
        pruned_features=pruned_features,
        features=tuple(stored_features),
    )
