from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.extraction.normalization import (
    normalize_extracted_text as normalize_engine_text,
)
from hiring_radar.services.cv_engine.language.detection import detect_supported_language
from hiring_radar.services.cv_engine.models import SectionBlock, SectionName
from hiring_radar.services.cv_engine.parsing.dates import parse_date_range
from hiring_radar.services.cv_engine.parsing.experience_lines import (
    parse_experience_block as parse_engine_experience_block,
)
from hiring_radar.services.cv_engine.parsing.skills import (
    extract_skills_from_sections,
    extract_skills_from_text,
)
from hiring_radar.services.cv_engine.semantic.location_resolution import (
    resolve_location_candidate,
)
from hiring_radar.services.cv_engine.semantic.role_resolution import (
    resolve_role_candidate,
)
from hiring_radar.services.cv_engine.segmentation.section_detection import (
    HybridSectionDetectionStrategy,
)
from hiring_radar.services.cv_extraction import normalize_extracted_text
from hiring_radar.services.cv_profile_draft import (
    CvProfileDraft,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
)

HEURISTIC_CV_PARSER_VERSION = "heuristic-v0"
_RUNTIME_CONFIG = ParserRuntimeConfig()
_SECTION_DETECTION_STRATEGY = HybridSectionDetectionStrategy()


ROLE_HINT_KEYWORDS = frozenset(
    {
        "engineer",
        "developer",
        "analyst",
        "manager",
        "scientist",
        "architect",
        "consultant",
        "specialist",
        "lead",
        "administrator",
        "designer",
        "intern",
        "technician",
        "researcher",
        "mühendis",
        "geliştirici",
        "analist",
        "uzman",
        "yönetici",
        "tasarımcı",
        "praktikant",
        "ingenieur",
        "entwickler",
        "berater",
        "leiter",
        "spezialist",
        "forscher",
    }
)

LANGUAGE_PROFICIENCY_HINTS = frozenset(
    {
        "native",
        "fluent",
        "professional",
        "professional working proficiency",
        "conversational",
        "intermediate",
        "advanced",
        "beginner",
        "basic",
        "elementary",
        "mother tongue",
        "ana dil",
        "akıcı",
        "profesyonel",
        "orta",
        "ileri",
        "başlangıç",
        "muttersprache",
        "fließend",
        "grundkenntnisse",
        "fortgeschritten",
        "c2",
        "c1",
        "b2",
        "b1",
        "a2",
        "a1",
    }
)


DEGREE_HINT_KEYWORDS = frozenset(
    {
        "bsc",
        "msc",
        "bs",
        "ms",
        "ba",
        "ma",
        "b.eng",
        "m.eng",
        "phd",
        "mba",
        "bachelor",
        "master",
        "doctorate",
        "associate",
        "engineering",
        "mühendisliği",
        "muhendisligi",
        "lisans",
        "yüksek lisans",
        "yuksek lisans",
        "üniversite",
        "universite",
        "university",
        "universität",
        "universitat",
    }
)

KNOWN_LANGUAGE_NAMES = frozenset(
    {
        "english",
        "turkish",
        "türkçe",
        "turkce",
        "german",
        "deutsch",
        "french",
        "français",
        "francais",
        "spanish",
        "español",
        "espanol",
        "italian",
        "italiano",
        "portuguese",
        "português",
        "portugues",
        "arabic",
        "russian",
        "russkiy",
        "dutch",
        "nederlands",
        "chinese",
        "mandarin",
        "japanese",
        "korean",
    }
)

COMPANY_HINT_KEYWORDS = frozenset(
    {
        "gmbh",
        "llc",
        "inc",
        "corp",
        "corporation",
        "ltd",
        "limited",
        "company",
        "co",
        "co.",
        "holding",
        "holdings",
        "solutions",
        "systems",
        "software",
        "technologies",
        "technology",
        "labs",
        "lab",
        "group",
        "ag",
        "plc",
        "a.ş",
        "a. s",
        "as",
        "oy",
        "ab",
    }
)

INSTITUTION_HINT_KEYWORDS = frozenset(
    {
        "university",
        "universite",
        "üniversite",
        "universität",
        "universitat",
        "college",
        "institute",
        "institut",
        "school",
        "faculty",
        "academy",
        "lycee",
        "lycée",
        "high school",
        "technical university",
    }
)

SINGLE_CHARACTER_SKILL_TOKENS = frozenset({"c", "r"})

