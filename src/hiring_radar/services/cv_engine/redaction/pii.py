from __future__ import annotations

import re
from collections.abc import Iterable

from hiring_radar.services.cv_engine.config import RedactionConfig
from hiring_radar.services.cv_engine.models import ParsedCvData
from hiring_radar.services.cv_engine.redaction.models import PiiFinding, PiiType

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(
    r"(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}"
)
_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_ADDRESS_HINT_RE = re.compile(
    r"(?:\b(?:street|st\.|avenue|ave\.|road|rd\.|boulevard|blvd\.|"
    r"sokak|sk\.|cadde|caddesi|cd\.|mahallesi|mah\.|strasse|straße|weg|platz)\b)",
    re.IGNORECASE,
)
_PROFILE_HOST_RE = re.compile(
    r"(?:linkedin\.com/in/|github\.com/|stackoverflow\.com/users/)",
    re.IGNORECASE,
)


def detect_pii_findings(
    text: str,
    *,
    parsed_data: ParsedCvData | None = None,
    config: RedactionConfig | None = None,
) -> list[PiiFinding]:
    """Detect redactable PII fragments in CV text."""
    runtime_config = config or RedactionConfig()
    findings: list[PiiFinding] = []

    if runtime_config.redact_full_name and parsed_data and parsed_data.full_name:
        findings.extend(
            _find_literal_phrase(
                text,
                parsed_data.full_name,
                pii_type=PiiType.FULL_NAME,
                replacement_text="[REDACTED_NAME]",
                confidence=0.98,
                reason_codes=["parsed_full_name"],
                minimum_length=runtime_config.minimum_name_length,
            )
        )

    if runtime_config.redact_emails:
        findings.extend(
            _find_pattern_matches(
                text,
                _EMAIL_RE,
                pii_type=PiiType.EMAIL,
                replacement_factory=lambda _: "[REDACTED_EMAIL]",
                confidence=0.99,
                reason_codes=["regex_email"],
            )
        )

    if runtime_config.redact_phone_numbers:
        findings.extend(
            _find_pattern_matches(
                text,
                _PHONE_RE,
                pii_type=PiiType.PHONE_NUMBER,
                replacement_factory=lambda _: "[REDACTED_PHONE]",
                confidence=0.92,
                reason_codes=["regex_phone"],
                validator=_looks_like_phone_number,
            )
        )

    if runtime_config.redact_addresses:
        findings.extend(_detect_address_like_lines(text, runtime_config))

    if runtime_config.redact_social_handles:
        findings.extend(_detect_profile_urls(text, runtime_config))
    elif runtime_config.redact_links:
        findings.extend(
            _find_pattern_matches(
                text,
                _URL_RE,
                pii_type=PiiType.URL,
                replacement_factory=lambda _: "[REDACTED_URL]",
                confidence=0.85,
                reason_codes=["generic_url"],
            )
        )

    return _deduplicate_findings(findings)


def _find_literal_phrase(
    text: str,
    phrase: str,
    *,
    pii_type: PiiType,
    replacement_text: str,
    confidence: float,
    reason_codes: list[str],
    minimum_length: int,
) -> list[PiiFinding]:
    if len(phrase.strip()) < minimum_length:
        return []
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    return [
        PiiFinding(
            pii_type=pii_type,
            raw_text=match.group(0),
            replacement_text=replacement_text,
            start_offset=match.start(),
            end_offset=match.end(),
            confidence=confidence,
            reason_codes=reason_codes,
        )
        for match in pattern.finditer(text)
    ]


def _find_pattern_matches(
    text: str,
    pattern: re.Pattern[str],
    *,
    pii_type: PiiType,
    replacement_factory,
    confidence: float,
    reason_codes: list[str],
    validator=None,
) -> list[PiiFinding]:
    findings: list[PiiFinding] = []
    for match in pattern.finditer(text):
        raw_text = match.group(0)
        if validator is not None and not validator(raw_text):
            continue
        findings.append(
            PiiFinding(
                pii_type=pii_type,
                raw_text=raw_text,
                replacement_text=replacement_factory(raw_text),
                start_offset=match.start(),
                end_offset=match.end(),
                confidence=confidence,
                reason_codes=reason_codes,
            )
        )
    return findings


def _detect_address_like_lines(text: str, config: RedactionConfig) -> list[PiiFinding]:
    findings: list[PiiFinding] = []
    line_start = 0
    lines = text.splitlines()
    address_count = 0
    for line in lines:
        line_end = line_start + len(line)
        stripped = line.strip()
        if stripped and _looks_like_address_line(stripped):
            findings.append(
                PiiFinding(
                    pii_type=PiiType.ADDRESS,
                    raw_text=line,
                    replacement_text="[REDACTED_ADDRESS]",
                    start_offset=line_start,
                    end_offset=line_end,
                    confidence=0.83,
                    reason_codes=["address_line"],
                )
            )
            address_count += 1
            if address_count >= config.max_address_lines:
                break
        line_start = line_end + 1
    return findings


def _detect_profile_urls(text: str, config: RedactionConfig) -> list[PiiFinding]:
    findings: list[PiiFinding] = []
    for match in _URL_RE.finditer(text):
        raw_text = match.group(0)
        if not _PROFILE_HOST_RE.search(raw_text):
            continue
        replacement_text = "[REDACTED_PROFILE]"
        if config.preserve_domains:
            replacement_text = _redact_profile_handle(raw_text)
        findings.append(
            PiiFinding(
                pii_type=PiiType.SOCIAL_PROFILE,
                raw_text=raw_text,
                replacement_text=replacement_text,
                start_offset=match.start(),
                end_offset=match.end(),
                confidence=0.95,
                reason_codes=["profile_url"],
            )
        )
    return findings


def _redact_profile_handle(url: str) -> str:
    if "/in/" in url:
        prefix, _, _ = url.partition("/in/")
        return f"{prefix}/in/[REDACTED_PROFILE]"
    if "github.com/" in url:
        prefix, _, _ = url.partition("github.com/")
        return f"{prefix}github.com/[REDACTED_PROFILE]"
    if "stackoverflow.com/users/" in url:
        prefix, _, _ = url.partition("stackoverflow.com/users/")
        return f"{prefix}stackoverflow.com/users/[REDACTED_PROFILE]"
    return "[REDACTED_PROFILE]"


def _looks_like_phone_number(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 7 <= len(digits) <= 16


def _looks_like_address_line(value: str) -> bool:
    has_hint = bool(_ADDRESS_HINT_RE.search(value))
    has_digit = any(char.isdigit() for char in value)
    has_separator = "," in value or ";" in value
    return has_hint and (has_digit or has_separator)


def _deduplicate_findings(findings: Iterable[PiiFinding]) -> list[PiiFinding]:
    deduped: list[PiiFinding] = []
    seen: set[tuple[PiiType, int, int, str]] = set()
    for item in sorted(findings, key=lambda finding: (finding.start_offset, -finding.end_offset)):
        key = (item.pii_type, item.start_offset, item.end_offset, item.raw_text)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
