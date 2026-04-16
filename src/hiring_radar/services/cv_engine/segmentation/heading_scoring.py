from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.services.cv_engine.config import SectionDetectionConfig
from hiring_radar.services.cv_engine.language.aliases import best_section_alias_match
from hiring_radar.services.cv_engine.models import SectionName


@dataclass(frozen=True, slots=True)
class HeadingScoreBreakdown:
    """Detailed heading-scoring result for one text line."""

    candidate: str
    normalized_candidate: str
    section_name: SectionName | None
    alias_ratio: float
    uppercase_signal: float
    short_line_signal: float
    punctuation_signal: float
    token_shape_signal: float
    score: float
    composite_sections: tuple[SectionName, ...]



def score_heading_candidate(
    *,
    line: str,
    language: str,
    config: SectionDetectionConfig,
) -> HeadingScoreBreakdown:
    """Score one normalized line as a possible section heading."""
    token_count = len([token for token in line.split() if token])
    best_section, alias_ratio, composite_sections = best_section_alias_match(
        line,
        language,
    )

    uppercase_signal = _compute_uppercase_signal(line)
    short_line_signal = _compute_short_line_signal(
        token_count=token_count,
        max_heading_words=config.max_heading_words,
    )
    punctuation_signal = _compute_punctuation_signal(line)
    token_shape_signal = _compute_token_shape_signal(token_count)

    score = alias_ratio * 0.62
    score += uppercase_signal * config.uppercase_bonus
    score += short_line_signal * 0.08
    score += punctuation_signal * 0.05
    score += token_shape_signal * 0.03
    score = min(score, 1.0)

    return HeadingScoreBreakdown(
        candidate=line,
        normalized_candidate=line.casefold().strip(),
        section_name=best_section,
        alias_ratio=alias_ratio,
        uppercase_signal=uppercase_signal,
        short_line_signal=short_line_signal,
        punctuation_signal=punctuation_signal,
        token_shape_signal=token_shape_signal,
        score=score,
        composite_sections=composite_sections,
    )



def is_heading_candidate(
    breakdown: HeadingScoreBreakdown,
    *,
    config: SectionDetectionConfig,
) -> bool:
    """Return whether the scored line should be treated as a heading."""
    if breakdown.section_name is None:
        return False
    if breakdown.alias_ratio < config.fuzzy_alias_min_ratio:
        return False
    return breakdown.score >= config.minimum_heading_score



def _compute_uppercase_signal(line: str) -> float:
    alpha_characters = [character for character in line if character.isalpha()]
    if not alpha_characters:
        return 0.0
    uppercase_count = sum(character.isupper() for character in alpha_characters)
    return uppercase_count / len(alpha_characters)



def _compute_short_line_signal(*, token_count: int, max_heading_words: int) -> float:
    if token_count <= 0 or token_count > max_heading_words:
        return 0.0
    distance = max_heading_words - token_count
    return min(1.0, 0.45 + (distance / max_heading_words))



def _compute_punctuation_signal(line: str) -> float:
    stripped = line.strip()
    if not stripped:
        return 0.0
    if stripped.endswith((":", ";", ".", ",")):
        return 0.25
    return 1.0



def _compute_token_shape_signal(token_count: int) -> float:
    if token_count == 1:
        return 1.0
    if token_count == 2:
        return 0.9
    if token_count <= 4:
        return 0.7
    if token_count <= 6:
        return 0.45
    return 0.1
