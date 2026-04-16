from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


@dataclass(slots=True, frozen=True)
class AiAuditFinalizeResult:
    evaluation_status: str
    evaluation_score: float
    manual_edit_distance: int
    resolved_after_snapshot_json: str


def dumps_snapshot(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def loads_snapshot(payload: str | None) -> Any:
    if payload is None or payload == "":
        return None
    return json.loads(payload)


def normalize_snapshot(value: Any) -> Any:
    if isinstance(value, tuple):
        return [normalize_snapshot(item) for item in value]
    if isinstance(value, list):
        return [normalize_snapshot(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_snapshot(val) for key, val in sorted(value.items())}
    if isinstance(value, str):
        return value.strip()
    return value


def compare_saved_snapshot(ai_after: Any, saved_value: Any) -> AiAuditFinalizeResult:
    normalized_ai = normalize_snapshot(ai_after)
    normalized_saved = normalize_snapshot(saved_value)
    evaluation_status = "accepted" if normalized_ai == normalized_saved else "modified"
    ai_text = dumps_snapshot(normalized_ai)
    saved_text = dumps_snapshot(normalized_saved)
    manual_edit_distance = estimate_manual_edit_distance(ai_text, saved_text)
    evaluation_score = 1.0 if evaluation_status == "accepted" else 0.65
    return AiAuditFinalizeResult(
        evaluation_status=evaluation_status,
        evaluation_score=evaluation_score,
        manual_edit_distance=manual_edit_distance,
        resolved_after_snapshot_json=saved_text,
    )


def estimate_manual_edit_distance(before_text: str, after_text: str) -> int:
    if before_text == after_text:
        return 0
    matcher = SequenceMatcher(a=before_text, b=after_text)
    ratio = matcher.ratio()
    base = max(len(before_text), len(after_text), 1)
    return int(round(base * (1 - ratio)))



def derive_evaluation_score(status: str | None) -> float | None:
    if status is None:
        return None
    normalized = status.strip().lower()
    if normalized == "accepted":
        return 1.0
    if normalized == "modified":
        return 0.65
    if normalized == "rejected":
        return 0.0
    if normalized == "reverted":
        return 0.25
    return None
