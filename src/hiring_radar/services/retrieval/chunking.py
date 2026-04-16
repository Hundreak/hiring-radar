from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP_PARAGRAPHS = 1


@dataclass(slots=True, frozen=True)
class ChunkDraft:
    content: str
    token_estimate: int
    metadata_json: dict[str, object] = field(default_factory=dict)


def estimate_token_count(text: str) -> int:
    normalized = text.strip()
    if not normalized:
        return 0
    # Cheap deterministic approximation that is stable across environments.
    word_count = len(normalized.split())
    return max(1, int(word_count * 1.25))


def _normalize_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [paragraph.strip() for paragraph in normalized.split("\n\n")]
    return [paragraph for paragraph in paragraphs if paragraph]


def chunk_text(
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_paragraphs: int = DEFAULT_OVERLAP_PARAGRAPHS,
) -> list[ChunkDraft]:
    paragraphs = _normalize_paragraphs(text)
    if not paragraphs:
        normalized = text.strip()
        if not normalized:
            return []
        return [
            ChunkDraft(
                content=normalized,
                token_estimate=estimate_token_count(normalized),
                metadata_json={"paragraph_start": 0, "paragraph_end": 0},
            )
        ]

    chunks: list[ChunkDraft] = []
    current: list[str] = []
    current_length = 0
    start_index = 0

    for index, paragraph in enumerate(paragraphs):
        projected_length = current_length + (2 if current else 0) + len(paragraph)
        if current and projected_length > max_chars:
            content = "\n\n".join(current).strip()
            chunks.append(
                ChunkDraft(
                    content=content,
                    token_estimate=estimate_token_count(content),
                    metadata_json={
                        "paragraph_start": start_index,
                        "paragraph_end": index - 1,
                    },
                )
            )

            overlap = current[-overlap_paragraphs:] if overlap_paragraphs > 0 else []
            current = list(overlap)
            current_length = sum(len(item) for item in current) + max(0, len(current) - 1) * 2
            start_index = max(0, index - len(overlap))

        if not current:
            start_index = index

        current.append(paragraph)
        current_length += (2 if len(current) > 1 else 0) + len(paragraph)

    if current:
        content = "\n\n".join(current).strip()
        chunks.append(
            ChunkDraft(
                content=content,
                token_estimate=estimate_token_count(content),
                metadata_json={
                    "paragraph_start": start_index,
                    "paragraph_end": len(paragraphs) - 1,
                },
            )
        )

    return chunks
