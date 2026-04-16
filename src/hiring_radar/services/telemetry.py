from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import uuid

from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiAuditRecord


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def generate_telemetry_ref() -> str:
    return f"ai_{uuid.uuid4().hex[:16]}"


def build_response_preview(payload: object, *, max_chars: int) -> str | None:
    if max_chars <= 0:
        return None
    try:
        if hasattr(payload, "model_dump"):
            serialized = json.dumps(payload.model_dump(), ensure_ascii=False, sort_keys=True)
        elif isinstance(payload, dict):
            serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        else:
            serialized = str(payload)
    except Exception:
        return None
    serialized = serialized.strip()
    if not serialized:
        return None
    if len(serialized) <= max_chars:
        return serialized
    return f"{serialized[: max_chars - 1]}…"


def persist_ai_audit_record(config: LocalAiRuntimeConfig, record: AiAuditRecord) -> str:
    if not config.audit_enabled:
        return "disabled"
    base_dir = Path(config.audit_log_dir)
    if not base_dir.is_absolute():
        base_dir = Path.cwd() / base_dir
    base_dir.mkdir(parents=True, exist_ok=True)
    day = record.completed_at[:10]
    target = base_dir / f"{day}.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.model_dump(), ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return str(target)