SECTION_ALIASES: dict[str, frozenset[str]] = {
    "summary": frozenset(
        {
            "summary",
            "professional summary",
            "executive summary",
            "profile",
            "about",
            "objective",
            "career summary",
            "personal profile",
            "professional profile",
            "career profile",
            "özet",
            "profil",
            "profil özeti",
            "kariyer özeti",
            "zusammenfassung",
            "profilzusammenfassung",
            "kurzprofil",
        }
    ),
    "skills": frozenset(
        {
            "skills",
            "technical skills",
            "core skills",
            "tech stack",
            "technologies",
            "competencies",
            "expertise",
            "key skills",
            "core competencies",
            "technical competencies",
            "skills & tools",
            "skills and tools",
            "tools & technologies",
            "tools and technologies",
            "technical expertise",
            "professional skills",
            "programming languages",
            "frameworks & tools",
            "frameworks and tools",
            "tech skills",
            "it skills",
            "tools",
            "beceriler",
            "teknik beceriler",
            "yetkinlikler",
            "uzmanlık alanları",
            "araçlar ve teknolojiler",
            "teknik yetkinlikler",
            "fähigkeiten",
            "kenntnisse",
            "technologien",
            "kompetenzen",
            "schlüsselkompetenzen",
            "technische fähigkeiten",
            "werkzeuge und technologien",
        }
    ),
    "experience": frozenset(
        {
            "experience",
            "work experience",
            "employment history",
            "professional experience",
            "career history",
            "work history",
            "employment",
            "relevant experience",
            "professional background",
            "positions held",
            "career",
            "iş deneyimi",
            "deneyim",
            "tecrübe",
            "profesyonel deneyim",
            "iş geçmişi",
            "berufserfahrung",
            "arbeitserfahrung",
            "beruflicher werdegang",
            "berufliche laufbahn",
            "bisherige positionen",
        }
    ),
    "education": frozenset(
        {
            "education",
            "academic background",
            "academic history",
            "education history",
            "qualifications",
            "degrees",
            "certifications",
            "certifications & education",
            "academic qualifications",
            "educational background",
            "eğitim",
            "öğrenim",
            "akademik geçmiş",
            "eğitim bilgileri",
            "sertifikalar",
            "ausbildung",
            "bildung",
            "akademischer hintergrund",
            "qualifikationen",
            "studium",
            "abschlüsse",
        }
    ),
    "languages": frozenset(
        {
            "languages",
            "language",
            "language skills",
            "language proficiency",
            "diller",
            "dil",
            "sprachen",
            "sprachkenntnisse",
        }
    ),
    "target_roles": frozenset(
        {
            "target roles",
            "target role",
            "desired position",
            "desired roles",
            "career objective",
            "target position",
            "hedef rol",
            "hedef roller",
            "hedef pozisyon",
            "hedef pozisyonlar",
            "zielposition",
            "zielrolle",
            "gewünschte position",
        }
    ),
    "preferences": frozenset(
        {
            "preferences",
            "work preferences",
            "location preferences",
            "remote preference",
            "work authorization",
            "tercihler",
            "çalışma tercihleri",
            "lokasyon tercihleri",
            "arbeitspräferenzen",
            "standortpräferenzen",
        }
    ),
}

def _alias_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    collapsed = re.sub(r"\s+", " ", without_marks).strip()
    return collapsed.casefold()

NORMALIZED_SECTION_ALIASES: dict[str, frozenset[str]] = {
    canonical_name: frozenset(_alias_key(alias) for alias in aliases)
    for canonical_name, aliases in SECTION_ALIASES.items()
}

SECTION_ALIAS_PREFIXES: tuple[tuple[str, str], ...] = tuple(
    sorted(
        (
            (_alias_key(alias), canonical_name)
            for canonical_name, aliases in SECTION_ALIASES.items()
            for alias in aliases
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
)

EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
URL_HINT_RE = re.compile(r"(https?://|www\.|linkedin|github)", re.IGNORECASE)
LINKEDIN_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?",
    re.IGNORECASE,
)
GITHUB_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?",
    re.IGNORECASE,
)
YEAR_TOKEN_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
YEAR_RANGE_RE = re.compile(
    r"(?P<start>(?:19|20)\d{2})\s*(?:-|–|—|to)\s*"
    r"(?P<end>(?:19|20)\d{2}|present|current|ongoing|heute|devam)",
    re.IGNORECASE,
)


def parse_cv_text_to_profile_draft(extracted_text: str | None) -> CvProfileDraft:
    cleaned_text = normalize_extracted_text(extracted_text)
    if cleaned_text is None:
        return CvProfileDraft()

    prepared_text = _prepare_cv_text_for_parsing(cleaned_text)

    preamble_lines, sections = _segment_cv_sections(prepared_text)

    # Contact info extraction from preamble
    full_name = _extract_full_name(preamble_lines)
    email = _extract_email(preamble_lines)
    phone = _extract_phone(preamble_lines)
    linkedin_url = _extract_linkedin_url(prepared_text)
    github_url = _extract_github_url(prepared_text)

    headline = _extract_headline(preamble_lines)
    summary = _extract_summary(preamble_lines, sections, headline)
    skills = _extract_skills(sections)
    if not skills:
        skills = _extract_fallback_skills(preamble_lines)

    target_roles = _extract_target_roles(sections, headline)
    preferred_locations = _extract_preferred_locations(preamble_lines, sections)
    remote_preference = _extract_remote_preference(prepared_text, sections)

    language_entries = _extract_language_entries(sections)
    if not language_entries:
        language_entries = _extract_fallback_language_entries(preamble_lines)

    experience_entries = _extract_experience_entries(sections)
    if not experience_entries:
        experience_entries = _extract_fallback_experience_entries(preamble_lines)

    education_entries = _extract_education_entries(sections)
    if not education_entries:
        education_entries = _extract_fallback_education_entries(preamble_lines)

    return build_cv_profile_draft(
        full_name=full_name,
        email=email,
        phone=phone,
        linkedin_url=linkedin_url,
        github_url=github_url,
        headline=headline,
        summary=summary,
        skills=skills,
        target_roles=target_roles,
        preferred_locations=preferred_locations,
        remote_preference=remote_preference,
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=language_entries,
    )



