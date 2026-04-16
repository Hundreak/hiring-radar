from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hiring_radar.services.cv_engine.ats.models import (
    AtsCompatibilityReport,
    AtsLevel,
)
from hiring_radar.services.cv_engine.compliance.audit import build_parse_audit_event
from hiring_radar.services.cv_engine.compliance.policies import DataRetentionPolicy
from hiring_radar.services.cv_engine.compliance.retention import (
    RetentionDisposition,
    evaluate_retention,
)
from hiring_radar.services.cv_engine.enterprise.models import DocumentFingerprints
from hiring_radar.services.cv_engine.redaction.models import RedactionResult


def test_retention_evaluates_active_artifact() -> None:
    now = datetime(2026, 4, 8, tzinfo=UTC)
    decision = evaluate_retention(
        artifact_kind="parsed_output",
        created_at="2026-04-01T00:00:00Z",
        policy=DataRetentionPolicy(parsed_output_days=30),
        now=now,
    )

    assert decision.disposition == RetentionDisposition.KEEP
    assert decision.remaining_days >= 0


def test_retention_evaluates_expired_artifact() -> None:
    now = datetime(2026, 4, 8, tzinfo=UTC)
    created_at = (now - timedelta(days=40)).replace(microsecond=0).isoformat()
    decision = evaluate_retention(
        artifact_kind="cache_entry",
        created_at=created_at,
        policy=DataRetentionPolicy(cache_entry_days=14),
        now=now,
    )

    assert decision.disposition == RetentionDisposition.EXPIRE
    assert decision.reason == "cache_entry_retention_elapsed"


def test_build_parse_audit_event_collects_enterprise_context() -> None:
    audit = build_parse_audit_event(
        event_id="evt-001",
        source_path="uploads/cv/alice.pdf",
        parser_version="cv-engine-v2",
        warning_codes=["ocr_warning"],
        quality_band="medium",
        fingerprints=DocumentFingerprints(
            document_sha256="doc-sha",
            content_sha256="content-sha",
            content_simhash="abc123",
            normalized_character_count=100,
            normalized_token_count=20,
            person_fingerprint="person-sha",
        ),
        ats_report=AtsCompatibilityReport(score=81, level=AtsLevel.HIGH),
        redaction_result=RedactionResult(
            original_text="Alice Example alice@example.com",
            redacted_text="[REDACTED_NAME] [REDACTED_EMAIL]",
        ),
        cache_hit=True,
        version_relation="updated_version",
        metadata={"tenant": "demo"},
    )

    assert audit.document_sha256 == "doc-sha"
    assert audit.content_sha256 == "content-sha"
    assert audit.person_fingerprint == "person-sha"
    assert audit.ats_score == 81
    assert audit.redaction_finding_count == 0
    assert audit.cache_hit is True
    assert audit.version_relation == "updated_version"
    assert audit.metadata["tenant"] == "demo"
