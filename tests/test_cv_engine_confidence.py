from __future__ import annotations

from hiring_radar.services.cv_engine.config import ConfidenceScoringConfig
from hiring_radar.services.cv_engine.scoring.confidence import (
    clamp_confidence_score,
    combine_confidence_components,
    derive_confidence_level,
)


def test_combine_confidence_components_applies_bonuses_and_penalties() -> None:
    config = ConfidenceScoringConfig()
    assessment = combine_confidence_components(
        base_score=0.5,
        bonuses=[("section", 0.2), ("context", 0.1)],
        penalties=[("ambiguity", 0.05)],
        config=config,
        reasons=["section", "context", "ambiguity"],
    )

    assert assessment.score == 0.75
    assert assessment.level.value == "medium"
    assert "section" in assessment.bonuses
    assert "ambiguity" in assessment.penalties



def test_derive_confidence_level_maps_thresholds() -> None:
    config = ConfidenceScoringConfig(high_threshold=0.8, medium_threshold=0.55)

    assert derive_confidence_level(0.9, config).value == "high"
    assert derive_confidence_level(0.6, config).value == "medium"
    assert derive_confidence_level(0.4, config).value == "low"



def test_clamp_confidence_score_bounds_values() -> None:
    assert clamp_confidence_score(1.5) == 1.0
    assert clamp_confidence_score(-0.2) == 0.0
