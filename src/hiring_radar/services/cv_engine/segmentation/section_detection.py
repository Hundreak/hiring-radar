from __future__ import annotations

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.models import (
    ParseContext,
    SectionBlock,
    SectionDetectionArtifact,
    SectionName,
)
from hiring_radar.services.cv_engine.protocols import SectionDetectionStrategy
from hiring_radar.services.cv_engine.segmentation.heading_scoring import (
    is_heading_candidate,
    score_heading_candidate,
)


class HybridSectionDetectionStrategy(SectionDetectionStrategy):
    """Detect logical CV sections with fuzzy aliases and heading heuristics."""

    def detect_sections(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> SectionDetectionArtifact:
        lines = context.normalized.lines if context.normalized else []
        language = context.detected_language or config.language_detection.fallback_language
        if not lines:
            return SectionDetectionArtifact(
                sections=[],
                unassigned_lines=[],
                metadata={"detected_language": language, "heading_count": 0},
            )

        sections: list[SectionBlock] = []
        preamble_lines: list[str] = []
        current_section: SectionBlock | None = None
        heading_count = 0

        for line in lines:
            if not line:
                if current_section is not None and current_section.lines:
                    current_section.lines.append("")
                continue

            breakdown = score_heading_candidate(
                line=line,
                language=language,
                config=config.section_detection,
            )
            if is_heading_candidate(breakdown, config=config.section_detection):
                heading_count += 1
                current_section = SectionBlock(
                    name=breakdown.section_name or SectionName.OTHER,
                    heading=line,
                    lines=[],
                    confidence=breakdown.score,
                    metadata={
                        "heading_score": breakdown.score,
                        "alias_ratio": breakdown.alias_ratio,
                        "composite_sections": [
                            item.value for item in breakdown.composite_sections
                        ],
                    },
                )
                sections.append(current_section)
                continue

            if current_section is None:
                preamble_lines.append(line)
                continue

            current_section.lines.append(line)

        if not sections:
            return SectionDetectionArtifact(
                sections=[
                    SectionBlock(
                        name=SectionName.OTHER,
                        heading=None,
                        lines=[line for line in lines if line],
                        confidence=0.35,
                        metadata={"fallback": "no_headings_detected"},
                    )
                ],
                unassigned_lines=[],
                metadata={"detected_language": language, "heading_count": 0},
            )

        if preamble_lines:
            sections.insert(
                0,
                SectionBlock(
                    name=SectionName.HEADER,
                    heading=None,
                    lines=preamble_lines,
                    confidence=0.82,
                    metadata={"source": "preamble"},
                ),
            )

        cleaned_sections = [_trim_trailing_blank_lines(section) for section in sections]
        return SectionDetectionArtifact(
            sections=cleaned_sections,
            unassigned_lines=[],
            metadata={
                "detected_language": language,
                "heading_count": heading_count,
                "section_count": len(cleaned_sections),
            },
        )



def _trim_trailing_blank_lines(section: SectionBlock) -> SectionBlock:
    lines = list(section.lines)
    while lines and not lines[-1]:
        lines.pop()
    return section.model_copy(update={"lines": lines})
