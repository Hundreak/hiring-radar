from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path

UPLOAD_ROOT_ENV_VAR = "HIRING_RADAR_UPLOAD_DIR"
DEFAULT_UPLOAD_ROOT = "data/uploads"
MAX_CV_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_LANGUAGE_CERTIFICATE_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_AVATAR_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SKILL_EVIDENCE_UPLOAD_BYTES = 5 * 1024 * 1024

CV_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg"}
CV_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
}

LANGUAGE_CERTIFICATE_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
LANGUAGE_CERTIFICATE_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

AVATAR_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
AVATAR_ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}

SKILL_EVIDENCE_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
SKILL_EVIDENCE_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


class InvalidUploadError(ValueError):
    """Raised when an uploaded file fails validation."""


@dataclass(slots=True, frozen=True)
class StoredProfileFile:
    original_filename: str
    storage_path: str
    absolute_path: Path
    file_size_bytes: int


def _sanitize_filename(filename: str) -> str:
    base_name = Path(filename).name.strip()
    if not base_name:
        raise InvalidUploadError("A file name is required.")

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._")
    if not safe_name:
        raise InvalidUploadError("The uploaded file name is invalid.")

    return safe_name


def _resolve_upload_root() -> Path:
    configured_root = os.environ.get(UPLOAD_ROOT_ENV_VAR, DEFAULT_UPLOAD_ROOT).strip()
    if not configured_root:
        configured_root = DEFAULT_UPLOAD_ROOT

    root = Path(configured_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _validate_file(
    *,
    filename: str | None,
    content_type: str | None,
    file_size_bytes: int,
    allowed_extensions: set[str],
    allowed_content_types: set[str],
    max_file_size_bytes: int,
    kind: str,
) -> None:
    if not filename:
        raise InvalidUploadError(f"{kind} file name is required.")

    extension = Path(filename).suffix.lower()
    if extension not in allowed_extensions:
        raise InvalidUploadError(
            f"Unsupported {kind.lower()} file type. Allowed extensions: "
            f"{', '.join(sorted(allowed_extensions))}."
        )

    if content_type and content_type not in allowed_content_types:
        raise InvalidUploadError(
            f"Unsupported {kind.lower()} content type: {content_type}."
        )

    if file_size_bytes <= 0:
        raise InvalidUploadError(f"{kind} file is empty.")

    if file_size_bytes > max_file_size_bytes:
        raise InvalidUploadError(
            f"{kind} file exceeds the size limit of {max_file_size_bytes // (1024 * 1024)} MB."
        )


def validate_cv_upload(
    *,
    filename: str | None,
    content_type: str | None,
    file_size_bytes: int,
) -> None:
    _validate_file(
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        allowed_extensions=CV_ALLOWED_EXTENSIONS,
        allowed_content_types=CV_ALLOWED_CONTENT_TYPES,
        max_file_size_bytes=MAX_CV_UPLOAD_BYTES,
        kind="CV",
    )


def validate_language_certificate_upload(
    *,
    filename: str | None,
    content_type: str | None,
    file_size_bytes: int,
) -> None:
    _validate_file(
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        allowed_extensions=LANGUAGE_CERTIFICATE_ALLOWED_EXTENSIONS,
        allowed_content_types=LANGUAGE_CERTIFICATE_ALLOWED_CONTENT_TYPES,
        max_file_size_bytes=MAX_LANGUAGE_CERTIFICATE_UPLOAD_BYTES,
        kind="Language certificate",
    )


def validate_skill_evidence_upload(
    *,
    filename: str | None,
    content_type: str | None,
    file_size_bytes: int,
) -> None:
    _validate_file(
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        allowed_extensions=SKILL_EVIDENCE_ALLOWED_EXTENSIONS,
        allowed_content_types=SKILL_EVIDENCE_ALLOWED_CONTENT_TYPES,
        max_file_size_bytes=MAX_SKILL_EVIDENCE_UPLOAD_BYTES,
        kind="Skill evidence",
    )


def validate_avatar_upload(
    *,
    filename: str | None,
    content_type: str | None,
    file_size_bytes: int,
) -> None:
    _validate_file(
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        allowed_extensions=AVATAR_ALLOWED_EXTENSIONS,
        allowed_content_types=AVATAR_ALLOWED_CONTENT_TYPES,
        max_file_size_bytes=MAX_AVATAR_UPLOAD_BYTES,
        kind="Avatar",
    )


def resolve_profile_storage_path(storage_path: str) -> Path:
    normalized = storage_path.strip().replace('\\', '/')
    if not normalized:
        raise InvalidUploadError('Stored file path is invalid.')

    relative_path = Path(normalized)
    if relative_path.is_absolute() or '..' in relative_path.parts:
        raise InvalidUploadError('Stored file path is invalid.')

    return (_resolve_upload_root() / relative_path).resolve()


def store_profile_file(
    *,
    subscriber_id: int,
    category: str,
    original_filename: str,
    content: bytes,
) -> StoredProfileFile:
    safe_name = _sanitize_filename(original_filename)
    upload_root = _resolve_upload_root()

    relative_directory = Path(f"subscriber_{subscriber_id}") / category
    absolute_directory = upload_root / relative_directory
    absolute_directory.mkdir(parents=True, exist_ok=True)

    stored_name = f"{secrets.token_hex(8)}_{safe_name}"
    absolute_path = absolute_directory / stored_name
    absolute_path.write_bytes(content)

    return StoredProfileFile(
        original_filename=safe_name,
        storage_path=(relative_directory / stored_name).as_posix(),
        absolute_path=absolute_path,
        file_size_bytes=len(content),
    )
