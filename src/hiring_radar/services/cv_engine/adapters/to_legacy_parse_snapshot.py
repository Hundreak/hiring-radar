from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hiring_radar.services.cv_engine.models import ParseContext, ParsedCvData, ParserResult
from hiring_radar.services.cv_profile_draft import (
    CvProfileDraft,
    CvProfileDraftSnapshot,
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

    return build_cv_profile_draft(
        headline=_choose_headline(parsed_data),
        summary=parsed_data.summary,
        skills=[skill.canonical_name for skill in parsed_data.skills],
        target_roles=_string_list(metadata.get('target_roles')),
        preferred_locations=parsed_data.locations,
        remote_preference=_optional_string(metadata.get('remote_preference')),
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=language_entries,
    )



def _choose_headline(parsed_data: ParsedCvData) -> str | None:
    experience_title = next(
        (
            item.title
            for item in parsed_data.experience_lines
            if item.title is not None and item.title.strip()
        ),
        None,
    )
    return _optional_string(parsed_data.metadata.get('headline')) or experience_title



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
