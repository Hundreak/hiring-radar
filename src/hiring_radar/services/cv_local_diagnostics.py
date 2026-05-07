from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hiring_radar.models import SubscriberCvUpload, SubscriberProfile
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_FAILED,
    SUPPORTED_CV_EXTRACTION_EXTENSIONS,
    CvExtractionError,
    extract_text_from_cv_file,
    infer_cv_file_format,
    normalize_extracted_text,
)
from hiring_radar.services.cv_ocr_quality import score_ocr_quality
from hiring_radar.services.cv_parse_pipeline import (
    build_cv_profile_draft_snapshot_from_cv_upload,
    cv_profile_draft_snapshot_to_dict,
)
from hiring_radar.services.cv_profile_auto_apply import replace_profile_from_cv_draft
from hiring_radar.services.cv_profile_draft import CvProfileDraftSnapshot


@dataclass(slots=True, frozen=True)
class LocalCvInspectionResult:
    """A deterministic terminal-friendly inspection result for one local CV file."""

    path: str
    filename: str
    supported: bool
    success: bool
    file_format: str
    content_type: str | None
    file_size_bytes: int
    parse_status: str
    extraction_method: str | None = None
    used_ocr: bool = False
    page_count: int = 0
    extracted_character_count: int = 0
    quality: dict[str, Any] | None = None
    snapshot: CvProfileDraftSnapshot | None = None
    profile_after_apply: dict[str, Any] | None = None
    text_preview: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        snapshot_payload = (
            cv_profile_draft_snapshot_to_dict(self.snapshot)
            if self.snapshot is not None
            else None
        )
        draft_payload = (
            snapshot_payload.get("draft")
            if isinstance(snapshot_payload, dict)
            else None
        )

        return {
            "path": self.path,
            "filename": self.filename,
            "supported": self.supported,
            "success": self.success,
            "file_format": self.file_format,
            "content_type": self.content_type,
            "file_size_bytes": self.file_size_bytes,
            "parse_status": self.parse_status,
            "extraction_method": self.extraction_method,
            "used_ocr": self.used_ocr,
            "page_count": self.page_count,
            "extracted_character_count": self.extracted_character_count,
            "quality": self.quality,
            "snapshot": snapshot_payload,
            "profile_after_apply": self.profile_after_apply,
            "text_preview": self.text_preview,
            "error": self.error,
            # Convenience aliases for terminal/debug scripts. Keep the canonical
            # keys above stable, but expose the names that mirror the CLI output.
            "status": self.parse_status,
            "method": self.extraction_method,
            "draft": draft_payload,
        }


def inspect_local_cv_file(
    file_path: str | Path,
    *,
    ai_structuring_mode: str | None = None,
    text_preview_chars: int = 0,
) -> LocalCvInspectionResult:
    """Run extraction + draft parsing + profile-placement simulation for a CV file."""
    path = Path(file_path)
    content_type = mimetypes.guess_type(path.name)[0]
    file_size = path.stat().st_size if path.exists() else 0
    file_format = infer_cv_file_format(path.name, content_type)
    supported = path.suffix.lower() in SUPPORTED_CV_EXTRACTION_EXTENSIONS

    if not supported:
        return LocalCvInspectionResult(
            path=str(path),
            filename=path.name,
            supported=False,
            success=False,
            file_format=file_format,
            content_type=content_type,
            file_size_bytes=file_size,
            parse_status="unsupported",
            error=(
                "Unsupported extension. Supported CV extensions: "
                f"{', '.join(sorted(SUPPORTED_CV_EXTRACTION_EXTENSIONS))}."
            ),
        )

    parsed_at = "1970-01-01T00:00:00Z"
    try:
        extraction = extract_text_from_cv_file(path)
        extracted_text = normalize_extracted_text(extraction.extracted_text)
        quality_report = score_ocr_quality(
            extracted_text,
            extraction_method=extraction.extraction_method,
        )
        upload = SubscriberCvUpload(
            id=0,
            subscriber_id=0,
            original_filename=path.name,
            storage_path=str(path),
            content_type=content_type,
            file_size_bytes=file_size,
            extracted_text=extracted_text,
            parse_status=extraction.parse_status,
            uploaded_at=parsed_at,
            parsed_at=parsed_at,
        )
        snapshot = build_cv_profile_draft_snapshot_from_cv_upload(
            upload,
            ai_structuring_mode=ai_structuring_mode,
        )
        profile_after_apply = _simulate_profile_replacement(snapshot, filename=path.name)
        preview = _build_text_preview(extracted_text, text_preview_chars)
        return LocalCvInspectionResult(
            path=str(path),
            filename=path.name,
            supported=True,
            success=extraction.parse_status == "parsed",
            file_format=file_format,
            content_type=content_type,
            file_size_bytes=file_size,
            parse_status=extraction.parse_status,
            extraction_method=extraction.extraction_method,
            used_ocr=extraction.used_ocr,
            page_count=extraction.page_count,
            extracted_character_count=len(extracted_text or ""),
            quality=quality_report.to_dict(),
            snapshot=snapshot,
            profile_after_apply=profile_after_apply,
            text_preview=preview,
        )
    except CvExtractionError as exc:
        return LocalCvInspectionResult(
            path=str(path),
            filename=path.name,
            supported=True,
            success=False,
            file_format=file_format,
            content_type=content_type,
            file_size_bytes=file_size,
            parse_status=CV_PARSE_STATUS_FAILED,
            error=str(exc),
        )


