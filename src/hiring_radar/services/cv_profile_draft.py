from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

MIN_SUPPORTED_YEAR = 1900
MAX_SUPPORTED_YEAR = 2100


@dataclass(slots=True, frozen=True)
class CvDraftEducationEntry:
    school_name: str
    degree_name: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


@dataclass(slots=True, frozen=True)
class CvDraftExperienceEntry:
    title: str
    company_name: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    summary: str | None = None


@dataclass(slots=True, frozen=True)
class CvDraftLanguageEntry:
    language_name: str
    proficiency_level: str | None = None
    notes: str | None = None


@dataclass(slots=True, frozen=True)
class CvDraftCertificationEntry:
    certificate_name: str
    issuer_name: str | None = None
    issued_year: int | None = None


@dataclass(slots=True, frozen=True)
class CvProfileDraft:
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    headline: str | None = None
    summary: str | None = None
    skills: tuple[str, ...] = ()
    target_roles: tuple[str, ...] = ()
    preferred_locations: tuple[str, ...] = ()
    remote_preference: str | None = None
    education_entries: tuple[CvDraftEducationEntry, ...] = ()
    experience_entries: tuple[CvDraftExperienceEntry, ...] = ()
    language_entries: tuple[CvDraftLanguageEntry, ...] = ()
    certification_entries: tuple[CvDraftCertificationEntry, ...] = ()


@dataclass(slots=True, frozen=True)
class CvProfileDraftSnapshot:
    generated_at: str
    source_upload_id: int | None = None
    source_filename: str | None = None
    source_parse_status: str | None = None
    parser_version: str | None = None
    draft: CvProfileDraft = CvProfileDraft()


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _normalize_full_name_string(value: str | None) -> str | None:
    """Normalize display-only name casing while avoiding identity guesses.

    OCR/layout extraction often returns names in all caps. Converting
    ``BULUT KARABULUT`` to ``Bulut Karabulut`` is a presentation cleanup, not
    an identity correction. We intentionally avoid changing mixed-case names,
    initials, dotted abbreviations, and one/two-letter tokens where casing may
    be meaningful.
    """
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None

    if not _looks_like_all_caps_person_name(cleaned):
        return cleaned

    use_turkish_casing = any(ch in cleaned for ch in "ÇĞİÖŞÜ")
    return " ".join(
        _title_case_name_word(word, use_turkish_casing=use_turkish_casing)
        for word in cleaned.split()
    )


def _looks_like_all_caps_person_name(value: str) -> bool:
    if "." in value or any(ch.isdigit() for ch in value):
        return False
    if re.search(r"[a-zà-öø-ÿçğıöşü]", value):
        return False
    if not re.search(r"[A-ZÀ-ÖØ-ÞÇĞİÖŞÜ]", value):
        return False
    if not re.fullmatch(r"[A-ZÀ-ÖØ-ÞÇĞİÖŞÜ'\- ]+", value):
        return False

    words = value.split()
    if not (2 <= len(words) <= 5):
        return False

    # Preserve likely initials/abbreviated names such as "AJ LEE" instead of
    # guessing that "AJ" should become "Aj".
    return all(len(re.sub(r"[^A-ZÀ-ÖØ-ÞÇĞİÖŞÜ]", "", word)) > 2 for word in words)


def _title_case_name_word(word: str, *, use_turkish_casing: bool) -> str:
    parts = re.split(r"([\-'])", word)
    return "".join(
        _title_case_name_part(part, use_turkish_casing=use_turkish_casing)
        if part not in {"-", "'"}
        else part
        for part in parts
    )


def _title_case_name_part(part: str, *, use_turkish_casing: bool) -> str:
    if not part:
        return part
    lowered = _turkish_lower(part) if use_turkish_casing else part.lower()
    return lowered[0].upper() + lowered[1:]


def _turkish_lower(value: str) -> str:
    return value.translate(str.maketrans({"I": "ı", "İ": "i"})).lower()


def _normalize_phone_string(value: str | None) -> str | None:
    """Normalize contact phone display without guessing missing/misread digits."""
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None

    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;|·•")
    cleaned = re.sub(r"\s*\(\s*", "(", cleaned)
    cleaned = re.sub(r"\s*\)\s*", ") ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\s*([\-./])\s*", r"\1", cleaned)

    turkish_local = _format_turkish_local_phone_number(cleaned)
    if turkish_local is not None:
        return turkish_local

    return cleaned


def _format_turkish_local_phone_number(value: str) -> str | None:
    """Format compact Turkish domestic phone numbers for display.

    OCR can collapse ``0212 123 24 25`` into ``02121232425``. Restoring
    grouping is safe; changing digits is not, so this function never attempts
    digit repair.
    """
    stripped = value.strip()
    if stripped.startswith("+"):
        return None

    digits = re.sub(r"\D", "", stripped)
    if not (len(digits) == 11 and digits.startswith("0")):
        return None

    return f"{digits[:4]} {digits[4:7]} {digits[7:9]} {digits[9:]}"


