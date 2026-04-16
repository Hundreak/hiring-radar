from __future__ import annotations

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.models import SectionBlock, SectionName
from hiring_radar.services.cv_engine.semantic.skill_resolution import (
    resolve_skill_mentions_from_sections,
    resolve_skill_mentions_from_text,
)


def test_resolve_skill_mentions_from_text_returns_provenance_and_category() -> None:
    skills = resolve_skill_mentions_from_text(
        "Built APIs with FastAPI, PostgreSQL and Docker.",
        section_name="summary",
    )

    fastapi = next(item for item in skills if item.canonical_name == "FastAPI")
    assert fastapi.category == "backend_frameworks"
    assert fastapi.provenance is not None
    assert fastapi.confidence_assessment is not None
    assert fastapi.confidence_assessment.level.value in {"high", "medium"}



def test_resolve_skill_mentions_from_sections_suppresses_ambiguous_react_outside_skill_context() -> None:
    sections = [
        SectionBlock(
            name=SectionName.SUMMARY,
            heading="Summary",
            lines=["We react to market changes quickly and align roadmap decisions."],
            confidence=0.92,
        )
    ]

    skills = resolve_skill_mentions_from_sections(sections)
    canonical_names = [item.canonical_name for item in skills]
    assert "React" not in canonical_names



def test_resolve_skill_mentions_from_sections_prefers_skill_section_signal() -> None:
    runtime_config = ParserRuntimeConfig()
    sections = [
        SectionBlock(
            name=SectionName.EXPERIENCE,
            heading="Experience",
            lines=["Built services with Python and FastAPI."],
            confidence=0.8,
        ),
        SectionBlock(
            name=SectionName.SKILLS,
            heading="Skills",
            lines=["Python", "FastAPI", "Docker"],
            confidence=0.95,
        ),
    ]

    skills = resolve_skill_mentions_from_sections(sections, config=runtime_config)
    fastapi = next(item for item in skills if item.canonical_name == "FastAPI")
    assert fastapi.source_section == "skills"
    assert fastapi.confidence >= 0.8
