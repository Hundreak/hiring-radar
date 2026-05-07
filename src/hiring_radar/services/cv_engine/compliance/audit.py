from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from hiring_radar.services.cv_engine.ats.models import AtsCompatibilityReport
from hiring_radar.services.cv_engine.enterprise.models import DocumentFingerprints
from hiring_radar.services.cv_engine.redaction.models import RedactionResult


class ParseAuditEvent(BaseModel):
    """Audit-safe parse event payload for compliance and observability."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    source_path: str
    parser_version: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat()
    )
    document_sha256: str | None = None
    content_sha256: str | None = None
    person_fingerprint: str | None = None
    quality_band: str | None = None
    ats_score: int | None = None
    redaction_finding_count: int = 0
    cache_hit: bool = False
    version_relation: str | None = None
    warning_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_parse_audit_event(
    *,
    event_id: str,
    source_path: str,
    parser_version: str,
    warning_codes: list[str] | None = None,
    quality_band: str | None = None,
    fingerprints: DocumentFingerprints | None = None,
    ats_report: AtsCompatibilityReport | None = None,
    redaction_result: RedactionResult | None = None,
    cache_hit: bool = False,
    version_relation: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ParseAuditEvent:
    """Build a normalized audit payload for one parse execution."""
    return ParseAuditEvent(
        event_id=event_id,
        source_path=source_path,
        parser_version=parser_version,
        document_sha256=fingerprints.document_sha256 if fingerprints else None,
        content_sha256=fingerprints.content_sha256 if fingerprints else None,
        person_fingerprint=fingerprints.person_fingerprint if fingerprints else None,
        quality_band=quality_band,
        ats_score=ats_report.score if ats_report is not None else None,
        redaction_finding_count=(
            len(redaction_result.findings) if redaction_result is not None else 0
        ),
        cache_hit=cache_hit,
        version_relation=version_relation,
        warning_codes=list(warning_codes or []),
        metadata=dict(metadata or {}),
    )


def build_parse_run_metadata_json(
    *,
    parser_version: str | None,
    source_upload_id: int | None,
    source_filename: str | None,
    source_parse_status: str | None,
    generated_at: str | None,
    enterprise_metadata: Mapping[str, Any] | None = None,
    ocr_quality: Mapping[str, Any] | None = None,
) -> str:
    """Serialize durable metadata for one persisted parse run."""
    payload = {
        "schema_version": 1,
        "parse": {
            "parser_version": parser_version,
            "source_upload_id": source_upload_id,
            "source_filename": source_filename,
            "source_parse_status": source_parse_status,
            "generated_at": generated_at,
        },
        "enterprise": dict(enterprise_metadata or {}),
        "ocr_quality": dict(ocr_quality or {}),
    }
    return _dump_metadata(payload)


def extract_enterprise_metadata_from_parse_run_metadata_json(
    metadata_json: str | None,
) -> dict[str, Any] | None:
    """Extract stored enterprise metadata from a parse-run metadata blob."""
    payload = _load_metadata_json(metadata_json)
    enterprise = payload.get("enterprise")
    if not isinstance(enterprise, Mapping):
        return None
    return dict(enterprise)


def extract_ocr_quality_from_parse_run_metadata_json(
    metadata_json: str | None,
) -> dict[str, Any] | None:
    """Extract stored OCR quality from a parse-run metadata blob."""
    payload = _load_metadata_json(metadata_json)
    ocr_quality = payload.get("ocr_quality")
    if not isinstance(ocr_quality, Mapping):
        return None
    return dict(ocr_quality)


def build_apply_audit_metadata_json(
    *,
    parse_run_metadata_json: str | None,
    operator_context: Mapping[str, Any] | None,
    selected_operation_count: int,
    applied_change_count: int,
    resulting_apply_status: str,
    remaining_actionable_change_count: int,
) -> str:
    """Serialize enterprise-aware metadata for one apply audit row."""
    parse_payload = _load_metadata_json(parse_run_metadata_json)
    enterprise = parse_payload.get("enterprise")
    parse_info = parse_payload.get("parse")
    payload = {
        "schema_version": 1,
        "parse": dict(parse_info) if isinstance(parse_info, Mapping) else {},
        "enterprise": dict(enterprise) if isinstance(enterprise, Mapping) else {},
        "operator_context": (
            dict(operator_context) if isinstance(operator_context, Mapping) else {}
        ),
        "apply_summary": {
            "selected_operation_count": selected_operation_count,
            "applied_change_count": applied_change_count,
            "resulting_apply_status": resulting_apply_status,
            "remaining_actionable_change_count": (
                remaining_actionable_change_count
            ),
        },
    }
    return _dump_metadata(payload)


def _load_metadata_json(metadata_json: str | None) -> dict[str, Any]:
    if metadata_json is None or not metadata_json.strip():
        return {}
    try:
        payload = json.loads(metadata_json)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _dump_metadata(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
