from __future__ import annotations

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.models import (
    DocumentIngestionArtifact,
    ExtractionArtifact,
    NormalizedTextArtifact,
    ParseContext,
    SectionName,
)
from hiring_radar.services.cv_engine.segmentation.heading_scoring import (
    is_heading_candidate,
    score_heading_candidate,
)
from hiring_radar.services.cv_engine.segmentation.section_detection import (
    HybridSectionDetectionStrategy,
)


def _build_context(*, lines: list[str], language: str) -> ParseContext:
    return ParseContext(
        ingestion=DocumentIngestionArtifact(
            source_path="/tmp/alice_cv.pdf",
            filename="alice_cv.pdf",
            extension=".pdf",
            file_size_bytes=1024,
        ),
        extraction=ExtractionArtifact(
            text="\n".join(lines),
            extraction_method="pdf_text",
            used_ocr=False,
            page_count=1,
        ),
        normalized=NormalizedTextArtifact(
            text="\n".join(lines),
            lines=lines,
        ),
        detected_language=language,
    )



def test_heading_scoring_recognizes_composite_uppercase_heading() -> None:
    config = ParserRuntimeConfig()
    breakdown = score_heading_candidate(
        line="WORK EXPERIENCE & PROJECTS",
        language="en",
        config=config.section_detection,
    )

    assert breakdown.section_name == SectionName.EXPERIENCE
    assert SectionName.PROJECTS in breakdown.composite_sections
    assert breakdown.alias_ratio >= 0.72
    assert is_heading_candidate(breakdown, config=config.section_detection) is True



def test_section_detection_builds_header_and_named_sections_for_turkish_cv() -> None:
    strategy = HybridSectionDetectionStrategy()
    config = ParserRuntimeConfig()
    context = _build_context(
        language="tr",
        lines=[
            "Ayşe Yılmaz",
            "Senior Backend Engineer",
            "ÖZET",
            "Dağıtık sistemler ve FastAPI üzerine çalışıyorum.",
            "İŞ DENEYİMİ",
            "Senior Backend Engineer",
            "ACME Teknoloji",
            "YETENEKLER",
            "Python",
            "FastAPI",
        ],
    )

    artifact = strategy.detect_sections(context=context, config=config)

    assert [section.name for section in artifact.sections] == [
        SectionName.HEADER,
        SectionName.SUMMARY,
        SectionName.EXPERIENCE,
        SectionName.SKILLS,
    ]
    assert artifact.sections[0].lines == ["Ayşe Yılmaz", "Senior Backend Engineer"]
    assert artifact.sections[1].heading == "ÖZET"
    assert artifact.sections[2].heading == "İŞ DENEYİMİ"
    assert artifact.sections[3].lines == ["Python", "FastAPI"]



def test_section_detection_falls_back_to_other_when_no_headings_are_present() -> None:
    strategy = HybridSectionDetectionStrategy()
    config = ParserRuntimeConfig()
    context = _build_context(
        language="de",
        lines=[
            "Max Mustermann",
            "Senior Software Engineer",
            "Berlin | max@example.com",
            "Python, FastAPI, PostgreSQL",
        ],
    )

    artifact = strategy.detect_sections(context=context, config=config)

    assert len(artifact.sections) == 1
    assert artifact.sections[0].name == SectionName.OTHER
    assert artifact.sections[0].metadata["fallback"] == "no_headings_detected"
