from __future__ import annotations

from collections import defaultdict

from hiring_radar.services.cv_engine.redaction.models import PiiFinding


def apply_redactions(text: str, findings: list[PiiFinding]) -> str:
    """Apply non-overlapping findings from right to left."""
    ordered = sorted(findings, key=lambda item: (item.start_offset, item.end_offset))
    non_overlapping: list[PiiFinding] = []
    last_end = -1
    for item in ordered:
        if item.start_offset < last_end:
            continue
        non_overlapping.append(item)
        last_end = item.end_offset

    redacted = text
    for item in reversed(non_overlapping):
        redacted = (
            redacted[: item.start_offset]
            + item.replacement_text
            + redacted[item.end_offset :]
        )
    return redacted


def build_redaction_map(findings: list[PiiFinding]) -> dict[str, list[str]]:
    """Group original redacted values by PII type name."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in findings:
        key = item.pii_type.value
        if item.raw_text not in grouped[key]:
            grouped[key].append(item.raw_text)
    return dict(grouped)
