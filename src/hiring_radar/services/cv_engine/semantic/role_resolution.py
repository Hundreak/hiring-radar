from __future__ import annotations

import re

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.scoring.confidence import combine_confidence_components
from hiring_radar.services.cv_engine.semantic.models import (
    FieldProvenance,
    FieldSource,
    ResolvedRoleSignal,
    SemanticEvidence,
)

_ROLE_TOKENS = {
    "engineer": ("individual_contributor", "engineering"),
    "developer": ("individual_contributor", "engineering"),
    "architect": ("lead", "architecture"),
    "manager": ("manager", "management"),
    "director": ("director", "management"),
    "analyst": ("individual_contributor", "analytics"),
    "consultant": ("individual_contributor", "consulting"),
    "scientist": ("individual_contributor", "data_science"),
    "lead": ("lead", "leadership"),
    "specialist": ("individual_contributor", "specialist"),
    "mühendis": ("individual_contributor", "engineering"),
    "geliştirici": ("individual_contributor", "engineering"),
    "uzman": ("individual_contributor", "specialist"),
    "yönetici": ("manager", "management"),
    "mimar": ("lead", "architecture"),
    "ingenieur": ("individual_contributor", "engineering"),
    "entwickler": ("individual_contributor", "engineering"),
    "berater": ("individual_contributor", "consulting"),
    "leiter": ("lead", "leadership"),
    "managerin": ("manager", "management"),
}

_SENIORITY_HINTS = {
    "junior": "junior",
    "mid": "mid",
    "senior": "senior",
    "staff": "staff",
    "principal": "principal",
    "lead": "lead",
    "manager": "manager",
    "director": "director",
    "junioren": "junior",
    "senioren": "senior",
}

_ROLE_SPLIT_RE = re.compile(r"[|,;/]+")


def resolve_role_candidate(
    text: str,
    *,
    section_name: str | None = None,
    config: ParserRuntimeConfig | None = None,
) -> ResolvedRoleSignal | None:
    """Resolve one role/title candidate from text."""
    runtime_config = config or ParserRuntimeConfig()
    cleaned = re.sub(r"\s+", " ", text).strip(" |-–—,:;")
    if not cleaned:
        return None

    lowered = cleaned.casefold()
    matched_tokens = [token for token in _ROLE_TOKENS if re.search(rf"\b{re.escape(token)}\b", lowered)]
    if not matched_tokens:
        return None

    seniority = next(
        (
            value
            for key, value in _SENIORITY_HINTS.items()
            if re.search(rf"\b{re.escape(key)}\b", lowered)
        ),
        None,
    )
    function_family = _ROLE_TOKENS[matched_tokens[0]][1]

    bonuses: list[tuple[str, float]] = [("role_keyword_match", 0.18)]
    reasons = ["role_keyword_match"]
    if seniority is not None:
        bonuses.append(("seniority_detected", 0.08))
        reasons.append("seniority_detected")
    if section_name and section_name.casefold() in {"experience", "summary", "header"}:
        bonuses.append((f"section:{section_name.casefold()}", 0.08))
        reasons.append(f"section:{section_name.casefold()}")

    assessment = combine_confidence_components(
        base_score=runtime_config.confidence_scoring.base_score,
        bonuses=bonuses,
        penalties=(),
        config=runtime_config.confidence_scoring,
        reasons=reasons,
    )
    if assessment.score < runtime_config.semantic_resolution.role_signal_min_confidence:
        return None

    evidence = SemanticEvidence(
        text=cleaned,
        normalized_text=lowered,
        section_name=section_name,
        metadata={"matched_tokens": matched_tokens},
    )
    provenance = FieldProvenance(
        source=FieldSource.HEURISTIC,
        extractor="role_resolution",
        confidence=assessment.score,
        reasons=reasons,
        evidences=[evidence],
        metadata={"function_family": function_family, "seniority": seniority},
    )
    return ResolvedRoleSignal(
        title=cleaned,
        seniority=seniority,
        function_family=function_family,
        confidence=assessment.score,
        confidence_assessment=assessment,
        provenance=provenance,
    )
