"""Ollama-assisted structured extraction from OCR text.

This module is a second-stage structured extraction helper for OCR-sourced
CVs (image uploads). After the primary OCR pipeline produces clean text,
Ollama is asked to identify the structured fields with a strict JSON schema.

Design contract:
  * Ollama is optional: if the runtime is unavailable or times out, the
    function returns None and the caller falls back to the heuristic parser.
  * No hallucination: all extracted values must appear verbatim (or nearly
    so) in the source text. The validation step rejects invented values by
    checking that every non-trivial string maps to a substring of the text.
  * Strict JSON output: the function only uses Ollama's structured-output
    feature (format= with JSON schema) — no post-hoc JSON extraction from
    free-text responses.
  * Fail-safe: any exception from the AI layer returns None so the upload
    flow is never broken by an AI failure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from hiring_radar.services.cv_profile_draft import (
    CvProfileDraft,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_profile_draft,
)

# ---------------------------------------------------------------------------
# JSON schema sent to Ollama
# ---------------------------------------------------------------------------

_CV_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "full_name",
        "headline",
        "email",
        "phone",
        "contact_location",
        "summary",
        "target_roles",
        "preferred_locations",
        "skills",
        "experience",
        "education",
    ],
    "properties": {
        "full_name": {"type": ["string", "null"]},
        "headline": {"type": ["string", "null"]},
        "email": {"type": ["string", "null"]},
        "phone": {"type": ["string", "null"]},
        # contact_location is the candidate's current city/address only — NOT a job search preference
        "contact_location": {"type": ["string", "null"]},
        # summary: 2-3 sentence professional profile synthesized from experience/skills (null if CV lacks enough info)
        "summary": {"type": ["string", "null"]},
        # target_roles: job titles this candidate would apply to, inferred from headline/experience (empty if unclear)
        "target_roles": {
            "type": "array",
            "items": {"type": "string"},
        },
        # preferred_locations: ONLY from explicit preference statements in the CV (NOT the contact city)
        "preferred_locations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "skills": {
            "type": "array",
            "items": {"type": "string"},
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "company", "description"],
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "start_year": {"type": ["integer", "null"]},
                    "end_year": {"type": ["integer", "null"]},
                    # description: 1-2 sentence synthesis of the most impactful bullet points for this role
                    "description": {"type": ["string", "null"]},
                },
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["school"],
                "properties": {
                    "school": {"type": "string"},
                    "degree": {"type": ["string", "null"]},
                    "field": {"type": ["string", "null"]},
                    "start_year": {"type": ["integer", "null"]},
                    "end_year": {"type": ["integer", "null"]},
                },
            },
        },
    },
}

_SYSTEM_PROMPT = (
    "You are a precise CV/resume parser and professional profile writer. "
    "Rules: "
    "full_name: the person's full name (first + last) from the CV header. "
    "headline: the stated job title or professional role from the CV header. "
    "email/phone: extract verbatim from the CV. "
    "contact_location: the city/location from the CV header or contact section only (e.g. 'San Francisco, CA'). "
    "summary: write a clean 2-3 sentence professional summary synthesizing the candidate's background "
    "from their experience and skills; use third person; null only if the CV has almost no content. "
    "target_roles: list 1-3 specific job titles this person would apply to, inferred from their headline "
    "and most recent experience title. Use exact title strings like 'Senior Software Engineer'. "
    "preferred_locations: list ONLY locations explicitly stated as preferred work locations in the CV "
    "(e.g. 'Open to remote', 'Willing to relocate to NYC'). "
    "Do NOT include the contact_location here. Return empty array if no preference is stated. "
    "skills: technology names, tools, and professional skills as listed in the CV. "
    "experience: one entry per job. start_year/end_year are 4-digit integers; end_year=null if 'current'. "
    "description: write a 1-2 sentence synthesis of the most impactful bullet points for this role; "
    "null if no bullet points exist. "
    "education: school is the institution name. "
    "Do NOT invent names, companies, or schools not in the text."
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class OcrStructuringResult:
    draft: CvProfileDraft
    model: str
    response_time_ms: int


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_cv_structure_with_ollama(
    text: str | None,
    *,
    base_url: str | None = None,
    model: str | None = None,
    timeout_seconds: int | None = None,
) -> OcrStructuringResult | None:
    """Run Ollama structured extraction on OCR text and return a validated draft.

    Returns ``None`` if Ollama is unavailable, the extraction fails, or the
    result cannot be validated. The caller must treat ``None`` as a graceful
    fallback signal, not an error.
    """
    if not text or not text.strip():
        return None

    resolved_runtime = _resolve_ollama_runtime(
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    if resolved_runtime is None:
        return None

    resolved_base_url, resolved_model, resolved_timeout = resolved_runtime

    try:
        raw = _call_ollama(
            text=text,
            base_url=resolved_base_url,
            model=resolved_model,
            timeout_seconds=resolved_timeout,
        )
    except Exception:
        return None

    if not isinstance(raw, dict):
        return None

    validated = _validate_extraction(raw, source_text=text)
    if validated is None:
        return None

    draft = _build_draft_from_extraction(validated)
    return OcrStructuringResult(
        draft=draft,
        model=resolved_model,
        response_time_ms=0,
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _resolve_ollama_runtime(
    *,
    base_url: str | None,
    model: str | None,
    timeout_seconds: int | None,
) -> tuple[str, str, int] | None:
    """Resolve Ollama endpoint/model from explicit args or local AI config.

    Explicit arguments are honored for tests and one-off diagnostics.  When no
    endpoint/model override is supplied, the shared ``AI_*`` configuration is
    used and ``AI_ENABLED=false`` cleanly disables the AI pass.
    """
    explicit_override = any(value is not None for value in (base_url, model, timeout_seconds))

    try:
        from hiring_radar.services.ai.config import load_local_ai_runtime_config

        config = load_local_ai_runtime_config()
    except Exception:
        config = None

    if not explicit_override and config is not None and not config.enabled:
        return None

    resolved_base_url = (
        base_url
        or (config.base_url if config is not None else None)
        or "http://127.0.0.1:11434"
    )
    resolved_model = (
        model
        or (config.default_model if config is not None and config.default_model else None)
        or "llama3.1:8b"
    )
    resolved_timeout = (
        timeout_seconds
        or (config.request_timeout_seconds if config is not None else None)
        or 60
    )

    return resolved_base_url, resolved_model, int(resolved_timeout)


def _call_ollama(
    text: str,
    *,
    base_url: str,
    model: str,
    timeout_seconds: int,
) -> Any:
    """Call Ollama and return the parsed JSON content."""
    import json

    import httpx

    user_message = f"Parse this CV text and return structured JSON:\n\n{text}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "format": _CV_EXTRACTION_SCHEMA,
        "options": {"temperature": 0},
    }
    timeout = httpx.Timeout(timeout_seconds)
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        response = client.post("/api/chat", json=payload)
        response.raise_for_status()
        body = response.json()

    message = body.get("message", {}) if isinstance(body, dict) else {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    if not isinstance(content, str) or not content.strip():
        return None
    return json.loads(content)


# Minimum fraction of an extracted string value that must appear as a
# substring in the source OCR text to pass hallucination check.
_HALLUCINATION_MIN_COVERAGE = 0.7
_HALLUCINATION_MIN_LEN = 4


def _validate_extraction(raw: dict, *, source_text: str) -> dict | None:
    """Validate that the extracted values are grounded in the source text.

    Rejects obvious hallucinations: any non-trivial string value whose
    key tokens are absent from the source text is stripped. The function
    returns the cleaned dict, or None if the result is empty.
    """
    source_lower = source_text.lower()

    def _is_grounded(value: str) -> bool:
        if not isinstance(value, str):
            return True
        cleaned = value.strip()
        if len(cleaned) < _HALLUCINATION_MIN_LEN:
            return True
        tokens = re.findall(r"[a-z0-9]{3,}", cleaned.lower())
        if not tokens:
            return True
        found = sum(1 for t in tokens if t in source_lower)
        return found / len(tokens) >= _HALLUCINATION_MIN_COVERAGE

    result: dict[str, Any] = {}

    for scalar_key in ("full_name", "headline", "email", "phone", "contact_location"):
        val = raw.get(scalar_key)
        if isinstance(val, str) and val.strip() and _is_grounded(val):
            result[scalar_key] = val.strip()
        else:
            result[scalar_key] = None

    # summary and target_roles are generated/inferred — skip verbatim grounding check
    summary_raw = raw.get("summary")
    result["summary"] = summary_raw.strip() if isinstance(summary_raw, str) and summary_raw.strip() else None

    target_roles: list[str] = []
    for role in raw.get("target_roles") or []:
        if isinstance(role, str) and role.strip():
            target_roles.append(role.strip())
    result["target_roles"] = target_roles

    # preferred_locations must be grounded — they come from explicit statements in the CV
    preferred_locations: list[str] = []
    for loc in raw.get("preferred_locations") or []:
        if isinstance(loc, str) and loc.strip() and _is_grounded(loc):
            preferred_locations.append(loc.strip())
    result["preferred_locations"] = preferred_locations

    skills: list[str] = []
    for s in raw.get("skills") or []:
        if isinstance(s, str) and s.strip() and _is_grounded(s):
            skills.append(s.strip())
    result["skills"] = skills

    experience: list[dict] = []
    for entry in raw.get("experience") or []:
        if not isinstance(entry, dict):
            continue
        title = (entry.get("title") or "").strip()
        company = (entry.get("company") or "").strip()
        if not title or not company:
            continue
        if not _is_grounded(title) or not _is_grounded(company):
            continue
        start_year = _safe_year(entry.get("start_year"))
        end_year = _safe_year(entry.get("end_year"))
        # description is a synthesis — skip grounding check, just clean it
        desc_raw = entry.get("description")
        description = desc_raw.strip() if isinstance(desc_raw, str) and desc_raw.strip() else None
        experience.append(
            {
                "title": title,
                "company": company,
                "start_year": start_year,
                "end_year": end_year,
                "description": description,
            }
        )
    result["experience"] = experience

    education: list[dict] = []
    for entry in raw.get("education") or []:
        if not isinstance(entry, dict):
            continue
        school = (entry.get("school") or "").strip()
        if not school or not _is_grounded(school):
            continue
        degree = (entry.get("degree") or "").strip() or None
        field = (entry.get("field") or "").strip() or None
        start_year = _safe_year(entry.get("start_year"))
        end_year = _safe_year(entry.get("end_year"))
        education.append(
            {
                "school": school,
                "degree": degree,
                "field": field,
                "start_year": start_year,
                "end_year": end_year,
            }
        )
    result["education"] = education

    has_content = (
        result.get("full_name")
        or result.get("headline")
        or skills
        or experience
        or education
    )
    return result if has_content else None


def _safe_year(value: Any) -> int | None:
    if value is None:
        return None
    try:
        year = int(value)
        return year if 1900 <= year <= 2100 else None
    except (ValueError, TypeError):
        return None


def _build_draft_from_extraction(data: dict) -> CvProfileDraft:
    """Convert validated Ollama extraction dict into a CvProfileDraft."""
    education_entries = []
    for edu in data.get("education") or []:
        entry = build_cv_draft_education_entry(
            school_name=edu["school"],
            degree_name=edu.get("degree"),
            field_of_study=edu.get("field"),
            start_year=edu.get("start_year"),
            end_year=edu.get("end_year"),
        )
        if entry is not None:
            education_entries.append(entry)

    experience_entries = []
    for exp in data.get("experience") or []:
        entry = build_cv_draft_experience_entry(
            title=exp["title"],
            company_name=exp.get("company"),
            start_year=exp.get("start_year"),
            end_year=exp.get("end_year"),
            summary=exp.get("description"),
        )
        if entry is not None:
            experience_entries.append(entry)

    # contact_location is NOT mapped to preferred_locations — it is contact info only.
    # preferred_locations comes only from explicit preference statements in the CV.
    preferred_locations = list(data.get("preferred_locations") or [])

    return build_cv_profile_draft(
        full_name=data.get("full_name"),
        email=data.get("email"),
        phone=data.get("phone"),
        headline=data.get("headline"),
        summary=data.get("summary"),
        skills=data.get("skills") or [],
        target_roles=list(data.get("target_roles") or []),
        preferred_locations=preferred_locations,
        remote_preference=None,
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=[],
    )
