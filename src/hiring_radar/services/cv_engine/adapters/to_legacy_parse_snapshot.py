from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from hiring_radar.services.cv_engine.models import ParseContext, ParsedCvData, ParserResult
from hiring_radar.services.cv_profile_draft import (
    CvProfileDraft,
    CvProfileDraftSnapshot,
    build_cv_draft_certification_entry,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)


def parse_result_to_legacy_snapshot(
    result: ParserResult,
    *,
    source_upload_id: int | None = None,
    source_parse_status: str | None = None,
    source_filename: str | None = None,
    generated_at: str | None = None,
    parser_version: str = 'cv_engine_v2',
) -> CvProfileDraftSnapshot:
    """Convert a parser result into the current legacy draft snapshot model."""
    return parse_context_to_legacy_snapshot(
        result.context,
        source_upload_id=source_upload_id,
        source_parse_status=source_parse_status,
        source_filename=source_filename,
        generated_at=generated_at,
        parser_version=parser_version,
    )



def parse_context_to_legacy_snapshot(
    context: ParseContext,
    *,
    source_upload_id: int | None = None,
    source_parse_status: str | None = None,
    source_filename: str | None = None,
    generated_at: str | None = None,
    parser_version: str = 'cv_engine_v2',
) -> CvProfileDraftSnapshot:
    """Convert a parse context into a legacy profile draft snapshot."""
    resolved_status = source_parse_status or _derive_legacy_parse_status(context)
    draft = parsed_cv_data_to_legacy_draft(context.parsed_data)
    return build_cv_profile_draft_snapshot(
        source_upload_id=source_upload_id,
        source_filename=source_filename or context.ingestion.filename,
        source_parse_status=resolved_status,
        parser_version=parser_version,
        draft=draft,
        generated_at=generated_at,
    )



def parsed_cv_data_to_legacy_draft(parsed_data: ParsedCvData | None) -> CvProfileDraft:
    """Convert v2 parsed CV data into the current legacy profile draft model."""
    if parsed_data is None:
        return CvProfileDraft()

    metadata = parsed_data.metadata
    education_entries = [
        build_cv_draft_education_entry(
            school_name=item.get('school_name'),
            degree_name=item.get('degree_name'),
            field_of_study=item.get('field_of_study'),
            start_year=item.get('start_year'),
            end_year=item.get('end_year'),
        )
        for item in _mapping_list(metadata.get('education_entries'))
    ]
    experience_entries = [
        build_cv_draft_experience_entry(
            title=item.title,
            company_name=item.company_name,
            start_year=item.date_range.start_year if item.date_range is not None else None,
            end_year=(
                None
                if item.date_range is None or item.date_range.is_present
                else item.date_range.end_year
            ),
            summary=' '.join(item.summary_lines).strip() or None,
        )
        for item in parsed_data.experience_lines
    ]
    language_entries = [
        build_cv_draft_language_entry(
            language_name=item.get('language_name'),
            proficiency_level=item.get('proficiency_level'),
            notes=item.get('notes'),
        )
        for item in _mapping_list(metadata.get('language_entries'))
    ]
    certification_entries = _certification_entries_from_parsed_data(parsed_data)

    return build_cv_profile_draft(
        full_name=parsed_data.full_name,
        email=_first_non_empty(parsed_data.emails),
        phone=_first_non_empty(parsed_data.phone_numbers),
        linkedin_url=_first_link_matching(parsed_data.links, "linkedin"),
        github_url=_first_link_matching(parsed_data.links, "github"),
        headline=_choose_headline(parsed_data),
        summary=parsed_data.summary,
        skills=_filtered_skill_names(parsed_data),
        target_roles=_filtered_target_roles(
            metadata.get('target_roles'),
            full_name=parsed_data.full_name,
            headline=_choose_headline(parsed_data),
        ),
        preferred_locations=_filtered_location_values(parsed_data.locations),
        remote_preference=_optional_string(metadata.get('remote_preference')),
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=language_entries,
        certification_entries=certification_entries,
    )




def _certification_entries_from_parsed_data(parsed_data: ParsedCvData) -> list:
    entries = []
    for item in _coalesced_certification_items(parsed_data.certifications):
        certificate_name = _optional_string(item.get('certificate_name'))
        issuer_name = _optional_string(item.get('issuer_name') or item.get('issuer'))
        issued_year = item.get('issued_year') or item.get('issued_at')
        entry = build_cv_draft_certification_entry(
            certificate_name=certificate_name,
            issuer_name=issuer_name,
            issued_year=issued_year,
        )
        if entry is not None:
            entries.append(entry)
    return entries