def _prepare_cv_text_for_parsing(text: str) -> str:
    """Normalize extracted CV text before section segmentation.

    This pass is intentionally conservative. It only:
    - removes adjacent duplicate lines
    - merges two-line section headers like "Work" + "Experience"

    Args:
        text: Normalized extracted text.

    Returns:
        Parser-friendly normalized text.
    """
    raw_lines = [line.strip() for line in text.split("\n")]
    normalized_lines: list[str] = []
    index = 0

    while index < len(raw_lines):
        current_line = raw_lines[index].strip()

        if current_line:
            if index + 1 < len(raw_lines):
                next_line = raw_lines[index + 1].strip()
                if next_line:
                    combined_line = f"{current_line} {next_line}"
                    if _detect_section_name(combined_line) is not None:
                        current_line = combined_line
                        index += 1

            if normalized_lines:
                previous_line = normalized_lines[-1]
                if previous_line and _alias_key(previous_line) == _alias_key(current_line):
                    index += 1
                    continue

        normalized_lines.append(current_line)
        index += 1

    return "\n".join(normalized_lines)


def _segment_cv_sections(text: str) -> tuple[list[str], dict[str, list[str]]]:
    """Split extracted CV text into preamble lines and canonical sections.

    Args:
        text: Normalized extracted CV text.

    Returns:
        A tuple containing preamble lines and section-mapped content lines.
    """
    preamble_lines: list[str] = []
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            if current_section is None:
                preamble_lines.append("")
            else:
                sections.setdefault(current_section, []).append("")
            continue

        section_name = _detect_section_name(line)
        if section_name is not None:
            current_section = section_name
            sections.setdefault(current_section, [])
            continue

        inline_section = _split_inline_section_header(line)
        if inline_section is not None:
            current_section, payload = inline_section
            sections.setdefault(current_section, [])
            if payload is not None:
                sections[current_section].append(payload)
            continue

        if current_section is None:
            preamble_lines.append(line)
        else:
            sections.setdefault(current_section, []).append(line)

    return preamble_lines, sections



def _build_section_detection_context(text: str, lines: list[str]):
    from hiring_radar.services.cv_engine.models import (
        DocumentIngestionArtifact,
        ExtractionArtifact,
        NormalizedTextArtifact,
        ParseContext,
    )

    return ParseContext(
        ingestion=DocumentIngestionArtifact(
            source_path="cv_text",
            filename="cv.txt",
            extension=".txt",
            mime_type="text/plain",
            file_size_bytes=len(text.encode("utf-8")),
            fingerprint_sha256=None,
            encrypted=False,
        ),
        extraction=ExtractionArtifact(
            text=text,
            extraction_method="legacy_text",
            used_ocr=False,
            page_count=1,
        ),
        normalized=NormalizedTextArtifact(text=text, lines=lines),
        detected_language=None,
    )

def _detect_section_name(line: str) -> str | None:
    simplified = _simplify_section_header(line)
    for canonical_name, aliases in NORMALIZED_SECTION_ALIASES.items():
        if simplified in aliases:
            return canonical_name
    return None

def _split_inline_section_header(line: str) -> tuple[str, str | None] | None:
    """Extract inline section headers such as 'Skills: Python, SQL'.

    Args:
        line: Raw text line from extracted CV content.

    Returns:
        A tuple of canonical section name and optional payload when the line begins
        with a known section header, otherwise None.
    """
    stripped_line = re.sub(r"^[•·\-\s]+", "", line).strip()
    separator_match = re.search(r"\s[:\-–—]\s|\:\s*", stripped_line)
    if separator_match is None:
        return None

    header_candidate = stripped_line[: separator_match.start()].strip()
    payload_candidate = stripped_line[separator_match.end() :].strip()

    if not payload_candidate:
        return None

    canonical_name = _detect_section_name(header_candidate)
    if canonical_name is not None:
        return canonical_name, payload_candidate

    normalized_header = _alias_key(header_candidate)
    for alias_key, canonical_name in SECTION_ALIAS_PREFIXES:
        if normalized_header == alias_key:
            return canonical_name, payload_candidate

    return None

def _simplify_section_header(line: str) -> str:
    simplified = line.strip()
    simplified = re.sub(r"^[•·\-\s]+", "", simplified)
    simplified = re.sub(r"[:\-–—\s]+$", "", simplified)
    simplified = re.sub(r"\s+", " ", simplified)
    return _alias_key(simplified)


