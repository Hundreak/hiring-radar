from __future__ import annotations

import re

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.scoring.confidence import combine_confidence_components
from hiring_radar.services.cv_engine.semantic.models import (
    FieldProvenance,
    FieldSource,
    ResolvedLocationSignal,
    SemanticEvidence,
)

_CITY_HINTS = {
    "berlin": ("Berlin", "Germany"),
    "munich": ("Munich", "Germany"),
    "münchen": ("Munich", "Germany"),
    "hamburg": ("Hamburg", "Germany"),
    "istanbul": ("Istanbul", "Turkey"),
    "ankara": ("Ankara", "Turkey"),
    "izmir": ("Izmir", "Turkey"),
    "london": ("London", "United Kingdom"),
    "amsterdam": ("Amsterdam", "Netherlands"),
}
_REMOTE_HINTS = {"remote", "hybrid", "onsite", "uzaktan", "hibrit", "vor ort"}


def resolve_location_candidate(
    text: str,
    *,
    config: ParserRuntimeConfig | None = None,
) -> ResolvedLocationSignal | None:
    """Resolve one location candidate from text."""
    runtime_config = config or ParserRuntimeConfig()
    cleaned = re.sub(r"\s+", " ", text).strip(" |-–—,:;")
    if not cleaned:
        return None

    lowered = cleaned.casefold()
    bonuses: list[tuple[str, float]] = []
    reasons: list[str] = []
    city: str | None = None
    country: str | None = None
    remote_hint: str | None = None

    for token, (resolved_city, resolved_country) in _CITY_HINTS.items():
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            city = resolved_city
            country = resolved_country
            bonuses.append(("city_catalog_match", 0.18))
            reasons.append("city_catalog_match")
            break

    for hint in _REMOTE_HINTS:
        if hint in lowered:
            remote_hint = hint
            bonuses.append(("remote_hint", 0.1))
            reasons.append("remote_hint")
            break

    if "," in cleaned:
        bonuses.append(("comma_location_shape", 0.08))
        reasons.append("comma_location_shape")

    assessment = combine_confidence_components(
        base_score=runtime_config.confidence_scoring.base_score - 0.04,
        bonuses=bonuses,
        penalties=(),
        config=runtime_config.confidence_scoring,
        reasons=reasons,
    )
    if assessment.score < runtime_config.semantic_resolution.location_signal_min_confidence:
        return None

    evidence = SemanticEvidence(
        text=cleaned,
        normalized_text=lowered,
        metadata={"city": city, "country": country, "remote_hint": remote_hint},
    )
    provenance = FieldProvenance(
        source=FieldSource.HEURISTIC,
        extractor="location_resolution",
        confidence=assessment.score,
        reasons=reasons,
        evidences=[evidence],
    )
    return ResolvedLocationSignal(
        location_name=cleaned,
        normalized_country=country,
        normalized_city=city,
        remote_hint=remote_hint,
        confidence=assessment.score,
        confidence_assessment=assessment,
        provenance=provenance,
    )
