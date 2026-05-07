from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CanonicalJob, JobRecord, SubscriberProfileFeature
from hiring_radar.services.jobs.feature_engine import build_matching_readiness_features
from hiring_radar.services.jobs.normalization import (
    build_canonical_job_key,
    extract_location_city,
    extract_location_country,
    infer_employment_type,
    infer_seniority,
    infer_workplace_type,
    normalize_company_name,
    normalize_job_title,
)
from hiring_radar.services.matching.contracts import RankedJobMatch
from hiring_radar.services.matching.profile_features import refresh_subscriber_profile_features
from hiring_radar.services.matching.scoring import build_match_result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def _compute_freshness_score(legacy_job: JobRecord, *, refreshed_at: str) -> float:
    now_dt = _parse_iso_datetime(refreshed_at) or datetime.now(timezone.utc)
    reference_dt = (
        _parse_iso_datetime(legacy_job.posted_at)
        or _parse_iso_datetime(legacy_job.last_seen_at)
        or _parse_iso_datetime(legacy_job.first_seen_at)
    )
    if reference_dt is None:
        return 0.55
    age_days = max(0.0, (now_dt - reference_dt).total_seconds() / 86_400)
    if age_days <= 3:
        return 0.96
    if age_days <= 7:
        return 0.88
    if age_days <= 14:
        return 0.78
    if age_days <= 30:
        return 0.68
    if age_days <= 60:
        return 0.56
    return 0.44


_TRUST_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (0.78, ("greenhouse", "lever", "ashby", "smartrecruiters", "workday", "oracle", "myworkdayjobs")),
    (0.72, ("linkedin", "indeed", "glassdoor")),
    (0.66, ("careers", "jobs")),
)


def _compute_trust_score(legacy_job: JobRecord) -> float:
    haystack = " ".join(
        part.casefold()
        for part in (
            legacy_job.source_name,
            legacy_job.source_type,
            legacy_job.canonical_url,
        )
        if part
    )
    if not haystack:
        return 0.58
    for score, keywords in _TRUST_HINTS:
        if any(keyword in haystack for keyword in keywords):
            return score
    if legacy_job.canonical_url:
        return 0.62
    return 0.56


def build_transient_canonical_job(
    repository: HiringRadarRepository,
    *,
    legacy_job: JobRecord,
    refreshed_at: str,
) -> CanonicalJob:
    if legacy_job.id is None:
        raise ValueError("Legacy job must have an identifier before transient matching.")

    normalized_url = (legacy_job.canonical_url or "").strip()
    external_snapshot = (
        repository.get_job_external_context_snapshot_by_url(normalized_url)
        if normalized_url
        else None
    )
    description_text = None
    if external_snapshot is not None and external_snapshot.clean_text:
        description_text = external_snapshot.clean_text

    return CanonicalJob(
        id=legacy_job.id,
        canonical_key=build_canonical_job_key(
            company_name=legacy_job.company_name,
            title=legacy_job.title,
            location_text=legacy_job.location,
            apply_url=legacy_job.canonical_url,
            fallback_key=f"legacy:{legacy_job.id}",
        ),
        normalized_title=normalize_job_title(legacy_job.title),
        normalized_company_name=normalize_company_name(legacy_job.company_name),
        display_title=legacy_job.title,
        display_company_name=legacy_job.company_name,
        location_city=extract_location_city(legacy_job.location),
        country=extract_location_country(legacy_job.location),
        workplace_type=infer_workplace_type(legacy_job.location),
        employment_type=infer_employment_type(legacy_job.title, legacy_job.location, description_text),
        seniority=infer_seniority(legacy_job.title, description_text),
        description_text=description_text,
        description_html=None,
        posted_at=legacy_job.posted_at,
        apply_url=legacy_job.canonical_url,
        trust_score=_compute_trust_score(legacy_job),
        freshness_score=_compute_freshness_score(legacy_job, refreshed_at=refreshed_at),
        is_active=legacy_job.is_active,
        created_at=legacy_job.first_seen_at,
        updated_at=legacy_job.last_seen_at or refreshed_at,
    )


def score_legacy_job_for_subscriber(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    legacy_job: JobRecord,
    refreshed_at: str | None = None,
    profile_feature: SubscriberProfileFeature | None = None,
) -> RankedJobMatch:
    if legacy_job.id is None:
        raise ValueError("Legacy job must have an identifier before scoring.")
    effective_refreshed_at = refreshed_at or _utc_now_iso()
    if profile_feature is None:
        profile_feature = refresh_subscriber_profile_features(
            repository,
            subscriber_id=subscriber_id,
            refreshed_at=effective_refreshed_at,
        ).profile_feature
    transient_job = build_transient_canonical_job(
        repository,
        legacy_job=legacy_job,
        refreshed_at=effective_refreshed_at,
    )
    transient_feature = build_matching_readiness_features(
        repository,
        transient_job,
        refreshed_at=effective_refreshed_at,
    )
    result = build_match_result(
        subscriber_id=subscriber_id,
        profile_feature=profile_feature,
        job=transient_job,
        job_feature=transient_feature,
        behavioral_affinity_score=None,
    )
    return RankedJobMatch(
        job=transient_job,
        job_feature=transient_feature,
        profile_feature=profile_feature,
        result=result,
    )


def rank_legacy_jobs_for_subscriber(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    refreshed_at: str | None = None,
    jobs: Iterable[JobRecord] | None = None,
    limit: int | None = None,
    minimum_score: float = 0.0,
    active_only: bool = True,
) -> tuple[RankedJobMatch, ...]:
    effective_refreshed_at = refreshed_at or _utc_now_iso()
    profile_feature = refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=effective_refreshed_at,
    ).profile_feature
    source_jobs = list(jobs) if jobs is not None else repository.list_jobs()
    ranked: list[RankedJobMatch] = []
    for legacy_job in source_jobs:
        if legacy_job.id is None:
            continue
        if active_only and not legacy_job.is_active:
            continue
        ranked_match = score_legacy_job_for_subscriber(
            repository,
            subscriber_id=subscriber_id,
            legacy_job=legacy_job,
            refreshed_at=effective_refreshed_at,
            profile_feature=profile_feature,
        )
        if ranked_match.result.final_score < minimum_score:
            continue
        ranked.append(ranked_match)

    ranked.sort(
        key=lambda item: (
            item.result.final_score,
            item.result.fit_score,
            item.job_feature.match_readiness_score,
            item.job.trust_score,
            item.job.freshness_score,
            item.job.updated_at or "",
            item.job.id or 0,
        ),
        reverse=True,
    )
    if limit is not None:
        ranked = ranked[:limit]
    return tuple(ranked)
