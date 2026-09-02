from __future__ import annotations

import hashlib
import re
from pathlib import Path

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.enterprise.runtime import (
    enrich_and_store_parser_result,
    get_cached_parser_result_for_text,
)
from hiring_radar.services.cv_engine.extraction.normalization import (
    DeterministicTextNormalizationStrategy,
)
from hiring_radar.services.cv_engine.language.detection import (
    LightweightLanguageDetectionStrategy,
)
from hiring_radar.services.cv_engine.models import (
    DocumentIngestionArtifact,
    ExtractionArtifact,
    ParseContext,
    ParsedCvData,
    ParsedDateRange,
    ParsedExperienceLine,
    ParsedSkill,
    ParserResult,
    SectionBlock,
    SectionName,
)
from hiring_radar.services.cv_engine.orchestrator import CvParserOrchestrator
from hiring_radar.services.cv_engine.parsing.skills import extract_skills_from_sections
from hiring_radar.services.cv_engine.protocols import (
    EntityExtractionStrategy,
    ExtractionStrategy,
    IngestionStrategy,
)
from hiring_radar.services.cv_engine.scoring.quality import (
    DeterministicQualityScoringStrategy,
)
from hiring_radar.services.cv_engine.segmentation.section_detection import (
    HybridSectionDetectionStrategy,
)
from hiring_radar.services.cv_engine.semantic.location_resolution import (
    resolve_location_candidate,
)
from hiring_radar.services.cv_engine.semantic.role_resolution import (
    resolve_role_candidate,
)
from hiring_radar.services.cv_profile_parser import parse_cv_text_to_profile_draft

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(
    # Keep the candidate on a single visual line. Using \s here made education
    # date ranges bleed across newlines and show up as false phone numbers.
    r"(?:\+?\d[\d \t().-]{7,}\d)",
    re.IGNORECASE,
)
_YEAR_TOKEN_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
_YEAR_RANGE_RE = re.compile(
    r"(?P<start>(?:19|20)\d{2})\s*(?:-|–|—|to)\s*"
    r"(?P<end>(?:19|20)\d{2}|present|current|ongoing|heute|devam)",
    re.IGNORECASE,
)
_LINK_RE = re.compile(r"(?:https?://|www\.|linkedin\.com/|github\.com/)\S+", re.IGNORECASE)
_NAME_DISALLOWED_TOKENS = {
    "cv",
    "resume",
    "özgeçmiş",
    "lebenslauf",
    "profil",
    "profile",
}


class PreExtractedTextIngestionStrategy(IngestionStrategy):
    """Create ingestion metadata for an already extracted CV text payload."""

    def __init__(
        self,
        *,
        filename: str,
        source_hint: str | None = None,
        file_size_bytes: int | None = None,
    ) -> None:
        self._filename = filename or "cv.txt"
        self._source_hint = source_hint or self._filename
        self._file_size_bytes = max(file_size_bytes or 0, 0)

    def ingest(
        self,
        *,
        source_path: str,
        config: ParserRuntimeConfig,
    ) -> DocumentIngestionArtifact:
        del config, source_path
        path = Path(self._filename)
        return DocumentIngestionArtifact(
            source_path=self._source_hint,
            filename=self._filename,
            extension=path.suffix.lower(),
            mime_type=None,
            file_size_bytes=self._file_size_bytes,
            fingerprint_sha256=None,
            encrypted=False,
        )


