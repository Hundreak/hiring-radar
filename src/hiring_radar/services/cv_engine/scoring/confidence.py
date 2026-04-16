from __future__ import annotations

from collections.abc import Iterable

from hiring_radar.services.cv_engine.config import ConfidenceScoringConfig
from hiring_radar.services.cv_engine.semantic.models import (
    ConfidenceLevel,
    FieldConfidenceAssessment,
)


def clamp_confidence_score(value: float) -> float:
    """Clamp a numeric confidence score to the supported 0.0-1.0 range."""
    return max(0.0, min(1.0, value))


def derive_confidence_level(
    score: float,
    config: ConfidenceScoringConfig,
) -> ConfidenceLevel:
    """Map a numeric confidence score to a coarse confidence level."""
    normalized_score = clamp_confidence_score(score)
    if normalized_score >= config.high_threshold:
        return ConfidenceLevel.HIGH
    if normalized_score >= config.medium_threshold:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def combine_confidence_components(
    *,
    base_score: float,
    bonuses: Iterable[tuple[str, float]],
    penalties: Iterable[tuple[str, float]],
    config: ConfidenceScoringConfig,
    reasons: Iterable[str] = (),
) -> FieldConfidenceAssessment:
    """Build a confidence assessment from deterministic score components."""
    bonus_list = [item for item in bonuses if item[1] > 0.0]
    penalty_list = [item for item in penalties if item[1] > 0.0]
    score = base_score
    for _, value in bonus_list:
        score += value
    for _, value in penalty_list:
        score -= value
    clamped_score = round(clamp_confidence_score(score), 4)
    level = derive_confidence_level(clamped_score, config)
    return FieldConfidenceAssessment(
        score=clamped_score,
        level=level,
        reasons=list(reasons),
        bonuses=[name for name, _ in bonus_list],
        penalties=[name for name, _ in penalty_list],
    )
