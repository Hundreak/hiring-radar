from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from difflib import SequenceMatcher

from hiring_radar.services.cv_engine.models import SectionName

SECTION_ALIASES_BY_LANGUAGE: dict[str, dict[SectionName, tuple[str, ...]]] = {
    "en": {
        SectionName.HEADER: (
            "personal information",
            "contact information",
            "profile details",
        ),
        SectionName.SUMMARY: (
            "summary",
            "professional summary",
            "profile",
            "about",
            "about me",
            "executive summary",
        ),
        SectionName.EXPERIENCE: (
            "experience",
            "work experience",
            "professional experience",
            "employment history",
            "career history",
        ),
        SectionName.EDUCATION: (
            "education",
            "academic background",
            "academic history",
            "qualifications",
        ),
        SectionName.SKILLS: (
            "skills",
            "technical skills",
            "core skills",
            "tools",
            "skills and tools",
            "competencies",
            "tech stack",
            "techstack",
            "techstack & skills",
            "tech stack & skills",
            "techstack and skills",
            "tech stack and skills",
            "technical stack",
            "my stack",
            "stack",
            "technologies",
            "expertise",
        ),
        SectionName.LANGUAGES: (
            "languages",
            "language skills",
            "linguistic skills",
        ),
        SectionName.PROJECTS: (
            "projects",
            "selected projects",
            "project experience",
        ),
        SectionName.CERTIFICATIONS: (
            "certifications",
            "certificates",
            "licenses",
            "licenses and certifications",
        ),
        SectionName.LINKS: (
            "links",
            "online profiles",
            "profiles",
            "portfolio",
        ),
    },
    "tr": {
        SectionName.HEADER: (
            "kişisel bilgiler",
            "iletişim bilgileri",
            "profil bilgileri",
        ),
        SectionName.SUMMARY: (
            "özet",
            "profil özeti",
            "hakkımda",
            "kariyer özeti",
            "profesyonel özet",
        ),
        SectionName.EXPERIENCE: (
            "deneyim",
            "iş deneyimi",
            "profesyonel deneyim",
            "çalışma deneyimi",
            "kariyer geçmişi",
        ),
        SectionName.EDUCATION: (
            "eğitim",
            "eğitim bilgileri",
            "akademik geçmiş",
            "öğrenim durumu",
        ),
        SectionName.SKILLS: (
            "yetenekler",
            "beceriler",
            "teknik beceriler",
            "uzmanlıklar",
            "araçlar ve teknolojiler",
        ),
        SectionName.LANGUAGES: (
            "diller",
            "yabancı diller",
            "dil bilgisi",
            "dil yetkinlikleri",
        ),
        SectionName.PROJECTS: (
            "projeler",
            "seçilmiş projeler",
            "proje deneyimi",
        ),
        SectionName.CERTIFICATIONS: (
            "sertifikalar",
            "sertifika",
            "sertifikasyonlar",
            "lisanslar ve sertifikalar",
        ),
        SectionName.LINKS: (
            "bağlantılar",
            "çevrimiçi profiller",
            "portföy",
            "profiller",
        ),
    },
    "de": {
        SectionName.HEADER: (
            "persönliche daten",
            "kontaktinformationen",
            "profilinformationen",
        ),
        SectionName.SUMMARY: (
            "zusammenfassung",
            "profil",
            "über mich",
            "kurzprofil",
            "berufliches profil",
        ),
        SectionName.EXPERIENCE: (
            "berufserfahrung",
            "erfahrung",
            "arbeitserfahrung",
            "professionelle erfahrung",
            "laufbahn",
        ),
        SectionName.EDUCATION: (
            "ausbildung",
            "bildung",
            "akademischer hintergrund",
            "qualifikationen",
        ),
        SectionName.SKILLS: (
            "fähigkeiten",
            "kenntnisse",
            "technische kenntnisse",
            "kompetenzen",
            "tools und technologien",
        ),
        SectionName.LANGUAGES: (
            "sprachen",
            "sprachkenntnisse",
            "fremdsprachen",
        ),
        SectionName.PROJECTS: (
            "projekte",
            "ausgewählte projekte",
            "projekterfahrung",
        ),
        SectionName.CERTIFICATIONS: (
            "zertifikate",
            "zertifizierungen",
            "lizenzen",
            "lizenzen und zertifikate",
        ),
        SectionName.LINKS: (
            "links",
            "online profile",
            "portfolio",
            "profile",
        ),
    },
}

_WORD_SPLIT_RE = re.compile(r"[\s/&,+|·•:;()\[\]{}\\-]+")


def fold_for_matching(value: str) -> str:
    """Fold text into an accent-insensitive matching representation."""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character))



def normalize_alias_text(value: str) -> str:
    """Normalize a heading or alias for fuzzy and token matching."""
    folded = fold_for_matching(value).lower()
    collapsed = re.sub(r"[^\w\s/&,+|·•-]", " ", folded)
    collapsed = re.sub(r"\s+", " ", collapsed).strip()
    return collapsed



def tokenize_alias_text(value: str) -> tuple[str, ...]:
    """Tokenize normalized alias text into non-empty tokens."""
    normalized = normalize_alias_text(value)
    return tuple(token for token in _WORD_SPLIT_RE.split(normalized) if token)



def get_section_aliases(language: str) -> dict[SectionName, tuple[str, ...]]:
    """Return section aliases for a supported language with English fallback."""
    if language in SECTION_ALIASES_BY_LANGUAGE:
        return SECTION_ALIASES_BY_LANGUAGE[language]
    return SECTION_ALIASES_BY_LANGUAGE["en"]



def iter_all_section_aliases(language: str) -> Iterable[tuple[SectionName, str]]:
    """Yield all normalized aliases for one language."""
    for section_name, aliases in get_section_aliases(language).items():
        for alias in aliases:
            yield section_name, alias



def fuzzy_alias_ratio(candidate: str, alias: str) -> float:
    """Return a token-aware fuzzy ratio between a heading candidate and alias."""
    normalized_candidate = normalize_alias_text(candidate)
    normalized_alias = normalize_alias_text(alias)
    if not normalized_candidate or not normalized_alias:
        return 0.0

    if normalized_candidate == normalized_alias:
        return 1.0
    if normalized_alias in normalized_candidate:
        return 0.95

    candidate_tokens = set(tokenize_alias_text(normalized_candidate))
    alias_tokens = set(tokenize_alias_text(normalized_alias))
    token_overlap = 0.0
    if candidate_tokens and alias_tokens:
        token_overlap = len(candidate_tokens & alias_tokens) / max(len(alias_tokens), 1)

    sequence_ratio = SequenceMatcher(
        a=normalized_candidate,
        b=normalized_alias,
    ).ratio()
    return max(sequence_ratio, token_overlap)



def best_section_alias_match(
    candidate: str,
    language: str,
) -> tuple[SectionName | None, float, tuple[SectionName, ...]]:
    """Find the best matching section for a heading candidate.

    Returns the primary section, its match ratio, and any composite section hints.
    """
    normalized_candidate = normalize_alias_text(candidate)
    best_section: SectionName | None = None
    best_ratio = 0.0
    composite_matches: list[SectionName] = []

    for section_name, alias in iter_all_section_aliases(language):
        ratio = fuzzy_alias_ratio(normalized_candidate, alias)
        if ratio >= 0.72 and section_name not in composite_matches:
            composite_matches.append(section_name)
        if ratio > best_ratio:
            best_ratio = ratio
            best_section = section_name

    composite_sections = tuple(composite_matches)
    return best_section, best_ratio, composite_sections
