from __future__ import annotations

from hiring_radar.services.cv_engine.models import ParsedCvData
from hiring_radar.services.cv_engine.redaction import redact_cv_text
from hiring_radar.services.cv_engine.redaction.models import PiiType


def test_redact_cv_text_masks_name_email_phone_and_profile_handle() -> None:
    text = (
        "Alice Example\n"
        "alice@example.com\n"
        "+49 171 1234567\n"
        "https://linkedin.com/in/alice-example\n"
        "Backend Engineer\n"
    )
    parsed_data = ParsedCvData(full_name="Alice Example")

    result = redact_cv_text(text, parsed_data=parsed_data)

    assert "Alice Example" not in result.redacted_text
    assert "alice@example.com" not in result.redacted_text
    assert "+49 171 1234567" not in result.redacted_text
    assert "linkedin.com/in/[REDACTED_PROFILE]" in result.redacted_text
    assert "Backend Engineer" in result.redacted_text
    assert {finding.pii_type for finding in result.findings} >= {
        PiiType.FULL_NAME,
        PiiType.EMAIL,
        PiiType.PHONE_NUMBER,
        PiiType.SOCIAL_PROFILE,
    }


def test_redact_cv_text_masks_address_like_lines() -> None:
    text = (
        "Alice Example\n"
        "Mustafa Kemal Caddesi No: 14, Ankara\n"
        "alice@example.com\n"
    )
    parsed_data = ParsedCvData(full_name="Alice Example")

    result = redact_cv_text(text, parsed_data=parsed_data)

    assert "Mustafa Kemal Caddesi" not in result.redacted_text
    assert "[REDACTED_ADDRESS]" in result.redacted_text
    assert any(finding.pii_type == PiiType.ADDRESS for finding in result.findings)


def test_redact_cv_text_returns_warning_when_no_pii_found() -> None:
    text = "Experienced backend engineer with Python and distributed systems background."

    result = redact_cv_text(text)

    assert result.redacted_text == text
    assert result.findings == []
    assert result.warnings == ["No redactable PII findings were detected."]
