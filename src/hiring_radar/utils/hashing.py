from __future__ import annotations

import hashlib


def normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def build_job_fingerprint(
    *,
    company_name: str,
    title: str,
    location: str | None,
    canonical_url: str,
) -> str:
    normalized_parts = [
        normalize_text(company_name).lower(),
        normalize_text(title).lower(),
        normalize_text(location or "").lower(),
        canonical_url.strip().lower(),
    ]
    raw_value = "||".join(normalized_parts)
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()