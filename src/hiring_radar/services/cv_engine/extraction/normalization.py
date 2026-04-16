from __future__ import annotations

import re
import unicodedata

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.models import NormalizedTextArtifact, ParseContext
from hiring_radar.services.cv_engine.protocols import NormalizationStrategy

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_HORIZONTAL_WHITESPACE_RE = re.compile(r"[\t\x0b\x0c\r ]+")
_REPEATED_PUNCTUATION_RE = re.compile(r"([|/\\_~`=*#])\1{2,}")
_MULTI_BLANK_RE = re.compile(r"\n{3,}")
_BULLET_PREFIX_RE = re.compile(r"^\s*[•·▪◦●○■□►▸▹▶-]\s*")
_LINE_NOISE_RE = re.compile(r"^[^\w\s]{4,}$")
_PAGE_LABEL_RE = re.compile(r"^page\s+\d+\s*(of\s*\d+)?$", re.IGNORECASE)


class DeterministicTextNormalizationStrategy(NormalizationStrategy):
    """Normalize extracted CV text for downstream section and entity parsing."""

    def normalize(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> NormalizedTextArtifact:
        raw_text = context.extraction.text if context.extraction else ""
        return normalize_extracted_text(raw_text)



def normalize_extracted_text(text: str) -> NormalizedTextArtifact:
    """Normalize OCR/PDF extracted text into deterministic lines and metadata."""
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = _ZERO_WIDTH_RE.sub("", normalized)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _REPEATED_PUNCTUATION_RE.sub(r"\1", normalized)

    cleaned_lines: list[str] = []
    removed_noise_fragments: list[str] = []

    for line in normalized.split("\n"):
        cleaned_line, removed_fragment = _normalize_line(line)
        if removed_fragment:
            removed_noise_fragments.append(removed_fragment)
        if cleaned_line is None:
            continue
        cleaned_lines.append(cleaned_line)

    compacted_lines = _collapse_blank_lines(cleaned_lines)
    normalized_text = "\n".join(compacted_lines).strip()
    normalized_text = _MULTI_BLANK_RE.sub("\n\n", normalized_text)

    return NormalizedTextArtifact(
        text=normalized_text,
        lines=compacted_lines,
        removed_noise_fragments=removed_noise_fragments,
        metadata={
            "original_line_count": len(normalized.split("\n")),
            "normalized_line_count": len(compacted_lines),
            "removed_noise_count": len(removed_noise_fragments),
        },
    )



def _normalize_line(line: str) -> tuple[str | None, str | None]:
    collapsed = _HORIZONTAL_WHITESPACE_RE.sub(" ", line).strip()
    if not collapsed:
        return "", None

    collapsed = _BULLET_PREFIX_RE.sub("", collapsed)
    collapsed = collapsed.replace("–", "-").replace("—", "-")
    collapsed = collapsed.replace("•", "")
    collapsed = re.sub(r"\s+", " ", collapsed).strip(" ;|·•")

    if not collapsed:
        return None, line
    if _PAGE_LABEL_RE.match(collapsed):
        return None, line.strip()
    if _looks_like_noise(collapsed):
        return None, line.strip()
    return collapsed, None



def _looks_like_noise(value: str) -> bool:
    if _LINE_NOISE_RE.match(value):
        return True

    alpha_count = sum(character.isalpha() for character in value)
    digit_count = sum(character.isdigit() for character in value)
    non_alnum_count = sum(
        not character.isalnum() and not character.isspace() for character in value
    )
    length = max(len(value), 1)

    if alpha_count == 0 and digit_count == 0:
        return True
    if alpha_count <= 1 and non_alnum_count / length >= 0.55:
        return True
    if value.count("�") >= 2:
        return True
    return False



def _collapse_blank_lines(lines: list[str]) -> list[str]:
    compacted: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if previous_blank:
                continue
            previous_blank = True
            compacted.append("")
            continue
        previous_blank = False
        compacted.append(line)
    while compacted and compacted[0] == "":
        compacted.pop(0)
    while compacted and compacted[-1] == "":
        compacted.pop()
    return compacted
