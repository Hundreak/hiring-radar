from __future__ import annotations

from collections.abc import Iterable

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig, SkillExtractionConfig
from hiring_radar.services.cv_engine.models import ParsedSkill, SectionBlock, SectionName
from hiring_radar.services.cv_engine.semantic.skill_resolution import (
    resolve_skill_mentions_from_sections,
    resolve_skill_mentions_from_text,
)

_SECTION_DEFAULT = SectionName.OTHER


def extract_skills_from_sections(
    sections: Iterable[SectionBlock],
    *,
    config: SkillExtractionConfig | None = None,
) -> list[ParsedSkill]:
    """Extract canonicalized skills from a list of sections."""
    runtime_config = ParserRuntimeConfig()
    if config is not None:
        runtime_config.skill_extraction = config
    resolved_skills = resolve_skill_mentions_from_sections(
        sections,
        config=runtime_config,
    )
    return [_resolved_to_parsed(skill) for skill in resolved_skills]



def extract_skills_from_text(
    text: str,
    *,
    section_name: SectionName | None = None,
    config: SkillExtractionConfig | None = None,
) -> list[ParsedSkill]:
    """Extract skills from text using word-boundary and section-aware heuristics."""
    runtime_config = ParserRuntimeConfig()
    if config is not None:
        runtime_config.skill_extraction = config
    resolved_skills = resolve_skill_mentions_from_text(
        text,
        section_name=(section_name or _SECTION_DEFAULT).value,
        config=runtime_config,
    )
    return [_resolved_to_parsed(skill) for skill in resolved_skills]



def _resolved_to_parsed(skill) -> ParsedSkill:
    return ParsedSkill(
        canonical_name=skill.canonical_name,
        matched_text=skill.matched_alias,
        source_section=(
            SectionName(skill.source_section)
            if skill.source_section in {item.value for item in SectionName}
            else _SECTION_DEFAULT
        ),
        confidence=skill.confidence,
        category=skill.category,
        skill_type=skill.skill_type,
        confidence_assessment=skill.confidence_assessment,
        provenance=skill.provenance,
    )
