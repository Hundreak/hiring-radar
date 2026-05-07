from hiring_radar.services.matching.contracts import (
    DeterministicMatchResult,
    ExternalSourceInsights,
    ExternalSourceMetadata,
    MatchExplanationBreakdownItem,
    MatchExplanationEvidencePoint,
    MatchExplanationGapItem,
    MatchExplanationPayload,
    MatchScoreComponent,
    ProfileFeatureRefreshResult,
    RankedJobMatch,
)
from hiring_radar.services.matching.catalog import (
    DeterministicMatchCatalog,
    build_deterministic_match_catalog,
    get_ranked_match_for_canonical_job,
)
from hiring_radar.services.matching.engine import (
    rank_canonical_jobs_for_subscriber,
    score_canonical_job_for_subscriber,
)
from hiring_radar.services.matching.external_context import build_cached_external_source_insights
from hiring_radar.services.matching.explanations import ExplanationGenerator
from hiring_radar.services.matching.legacy_runtime import (
    build_transient_canonical_job,
    rank_legacy_jobs_for_subscriber,
    score_legacy_job_for_subscriber,
)
from hiring_radar.services.matching.profile_features import (
    build_subscriber_profile_features,
    refresh_subscriber_profile_features,
)

__all__ = [
    "DeterministicMatchCatalog",
    "DeterministicMatchResult",
    "ExplanationGenerator",
    "build_transient_canonical_job",
    "rank_legacy_jobs_for_subscriber",
    "score_legacy_job_for_subscriber",
    "ExternalSourceInsights",
    "ExternalSourceMetadata",
    "MatchExplanationBreakdownItem",
    "MatchExplanationEvidencePoint",
    "MatchExplanationGapItem",
    "MatchExplanationPayload",
    "MatchScoreComponent",
    "ProfileFeatureRefreshResult",
    "RankedJobMatch",
    "build_cached_external_source_insights",
    "build_deterministic_match_catalog",
    "build_subscriber_profile_features",
    "get_ranked_match_for_canonical_job",
    "rank_canonical_jobs_for_subscriber",
    "refresh_subscriber_profile_features",
    "score_canonical_job_for_subscriber",
]