def _coalesced_certification_items(values: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not values:
        return []

    coalesced: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_item in values:
        if not isinstance(raw_item, Mapping):
            continue
        raw_name = _optional_string(raw_item.get('certificate_name') or raw_item.get('name'))
        if raw_name is None:
            continue

        issued_year, certificate_text = _split_leading_year(raw_name)
        issuer_name = _optional_string(raw_item.get('issuer_name') or raw_item.get('issuer'))
        if issuer_name is None:
            certificate_text, issuer_name = _split_certificate_issuer(certificate_text)

        item = {
            'certificate_name': certificate_text,
            'issuer_name': issuer_name,
            'issued_year': issued_year or raw_item.get('issued_year') or raw_item.get('issued_at'),
        }

        if current is not None and issued_year is None and not _looks_like_certificate_start(certificate_text):
            if current.get('issuer_name'):
                current['issuer_name'] = ' '.join(
                    part for part in (current.get('issuer_name'), certificate_text) if part
                ).strip()
            else:
                current['certificate_name'] = ' '.join(
                    part for part in (current.get('certificate_name'), certificate_text) if part
                ).strip()
            if current.get('issuer_name') is None and issuer_name:
                current['issuer_name'] = issuer_name
            continue

        if current is not None:
            coalesced.append(_normalize_certification_item(current))
        current = item

    if current is not None:
        coalesced.append(_normalize_certification_item(current))

    return [item for item in coalesced if item.get('certificate_name')]


def _normalize_certification_item(item: dict[str, Any]) -> dict[str, Any]:
    certificate_name = _optional_string(item.get('certificate_name')) or ''
    issuer_name = _optional_string(item.get('issuer_name'))
    certificate_name, inferred_issuer = _split_certificate_issuer(certificate_name)
    if issuer_name is None:
        issuer_name = inferred_issuer
    return {
        'certificate_name': certificate_name,
        'issuer_name': issuer_name,
        'issued_year': item.get('issued_year'),
    }


def _split_leading_year(value: str) -> tuple[int | None, str]:
    import re

    match = re.match(r'^((?:19|20)\d{2})\s+(.+)$', value.strip())
    if match is None:
        return None, value.strip()
    return int(match.group(1)), match.group(2).strip()


def _split_certificate_issuer(value: str) -> tuple[str, str | None]:
    parts = [part.strip() for part in value.split(',') if part.strip()]
    if len(parts) < 2:
        return value.strip(), None
    return parts[0], ', '.join(parts[1:])


def _looks_like_certificate_start(value: str) -> bool:
    lowered = value.casefold()
    return any(
        marker in lowered
        for marker in (
            'certified',
            'certificate',
            'certification',
            'professional',
            'license',
            'licence',
            'sertifika',
            'sertifikalı',
        )
    )


def _first_non_empty(values: list[str] | None) -> str | None:
    if not values:
        return None
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _first_link_matching(values: list[str] | None, keyword: str) -> str | None:
    if not values:
        return None
    lowered_keyword = keyword.lower()
    for value in values:
        if isinstance(value, str) and lowered_keyword in value.lower():
            return value.strip() or None
    return None



def _choose_headline(parsed_data: ParsedCvData) -> str | None:
    metadata_headline = _optional_string(parsed_data.metadata.get('headline'))
    if metadata_headline and not _value_matches_name(metadata_headline, parsed_data.full_name):
        return metadata_headline

    experience_title = next(
        (
            item.title
            for item in parsed_data.experience_lines
            if item.title is not None and item.title.strip()
        ),
        None,
    )
    return _optional_string(experience_title)


_GENERIC_DERIVED_SKILLS = frozenset(
    {
        'communication',
        'communications',
        'management',
        'leadership',
        'teamwork',
        'problem solving',
        'organization',
        'planning',
    }
)
_ROLE_KEYWORDS = frozenset(
    {
        'engineer',
        'developer',
        'coordinator',
        'manager',
        'analyst',
        'specialist',
        'consultant',
        'intern',
        'technician',
        'architect',
        'mühendis',
        'muhendis',
        'koordinatör',
        'koordinator',
    }
)


def _filtered_skill_names(parsed_data: ParsedCvData) -> list[str]:
    values: list[str] = []
    for skill in parsed_data.skills:
        name = _optional_string(skill.canonical_name)
        if name is None:
            continue
        key = _alias_key(name)
        section_name = getattr(skill.source_section, 'value', skill.source_section)
        section_key = str(section_name or '').casefold()
        if key in _GENERIC_DERIVED_SKILLS and section_key not in {'skills', 'technical_skills'}:
            continue
        values.append(name)
    return values


def _filtered_target_roles(
    value: object,
    *,
    full_name: str | None,
    headline: str | None,
) -> list[str]:
    roles: list[str] = []
    for item in _string_list(value):
        if _value_matches_name(item, full_name):
            continue
        if not _looks_like_role_value(item):
            continue
        roles.append(item)

    if roles:
        return roles
    if (
        headline
        and _looks_like_role_value(headline)
        and not _value_matches_name(headline, full_name)
    ):
        return [headline]
    return []


def _filtered_location_values(values: list[str] | None) -> list[str]:
    if not values:
        return []

    filtered: list[str] = []
    for value in values:
        cleaned = _optional_string(value)
        if cleaned is None:
            continue
        if len(cleaned) > 80:
            continue
        lowered = cleaned.casefold()
        if any(
            marker in lowered
            for marker in ('project', 'process', 'aircraft', 'customer', 'regulation')
        ):
            continue
        filtered.append(cleaned)
    return filtered


def _value_matches_name(value: str | None, full_name: str | None) -> bool:
    if value is None or full_name is None:
        return False
    return _alias_key(value) == _alias_key(full_name)


def _looks_like_role_value(value: str) -> bool:
    key = _alias_key(value)
    return any(re.search(rf'\b{re.escape(keyword)}\b', key) for keyword in _ROLE_KEYWORDS)


def _alias_key(value: str) -> str:
    lowered = value.casefold().replace('ı', 'i')
    return re.sub(r'\s+', ' ', lowered).strip()



def _derive_legacy_parse_status(context: ParseContext) -> str:
    if context.parsed_data is None:
        return 'failed'
    if not any(
        [
            context.parsed_data.full_name,
            context.parsed_data.summary,
            context.parsed_data.skills,
            context.parsed_data.experience_lines,
        ]
    ):
        return 'empty'
    return 'parsed'



def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]



def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]



def _optional_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None
