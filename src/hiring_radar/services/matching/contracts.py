from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from hiring_radar.models import CanonicalJob, CanonicalJobFeature, SubscriberProfileFeature


@dataclass(slots=True, frozen=True)
class ProfileFeatureRefreshResult:
    subscriber_id: int
    created: bool
    profile_feature: SubscriberProfileFeature


@dataclass(slots=True, frozen=True)
class MatchScoreComponent:
    name: str
    weight: float
    raw_score: float
    weighted_score: float
    summary: str
    matched_terms: tuple[str, ...] = ()
    missing_terms: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class JobAnalysisCoverage:
    level: Literal["limited", "moderate", "strong"] = "limited"
    score: float = 0.0
    summary: str = ""
    content_sources: tuple[str, ...] = ()
    detected_signal_types: tuple[str, ...] = ()
    found_sections: tuple[str, ...] = ()
    missing_sections: tuple[str, ...] = ()
    warning: str | None = None
    provider_confidence: float | None = None


@dataclass(slots=True, frozen=True)
class DeterministicMatchResult:
    subscriber_id: int
    canonical_job_id: int
    fit_score: float
    catalog_score: float
    final_score: float
    behavioral_affinity_score: float | None
    matched: bool
    explanation_summary: str
    matched_skill_terms: tuple[str, ...]
    missing_skill_terms: tuple[str, ...]
    matched_location_terms: tuple[str, ...]
    components: tuple[MatchScoreComponent, ...]
    blocker_terms: tuple[str, ...] = ()
    analysis_coverage: JobAnalysisCoverage | None = None


@dataclass(slots=True, frozen=True)
class RankedJobMatch:
    job: CanonicalJob
    job_feature: CanonicalJobFeature
    profile_feature: SubscriberProfileFeature
    result: DeterministicMatchResult


@dataclass(slots=True, frozen=True)
class MatchExplanationBreakdownItem:
    component_key: str
    label: str
    weight: float
    raw_score: float
    weighted_score: float
    impact: Literal["strong", "moderate", "weak"]
    summary: str
    evidence_terms: tuple[str, ...] = ()
    missing_terms: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class MatchExplanationEvidencePoint:
    code: str
    title: str
    detail: str
    supporting_terms: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class MatchExplanationGapItem:
    code: str
    title: str
    detail: str
    severity: Literal["high", "medium", "low"]
    missing_terms: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class ExternalSourceMetadata:
    source_url: str = ""
    final_url: str | None = None
    source_domain: str | None = None
    fetch_status: str = "unavailable"
    http_status: int | None = None
    page_title: str | None = None
    site_name: str | None = None
    fetched_at: str | None = None
    content_digest: str | None = None
    text_char_count: int = 0
    provider_name: str | None = None
    acquisition_method: str | None = None
    provider_confidence: float | None = None


@dataclass(slots=True, frozen=True)
class ExternalSourceInsights:
    enrichment_status: Literal["unavailable", "cached", "live", "error"] = "unavailable"
    site_specific_requirements: tuple[str, ...] = ()
    company_culture_clues: tuple[str, ...] = ()
    responsibility_clues: tuple[str, ...] = ()
    technology_stack_terms: tuple[str, ...] = ()
    original_source_metadata: ExternalSourceMetadata = field(default_factory=ExternalSourceMetadata)
    clean_text: str = ""
    meta_description: str | None = None
    section_lines: dict[str, tuple[str, ...]] = field(default_factory=dict)
    section_blocks: dict[str, tuple[str, ...]] = field(default_factory=dict)
    raw_capture_metadata: dict[str, Any] = field(default_factory=dict)
    warning: str | None = None


@dataclass(slots=True, frozen=True)
class MatchExplanationPayload:
    summary: str
    fit_score: float
    catalog_score: float
    final_score: float
    behavioral_affinity_score: float | None
    matched_skill_terms: tuple[str, ...]
    missing_skill_terms: tuple[str, ...]
    matched_location_terms: tuple[str, ...]
    matching_score_breakdown: tuple[MatchExplanationBreakdownItem, ...]
    key_evidence_points: tuple[MatchExplanationEvidencePoint, ...]
    gap_analysis: tuple[MatchExplanationGapItem, ...]
    top_reasons: tuple[str, ...]
    external_source_insights: ExternalSourceInsights = field(default_factory=ExternalSourceInsights)
    analysis_coverage: JobAnalysisCoverage | None = None