def _normalize_token_list(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []

    for value in values:
        cleaned = _clean_optional_string(value)
        if cleaned is None:
            continue

        key = cleaned.casefold()
        if key in seen:
            continue

        seen.add(key)
        normalized.append(cleaned)

    return tuple(normalized)


def normalize_year(value: int | str | None) -> int | None:
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        if not cleaned.isdigit():
            return None
        parsed = int(cleaned)
    else:
        parsed = value

    if MIN_SUPPORTED_YEAR <= parsed <= MAX_SUPPORTED_YEAR:
        return parsed

    return None


def build_cv_draft_education_entry(
    *,
    school_name: str | None,
    degree_name: str | None = None,
    field_of_study: str | None = None,
    start_year: int | str | None = None,
    end_year: int | str | None = None,
) -> CvDraftEducationEntry | None:
    cleaned_school_name = _clean_optional_string(school_name)
    if cleaned_school_name is None:
        return None

    return CvDraftEducationEntry(
        school_name=cleaned_school_name,
        degree_name=_clean_optional_string(degree_name),
        field_of_study=_clean_optional_string(field_of_study),
        start_year=normalize_year(start_year),
        end_year=normalize_year(end_year),
    )


def build_cv_draft_experience_entry(
    *,
    title: str | None,
    company_name: str | None = None,
    start_year: int | str | None = None,
    end_year: int | str | None = None,
    summary: str | None = None,
) -> CvDraftExperienceEntry | None:
    cleaned_title = _clean_optional_string(title)
    if cleaned_title is None:
        return None

    return CvDraftExperienceEntry(
        title=cleaned_title,
        company_name=_clean_optional_string(company_name),
        start_year=normalize_year(start_year),
        end_year=normalize_year(end_year),
        summary=_clean_optional_string(summary),
    )


def build_cv_draft_language_entry(
    *,
    language_name: str | None,
    proficiency_level: str | None = None,
    notes: str | None = None,
) -> CvDraftLanguageEntry | None:
    cleaned_language_name = _clean_optional_string(language_name)
    if cleaned_language_name is None:
        return None

    return CvDraftLanguageEntry(
        language_name=cleaned_language_name,
        proficiency_level=_clean_optional_string(proficiency_level),
        notes=_clean_optional_string(notes),
    )


def build_cv_draft_certification_entry(
    *,
    certificate_name: str | None,
    issuer_name: str | None = None,
    issued_year: int | str | None = None,
) -> CvDraftCertificationEntry | None:
    cleaned_certificate_name = _clean_optional_string(certificate_name)
    if cleaned_certificate_name is None:
        return None

    return CvDraftCertificationEntry(
        certificate_name=cleaned_certificate_name,
        issuer_name=_clean_optional_string(issuer_name),
        issued_year=normalize_year(issued_year),
    )


def build_cv_profile_draft(
    *,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    linkedin_url: str | None = None,
    github_url: str | None = None,
    headline: str | None = None,
    summary: str | None = None,
    skills: tuple[str, ...] | list[str] = (),
    target_roles: tuple[str, ...] | list[str] = (),
    preferred_locations: tuple[str, ...] | list[str] = (),
    remote_preference: str | None = None,
    education_entries: tuple[CvDraftEducationEntry | None, ...]
    | list[CvDraftEducationEntry | None] = (),
    experience_entries: tuple[CvDraftExperienceEntry | None, ...]
    | list[CvDraftExperienceEntry | None] = (),
    language_entries: tuple[CvDraftLanguageEntry | None, ...]
    | list[CvDraftLanguageEntry | None] = (),
    certification_entries: tuple[CvDraftCertificationEntry | None, ...]
    | list[CvDraftCertificationEntry | None] = (),
) -> CvProfileDraft:
    return CvProfileDraft(
        full_name=_normalize_full_name_string(full_name),
        email=_clean_optional_string(email),
        phone=_normalize_phone_string(phone),
        linkedin_url=_clean_optional_string(linkedin_url),
        github_url=_clean_optional_string(github_url),
        headline=_clean_optional_string(headline),
        summary=_clean_optional_string(summary),
        skills=_normalize_token_list(skills),
        target_roles=_normalize_token_list(target_roles),
        preferred_locations=_normalize_token_list(preferred_locations),
        remote_preference=_clean_optional_string(remote_preference),
        education_entries=tuple(item for item in education_entries if item is not None),
        experience_entries=tuple(
            item for item in experience_entries if item is not None
        ),
        language_entries=tuple(item for item in language_entries if item is not None),
        certification_entries=tuple(
            item for item in certification_entries if item is not None
        ),
    )


def build_cv_profile_draft_snapshot(
    *,
    source_upload_id: int | None = None,
    source_filename: str | None = None,
    source_parse_status: str | None = None,
    parser_version: str | None = None,
    draft: CvProfileDraft | None = None,
    generated_at: str | None = None,
) -> CvProfileDraftSnapshot:
    resolved_generated_at = generated_at or (
        datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    return CvProfileDraftSnapshot(
        generated_at=resolved_generated_at,
        source_upload_id=source_upload_id,
        source_filename=_clean_optional_string(source_filename),
        source_parse_status=_clean_optional_string(source_parse_status),
        parser_version=_clean_optional_string(parser_version),
        draft=draft or CvProfileDraft(),
    )