from __future__ import annotations

import re
from collections.abc import Iterable

from hiring_radar.services.cv_engine.config import (
    ParserRuntimeConfig,
    SkillExtractionConfig,
)
from hiring_radar.services.cv_engine.models import SectionBlock
from hiring_radar.services.cv_engine.scoring.confidence import (
    combine_confidence_components,
)
from hiring_radar.services.cv_engine.semantic.models import (
    FieldProvenance,
    FieldSource,
    ResolvedSkill,
    SemanticEvidence,
)
from hiring_radar.services.cv_engine.semantic.skill_catalog import (
    SkillCatalogEntry,
    iter_skill_catalog_entries,
)

_AMBIGUOUS_CONTEXT_RE = re.compile(
    r"\b(?:using|with|built|developed|experience|worked|stack|tooling|framework|backend|frontend|api|cloud|database|microservice|testing|automation)\b",
    re.IGNORECASE,
)


class SkillResolver:
    """Resolve semantic skills from free text and logical sections."""

    def __init__(self, config: ParserRuntimeConfig | None = None) -> None:
        self._config = config or ParserRuntimeConfig()

    def resolve_from_sections(self, sections: Iterable[SectionBlock]) -> list[ResolvedSkill]:
        """Resolve canonical skills from logical section blocks."""
        collected: dict[str, ResolvedSkill] = {}
        for section in sections:
            section_text = "\n".join(section.lines)
            for skill in self.resolve_from_text(
                section_text,
                section_name=section.name.value,
            ):
                key = skill.canonical_name.casefold()
                existing = collected.get(key)
                if existing is None or skill.confidence > existing.confidence:
                    collected[key] = skill
        return sorted(
            collected.values(),
            key=lambda item: (-item.confidence, item.canonical_name.casefold()),
        )

    def resolve_from_text(
        self,
        text: str,
        *,
        section_name: str | None = None,
    ) -> list[ResolvedSkill]:
        """Resolve canonical skills from one text fragment."""
        config = self._config.skill_extraction
        section_key = (section_name or "other").casefold()
        matches: dict[str, ResolvedSkill] = {}
        duplicate_hits: dict[str, int] = {}

        for entry in iter_skill_catalog_entries():
            for alias in entry.aliases:
                if len(alias) < config.minimum_skill_length:
                    continue
                for match in _iter_alias_matches(text, alias):
                    if not _is_valid_match(
                        entry=entry,
                        text=text,
                        match=match,
                        section_name=section_key,
                    ):
                        continue
                    key = entry.canonical_name.casefold()
                    duplicate_hits[key] = duplicate_hits.get(key, 0) + 1
                    resolved = _build_resolved_skill(
                        entry=entry,
                        matched_text=match.group(0),
                        section_name=section_key,
                        full_text=text,
                        config=config,
                        runtime_config=self._config,
                        duplicate_count=duplicate_hits[key],
                    )
                    existing = matches.get(key)
                    if existing is None or resolved.confidence > existing.confidence:
                        matches[key] = resolved

        return sorted(
            matches.values(),
            key=lambda item: (-item.confidence, item.canonical_name.casefold()),
        )


def resolve_skill_mentions_from_sections(
    sections: Iterable[SectionBlock],
    *,
    config: ParserRuntimeConfig | None = None,
) -> list[ResolvedSkill]:
    """Resolve semantic skills from sections."""
    return SkillResolver(config).resolve_from_sections(sections)


def resolve_skill_mentions_from_text(
    text: str,
    *,
    section_name: str | None = None,
    config: ParserRuntimeConfig | None = None,
) -> list[ResolvedSkill]:
    """Resolve semantic skills from one text fragment."""
    return SkillResolver(config).resolve_from_text(text, section_name=section_name)


def _iter_alias_matches(text: str, alias: str) -> Iterable[re.Match[str]]:
    if re.fullmatch(r"[A-Za-z0-9]+", alias):
        pattern = re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.IGNORECASE)
    else:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
    return pattern.finditer(text)


def _is_valid_match(
    *,
    entry: SkillCatalogEntry,
    text: str,
    match: re.Match[str],
    section_name: str,
) -> bool:
    if not entry.ambiguous:
        return True
    if section_name in {"skills", "projects"}:
        return True
    window_start = max(match.start() - 48, 0)
    window_end = min(match.end() + 48, len(text))
    window_text = text[window_start:window_end]
    return _AMBIGUOUS_CONTEXT_RE.search(window_text) is not None


def _build_resolved_skill(
    *,
    entry: SkillCatalogEntry,
    matched_text: str,
    section_name: str,
    full_text: str,
    config: SkillExtractionConfig,
    runtime_config: ParserRuntimeConfig,
    duplicate_count: int,
) -> ResolvedSkill:
    bonuses: list[tuple[str, float]] = [("catalog_alias_match", 0.12)]
    penalties: list[tuple[str, float]] = []
    reasons = ["catalog_alias_match"]

    section_boost = config.section_boosts.get(section_name, 0.0)
    if section_boost:
        bonuses.append((f"section:{section_name}", section_boost))
        reasons.append(f"section:{section_name}")

    if _has_context_signal(full_text):
        bonuses.append(("context_match", config.context_bonus))
        reasons.append("context_match")

    if entry.ambiguous:
        penalties.append(("ambiguous_skill", config.ambiguous_skill_penalty))
        reasons.append("ambiguous_skill")

    duplicate_penalty = max(duplicate_count - 1, 0) * config.duplicate_skill_decay
    if duplicate_penalty:
        penalties.append(("duplicate_decay", duplicate_penalty))

    assessment = combine_confidence_components(
        base_score=config.default_confidence,
        bonuses=bonuses,
        penalties=penalties,
        config=runtime_config.confidence_scoring,
        reasons=reasons,
    )
    evidence = SemanticEvidence(
        text=matched_text,
        normalized_text=matched_text.casefold(),
        section_name=section_name,
        matched_alias=matched_text,
        metadata={"category": entry.category},
    )
    provenance = FieldProvenance(
        source=FieldSource.CATALOG,
        extractor="skill_resolution",
        confidence=assessment.score,
        reasons=reasons,
        evidences=[evidence],
        metadata={
            "canonical_name": entry.canonical_name,
            "category": entry.category,
            "skill_type": entry.skill_type,
        },
    )
    return ResolvedSkill(
        canonical_name=entry.canonical_name,
        display_name=entry.canonical_name,
        matched_alias=matched_text,
        category=entry.category,
        skill_type=entry.skill_type,
        source_section=section_name,
        ambiguous=entry.ambiguous,
        confidence=assessment.score,
        confidence_assessment=assessment,
        provenance=provenance,
    )


def _has_context_signal(text: str) -> bool:
    return _AMBIGUOUS_CONTEXT_RE.search(text) is not None
