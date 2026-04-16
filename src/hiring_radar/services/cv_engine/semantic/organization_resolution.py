from __future__ import annotations

import re

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.scoring.confidence import combine_confidence_components
from hiring_radar.services.cv_engine.semantic.models import (
    FieldProvenance,
    FieldSource,
    ResolvedOrganizationSignal,
    SemanticEvidence,
)

_ORG_HINT_RE = re.compile(
    r"\b(?:llc|inc\.?|corp\.?|corporation|ltd\.?|limited|gmbh|ag|plc|holding|holdings|group|solutions|systems|technologies|technology|a\.ş\.?|as|oy|ab)\b",
    re.IGNORECASE,
)


def resolve_organization_candidate(
    text: str,
    *,
    config: ParserRuntimeConfig | None = None,
) -> ResolvedOrganizationSignal | None:
    """Resolve one organization/company candidate from text."""
    runtime_config = config or ParserRuntimeConfig()
    cleaned = re.sub(r"\s+", " ", text).strip(" |-–—,:;")
    if not cleaned:
        return None

    words = cleaned.split()
    if len(words) > 6 and not _ORG_HINT_RE.search(cleaned):
        return None
    lowercase_initials = sum(
        1 for word in words if word[:1].isalpha() and word[:1].islower()
    )
    if lowercase_initials >= 3:
        return None
    bonuses: list[tuple[str, float]] = []
    reasons: list[str] = []

    if _ORG_HINT_RE.search(cleaned):
        bonuses.append(("legal_suffix", 0.2))
        reasons.append("legal_suffix")

    if 1 <= len(words) <= 6 and all(
        not word[:1].isalpha() or word[:1].isupper() for word in words
    ):
        bonuses.append(("capitalization_pattern", 0.14))
        reasons.append("capitalization_pattern")

    if len(words) >= 2:
        bonuses.append(("multi_token_org", 0.08))
        reasons.append("multi_token_org")

    assessment = combine_confidence_components(
        base_score=runtime_config.confidence_scoring.base_score - 0.02,
        bonuses=bonuses,
        penalties=(),
        config=runtime_config.confidence_scoring,
        reasons=reasons,
    )
    if assessment.score < runtime_config.semantic_resolution.organization_signal_min_confidence:
        return None

    evidence = SemanticEvidence(
        text=cleaned,
        normalized_text=cleaned.casefold(),
        metadata={"word_count": len(words)},
    )
    provenance = FieldProvenance(
        source=FieldSource.HEURISTIC,
        extractor="organization_resolution",
        confidence=assessment.score,
        reasons=reasons,
        evidences=[evidence],
    )
    return ResolvedOrganizationSignal(
        organization_name=cleaned,
        organization_type="company",
        confidence=assessment.score,
        confidence_assessment=assessment,
        provenance=provenance,
    )