def inspect_local_cv_directory(
    directory: str | Path,
    *,
    ai_structuring_mode: str | None = None,
    text_preview_chars: int = 0,
    include_unsupported: bool = False,
) -> list[LocalCvInspectionResult]:
    """Inspect local CV files in stable filename order.

    By default, non-CV helper files in the folder (for example previous JSON
    reports) are ignored so repeated diagnostics stay clean.
    """
    root = Path(directory).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"CV directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"CV path is not a directory: {root}")

    results: list[LocalCvInspectionResult] = []
    for path in sorted(item for item in root.iterdir() if item.is_file()):
        if (
            not include_unsupported
            and path.suffix.lower() not in SUPPORTED_CV_EXTRACTION_EXTENSIONS
        ):
            continue
        results.append(
            inspect_local_cv_file(
                path,
                ai_structuring_mode=ai_structuring_mode,
                text_preview_chars=text_preview_chars,
            )
        )
    return results


def _simulate_profile_replacement(
    snapshot: CvProfileDraftSnapshot,
    *,
    filename: str,
) -> dict[str, Any]:
    """Show how the parsed draft lands on an empty subscriber profile."""
    result = replace_profile_from_cv_draft(
        snapshot=snapshot,
        profile=SubscriberProfile(
            subscriber_id=0,
            cv_filename=filename,
            cv_uploaded_at=snapshot.generated_at,
        ),
        education_entries=(),
        experience_entries=(),
        language_entries=(),
        certification_entries=(),
    )
    profile = result.profile
    return {
        "profile": {
            "phone": profile.phone,
            "headline": profile.headline,
            "summary": profile.summary,
            "target_roles": list(profile.target_roles),
            "skills": list(profile.skills),
            "preferred_locations": list(profile.preferred_locations),
            "remote_preference": profile.remote_preference,
            "cv_filename": profile.cv_filename,
            "cv_uploaded_at": profile.cv_uploaded_at,
        },
        "education_entries": [
            {
                "school_name": item.school_name,
                "degree_name": item.degree_name,
                "field_of_study": item.field_of_study,
                "start_year": item.start_year,
                "end_year": item.end_year,
            }
            for item in result.education_entries
        ],
        "experience_entries": [
            {
                "title": item.title,
                "company_name": item.company_name,
                "start_year": item.start_year,
                "end_year": item.end_year,
                "summary": item.summary,
            }
            for item in result.experience_entries
        ],
        "language_entries": [
            {
                "language_name": item.language_name,
                "proficiency_level": item.proficiency_level,
                "notes": item.notes,
            }
            for item in result.language_entries
        ],
        "certification_entries": [
            {
                "certificate_name": item.certificate_name,
                "issuer_name": item.issuer_name,
                "issued_year": item.issued_year,
            }
            for item in result.certification_entries
        ],
        "applied": {
            "scalar_fields": list(result.applied_scalar_fields),
            "list_fields": list(result.applied_list_fields),
            "contact_fields": list(result.applied_contact_fields),
            "added_education_entry_count": result.added_education_entry_count,
            "added_experience_entry_count": result.added_experience_entry_count,
            "added_language_entry_count": result.added_language_entry_count,
            "added_certification_entry_count": (
                result.added_certification_entry_count
            ),
            "total_applied_changes": result.total_applied_changes,
        },
    }


def _build_text_preview(text: str | None, max_chars: int) -> str | None:
    if max_chars <= 0 or not text:
        return None
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[:max_chars].rstrip()}…"
