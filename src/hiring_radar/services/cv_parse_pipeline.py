from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from hiring_radar.models import SubscriberCvUpload
from hiring_radar.services.cv_engine.adapters.to_legacy_parse_snapshot import (
    parse_result_to_legacy_snapshot,
)
from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.legacy_runtime import (
    build_foundation_parser_result_from_text,
)
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_PARSED,
    cv_extraction_uses_ocr,
    infer_cv_extraction_method,
    normalize_extracted_text,
)
from hiring_radar.services.cv_profile_draft import (
    CvDraftEducationEntry,
    CvDraftExperienceEntry,
    CvDraftLanguageEntry,
    CvProfileDraft,
    CvProfileDraftSnapshot,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)
from hiring_radar.services.cv_profile_parser import (
    HEURISTIC_CV_PARSER_VERSION,
    parse_cv_text_to_profile_draft,
)


def build_cv_profile_draft_snapshot_from_cv_upload(
    cv_upload: SubscriberCvUpload,
) -> CvProfileDraftSnapshot:
    """Build a normalized draft snapshot from a persisted CV upload.

    The function now attempts to run the v2 foundation parser bridge first and
    converts the result back into the current legacy snapshot contract. If the
    bridge fails for any reason, the legacy heuristic parser remains the safety
    fallback so existing user flows are preserved.

    Args:
        cv_upload: Finalized CV upload record.

    Returns:
        A normalized snapshot. Failed or empty uploads yield an empty draft while
        preserving metadata about the source upload.
    """
    extracted_text = normalize_extracted_text(cv_upload.extracted_text)
    generated_at = cv_upload.parsed_at or cv_upload.uploaded_at

    if cv_upload.parse_status == CV_PARSE_STATUS_PARSED and extracted_text is not None:
        snapshot = _build_v2_legacy_compatible_snapshot(
            cv_upload=cv_upload,
            extracted_text=extracted_text,
            generated_at=generated_at,
        )
        if snapshot is not None:
            return snapshot

        draft = parse_cv_text_to_profile_draft(extracted_text)
        return build_cv_profile_draft_snapshot(
            source_upload_id=cv_upload.id,
            source_filename=cv_upload.original_filename,
            source_parse_status=cv_upload.parse_status,
            parser_version=HEURISTIC_CV_PARSER_VERSION,
            generated_at=generated_at,
            draft=draft,
        )

    return build_cv_profile_draft_snapshot(
        source_upload_id=cv_upload.id,
        source_filename=cv_upload.original_filename,
        source_parse_status=cv_upload.parse_status,
        parser_version=None,
        generated_at=generated_at,
        draft=CvProfileDraft(),
    )


def _build_v2_legacy_compatible_snapshot(
    *,
    cv_upload: SubscriberCvUpload,
    extracted_text: str,
    generated_at: str,
) -> CvProfileDraftSnapshot | None:
    """Run the v2 foundation bridge and map it to the legacy snapshot shape."""
    try:
        result = build_foundation_parser_result_from_text(
            extracted_text=extracted_text,
            filename=cv_upload.original_filename,
            used_ocr=cv_extraction_uses_ocr(
                cv_upload.original_filename,
                cv_upload.content_type,
            ),
            extraction_method=infer_cv_extraction_method(
                cv_upload.original_filename,
                cv_upload.content_type,
            ),
            page_count=1,
            config=ParserRuntimeConfig(),
        )
    except Exception:
        return None

    return parse_result_to_legacy_snapshot(
        result,
        source_upload_id=cv_upload.id,
        source_parse_status=cv_upload.parse_status,
        source_filename=cv_upload.original_filename,
        generated_at=generated_at,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
    )


def cv_profile_draft_snapshot_to_dict(
    snapshot: CvProfileDraftSnapshot,
) -> dict[str, Any]:
    """Convert a draft snapshot into a JSON-ready dictionary.

    Args:
        snapshot: Snapshot object to serialize.

    Returns:
        A dictionary composed only of JSON-safe values.
    """
    return {
        "generated_at": snapshot.generated_at,
        "source_upload_id": snapshot.source_upload_id,
        "source_filename": snapshot.source_filename,
        "source_parse_status": snapshot.source_parse_status,
        "parser_version": snapshot.parser_version,
        "draft": _cv_profile_draft_to_dict(snapshot.draft),
    }


