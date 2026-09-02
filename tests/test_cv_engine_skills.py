from __future__ import annotations

from hiring_radar.services.cv_engine.models import SectionBlock, SectionName
from hiring_radar.services.cv_engine.parsing.skills import (
    extract_skills_from_sections,
    extract_skills_from_text,
)


def test_extract_skills_from_text_uses_word_boundaries() -> None:
    skills = extract_skills_from_text(
        "Strong experience with FastAPI, Python and PostgreSQL.",
        section_name=SectionName.SUMMARY,
    )

    canonical_names = [item.canonical_name for item in skills]
    assert "FastAPI" in canonical_names
    assert "Python" in canonical_names
    assert "PostgreSQL" in canonical_names



def test_extract_skills_from_text_avoids_ambiguous_react_false_positive() -> None:
    skills = extract_skills_from_text(
        "We react to market changes quickly and adapt our roadmap.",
        section_name=SectionName.SUMMARY,
    )

    canonical_names = [item.canonical_name for item in skills]
    assert "React" not in canonical_names



def test_extract_skills_from_sections_applies_section_aware_confidence() -> None:
    sections = [
        SectionBlock(
            name=SectionName.SKILLS,
            heading="Skills",
            lines=["Python", "FastAPI", "Docker"],
            confidence=0.9,
        ),
        SectionBlock(
            name=SectionName.EXPERIENCE,
            heading="Experience",
            lines=["Built APIs with Python and FastAPI"],
            confidence=0.8,
        ),
    ]

    skills = extract_skills_from_sections(sections)
    canonical_names = [item.canonical_name for item in skills]

    assert canonical_names[:3] == ["Docker", "FastAPI", "Python"]
    fastapi_skill = next(item for item in skills if item.canonical_name == "FastAPI")
    assert fastapi_skill.source_section == SectionName.SKILLS
    assert fastapi_skill.confidence >= 0.9
