from __future__ import annotations

from collections.abc import Mapping

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CanonicalJob, CanonicalJobFeature, SubscriberProfileFeature
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.matching.contracts import DeterministicMatchResult, RankedJobMatch
from hiring_radar.services.matching.profile_features import refresh_subscriber_profile_features
from hiring_radar.services.matching.scoring import build_match_result


def _ensure_canonical_matching_corpus_ready(
    repository: HiringRadarRepository,
    *,
    refreshed_at: str,
    active_only: bool,
) -> None:
    active_jobs = repository.list_canonical_jobs(active_only=active_only)
    if not active_jobs:
        return

    existing_features = repository.list_canonical_job_features(active_only=active_only)
    existing_ids = {feature.canonical_job_id for feature in existing_features}
    missing_ids = [job.id or 0 for job in active_jobs if (job.id or 0) not in existing_ids]
    if not missing_ids:
        return

    refresh_matching_readiness_features(
        repository,
        refreshed_at=refreshed_at,
        canonical_job_ids=missing_ids,
    )


def score_canonical_job_for_subscriber(
    *,
    subscriber_id: int,
    profile_feature: SubscriberProfileFeature,
    job: CanonicalJob,
    job_feature: CanonicalJobFeature,
    behavioral_affinity_score: float | None = None,
) -> DeterministicMatchResult:
    if job.id is None:
        raise ValueError("Canonical job must have a persisted identifier before scoring.")
    if job_feature.canonical_job_id != job.id:
        raise ValueError("Canonical job and canonical job feature identifiers do not match.")
    return build_match_result(
        subscriber_id=subscriber_id,
        profile_feature=profile_feature,
        job=job,
        job_feature=job_feature,
        behavioral_affinity_score=behavioral_affinity_score,
    )


def rank_canonical_jobs_for_subscriber(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    refreshed_at: str,
    limit: int | None = None,
    minimum_score: float = 0.0,
    behavioral_affinity_by_job_id: Mapping[int, float] | None = None,
    active_only: bool = True,
) -> tuple[RankedJobMatch, ...]:
    _ensure_canonical_matching_corpus_ready(
        repository,
        refreshed_at=refreshed_at,
        active_only=active_only,
    )
    refresh_result = refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=refreshed_at,
    )
    profile_feature = refresh_result.profile_feature
    job_pairs = repository.list_matchable_canonical_job_feature_pairs(active_only=active_only)

    affinity_by_job_id: dict[int, float]
    if behavioral_affinity_by_job_id is None:
        affinity_by_job_id = repository.list_subscriber_job_behavioral_affinity_scores(
            subscriber_id=subscriber_id,
            canonical_job_ids=[job.id or 0 for job, _ in job_pairs],
            active_only=active_only,
        )
    else:
        affinity_by_job_id = {int(job_id): float(score) for job_id, score in behavioral_affinity_by_job_id.items()}

    ranked: list[RankedJobMatch] = []
    for job, job_feature in job_pairs:
        job_id = job.id or 0
        behavioral_affinity_score = affinity_by_job_id.get(job_id)
        result = score_canonical_job_for_subscriber(
            subscriber_id=subscriber_id,
            profile_feature=profile_feature,
            job=job,
            job_feature=job_feature,
            behavioral_affinity_score=behavioral_affinity_score,
        )
        if result.final_score < minimum_score:
            continue
        ranked.append(
            RankedJobMatch(
                job=job,
                job_feature=job_feature,
                profile_feature=profile_feature,
                result=result,
            )
        )

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
