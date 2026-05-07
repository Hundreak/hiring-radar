from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CanonicalJob, CanonicalJobFeature, SubscriberProfileFeature
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.matching.contracts import RankedJobMatch
from hiring_radar.services.matching.engine import rank_canonical_jobs_for_subscriber, score_canonical_job_for_subscriber
from hiring_radar.services.matching.profile_features import refresh_subscriber_profile_features


@dataclass(slots=True, frozen=True)
class DeterministicMatchCatalog:
    refreshed_at: str
    profile_feature: SubscriberProfileFeature
    ranked_matches: tuple[RankedJobMatch, ...]
    ranked_matches_by_job_id: Mapping[int, RankedJobMatch]


def build_deterministic_match_catalog(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    refreshed_at: str,
    limit: int | None = None,
    minimum_score: float = 0.0,
    active_only: bool = True,
) -> DeterministicMatchCatalog | None:
    canonical_jobs = repository.list_canonical_jobs(active_only=active_only)
    if not canonical_jobs:
        return None

    profile_feature_result = refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=refreshed_at,
    )
    ranked_matches = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=refreshed_at,
        limit=limit,
        minimum_score=minimum_score,
        active_only=active_only,
    )
    ranked_by_job_id = {
        match.job.id or 0: match
        for match in ranked_matches
        if match.job.id is not None
    }
    return DeterministicMatchCatalog(
        refreshed_at=refreshed_at,
        profile_feature=profile_feature_result.profile_feature,
        ranked_matches=ranked_matches,
        ranked_matches_by_job_id=ranked_by_job_id,
    )


def get_ranked_match_for_canonical_job(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    canonical_job_id: int,
    refreshed_at: str,
    active_only: bool = True,
    behavioral_affinity_by_job_id: Mapping[int, float] | None = None,
) -> RankedJobMatch | None:
    if canonical_job_id <= 0:
        return None

    catalog = build_deterministic_match_catalog(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at=refreshed_at,
        limit=None,
        minimum_score=0.0,
        active_only=active_only,
    )
    if catalog is None:
        return None

    ranked_match = catalog.ranked_matches_by_job_id.get(canonical_job_id)
    if ranked_match is not None:
        return ranked_match

    job = repository.get_canonical_job_by_id(canonical_job_id)
    if job is None or (active_only and not job.is_active):
        return None

    job_feature = repository.get_canonical_job_feature(canonical_job_id=canonical_job_id)
    if job_feature is None:
        refresh_matching_readiness_features(
            repository,
            refreshed_at=refreshed_at,
            canonical_job_ids=[canonical_job_id],
        )
        job_feature = repository.get_canonical_job_feature(canonical_job_id=canonical_job_id)
    if job_feature is None:
        return None

    behavioral_affinity_score: float | None = None
    if behavioral_affinity_by_job_id is not None:
        behavioral_affinity_score = behavioral_affinity_by_job_id.get(canonical_job_id)
    else:
        behavioral_affinity_score = repository.list_subscriber_job_behavioral_affinity_scores(
            subscriber_id=subscriber_id,
            canonical_job_ids=[canonical_job_id],
            active_only=active_only,
        ).get(canonical_job_id)

    result = score_canonical_job_for_subscriber(
        subscriber_id=subscriber_id,
        profile_feature=catalog.profile_feature,
        job=job,
        job_feature=job_feature,
        behavioral_affinity_score=behavioral_affinity_score,
    )
    return RankedJobMatch(
        job=job,
        job_feature=job_feature,
        profile_feature=catalog.profile_feature,
        result=result,
    )
