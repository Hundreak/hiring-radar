from __future__ import annotations

from hiring_radar.services.cv_engine.segmentation.heading_scoring import (
    HeadingScoreBreakdown,
    is_heading_candidate,
    score_heading_candidate,
)
from hiring_radar.services.cv_engine.segmentation.section_detection import (
    HybridSectionDetectionStrategy,
)

__all__ = [
    "HeadingScoreBreakdown",
    "HybridSectionDetectionStrategy",
    "is_heading_candidate",
    "score_heading_candidate",
]
