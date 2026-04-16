from __future__ import annotations

from hiring_radar.services.cv_engine.config import RedactionConfig
from hiring_radar.services.cv_engine.models import ParsedCvData
from hiring_radar.services.cv_engine.redaction.models import RedactionResult
from hiring_radar.services.cv_engine.redaction.pii import detect_pii_findings
from hiring_radar.services.cv_engine.redaction.rules import (
    apply_redactions,
    build_redaction_map,
)


def redact_cv_text(
    text: str,
    *,
    parsed_data: ParsedCvData | None = None,
    config: RedactionConfig | None = None,
) -> RedactionResult:
    """Create a redacted CV artifact while preserving parseability."""
    runtime_config = config or RedactionConfig()
    findings = detect_pii_findings(text, parsed_data=parsed_data, config=runtime_config)
    redacted_text = apply_redactions(text, findings)
    warnings: list[str] = []
    if not findings:
        warnings.append("No redactable PII findings were detected.")
    if text == redacted_text and findings:
        warnings.append("Redaction findings were produced but text remained unchanged.")
    return RedactionResult(
        original_text=text,
        redacted_text=redacted_text,
        findings=findings,
        redaction_map=build_redaction_map(findings),
        warnings=warnings,
    )
