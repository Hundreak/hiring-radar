from __future__ import annotations

import re
from dataclasses import dataclass

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import SubscriberAiLearnedMemory


@dataclass(slots=True, frozen=True)
class LearnedMemoryCandidate:
    memory_key: str
    memory_note: str
    confidence: float


_ROLE_PATTERNS = (
    "embedded",
    "firmware",
    "backend",
    "python",
    "electronics",
    "rf",
    "stm32",
    "ai",
)


def extract_learning_memory_candidates(
    *,
    prompt: str,
    locale: str,
) -> list[LearnedMemoryCandidate]:
    text = " ".join(prompt.strip().split())
    lowered = text.lower()
    candidates: list[LearnedMemoryCandidate] = []

    for pattern in _ROLE_PATTERNS:
        if pattern in lowered:
            candidates.append(
                LearnedMemoryCandidate(
                    memory_key=f"interest:{pattern}",
                    memory_note=f"User repeatedly shows interest in {pattern} oriented guidance.",
                    confidence=0.56,
                )
            )

    if any(term in lowered for term in ("uzaktan", "remote", "hybrid", "hibrit")):
        candidates.append(
            LearnedMemoryCandidate(
                memory_key="preference:work_mode",
                memory_note="User cares about work mode preferences when discussing career direction.",
                confidence=0.62,
            )
        )

    if re.search(r"\b(cv|özgeçmiş|resume)\b", lowered):
        candidates.append(
            LearnedMemoryCandidate(
                memory_key="workflow:cv_improvement",
                memory_note="User uses copilot for CV and profile improvement workflows.",
                confidence=0.64,
            )
        )

    deduped: dict[str, LearnedMemoryCandidate] = {}
    for candidate in candidates:
        deduped[candidate.memory_key] = candidate
    return list(deduped.values())


def persist_learning_memory_candidates(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    candidates: list[LearnedMemoryCandidate],
    observed_at: str,
) -> list[SubscriberAiLearnedMemory]:
    stored: list[SubscriberAiLearnedMemory] = []
    for candidate in candidates:
        stored.append(
            repository.upsert_subscriber_ai_learned_memory(
                subscriber_id,
                memory_key=candidate.memory_key,
                memory_note=candidate.memory_note,
                source_type="conversation",
                confidence=candidate.confidence,
                observed_at=observed_at,
            )
        )
    return stored
