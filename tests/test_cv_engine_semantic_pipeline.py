from __future__ import annotations

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.legacy_runtime import (
    build_foundation_parser_result_from_text,
)
from hiring_radar.services.cv_engine.models import ParserStatus


SAMPLE_CV_TEXT = """
Alice Example
Senior Backend Engineer
alice@example.com | Berlin, Germany | https://github.com/alice

Summary
Backend engineer with strong FastAPI, Python, Docker and PostgreSQL experience.

Skills
Python
FastAPI
Docker
PostgreSQL
Communication

Experience
Senior Backend Engineer
Example Solutions GmbH
Jan 2020 - Present
Built APIs and platform tooling with Python, FastAPI and Docker.

Projects
Hiring Radar Platform - https://example.com/projects/hiring-radar

Certifications
AWS Certified Developer
""".strip()


def test_semantic_pipeline_enriches_skills_links_and_experience() -> None:
    result = build_foundation_parser_result_from_text(
        extracted_text=SAMPLE_CV_TEXT,
        filename="alice_cv.pdf",
        used_ocr=False,
        extraction_method="pdf_text",
        page_count=1,
        config=ParserRuntimeConfig(),
    )

    assert result.status in {ParserStatus.SUCCEEDED, ParserStatus.PARTIAL}
    assert result.context.parsed_data is not None
    parsed = result.context.parsed_data

    assert parsed.links
    assert parsed.projects
    assert parsed.certifications
    assert parsed.total_years_experience is not None
    assert any(skill.provenance is not None for skill in parsed.skills)
    assert parsed.experience_lines[0].title_provenance is not None
    assert parsed.metadata["headline"] == "Senior Backend Engineer"
    assert "backend_frameworks" in parsed.metadata["semantic_skill_categories"]
