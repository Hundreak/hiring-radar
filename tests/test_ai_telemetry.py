from __future__ import annotations

import json
from pathlib import Path

from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiAuditRecord
from hiring_radar.services.ai.telemetry import (
    build_response_preview,
    generate_telemetry_ref,
    persist_ai_audit_record,
)


def test_generate_telemetry_ref_has_expected_prefix() -> None:
    value = generate_telemetry_ref()
    assert value.startswith("ai_")
    assert len(value) > 6


def test_build_response_preview_truncates() -> None:
    preview = build_response_preview({"value": "x" * 300}, max_chars=32)
    assert preview is not None
    assert preview.endswith("…")
    assert len(preview) == 32


def test_persist_ai_audit_record_writes_jsonl(tmp_path: Path) -> None:
    config = LocalAiRuntimeConfig(
        enabled=True,
        audit_enabled=True,
        audit_log_dir=str(tmp_path / "audit"),
        default_model="llama3.1:8b",
    )
    record = AiAuditRecord(
        telemetry_ref="ai_testref",
        task_name="headline_summary",
        endpoint_name="/api/user/ai/profile/headline-summary",
        runtime="ollama",
        model="llama3.1:8b",
        locale="tr",
        subscriber_id=7,
        success=True,
        response_valid=True,
        warning_count=0,
        duration_ms=21,
        started_at="2026-04-12T12:00:00Z",
        completed_at="2026-04-12T12:00:01Z",
        response_preview='{"headline_options":[]}',
    )
    path = persist_ai_audit_record(config, record)
    payload = json.loads(Path(path).read_text(encoding="utf-8").strip())
    assert payload["telemetry_ref"] == "ai_testref"
    assert payload["task_name"] == "headline_summary"
