from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from pathlib import Path

from hiring_radar.services.cv_engine.enterprise.models import DocumentFingerprints

_NON_WORD_RE = re.compile(r"[^\w\s+#./-]+", re.UNICODE)
_PHONE_DIGIT_RE = re.compile(r"\d+")
_TOKEN_RE = re.compile(
    r"[a-zA-Z0-9ğüşöçıİĞÜŞÖÇäöüÄÖÜß+#./-]+",
    re.UNICODE,
)
_WHITESPACE_RE = re.compile(r"\s+")


def compute_document_sha256(content: bytes | bytearray | memoryview) -> str:
    """Return a hexadecimal SHA-256 digest for raw document bytes."""
    digest = hashlib.sha256()
    digest.update(bytes(content))
    return digest.hexdigest()


def compute_document_sha256_from_path(path: str | Path) -> str:
    """Return a SHA-256 digest for a file on disk."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text_for_content_fingerprint(text: str) -> str:
    """Normalize extracted CV text for stable semantic fingerprinting."""
    lowered = text.casefold().replace("\r\n", "\n").replace("\r", "\n")
    stripped_lines: list[str] = []
    for line in lowered.split("\n"):
        compact = _WHITESPACE_RE.sub(" ", line).strip()
        if not compact:
            continue
        cleaned = _NON_WORD_RE.sub(" ", compact)
        cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
        if cleaned:
            stripped_lines.append(cleaned)
    return "\n".join(stripped_lines)


def compute_content_sha256(normalized_text: str) -> str:
    """Return a SHA-256 digest for normalized text."""
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def tokenize_for_simhash(normalized_text: str) -> list[str]:
    """Tokenize normalized text into stable lowercase units."""
    return _TOKEN_RE.findall(normalized_text)


def compute_simhash(tokens: Iterable[str], *, bit_count: int = 64) -> str:
    """Compute a deterministic SimHash for a token stream."""
    weights = [0] * bit_count
    for token in tokens:
        token_digest = hashlib.sha256(token.encode("utf-8")).digest()
        token_int = int.from_bytes(token_digest, byteorder="big", signed=False)
        for bit_index in range(bit_count):
            mask = 1 << bit_index
            if token_int & mask:
                weights[bit_index] += 1
            else:
                weights[bit_index] -= 1
    fingerprint = 0
    for bit_index, weight in enumerate(weights):
        if weight >= 0:
            fingerprint |= 1 << bit_index
    hex_length = bit_count // 4
    return f"{fingerprint:0{hex_length}x}"


def compute_person_fingerprint(
    *,
    full_name: str | None,
    email: str | None,
    phone: str | None,
) -> str | None:
    """Build a stable person fingerprint from weak identity signals."""
    normalized_parts: list[str] = []
    normalized_name = _normalize_name(full_name)
    normalized_email = _normalize_email(email)
    normalized_phone = _normalize_phone(phone)
    if normalized_name:
        normalized_parts.append(f"name:{normalized_name}")
    if normalized_email:
        normalized_parts.append(f"email:{normalized_email}")
    if normalized_phone:
        normalized_parts.append(f"phone:{normalized_phone}")
    if not normalized_parts:
        return None
    payload = "|".join(normalized_parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_document_fingerprints(
    *,
    text: str,
    raw_bytes: bytes | bytearray | memoryview | None = None,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    simhash_bits: int = 64,
) -> DocumentFingerprints:
    """Build all identity signals required by enterprise parser features."""
    normalized_text = normalize_text_for_content_fingerprint(text)
    tokens = tokenize_for_simhash(normalized_text)
    return DocumentFingerprints(
        document_sha256=(compute_document_sha256(raw_bytes) if raw_bytes is not None else None),
        content_sha256=compute_content_sha256(normalized_text),
        content_simhash=compute_simhash(tokens, bit_count=simhash_bits),
        normalized_character_count=len(normalized_text),
        normalized_token_count=len(tokens),
        person_fingerprint=compute_person_fingerprint(
            full_name=full_name,
            email=email,
            phone=phone,
        ),
        normalized_text_preview=normalized_text[:400] or None,
    )


def _normalize_name(value: str | None) -> str | None:
    if value is None:
        return None
    compact = _WHITESPACE_RE.sub(" ", value.casefold()).strip()
    compact = _NON_WORD_RE.sub(" ", compact)
    compact = _WHITESPACE_RE.sub(" ", compact).strip()
    return compact or None


def _normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(_PHONE_DIGIT_RE.findall(value))
    if len(digits) > 10:
        digits = digits[-10:]
    return digits or None