def _clean_token(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    cleaned = cleaned.strip("•·|-–—,:;/")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or None


def _looks_like_contact_line(line: str) -> bool:
    if EMAIL_RE.search(line) or URL_HINT_RE.search(line):
        return True

    phone_match = PHONE_RE.search(line)
    if phone_match is None:
        return False

    matched_text = phone_match.group().strip()

    if YEAR_RANGE_RE.fullmatch(matched_text):
        return False
    if YEAR_TOKEN_RE.fullmatch(matched_text):
        return False

    return True

def _looks_like_role_line(line: str) -> bool:
    lowered = line.casefold()
    return any(keyword in lowered for keyword in ROLE_HINT_KEYWORDS)


def _extract_headline(preamble_lines: list[str]) -> str | None:
    candidates = [
        line
        for line in preamble_lines
        if line and not _looks_like_contact_line(line) and _detect_section_name(line) is None
    ]
    if not candidates:
        return None

    if len(candidates) >= 2:
        first_candidate = candidates[0]
        second_candidate = candidates[1]
        if not _looks_like_role_line(first_candidate) and _looks_like_role_line(
            second_candidate
        ):
            return _clean_token(second_candidate)

    for candidate in candidates:
        if _looks_like_role_line(candidate) and len(candidate) <= 100:
            return _clean_token(candidate)

    return _clean_token(candidates[0])


def _extract_full_name(preamble_lines: list[str]) -> str | None:
    """Extract the candidate's full name from the preamble.

    The name is typically the first non-contact, non-role, non-skill line.
    """
    for line in preamble_lines:
        if not line:
            continue
        if _looks_like_contact_line(line):
            continue
        if _detect_section_name(line) is not None:
            continue
        if _looks_like_skill_line(line):
            continue
        if _looks_like_language_line(line):
            continue
        if _contains_year_information(line):
            continue
        # Name lines are typically short, no role keywords, and come first
        cleaned = _clean_token(line)
        if cleaned is None:
            continue
        # A name is typically under 60 chars, doesn't look like a role,
        # and has 1-4 words (first, middle, last, suffix)
        words = cleaned.split()
        if 1 <= len(words) <= 5 and len(cleaned) <= 60:
            if not _looks_like_role_line(cleaned):
                return cleaned
        # If the first non-contact line is a role line, skip it and look
        # for a name line before it — but typically name is the very first
        break
    return None


def _extract_email(preamble_lines: list[str]) -> str | None:
    """Extract the first email address from the preamble."""
    for line in preamble_lines:
        match = EMAIL_RE.search(line or "")
        if match:
            return match.group().strip()
    return None


def _extract_phone(preamble_lines: list[str]) -> str | None:
    """Extract a phone number from the preamble."""
    for line in preamble_lines:
        if not line:
            continue
        match = PHONE_RE.search(line)
        if match:
            candidate = match.group().strip()
            # Exclude year-like numbers
            if YEAR_RANGE_RE.fullmatch(candidate) or YEAR_TOKEN_RE.fullmatch(candidate):
                continue
            # Clean up whitespace
            return re.sub(r"\s+", " ", candidate).strip()
    return None


def _extract_linkedin_url(text: str) -> str | None:
    """Extract a LinkedIn profile URL from the full text."""
    match = LINKEDIN_URL_RE.search(text)
    if match:
        url = match.group().strip().rstrip("/")
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return None


def _extract_github_url(text: str) -> str | None:
    """Extract a GitHub profile URL from the full text."""
    match = GITHUB_URL_RE.search(text)
    if match:
        url = match.group().strip().rstrip("/")
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return None


def _extract_summary(
    preamble_lines: list[str],
    sections: dict[str, list[str]],
    headline: str | None,
) -> str | None:
    summary_lines = [line for line in sections.get("summary", []) if line]
    if summary_lines:
        candidate_lines = summary_lines[:3]
        if (
            headline is not None
            and candidate_lines
            and _alias_key(candidate_lines[0]) == _alias_key(headline)
        ):
            candidate_lines = candidate_lines[1:]
        return _clean_token(" ".join(candidate_lines))

    for line in preamble_lines:
        if not line:
            continue
        if _looks_like_contact_line(line):
            continue
        if headline is not None and _alias_key(line) == _alias_key(headline):
            continue
        if _looks_like_skill_line(line):
            continue
        if _looks_like_language_line(line):
            continue
        if _contains_year_information(line):
            continue
        if len(line) >= 60:
            return _clean_token(line)

    preamble_paragraphs = _collapse_paragraphs(
        line
        for line in preamble_lines
        if line and not _looks_like_contact_line(line)
    )
    for paragraph in preamble_paragraphs:
        if len(paragraph) >= 80:
            return _clean_token(paragraph)

    return None


def _collapse_paragraphs(lines: Iterable[str]) -> list[str]:
    paragraphs: list[str] = []
    current_lines: list[str] = []

    for line in lines:
        if not line:
            if current_lines:
                paragraphs.append(" ".join(current_lines))
                current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        paragraphs.append(" ".join(current_lines))

    return paragraphs


def _extract_skills(sections: dict[str, list[str]]) -> list[str]:
    skills: list[str] = []
    seen_lower: set[str] = set()

    for line in sections.get("skills", []):
        if not line:
            continue

        # Handle "Category: skill1, skill2" and "Category - skill1, skill2"
        payload = line
        category_match = re.match(
            r"^([A-Za-zÇĞİÖŞÜçğıöşüÄÖÜäöüß\s&/]+?)\s*[:–—-]\s*(.+)$",
            line,
        )
        if category_match:
            payload = category_match.group(2)

        for token in re.split(r"[|,;•·]", payload):
            cleaned_token = _clean_token(token)
            if cleaned_token is None:
                continue
            # Strip parenthetical notes like "Python (3.11+)"
            base_token = re.sub(r"\s*\([^)]*\)\s*$", "", cleaned_token).strip()
            if not base_token:
                continue
            if len(base_token) == 1 and _alias_key(base_token) not in SINGLE_CHARACTER_SKILL_TOKENS:
                continue
            if len(base_token) > 40:
                continue
            lower = base_token.casefold()
            if lower in seen_lower:
                continue
            seen_lower.add(lower)
            skills.append(base_token)

    return skills


def _extract_fallback_skills(preamble_lines: list[str]) -> list[str]:
    skills: list[str] = []

    for line in preamble_lines:
        if not _looks_like_skill_line(line):
            continue

        for token in re.split(r"[|,;•·]", line):
            cleaned_token = _clean_token(token)
            if cleaned_token is None:
                continue
            lowered_token = _alias_key(cleaned_token)

            if len(cleaned_token) == 1 and lowered_token not in SINGLE_CHARACTER_SKILL_TOKENS:
                continue
            if len(cleaned_token) > 40:
                continue

            skills.append(cleaned_token)

    return skills


def _extract_target_roles(
    sections: dict[str, list[str]], headline: str | None
) -> list[str]:
    explicit_roles: list[str] = []

    for line in sections.get("target_roles", []):
        if not line:
            continue
        if _detect_section_name(line) is not None or _contains_year_information(line):
            continue

        for token in re.split(r"[|,;]", line):
            cleaned_token = _clean_token(token)
            if cleaned_token is None:
                continue
            if _detect_section_name(cleaned_token) is not None:
                continue
            if _contains_year_information(cleaned_token):
                continue
            explicit_roles.append(cleaned_token)

    if explicit_roles:
        return explicit_roles

    if headline and _looks_like_role_line(headline):
        return [headline]

    return []


def _extract_preferred_locations(
    preamble_lines: list[str], sections: dict[str, list[str]]
) -> list[str]:
    locations: list[str] = []

    for line in sections.get("preferences", []):
        if not line:
            continue
        lowered = _alias_key(line)
        if "location" in lowered or "lokasyon" in lowered or "standort" in lowered:
            payload = line.split(":", 1)[1] if ":" in line else line
            locations.extend(_parse_location_tokens(payload))

    for line in preamble_lines:
        if not line:
            continue
        if "|" not in line and "," not in line and ";" not in line:
            continue
        if _looks_like_skill_line(line):
            continue
        if _looks_like_language_line(line):
            continue
        if _contains_year_information(line):
            continue

        locations.extend(_parse_location_tokens(line))

    return locations


def _parse_location_tokens(text: str) -> list[str]:
    locations: list[str] = []

    for raw_token in re.split(r"[|,;/]", text):
        token = _clean_token(raw_token)
        if token is None:
            continue

        lowered_token = _alias_key(token)

        if _looks_like_contact_line(token):
            continue
        if lowered_token in {"remote", "hybrid", "onsite", "uzaktan", "hibrit"}:
            continue
        if _contains_keyword_signal(token, COMPANY_HINT_KEYWORDS):
            continue
        if _contains_keyword_signal(token, INSTITUTION_HINT_KEYWORDS):
            continue
        if _looks_like_language_line(token):
            continue
        if _looks_like_skill_line(token):
            continue
        if _contains_year_information(token):
            continue
        if len(token) < 2 or len(token) > 40:
            continue

        locations.append(token)

    return locations

def _extract_remote_preference(
    text: str, sections: dict[str, list[str]]
) -> str | None:
    preference_payload = " ".join(line for line in sections.get("preferences", []) if line)
    source_text = f"{preference_payload}\n{text}" if preference_payload else text
    lowered = _alias_key(source_text)

    if "hybrid" in lowered or "hibrit" in lowered:
        return "hybrid"
    if "remote" in lowered or "uzaktan" in lowered:
        return "remote"
    if (
        "onsite" in lowered
        or "on-site" in lowered
        or "on site" in lowered
        or "office" in lowered
        or "ofis" in lowered
        or "vor ort" in lowered
    ):
        return "onsite"

    return None


def _extract_language_entries(sections: dict[str, list[str]]) -> list:
    language_entries = []

    for line in sections.get("languages", []):
        if not line:
            continue

        raw_items = [item.strip() for item in re.split(r"[|,;/]", line) if item.strip()]
        if not raw_items:
            raw_items = [line]

        for raw_item in raw_items:
            language_name, proficiency_level = _parse_language_item(raw_item)
            entry = build_cv_draft_language_entry(
                language_name=language_name,
                proficiency_level=proficiency_level,
            )
            if entry is not None:
                language_entries.append(entry)

    return language_entries


def _extract_fallback_language_entries(
    preamble_lines: list[str],
) -> list:
    language_entries = []

    for line in preamble_lines:
        if not _looks_like_language_line(line):
            continue

        raw_items = [item.strip() for item in re.split(r"[|,;/]", line) if item.strip()]
        if not raw_items:
            raw_items = [line]

        for raw_item in raw_items:
            language_name, proficiency_level = _parse_language_item(raw_item)
            if language_name is None:
                continue
            if _alias_key(language_name) not in KNOWN_LANGUAGE_NAMES:
                continue

            entry = build_cv_draft_language_entry(
                language_name=language_name,
                proficiency_level=proficiency_level,
            )
            if entry is not None:
                language_entries.append(entry)

    return language_entries

def _parse_language_item(item: str) -> tuple[str | None, str | None]:
    cleaned_item = _clean_token(item)
    if cleaned_item is None:
        return None, None

    match = re.match(
        r"(?P<name>[A-Za-zÇĞİÖŞÜçğıöşüÄÖÜäöüß\s]+?)"
        r"\s*(?:[:\-–—]\s*|\((?=[^)]+\)))(?P<rest>.+?)\)?$",
        cleaned_item,
    )
    if match:
        language_name = _clean_token(match.group("name"))
        rest = _clean_token(match.group("rest"))
        return language_name, rest

    tokens = cleaned_item.split()
    if len(tokens) >= 2:
        trailing_token = tokens[-1]
        if trailing_token.casefold() in LANGUAGE_PROFICIENCY_HINTS:
            language_name = _clean_token(" ".join(tokens[:-1]))
            return language_name, trailing_token

    return cleaned_item, None


def _extract_experience_entries(sections: dict[str, list[str]]) -> list:
    blocks = _split_non_empty_blocks(sections.get("experience", []))
    entries = []

    for block in blocks:
        entry = _parse_experience_block(block)
        if entry is not None:
            entries.append(entry)

    return entries


def _extract_education_entries(sections: dict[str, list[str]]) -> list:
    blocks = _split_non_empty_blocks(sections.get("education", []))
    entries = []

    for block in blocks:
        entry = _parse_education_block(block)
        if entry is not None:
            entries.append(entry)

    return entries


def _split_non_empty_blocks(lines: list[str]) -> list[list[str]]:
    """Split section lines into semantic entry blocks.

    This splitter supports both blank-line-separated CV layouts and denser layouts
    where consecutive entries appear without blank lines.

    Args:
        lines: Section lines belonging to a single canonical section.

    Returns:
        A list of non-empty semantic blocks.
    """
    blocks: list[list[str]] = []
    current_block: list[str] = []

    for line in lines:
        if not line:
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue

        if _should_start_new_block(current_block, line):
            blocks.append(current_block)
            current_block = [line]
            continue

        current_block.append(line)

    if current_block:
        blocks.append(current_block)

    return blocks


def _should_start_new_block(current_block: list[str], line: str) -> bool:
    """Determine whether a line should start a new semantic block.

    Args:
        current_block: Current accumulated block.
        line: Candidate next line.

    Returns:
        True when the line likely starts a new experience or education entry.
    """
    if not current_block:
        return False

    current_block_has_year = any(
        _contains_year_information(item) for item in current_block
    )
    if not current_block_has_year:
        return False

    if _contains_year_information(line):
        return True

    cleaned_line = _clean_token(line)
    if cleaned_line is None:
        return False

    if "|" in cleaned_line and len(cleaned_line) <= 120:
        return True

    return False


def _looks_like_skill_line(line: str) -> bool:
    cleaned_line = _clean_token(line)
    if cleaned_line is None:
        return False

    if _looks_like_contact_line(cleaned_line):
        return False
    if _contains_year_information(cleaned_line):
        return False
    if _looks_like_role_line(cleaned_line):
        return False
    if _looks_like_language_line(cleaned_line):
        return False
    if _looks_like_education_line(cleaned_line):
        return False
    if len(cleaned_line) > 120:
        return False

    tokens = [
        token.strip()
        for token in re.split(r"[|,;•·]", cleaned_line)
        if token.strip()
    ]
    if len(tokens) < 3:
        return False

    for token in tokens:
        if len(token) > 40:
            return False
        lowered = _alias_key(token)
        if lowered in {"remote", "hybrid", "onsite", "uzaktan", "hibrit"}:
            return False
        if _contains_keyword_signal(token, COMPANY_HINT_KEYWORDS):
            return False
        if _contains_keyword_signal(token, INSTITUTION_HINT_KEYWORDS):
            return False

    return True

def _looks_like_language_line(line: str) -> bool:
    cleaned_line = _clean_token(line)
    if cleaned_line is None:
        return False

    raw_items = [item.strip() for item in re.split(r"[|,;/]", cleaned_line) if item.strip()]
    if not raw_items:
        raw_items = [cleaned_line]

    matched_count = 0
    for raw_item in raw_items:
        language_name, _proficiency_level = _parse_language_item(raw_item)
        if language_name is None:
            continue
        if _alias_key(language_name) in KNOWN_LANGUAGE_NAMES:
            matched_count += 1

    return matched_count > 0


def _contains_keyword_signal(text: str, keywords: frozenset[str]) -> bool:
    normalized_text = _alias_key(text)

    for keyword in keywords:
        normalized_keyword = _alias_key(keyword)

        if len(normalized_keyword) <= 4 and normalized_keyword.isalpha():
            if re.search(rf"\b{re.escape(normalized_keyword)}\b", normalized_text):
                return True
            continue

        if normalized_keyword in normalized_text:
            return True

    return False

def _looks_like_education_line(line: str) -> bool:
    cleaned_line = _clean_token(line)
    if cleaned_line is None:
        return False

    return _contains_keyword_signal(
        cleaned_line,
        DEGREE_HINT_KEYWORDS | INSTITUTION_HINT_KEYWORDS,
    )

def _looks_like_experience_line(line: str) -> bool:
    cleaned_line = _clean_token(line)
    if cleaned_line is None:
        return False

    if not _contains_year_information(cleaned_line):
        return False
    if _looks_like_education_line(cleaned_line):
        return False

    lowered_line = _alias_key(cleaned_line)

    if _looks_like_role_line(cleaned_line):
        return True
    if "|" in cleaned_line:
        return True
    if " at " in lowered_line or " @ " in lowered_line:
        return True
    if _contains_keyword_signal(cleaned_line, COMPANY_HINT_KEYWORDS):
        return True

    return False

def _extract_fallback_experience_entries(
    preamble_lines: list[str],
) -> list:
    entries = []
    candidate_lines = _build_fallback_candidate_lines(preamble_lines)

    index = 0
    while index < len(candidate_lines):
        line = candidate_lines[index]
        if not _looks_like_experience_line(line):
            index += 1
            continue

        block = [line]

        if index + 1 < len(candidate_lines):
            next_line = candidate_lines[index + 1]
            if (
                not _contains_year_information(next_line)
                and not _looks_like_skill_line(next_line)
                and not _looks_like_language_line(next_line)
                and not _looks_like_education_line(next_line)
            ):
                block.append(next_line)
                index += 1

        entry = _parse_experience_block(block)
        if entry is not None:
            entries.append(entry)

        index += 1

    return entries

def _extract_fallback_education_entries(
    preamble_lines: list[str],
) -> list:
    entries = []
    candidate_lines = _build_fallback_candidate_lines(preamble_lines)

    for line in candidate_lines:
        if not _looks_like_education_line(line):
            continue
        if not _contains_year_information(line):
            continue

        entry = _parse_education_block([line])
        if entry is not None:
            entries.append(entry)

    return entries

def _build_fallback_candidate_lines(lines: list[str]) -> list[str]:
    return [
        line
        for line in lines
        if line
        and not _looks_like_contact_line(line)
        and _detect_section_name(line) is None
    ]


def _build_fallback_timeline_blocks(lines: list[str]) -> list[list[str]]:
    filtered_lines = [
        line
        for line in lines
        if line
        and not _looks_like_contact_line(line)
        and _detect_section_name(line) is None
    ]

    blocks: list[list[str]] = []
    index = 0

    while index < len(filtered_lines):
        line = filtered_lines[index]
        if not _contains_year_information(line):
            index += 1
            continue

        block = [line]

        if index + 1 < len(filtered_lines):
            next_line = filtered_lines[index + 1]
            if (
                next_line
                and not _contains_year_information(next_line)
                and not _looks_like_contact_line(next_line)
                and _detect_section_name(next_line) is None
                and not _looks_like_skill_line(next_line)
                and not _looks_like_language_line(next_line)
            ):
                block.append(next_line)
                index += 1

        blocks.append(block)
        index += 1

    return blocks

def _parse_experience_block(block: list[str]):
    language = detect_supported_language(
        text="\n".join(block),
        supported_languages=_RUNTIME_CONFIG.language_detection.supported_languages,
        fallback_language=_RUNTIME_CONFIG.language_detection.fallback_language,
    )
    parsed = parse_engine_experience_block(
        block,
        language=language,
        config=_RUNTIME_CONFIG.experience_parsing,
    )
    if parsed.title is None:
        return None

    summary = _clean_token(" ".join(parsed.summary_lines))
    start_year = parsed.date_range.start_year if parsed.date_range else None
    end_year = parsed.date_range.end_year if parsed.date_range else None

    return build_cv_draft_experience_entry(
        title=parsed.title,
        company_name=parsed.company_name,
        start_year=start_year,
        end_year=end_year,
        summary=summary,
    )


def _parse_education_block(block: list[str]):
    entity_line, year_line, _summary = _resolve_entity_year_summary(block)
    if entity_line is None:
        return None

    start_year, end_year = _parse_year_range(year_line or entity_line)
    cleaned_entity = _remove_year_text(entity_line)

    # Try to split into school, degree, and field
    parts = re.split(r"\s*[|]\s*|\s+-\s+|\s*,\s+", cleaned_entity)
    parts = [_clean_token(p) for p in parts]
    parts = [p for p in parts if p]

    school_name: str | None = None
    degree_name: str | None = None
    field_of_study: str | None = None

    if len(parts) >= 3:
        # "School | Degree | Field" pattern
        school_name = parts[0]
        degree_name = parts[1]
        field_of_study = parts[2]
    elif len(parts) == 2:
        # Determine which is school and which is degree
        if _contains_keyword_signal(parts[0], INSTITUTION_HINT_KEYWORDS):
            school_name = parts[0]
            degree_name = parts[1]
        elif _contains_keyword_signal(parts[1], INSTITUTION_HINT_KEYWORDS):
            school_name = parts[1]
            degree_name = parts[0]
        else:
            school_name = parts[0]
            degree_name = parts[1]
    elif len(parts) == 1:
        school_name = parts[0]
    else:
        school_name, degree_name = _split_primary_secondary(
            cleaned_entity,
            separators=(" | ", "|", " - ", ", "),
        )

    if school_name is None:
        return None

    # Try to separate degree from field if degree contains both
    if degree_name and field_of_study is None:
        degree_field_match = re.match(
            r"^((?:B\.?Sc|M\.?Sc|B\.?A|M\.?A|B\.?Eng|M\.?Eng|PhD|MBA|BSc|MSc|BA|MA|"
            r"Bachelor|Master|Doctorate|Lisans|Yüksek Lisans|Diplom)\.?)\s+(?:in\s+|of\s+)?(.+)$",
            degree_name,
            re.IGNORECASE,
        )
        if degree_field_match:
            degree_name = degree_field_match.group(1).strip()
            field_of_study = degree_field_match.group(2).strip()

    return build_cv_draft_education_entry(
        school_name=school_name,
        degree_name=degree_name,
        field_of_study=field_of_study,
        start_year=start_year,
        end_year=end_year,
    )


def _resolve_entity_year_summary(
    block: list[str],
) -> tuple[str | None, str | None, str | None]:
    year_line_index: int | None = None
    for index, line in enumerate(block):
        if _contains_year_information(line):
            year_line_index = index
            break

    if year_line_index is None:
        first_line = block[0] if block else None
        summary = " ".join(block[1:]) if len(block) > 1 else None
        return first_line, None, _clean_token(summary)

    year_line = block[year_line_index]
    cleaned_year_line = _clean_token(_remove_year_text(year_line))

    if cleaned_year_line:
        summary_lines = [
            line
            for index, line in enumerate(block)
            if index != year_line_index and line != cleaned_year_line
        ]
        summary = _clean_token(" ".join(summary_lines)) if summary_lines else None
        return cleaned_year_line, year_line, summary

    if year_line_index > 0:
        entity_line = block[year_line_index - 1]
        summary_lines = block[year_line_index + 1 :]
        summary = _clean_token(" ".join(summary_lines))
        return entity_line, year_line, summary

    return None, year_line, None


def _contains_year_information(line: str) -> bool:
    return YEAR_RANGE_RE.search(line) is not None or YEAR_TOKEN_RE.search(line) is not None


def _parse_year_range(line: str) -> tuple[int | None, int | None]:
    language = detect_supported_language(
        text=line,
        supported_languages=_RUNTIME_CONFIG.language_detection.supported_languages,
        fallback_language=_RUNTIME_CONFIG.language_detection.fallback_language,
    )
    parsed = parse_date_range(line, language)
    if parsed is not None:
        return parsed.start_year, parsed.end_year

    years = [int(year) for year in YEAR_TOKEN_RE.findall(line)]
    if not years:
        return None, None
    if len(years) == 1:
        return years[0], None
    return years[0], years[1]


def _remove_year_text(line: str) -> str:
    without_ranges = YEAR_RANGE_RE.sub("", line)
    without_years = YEAR_TOKEN_RE.sub("", without_ranges)
    without_brackets = re.sub(r"\(\s*\)", "", without_years)
    without_extra_spacing = re.sub(r"\s+", " ", without_brackets)
    return without_extra_spacing.strip(" |-–—,:;")


def _split_primary_secondary(
    line: str, *, separators: tuple[str, ...]
) -> tuple[str | None, str | None]:
    cleaned_line = _clean_token(line)
    if cleaned_line is None:
        return None, None

    for separator in separators:
        if separator in cleaned_line:
            primary, secondary = cleaned_line.split(separator, 1)
            return _clean_token(primary), _clean_token(secondary)

    return cleaned_line, None