def cv_profile_draft_snapshot_to_json(snapshot: CvProfileDraftSnapshot) -> str:
    """Serialize a draft snapshot to a deterministic JSON string.

    Args:
        snapshot: Snapshot object to serialize.

    Returns:
        A UTF-8 safe JSON string with stable key ordering.
    """
    return json.dumps(
        cv_profile_draft_snapshot_to_dict(snapshot),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def cv_profile_draft_snapshot_from_json(snapshot_json: str) -> CvProfileDraftSnapshot:
    """Deserialize a persisted snapshot JSON string.

    Args:
        snapshot_json: Serialized snapshot JSON.

    Returns:
        A validated CV profile draft snapshot.

    Raises:
        ValueError: If the payload is malformed.
    """
    try:
        payload = json.loads(snapshot_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid CV profile draft snapshot JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid CV profile draft snapshot payload.")

    return cv_profile_draft_snapshot_from_dict(payload)


def cv_profile_draft_snapshot_from_dict(
    payload: Mapping[str, Any],
) -> CvProfileDraftSnapshot:
    """Deserialize a snapshot dictionary into a typed snapshot.

    Args:
        payload: JSON-compatible snapshot payload.

    Returns:
        A validated CV profile draft snapshot.

    Raises:
        ValueError: If the payload is malformed.
    """
    generated_at = _require_string(payload.get("generated_at"), "generated_at")
    draft_payload = payload.get("draft")
    if not isinstance(draft_payload, Mapping):
        raise ValueError("Invalid CV profile draft payload.")

    draft = _cv_profile_draft_from_dict(draft_payload)

    return build_cv_profile_draft_snapshot(
        source_upload_id=_optional_int(payload.get("source_upload_id")),
        source_filename=_optional_string(payload.get("source_filename")),
        source_parse_status=_optional_string(payload.get("source_parse_status")),
        parser_version=_optional_string(payload.get("parser_version")),
        generated_at=generated_at,
        draft=draft,
    )


def _cv_profile_draft_to_dict(draft: CvProfileDraft) -> dict[str, Any]:
    """Serialize a profile draft to a JSON-ready dictionary.

    Args:
        draft: Draft object to serialize.

    Returns:
        A dictionary representation of the draft.
    """
    return {
        "full_name": draft.full_name,
        "email": draft.email,
        "phone": draft.phone,
        "linkedin_url": draft.linkedin_url,
        "github_url": draft.github_url,
        "headline": draft.headline,
        "summary": draft.summary,
        "skills": list(draft.skills),
        "target_roles": list(draft.target_roles),
        "preferred_locations": list(draft.preferred_locations),
        "remote_preference": draft.remote_preference,
        "education_entries": [
            _cv_draft_education_entry_to_dict(item) for item in draft.education_entries
        ],
        "experience_entries": [
            _cv_draft_experience_entry_to_dict(item)
            for item in draft.experience_entries
        ],
        "language_entries": [
            _cv_draft_language_entry_to_dict(item) for item in draft.language_entries
        ],
    }


def _cv_profile_draft_from_dict(payload: Mapping[str, Any]) -> CvProfileDraft:
    """Deserialize a profile draft dictionary into a typed draft.

    Args:
        payload: JSON-compatible draft payload.

    Returns:
        A validated draft object.

    Raises:
        ValueError: If the draft payload is malformed.
    """
    education_entries = _education_entries_from_payload(
        payload.get("education_entries", [])
    )
    experience_entries = _experience_entries_from_payload(
        payload.get("experience_entries", [])
    )
    language_entries = _language_entries_from_payload(
        payload.get("language_entries", [])
    )

    return build_cv_profile_draft(
        full_name=_optional_string(payload.get("full_name")),
        email=_optional_string(payload.get("email")),
        phone=_optional_string(payload.get("phone")),
        linkedin_url=_optional_string(payload.get("linkedin_url")),
        github_url=_optional_string(payload.get("github_url")),
        headline=_optional_string(payload.get("headline")),
        summary=_optional_string(payload.get("summary")),
        skills=_string_list(payload.get("skills", []), "skills"),
        target_roles=_string_list(payload.get("target_roles", []), "target_roles"),
        preferred_locations=_string_list(
            payload.get("preferred_locations", []),
            "preferred_locations",
        ),
        remote_preference=_optional_string(payload.get("remote_preference")),
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=language_entries,
    )


def _education_entries_from_payload(
    payload: Any,
) -> list[CvDraftEducationEntry]:
    """Deserialize education entry payloads.

    Args:
        payload: Raw education payload.

    Returns:
        Validated education entries.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError("Invalid education_entries payload.")

    entries: list[CvDraftEducationEntry] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid education entry payload.")

        entry = build_cv_draft_education_entry(
            school_name=_require_string(item.get("school_name"), "school_name"),
            degree_name=_optional_string(item.get("degree_name")),
            field_of_study=_optional_string(item.get("field_of_study")),
            start_year=_optional_int(item.get("start_year")),
            end_year=_optional_int(item.get("end_year")),
        )
        if entry is None:
            raise ValueError("Invalid education entry payload.")
        entries.append(entry)

    return entries


def _experience_entries_from_payload(
    payload: Any,
) -> list[CvDraftExperienceEntry]:
    """Deserialize experience entry payloads.

    Args:
        payload: Raw experience payload.

    Returns:
        Validated experience entries.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError("Invalid experience_entries payload.")

    entries: list[CvDraftExperienceEntry] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid experience entry payload.")

        entry = build_cv_draft_experience_entry(
            title=_require_string(item.get("title"), "title"),
            company_name=_optional_string(item.get("company_name")),
            start_year=_optional_int(item.get("start_year")),
            end_year=_optional_int(item.get("end_year")),
            summary=_optional_string(item.get("summary")),
        )
        if entry is None:
            raise ValueError("Invalid experience entry payload.")
        entries.append(entry)

    return entries


def _language_entries_from_payload(
    payload: Any,
) -> list[CvDraftLanguageEntry]:
    """Deserialize language entry payloads.

    Args:
        payload: Raw language payload.

    Returns:
        Validated language entries.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError("Invalid language_entries payload.")

    entries: list[CvDraftLanguageEntry] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid language entry payload.")

        entry = build_cv_draft_language_entry(
            language_name=_require_string(item.get("language_name"), "language_name"),
            proficiency_level=_optional_string(item.get("proficiency_level")),
            notes=_optional_string(item.get("notes")),
        )
        if entry is None:
            raise ValueError("Invalid language entry payload.")
        entries.append(entry)

    return entries


def _cv_draft_education_entry_to_dict(
    entry: CvDraftEducationEntry,
) -> dict[str, Any]:
    """Serialize an education draft entry.

    Args:
        entry: Education entry to serialize.

    Returns:
        A dictionary representation of the education entry.
    """
    return {
        "school_name": entry.school_name,
        "degree_name": entry.degree_name,
        "field_of_study": entry.field_of_study,
        "start_year": entry.start_year,
        "end_year": entry.end_year,
    }


def _cv_draft_experience_entry_to_dict(
    entry: CvDraftExperienceEntry,
) -> dict[str, Any]:
    """Serialize an experience draft entry.

    Args:
        entry: Experience entry to serialize.

    Returns:
        A dictionary representation of the experience entry.
    """
    return {
        "title": entry.title,
        "company_name": entry.company_name,
        "start_year": entry.start_year,
        "end_year": entry.end_year,
        "summary": entry.summary,
    }


def _cv_draft_language_entry_to_dict(
    entry: CvDraftLanguageEntry,
) -> dict[str, Any]:
    """Serialize a language draft entry.

    Args:
        entry: Language entry to serialize.

    Returns:
        A dictionary representation of the language entry.
    """
    return {
        "language_name": entry.language_name,
        "proficiency_level": entry.proficiency_level,
        "notes": entry.notes,
    }


def _string_list(payload: Any, field_name: str) -> list[str]:
    """Validate a list of strings.

    Args:
        payload: Raw payload.
        field_name: Logical field name for error messages.

    Returns:
        A validated string list.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError(f"Invalid {field_name} payload.")

    values: list[str] = []
    for item in payload:
        if not isinstance(item, str):
            raise ValueError(f"Invalid {field_name} payload.")
        values.append(item)

    return values


def _require_string(value: Any, field_name: str) -> str:
    """Validate a required string field.

    Args:
        value: Raw field value.
        field_name: Logical field name.

    Returns:
        A validated string value.

    Raises:
        ValueError: If the field is missing or invalid.
    """
    if not isinstance(value, str):
        raise ValueError(f"Invalid {field_name} payload.")
    return value


def _optional_string(value: Any) -> str | None:
    """Validate an optional string field.

    Args:
        value: Raw field value.

    Returns:
        A string or None.

    Raises:
        ValueError: If the value type is invalid.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Invalid optional string payload.")
    return value


def _optional_int(value: Any) -> int | None:
    """Validate an optional integer field.

    Args:
        value: Raw field value.

    Returns:
        An integer or None.

    Raises:
        ValueError: If the value type is invalid.
    """
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError("Invalid optional integer payload.")
    return value