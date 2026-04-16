from __future__ import annotations

from hiring_radar.services.cv_engine.ats import AtsLevel, score_ats_compatibility
from hiring_radar.services.cv_engine.models import (
    ExtractionArtifact,
    ParsedCvData,
    ParsedDateRange,
    ParsedExperienceLine,
    ParsedSkill,
    QualityBand,
    QualityScoreResult,
    SectionBlock,
    SectionName,
)


def test_score_ats_compatibility_returns_high_for_structured_cv() -> None:
    parsed_data = ParsedCvData(
        full_name="Alice Example",
        emails=["alice@example.com"],
        phone_numbers=["+49 171 1234567"],
        summary="Senior backend engineer with distributed systems experience.",
        skills=[
            ParsedSkill(canonical_name="Python", matched_text="Python", confidence=0.92),
            ParsedSkill(canonical_name="FastAPI", matched_text="FastAPI", confidence=0.89),
            ParsedSkill(canonical_name="PostgreSQL", matched_text="PostgreSQL", confidence=0.84),
        ],
        experience_lines=[
            ParsedExperienceLine(
                title="Senior Backend Engineer",
                company_name="ACME GmbH",
                date_range=ParsedDateRange(
                    start_year=2021,
                    start_month=1,
                    end_year=None,
                    end_month=None,
                    is_present=True,
                    raw_text="Januar 2021 - Heute",
                    confidence=0.9,
                ),
                confidence=0.88,
            )
        ],
        section_names=[SectionName.HEADER, SectionName.SUMMARY, SectionName.EXPERIENCE, SectionName.SKILLS],
    )
    extraction = ExtractionArtifact(text="Example", extraction_method="pdf_text")
    quality = QualityScoreResult(score=87, band=QualityBand.HIGH)
    sections = [
        SectionBlock(name=SectionName.HEADER, lines=["Alice Example"]),
        SectionBlock(name=SectionName.SUMMARY, lines=["Summary"]),
        SectionBlock(name=SectionName.EXPERIENCE, lines=["Experience"]),
        SectionBlock(name=SectionName.SKILLS, lines=["Skills"]),
    ]

    report = score_ats_compatibility(
        parsed_data,
        sections=sections,
        extraction=extraction,
        quality=quality,
    )

    assert report.level == AtsLevel.HIGH
    assert report.score >= 78
    assert not any(issue.code == "missing_contact_bundle" for issue in report.issues)


def test_score_ats_compatibility_penalizes_ocr_and_missing_contact() -> None:
    parsed_data = ParsedCvData(
        skills=[ParsedSkill(canonical_name="Python", matched_text="Python", confidence=0.44)],
        experience_lines=[ParsedExperienceLine(title="Developer", confidence=0.45)],
        section_names=[SectionName.EXPERIENCE],
    )
    extraction = ExtractionArtifact(
        text="Example",
        extraction_method="image_ocr",
        used_ocr=True,
        layout_metadata={"is_multi_column": True},
    )
    quality = QualityScoreResult(score=31, band=QualityBand.LOW)

    report = score_ats_compatibility(parsed_data, extraction=extraction, quality=quality)

    assert report.level == AtsLevel.LOW
    issue_codes = {issue.code for issue in report.issues}
    assert "missing_contact_bundle" in issue_codes
    assert "ocr_source" in issue_codes
    assert "multi_column_layout" in issue_codes
    assert "low_quality_parse" in issue_codes


def test_score_ats_compatibility_warns_about_missing_standard_sections() -> None:
    parsed_data = ParsedCvData(
        full_name="Alice Example",
        emails=["alice@example.com"],
        section_names=[SectionName.HEADER],
    )

    report = score_ats_compatibility(parsed_data)

    codes = {issue.code for issue in report.issues}
    assert "missing_section_experience" in codes
    assert "missing_section_skills" in codes