class PreExtractedTextExtractionStrategy(ExtractionStrategy):
    """Surface persisted extraction text inside the v2 orchestrator."""

    def __init__(
        self,
        *,
        extracted_text: str,
        used_ocr: bool,
        extraction_method: str,
        page_count: int | None = None,
    ) -> None:
        self._extracted_text = extracted_text
        self._used_ocr = used_ocr
        self._extraction_method = extraction_method
        self._page_count = page_count

    def extract(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> ExtractionArtifact:
        del context, config
        return ExtractionArtifact(
            text=self._extracted_text,
            extraction_method=self._extraction_method,
            used_ocr=self._used_ocr,
            page_count=self._page_count,
            layout_metadata={},
            metadata={
                "pre_extracted": True,
                "text_sha256": hashlib.sha256(
                    self._extracted_text.encode("utf-8")
                ).hexdigest(),
            },
        )


class LegacyDraftBackedEntityExtractionStrategy(EntityExtractionStrategy):
    """Bridge the current legacy draft parser into the v2 engine context."""

    def extract_entities(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> ParsedCvData:
        text = context.normalized.text if context.normalized is not None else ""
        sections = context.sections.sections if context.sections is not None else []
        draft = parse_cv_text_to_profile_draft(text)
        enriched_skills = _merge_skills(
            draft_skills=draft.skills,
            extracted_skills=extract_skills_from_sections(
                sections,
                config=config.skill_extraction,
            ),
        )
        experience_lines = [
            _legacy_experience_to_parsed(item) for item in draft.experience_entries
        ]
        links = _deduplicate_strings(_LINK_RE.findall(text))
        projects = _extract_projects(sections, links)
        certifications = _extract_certifications(sections)
        headline = draft.headline or _derive_semantic_headline(experience_lines)
        target_roles = _derive_target_roles(draft=draft, experience_lines=experience_lines)
        locations = _derive_locations(
            preferred_locations=draft.preferred_locations,
            experience_lines=experience_lines,
        )

        return ParsedCvData(
            full_name=_extract_full_name(text, sections),
            emails=_deduplicate_strings(_EMAIL_RE.findall(text)),
            phone_numbers=_normalize_phone_numbers(_PHONE_RE.findall(text)),
            locations=locations,
            summary=draft.summary,
            skills=enriched_skills,
            experience_lines=experience_lines,
            section_names=[section.name for section in sections],
            links=links,
            projects=projects,
            certifications=certifications,
            total_years_experience=_estimate_total_years_experience(experience_lines),
            metadata={
                "headline": headline,
                "target_roles": target_roles,
                "remote_preference": draft.remote_preference,
                "education_entries": [
                    {
                        "school_name": item.school_name,
                        "degree_name": item.degree_name,
                        "field_of_study": item.field_of_study,
                        "start_year": item.start_year,
                        "end_year": item.end_year,
                    }
                    for item in draft.education_entries
                ],
                "language_entries": [
                    {
                        "language_name": item.language_name,
                        "proficiency_level": item.proficiency_level,
                        "notes": item.notes,
                    }
                    for item in draft.language_entries
                ],
                "bridge_mode": "legacy_draft_backed",
                "semantic_skill_categories": _group_skills_by_category(enriched_skills),
            },
        )


def build_foundation_parser_result_from_text(
    *,
    extracted_text: str,
    filename: str,
    used_ocr: bool = False,
    extraction_method: str = "persisted_extraction_text",
    page_count: int | None = None,
    config: ParserRuntimeConfig | None = None,
) -> ParserResult:
    """Run the v2 foundation over a pre-extracted text payload."""
    runtime_config = config or ParserRuntimeConfig()
    cached_result = get_cached_parser_result_for_text(
        extracted_text=extracted_text,
        config=runtime_config,
    )
    if cached_result is not None:
        return cached_result

    orchestrator = CvParserOrchestrator(
        ingestion_strategy=PreExtractedTextIngestionStrategy(
            filename=filename,
            source_hint=filename,
            file_size_bytes=len(extracted_text.encode("utf-8")),
        ),
        extraction_strategy=PreExtractedTextExtractionStrategy(
            extracted_text=extracted_text,
            used_ocr=used_ocr,
            extraction_method=extraction_method,
            page_count=page_count,
        ),
        normalization_strategy=DeterministicTextNormalizationStrategy(),
        language_detection_strategy=LightweightLanguageDetectionStrategy(),
        section_detection_strategy=HybridSectionDetectionStrategy(),
        entity_extraction_strategy=LegacyDraftBackedEntityExtractionStrategy(),
        quality_scoring_strategy=DeterministicQualityScoringStrategy(),
        config=runtime_config,
    )
    result = orchestrator.parse(source_path=filename)
    return enrich_and_store_parser_result(
        result=result,
        extracted_text=extracted_text,
        config=runtime_config,
    )



def _merge_skills(
    *,
    draft_skills: tuple[str, ...],
    extracted_skills: list[ParsedSkill],
) -> list[ParsedSkill]:
    extracted_by_key = {
        item.canonical_name.casefold(): item for item in extracted_skills
    }
    ordered: list[ParsedSkill] = []
    seen: set[str] = set()

    for skill_name in draft_skills:
        key = skill_name.casefold()
        skill = extracted_by_key.get(key)
        if skill is None:
            skill = ParsedSkill(
                canonical_name=skill_name,
                matched_text=skill_name,
                source_section=SectionName.SKILLS,
                confidence=0.84,
                category=None,
                skill_type="hard_skill",
            )
        ordered.append(skill)
        seen.add(key)

    for skill in extracted_skills:
        key = skill.canonical_name.casefold()
        if key in seen:
            continue
        if _is_redundant_skill_name(key, seen):
            continue
        ordered.append(skill)
        seen.add(key)

    return ordered


def _is_redundant_skill_name(candidate_key: str, existing_keys: set[str]) -> bool:
    if len(candidate_key) <= 4:
        return False
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(candidate_key)}(?![a-z0-9])")
    return any(pattern.search(existing_key) for existing_key in existing_keys)



def _extract_full_name(text: str, sections: list[SectionBlock]) -> str | None:
    header_lines = _candidate_header_lines(text=text, sections=sections)
    for line in header_lines:
        if _looks_like_person_name(line):
            return line
    return None



def _candidate_header_lines(text: str, sections: list[SectionBlock]) -> list[str]:
    if sections and sections[0].name == SectionName.HEADER:
        return [line for line in sections[0].lines if line.strip()]
    return [line.strip() for line in text.splitlines()[:4] if line.strip()]



def _looks_like_person_name(value: str) -> bool:
    stripped = value.strip()
    if not stripped or len(stripped) > 80:
        return False
    if "@" in stripped or any(token in stripped.lower() for token in ("http", "www.")):
        return False
    tokens = [token for token in re.split(r"\s+", stripped) if token]
    if len(tokens) < 2 or len(tokens) > 5:
        return False
    if any(token.casefold() in _NAME_DISALLOWED_TOKENS for token in tokens):
        return False
    return all(_looks_like_name_token(token) for token in tokens)



def _looks_like_name_token(token: str) -> bool:
    letters = [character for character in token if character.isalpha()]
    if not letters:
        return False
    if len(letters) < 2:
        return False
    return token[0].isupper() or token.isupper()



def _legacy_experience_to_parsed(item: object) -> ParsedExperienceLine:
    title = getattr(item, "title", None)
    company_name = getattr(item, "company_name", None)
    location = None
    title_signal = resolve_role_candidate(title or "", section_name="experience")
    company_signal = resolve_role_candidate(company_name or "", section_name="experience")
    organization_signal = None if company_signal is not None else None
    if company_name:
        from hiring_radar.services.cv_engine.semantic.organization_resolution import (
            resolve_organization_candidate,
        )

        organization_signal = resolve_organization_candidate(company_name)
    if getattr(item, "summary", None):
        location_signal = resolve_location_candidate(str(item.summary))
        if location_signal is not None:
            location = location_signal.location_name
        else:
            location_signal = None
    else:
        location_signal = None

    date_range = ParsedDateRange(
        start_year=getattr(item, "start_year", None),
        start_month=None,
        end_year=getattr(item, "end_year", None),
        end_month=None,
        is_present=getattr(item, "end_year", None) is None,
        raw_text=None,
        confidence=0.82,
    )
    return ParsedExperienceLine(
        title=title_signal.title if title_signal is not None else title,
        company_name=(
            organization_signal.organization_name
            if organization_signal is not None
            else company_name
        ),
        location=location,
        date_range=date_range,
        summary_lines=(
            [getattr(item, "summary", "")]
            if getattr(item, "summary", None)
            else []
        ),
        confidence=max(
            0.84,
            title_signal.confidence if title_signal is not None else 0.0,
            organization_signal.confidence if organization_signal is not None else 0.0,
        ),
        title_provenance=(title_signal.provenance if title_signal is not None else None),
        company_provenance=(
            organization_signal.provenance if organization_signal is not None else None
        ),
        location_provenance=(
            location_signal.provenance if location_signal is not None else None
        ),
        metadata={"legacy_bridge": True},
    )



def _deduplicate_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result



def _normalize_phone_numbers(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = re.sub(r"\s+", " ", value).strip(" .,-")
        if _looks_like_phone_false_positive(cleaned):
            continue
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 8:
            continue
        key = digits
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
    return normalized


def _looks_like_phone_false_positive(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if _YEAR_RANGE_RE.fullmatch(stripped) or _YEAR_TOKEN_RE.fullmatch(stripped):
        return True

    # Common CV dates such as "2012 - 2017" have exactly two four-digit years.
    # They satisfy broad phone regexes unless explicitly filtered here.
    digits = re.sub(r"\D", "", stripped)
    years = _YEAR_TOKEN_RE.findall(stripped)
    has_phone_marker = "+" in stripped or "(" in stripped or ")" in stripped
    if len(years) >= 2 and len(digits) <= 8 and not has_phone_marker:
        return True
    return False



def _derive_semantic_headline(experience_lines: list[ParsedExperienceLine]) -> str | None:
    for line in experience_lines:
        if line.title:
            return line.title
    return None



def _derive_target_roles(
    *,
    draft: object,
    experience_lines: list[ParsedExperienceLine],
) -> list[str]:
    draft_roles = list(getattr(draft, "target_roles", ()))
    if draft_roles:
        return draft_roles
    headline = getattr(draft, "headline", None)
    if isinstance(headline, str) and headline.strip():
        return [headline.strip()]
    role_titles = [line.title for line in experience_lines if line.title]
    return role_titles[:2]



def _derive_locations(
    *,
    preferred_locations: tuple[str, ...],
    experience_lines: list[ParsedExperienceLine],
) -> list[str]:
    if preferred_locations:
        return list(preferred_locations)
    locations = [line.location for line in experience_lines if line.location]
    return _deduplicate_strings(locations)



def _extract_projects(sections: list[SectionBlock], links: list[str]) -> list[dict[str, str]]:
    projects_section = next(
        (section for section in sections if section.name == SectionName.PROJECTS),
        None,
    )
    projects: list[dict[str, str]] = []
    if projects_section is not None:
        for line in projects_section.lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            matching_link = next(
                (item for item in links if cleaned in item or item in cleaned),
                None,
            )
            projects.append(
                {
                    "title": cleaned.split(" - ", maxsplit=1)[0],
                    "description": cleaned,
                    "url": matching_link or "",
                }
            )
    if projects:
        return projects[:5]
    return [
        {
            "title": _infer_project_title_from_url(link),
            "description": link,
            "url": link,
        }
        for link in links
    ][:3]



def _extract_certifications(sections: list[SectionBlock]) -> list[dict[str, str]]:
    certification_section = next(
        (section for section in sections if section.name == SectionName.CERTIFICATIONS),
        None,
    )
    if certification_section is None:
        return []

    records: list[str] = []
    current: str | None = None
    for raw_line in certification_section.lines:
        line = raw_line.strip()
        if not line:
            continue
        if _line_starts_new_certification(line) or current is None:
            if current is not None:
                records.append(current)
            current = line
            continue
        current = f"{current} {line}".strip()

    if current is not None:
        records.append(current)

    return [
        {"certificate_name": record, "issuer": "", "issued_at": ""}
        for record in records
        if record
    ][:5]


def _line_starts_new_certification(line: str) -> bool:
    lowered = line.casefold()
    return bool(_YEAR_TOKEN_RE.search(line)) or any(
        marker in lowered
        for marker in (
            "certified",
            "certification",
            "certificate",
            "professional",
            "license",
            "licence",
            "sertifika",
            "sertifikalı",
        )
    )



def _estimate_total_years_experience(experience_lines: list[ParsedExperienceLine]) -> float | None:
    month_totals = 0
    for item in experience_lines:
        if item.date_range is None or item.date_range.start_year is None:
            continue
        start_year = item.date_range.start_year
        start_month = item.date_range.start_month or 1
        end_year = item.date_range.end_year or start_year
        end_month = item.date_range.end_month or 12
        interval_months = max(((end_year - start_year) * 12) + (end_month - start_month + 1), 0)
        month_totals += interval_months
    if month_totals <= 0:
        return None
    return round(month_totals / 12.0, 1)



def _group_skills_by_category(skills: list[ParsedSkill]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for skill in skills:
        category = skill.category or "uncategorized"
        grouped.setdefault(category, []).append(skill.canonical_name)
    return {key: sorted(set(values), key=str.casefold) for key, values in grouped.items()}


def _infer_project_title_from_url(url: str) -> str:
    cleaned = url.rstrip('/').rsplit('/', maxsplit=1)[-1].strip()
    if not cleaned or '.' in cleaned:
        return 'Linked project'
    return cleaned.replace('-', ' ').replace('_', ' ').title()
