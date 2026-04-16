from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiAuditRecord


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def generate_telemetry_ref() -> str:
    return f"ai_{uuid4().hex}"


def build_response_preview(payload: Any, max_chars: int = 240) -> str:
    if isinstance(payload, BaseModel):
        text = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    elif isinstance(payload, (dict, list, tuple)):
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    else:
        text = str(payload)

    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:max_chars]
    return text[: max_chars - 1] + "…"


def persist_ai_audit_record(
    config: LocalAiRuntimeConfig,
    record: AiAuditRecord,
) -> Path | None:
    if not config.audit_enabled:
        return None

    log_dir = Path(config.audit_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(UTC).date().isoformat()
    target = log_dir / f"{stamp}.jsonl"
    line = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)

    with target.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")

    return target


__all__ = [
    "build_response_preview",
    "generate_telemetry_ref",
    "persist_ai_audit_record",
    "utc_now_iso",
]