from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.language.detection import detect_supported_language
from hiring_radar.services.cv_engine.parsing.dates import parse_date_range
from hiring_radar.services.cv_engine.parsing.experience_lines import (
    parse_experience_block as parse_engine_experience_block,
)
from hiring_radar.services.cv_engine.segmentation.section_detection import (
    HybridSectionDetectionStrategy,
)
from hiring_radar.services.cv_extraction import normalize_extracted_text
from hiring_radar.services.cv_profile_draft import (
    CvProfileDraft,
    build_cv_draft_certification_entry,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
)

HEURISTIC_CV_PARSER_VERSION = "heuristic-v0"
_RUNTIME_CONFIG = ParserRuntimeConfig()
_SECTION_DETECTION_STRATEGY = HybridSectionDetectionStrategy()


# Words that commonly start a split role title (first part of "Senior Software\nEngineer")
# Used to gate the split-role-line merge in _prepare_cv_text_for_parsing.
ROLE_QUALIFIER_WORDS = frozenset(
    {
        "senior", "junior", "lead", "principal", "staff", "head", "chief",
        "associate", "assistant", "executive", "vp", "director",
        "full-stack", "full stack", "back-end", "front-end",
        "backend", "frontend", "full", "data", "machine", "cloud",
        "site", "platform", "software", "hardware", "mobile", "web",
        "devops", "ml", "ai", "embedded", "network", "security",
        "kıdemli", "uzman", "baş",  # Turkish
        "leitender",  # German
    }
)

ROLE_HINT_KEYWORDS = frozenset(
    {
        "engineer",
        "developer",
        "analyst",
        "manager",
        "coordinator",
        "co-ordinator",
        "scientist",
        "architect",
        "assistant",
        "consultant",
        "specialist",
        "lead",
        "administrator",
        "designer",
        "intern",
        "technician",
        "researcher",
        "mühendis",
        "muhendis",
        "miihendis",  # common OCR misspelling for Turkish Mühendis
        "mühendisi",
        "muhendisi",
        "geliştirici",
        "analist",
        "uzman",
        "yönetici",
        "koordinatör",
        "koordinator",
        "koordinatörü",
        "koordinatoru",
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
        "azerbaijani",
        "uzbek",
        "kazakh",
        "ukrainian",
        "polish",
        "swedish",
        "norwegian",
        "danish",
        "finnish",
        "hungarian",
        "czech",
        "slovak",
        "romanian",
        "bulgarian",
        "greek",
        "hebrew",
        "persian",
        "farsi",
        "hindi",
        "urdu",
        "bengali",
        "thai",
        "vietnamese",
        "indonesian",
        "malay",
        "tagalog",
        "swahili",
        "yoruba",
    }
)

# Known technology/framework names that must never be stored as spoken languages.
# This blocklist is applied even when they appear inside a "languages" section,
# because CVs commonly use section headers like "Languages" to list programming
# languages rather than spoken ones, and parser artefacts can cross-pollute.
_TECH_NAMES_NOT_LANGUAGES: frozenset[str] = frozenset(
    {
        "python",
        "django",
        "flask",
        "fastapi",
        "javascript",
        "js",
        "typescript",
        "ts",
        "node",
        "nodejs",
        "react",
        "reactjs",
        "react native",
        "vue",
        "vuejs",
        "angular",
        "svelte",
        "jquery",
        "bootstrap",
        "tailwind",
        "css",
        "html",
        "sass",
        "scss",
        "java",
        "kotlin",
        "swift",
        "go",
        "golang",
        "rust",
        "ruby",
        "rails",
        "php",
        "laravel",
        "c",
        "c++",
        "c#",
        "dotnet",
        ".net",
        "scala",
        "elixir",
        "haskell",
        "clojure",
        "erlang",
        "r",
        "matlab",
        "lua",
        "perl",
        "bash",
        "shell",
        "powershell",
        "postgresql",
        "postgres",
        "mysql",
        "sqlite",
        "mongodb",
        "redis",
        "elasticsearch",
        "cassandra",
        "dynamodb",
        "oracle",
        "mssql",
        "aws",
        "azure",
        "gcp",
        "heroku",
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "jenkins",
        "git",
        "github",
        "gitlab",
        "bitbucket",
        "linux",
        "ubuntu",
        "centos",
        "nginx",
        "apache",
        "celery",
        "rabbitmq",
        "kafka",
        "graphql",
        "rest",
        "grpc",
        "figma",
        "jira",
        "confluence",
        "trello",
        "slack",
        "postman",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "scikit",
        "sklearn",
        "keras",
        "opencv",
        "techstack",
        "techstack & skills",
        "tech stack",
        "tech stack & skills",
        "skills",
        "technologies",
        "frameworks",
        "libraries",
        "tools",
        "digitalocean",
        "vercel",
        "netlify",
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
        "kolej",
        "koleji",
        "institute",
        "institut",
        "school",
        "faculty",
        "academy",
        "lycee",
        "lycée",
        "high school",
        "lise",
        "lisesi",
        "okul",
        "okulu",
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
            "about me",
            "objective",
            "career summary",
            "career objective",
            "personal profile",
            "professional profile",
            "career profile",
            "bio",
            "biography",
            "intro",
            "introduction",
            "özet",
            "hakkımda",
            "profil",
            "profil özeti",
            "kariyer özeti",
            "profesyonel özet",
            "zusammenfassung",
            "profilzusammenfassung",
            "kurzprofil",
            "über mich",
            "berufliches profil",
        }
    ),
    "skills": frozenset(
        {
            "skills",
            "technical skills",
            "core skills",
            "tech stack",
            "techstack",
            "techstack & skills",
            "tech stack & skills",
            "techstack and skills",
            "tech stack and skills",
            "technologies",
            "competencies",
            "expertise",
            "key skills",
            "hard skills",
            "soft skills",
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
            "libraries & frameworks",
            "tools",
            "tech skills",
            "it skills",
            "skills summary",
            "skill set",
            "skill highlights",
            "technical stack",
            "my stack",
            "stack",
            "beceriler",
            "yetenekler",
            "teknik beceriler",
            "yetkinlikler",
            "yetenek",
            "uzmanlık alanları",
            "uzmanlıklar",
            "araçlar ve teknolojiler",
            "teknik yetkinlikler",
            "teknolojiler",
            "programlama dilleri",
            "fähigkeiten",
            "kenntnisse",
            "technologien",
            "kompetenzen",
            "schlüsselkompetenzen",
            "technische fähigkeiten",
            "technische kenntnisse",
            "werkzeuge und technologien",
            "programmiersprachen",
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
            "relevant employment",
            "other employment",
            "relevant experience",
            "professional background",
            "positions held",
            "career",
            "professional positions",
            "roles",
            "iş deneyimi",
            "deneyim",
            "tecrübe",
            "profesyonel deneyim",
            "iş geçmişi",
            "çalışma deneyimi",
            "kariyer geçmişi",
            "berufserfahrung",
            "arbeitserfahrung",
            "beruflicher werdegang",
            "berufliche laufbahn",
            "bisherige positionen",
            "erfahrung",
            "professionelle erfahrung",
            "laufbahn",
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
            "studies",
            "university education",
            "eğitim",
            "öğrenim",
            "öğrenim durumu",
            "akademik geçmiş",
            "eğitim bilgileri",
            "eğitim durumu",
            "sertifikalar",
            "ausbildung",
            "bildung",
            "akademischer hintergrund",
            "qualifikationen",
            "studium",
            "abschlüsse",
            "schulbildung",
        }
    ),
    "languages": frozenset(
        {
            "languages",
            "language",
            "language skills",
            "language proficiency",
            "linguistic skills",
            "spoken languages",
            "diller",
            "dil",
            "yabancı diller",
            "dil bilgisi",
            "dil yetkinlikleri",
            "sprachen",
            "sprachkenntnisse",
            "fremdsprachen",
        }
    ),
    "contact": frozenset(
        {
            "contact",
            "contact info",
            "contact information",
            "personal info",
            "personal information",
            "personal details",
            "iletişim",
            "iletişim bilgileri",
            "kontakt",
            "kontaktdaten",
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
            "desired job",
            "looking for",
            "position desired",
            "hedef rol",
            "hedef roller",
            "hedef pozisyon",
            "hedef pozisyonlar",
            "aradığım pozisyon",
            "kariyer hedefim",
            "zielposition",
            "zielrolle",
            "gewünschte position",
            "gesuchte position",
        }
    ),
    "preferences": frozenset(
        {
            "preferences",
            "work preferences",
            "location preferences",
            "remote preference",
            "work authorization",
            "availability",
            "tercihler",
            "çalışma tercihleri",
            "lokasyon tercihleri",
            "arbeitspräferenzen",
            "standortpräferenzen",
            "verfügbarkeit",
        }
    ),
    "projects": frozenset(
        {
            "projects",
            "selected projects",
            "personal projects",
            "side projects",
            "open source",
            "open source contributions",
            "projeler",
            "seçilmiş projeler",
            "kişisel projeler",
            "proje deneyimi",
            "projekte",
            "ausgewählte projekte",
            "projekterfahrung",
        }
    ),
    "ignore": frozenset(
        {
            "interests",
            "interests & achievements",
            "interests and achievements",
            "achievements",
            "interests/achievements",
            "references",
            "reference",
            "referees",
        }
    ),
    "certifications": frozenset(
        {
            "certificates",
            "licenses",
            "licenses and certifications",
            "sertifika",
            "sertifikasyonlar",
            "lisanslar ve sertifikalar",
            "zertifikate",
            "zertifizierungen",
            "lizenzen",
            "lizenzen und zertifikate",
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
PHONE_RE = re.compile(r"\+?[\d(][\d \t().-]{6,}\d")
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

    cleaned_text = _repair_common_ocr_artifacts(cleaned_text)
    prepared_text = _prepare_cv_text_for_parsing(cleaned_text)

    preamble_lines, sections = _segment_cv_sections(prepared_text)

    # Contact info extraction from both the header preamble and explicit
    # Personal/Contact sections. Some one-page CV templates put email/phone
    # under a "PERSONAL INFORMATION" header rather than beside the name.
    contact_lines = [*preamble_lines, *sections.get("contact", [])]
    full_name = _extract_full_name(preamble_lines)
    email = _extract_email(contact_lines) or _extract_email_from_text(prepared_text)
    phone = _extract_phone(contact_lines) or _extract_phone_from_text(prepared_text)
    linkedin_url = _extract_linkedin_url(prepared_text)
    github_url = _extract_github_url(prepared_text)

    headline = _extract_headline(preamble_lines)
    summary = _extract_summary(preamble_lines, sections, headline)
    skills = _extract_skills(sections)
    if not skills:
        skills = _extract_fallback_skills(preamble_lines)

    preferred_locations = _extract_preferred_locations(preamble_lines, sections)
    remote_preference = _extract_remote_preference(prepared_text, sections)

    language_entries = _extract_language_entries(sections)
    if not language_entries:
        language_entries = _extract_fallback_language_entries(preamble_lines)

    experience_entries = _extract_experience_entries(sections)
    if not experience_entries:
        experience_entries = _extract_fallback_experience_entries(preamble_lines)

    if _headline_should_fall_back_to_current_role(headline, full_name):
        headline = (
            _extract_headline_from_summary(summary)
            or _headline_from_experience_entries(experience_entries)
        )

    target_roles = _extract_target_roles(sections, headline)

    education_entries = _extract_education_entries(sections)
    if not education_entries:
        education_entries = _extract_fallback_education_entries(preamble_lines)

    certification_entries = _extract_certification_entries(sections)

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
        certification_entries=certification_entries,
    )



def _repair_common_ocr_artifacts(text: str) -> str:
    """Repair conservative OCR artefacts before field parsing.

    This is not a general spell-checker.  Only high-confidence replacements
    observed in OCR output are applied, mostly Turkish characters and percent
    signs that Tesseract commonly loses in image CVs.
    """
    replacements = (
        ("Kidemli Miihendis", "Kıdemli Mühendis"),
        ("Kidemli Mühendis", "Kıdemli Mühendis"),
        ("Kıdemli Miihendis", "Kıdemli Mühendis"),
        ("Miihendisliği", "Mühendisliği"),
        ("Miihendisi", "Mühendisi"),
        ("Miihendis", "Mühendis"),
        ("miihendisliği", "mühendisliği"),
        ("miihendisi", "mühendisi"),
        ("miihendis", "mühendis"),
        ("kavramsallastırmadan", "kavramsallaştırmadan"),
        ("kavramsallastirmadan", "kavramsallaştırmadan"),
        ("karmasık", "karmaşık"),
        ("Atatiirk", "Atatürk"),
        ("Bulvan", "Bulvarı"),
        ("Balikesir", "Balıkesir"),
    )
    repaired = text
    for source, target in replacements:
        repaired = repaired.replace(source, target)

    # Tesseract can read the @ sign as © or separate it with spaces in
    # coloured e-mail links. Repair only when both sides form a valid local
    # part and domain, so normal copyright symbols are left untouched.
    repaired = re.sub(
        r"\b([\w.+-]{2,})\s*(?:©|@)\s*([\w.-]+\.[A-Za-z]{2,})\b",
        r"\1@\2",
        repaired,
    )
    # OCR sometimes inserts a stray space inside a year: "201 1".
    repaired = re.sub(r"\b((?:19|20)\d)\s+(\d)\b", r"\1\2", repaired)

    # OCR often turns percentage signs in this template into digits: "%30"
    # becomes "9630"/"9650", and "%20 oranında" becomes
    # "620 oranında". Only fix these in percentage-context phrases.
    repaired = re.sub(r"(?<!\d)96(\d{2})(?!\d)(?=\s+artış)", r"%\1", repaired)
    repaired = re.sub(r"(?<!\d)620(?!\d)(?=\s+oranında)", "%20", repaired)
    return repaired


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
                    elif (
                        # Merge OCR-split role titles like "Senior Software" + "Engineer"
                        # Only merge when current_line starts with a known role qualifier
                        # word — this prevents merging personal names ("Alice Example")
                        # with the following headline ("Staff Platform Engineer").
                        _detect_section_name(current_line) is None
                        and current_line.split()[0].lower() in ROLE_QUALIFIER_WORDS
                        and _looks_like_role_line(combined_line)
                        and not _looks_like_role_line(current_line)
                        and len(current_line) < 40
                        and len(next_line) < 40
                        and not _looks_like_contact_line(current_line)
                        and not _looks_like_contact_line(next_line)
                        and not _contains_year_information(current_line)
                        and not _contains_year_information(next_line)
                    ):
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
            candidate_section, payload = inline_section
            # When already inside the skills section, common skill-category
            # sub-headers ("Languages:", "Frameworks:", "Tools:", etc.) should
            # stay inside skills rather than switch to the spoken-languages
            # section. Only treat the sub-header as a real section break when
            # the candidate differs from a skill-category sub-header.
            if (
                current_section == "skills"
                and _is_skill_category_subheader(line)
            ):
                sections.setdefault("skills", []).append(line)
                continue
            current_section = candidate_section
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

SKILL_CATEGORY_SUBHEADER_KEYS = frozenset(
    {
        "languages",
        "programming languages",
        "language",
        "frameworks",
        "framework",
        "libraries",
        "library",
        "tools",
        "tooling",
        "technologies",
        "technology",
        "tech",
        "tech stack",
        "stack",
        "platforms",
        "platform",
        "databases",
        "database",
        "cloud",
        "cloud services",
        "devops",
        "infrastructure",
        "backend",
        "frontend",
        "back end",
        "front end",
        "backend technologies",
        "frontend technologies",
        "mobile",
        "testing",
        "concepts",
        "methodologies",
        "protocols",
        "version control",
        "ide",
        "ides",
        "os",
        "operating systems",
    }
)


def _is_skill_category_subheader(line: str) -> bool:
    """Return True when a line looks like a skills-section sub-header.

    Inside a Technical Skills block, lines like ``Languages: Python, JavaScript``
    must be treated as a skill category, not as a section switch to the
    spoken-languages section.
    """
    stripped_line = re.sub(r"^[•·\-\s]+", "", line).strip()
    separator_match = re.search(r"\s[:\-–—]\s|\:\s*", stripped_line)
    if separator_match is None:
        return False
    header_candidate = stripped_line[: separator_match.start()].strip()
    payload_candidate = stripped_line[separator_match.end() :].strip()
    if not payload_candidate:
        return False
    return _alias_key(header_candidate) in SKILL_CATEGORY_SUBHEADER_KEYS


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
    # Strip leading non-alphanumeric characters (OCR icon decorators like @, ©, #, &, ★, etc.)
    simplified = re.sub(r"^[^\w\s]+\s*", "", simplified)
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
    normalized_line = _alias_key(line)
    if not normalized_line:
        return False

    for keyword in ROLE_HINT_KEYWORDS:
        normalized_keyword = _alias_key(keyword)
        if not normalized_keyword:
            continue
        if re.search(rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)", normalized_line):
            return True
    return False


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


def _headline_should_fall_back_to_current_role(
    headline: str | None, full_name: str | None
) -> bool:
    if headline is None:
        return True
    if full_name is not None and _alias_key(headline) == _alias_key(full_name):
        return True
    return not _looks_like_role_line(headline)


def _headline_from_experience_entries(experience_entries: list) -> str | None:
    for entry in experience_entries:
        title = getattr(entry, "title", None)
        cleaned = _clean_token(title)
        if cleaned and _looks_like_role_line(cleaned):
            return cleaned
    return None


def _extract_full_name(preamble_lines: list[str]) -> str | None:
    """Extract the candidate's full name from the preamble.

    The name is typically the first non-contact, non-role, non-skill line.
    Handles two-line name layouts (e.g. "OLIVIA\nCAMPOS") by merging the
    immediately following short alphabetic line into the name when both
    look like name tokens.
    """
    name_parts: list[str] = []
    for line in preamble_lines:
        if not line:
            if name_parts:
                break
            continue
        if _looks_like_contact_line(line):
            if name_parts:
                break
            continue
        if _detect_section_name(line) is not None:
            if name_parts:
                break
            continue
        if _looks_like_skill_line(line):
            if name_parts:
                break
            continue
        if _looks_like_language_line(line):
            if name_parts:
                break
            continue
        if _contains_year_information(line):
            if name_parts:
                break
            continue

        cleaned = _clean_token(line)
        if cleaned is None:
            if name_parts:
                break
            continue

        if _looks_like_role_line(cleaned):
            if name_parts:
                break
            return None

        words = cleaned.split()
        if not (1 <= len(words) <= 5 and len(cleaned) <= 60):
            if name_parts:
                break
            return None
        if not _looks_like_name_token(cleaned):
            if name_parts:
                break
            return None

        name_parts.append(cleaned)
        joined = " ".join(name_parts)
        # Stop when we already have enough words to form a plausible full name
        # (first + last, first + middle + last, etc.), so that role/contact
        # headers below the name are not swallowed.
        if len(joined.split()) >= 2:
            return joined

    if not name_parts:
        return None
    return " ".join(name_parts)


def _looks_like_name_token(value: str) -> bool:
    """Return True when the line looks like a plausible personal-name token."""
    stripped = value.strip()
    if not stripped:
        return False
    # Name tokens should be mostly letters/spaces/hyphens/apostrophes.
    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿÇĞİÖŞÜçğıöşü'\- .]+", stripped):
        return False
    # Exclude tokens that contain digits or URLs.
    if any(ch.isdigit() for ch in stripped):
        return False
    return True


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
            if _looks_like_phone_false_positive(candidate):
                continue
            return _normalize_phone_number(candidate)
    return None


def _extract_email_from_text(text: str) -> str | None:
    match = EMAIL_RE.search(text or "")
    return match.group().strip() if match else None


def _extract_phone_from_text(text: str) -> str | None:
    for match in PHONE_RE.finditer(text or ""):
        candidate = match.group().strip()
        if _looks_like_phone_false_positive(candidate):
            continue
        return _normalize_phone_number(candidate)
    return None


def _looks_like_phone_false_positive(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if YEAR_RANGE_RE.fullmatch(stripped) or YEAR_TOKEN_RE.fullmatch(stripped):
        return True
    digits = re.sub(r"\D", "", stripped)
    years = YEAR_TOKEN_RE.findall(stripped)
    has_phone_marker = "+" in stripped or "(" in stripped or ")" in stripped
    if len(years) >= 2 and len(digits) <= 8 and not has_phone_marker:
        return True
    return False


def _normalize_phone_number(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    cleaned = cleaned.strip(" ,;|·•")
    # Preserve "(123) 456-7890" style readability: keep one space after ")".
    cleaned = re.sub(r"\s*\(\s*", "(", cleaned)
    cleaned = re.sub(r"\s*\)\s*", ") ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Collapse spaces around other connectors while keeping the ") " spacing.
    cleaned = re.sub(r"\s*([\-./])\s*", r"\1", cleaned)

    turkish_local = _format_turkish_local_phone_number(cleaned)
    if turkish_local is not None:
        return turkish_local

    return cleaned


def _format_turkish_local_phone_number(value: str) -> str | None:
    """Format compact Turkish local phone numbers without guessing digits.

    OCR often collapses ``0212 123 24 25`` into ``02121232425``.  We can
    safely restore the grouping for Turkish local numbers, but we must not
    repair misread digits here; that belongs to review/AI-polish with user
    confirmation.
    """
    stripped = value.strip()
    if stripped.startswith("+"):
        return None

    digits = re.sub(r"\D", "", stripped)
    if not (len(digits) == 11 and digits.startswith("0")):
        return None

    # Turkish domestic display: area/operator code + subscriber chunks.
    # Examples: 0212 123 24 25, 0555 123 45 67.
    return f"{digits[:4]} {digits[4:7]} {digits[7:9]} {digits[9:]}"


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
        candidate_lines = summary_lines[:6]
        if (
            headline is not None
            and candidate_lines
            and _alias_key(candidate_lines[0]) == _alias_key(headline)
        ):
            candidate_lines = candidate_lines[1:]
        return _clean_token(" ".join(candidate_lines))

    # Many image/OCR CVs put the summary directly under the name/headline
    # without a dedicated ``Summary`` heading.  Returning the first long line
    # truncates multi-line summaries, so collect the first contiguous prose
    # paragraph after the short header fields.
    candidate_paragraphs: list[str] = []
    current_lines: list[str] = []
    started = False

    for line in preamble_lines:
        if not line:
            if current_lines:
                candidate_paragraphs.append(" ".join(current_lines))
                current_lines = []
            started = False
            continue

        if _looks_like_contact_line(line) or _detect_section_name(line) is not None:
            if current_lines:
                candidate_paragraphs.append(" ".join(current_lines))
                current_lines = []
            started = False
            continue
        if headline is not None and _alias_key(line) == _alias_key(headline):
            continue
        if not started and (
            _looks_like_skill_line(line)
            or _looks_like_language_line(line)
            or _contains_year_information(line)
        ):
            continue
        if started and (
            _looks_like_language_line(line) or _contains_year_information(line)
        ):
            break
        if started and _looks_like_skill_line(line):
            # A summary continuation can look like a comma-separated skill list
            # to the generic detector (e.g. "time, 5-10% below budget, ...").
            # Keep prose-like sentence continuations, but stop before compact
            # sectionless skill rows such as "Python | FastAPI | SQL".
            if len(line) < 45 or "." not in line:
                break

        # Skip short header/name fragments until real prose starts.
        if not started and len(line) < 50:
            continue

        started = True
        current_lines.append(line)

    if current_lines:
        candidate_paragraphs.append(" ".join(current_lines))

    cleaned_paragraphs = [_clean_token(paragraph) for paragraph in candidate_paragraphs]
    for cleaned in cleaned_paragraphs:
        if cleaned is not None and len(cleaned) >= 80:
            return cleaned
    for cleaned in cleaned_paragraphs:
        if cleaned is not None and len(cleaned) >= 50:
            return cleaned

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

    for line in _merge_wrapped_skill_lines(sections.get("skills", [])):
        if not line:
            continue

        for base_token in _iter_skill_tokens_from_line(line):
            lower = base_token.casefold()
            if lower in seen_lower:
                continue
            seen_lower.add(lower)
            skills.append(base_token)

    return skills


def _merge_wrapped_skill_lines(lines: list[str]) -> list[str]:
    """Join visual wraps inside a skills section before tokenization.

    Sidebar CV templates often wrap a single skill across two OCR lines, e.g.
    ``Engineering Product Data`` + ``Management Software (EPDMS)``.  Treating
    every physical line as an independent skill loses meaning, while blindly
    merging all short lines would combine separate skills such as ``3D CAD``
    and ``Pro-E CREO CAD``.  This helper only joins lines that carry explicit
    wrap cues or look like continuation fragments of a longer phrase.
    """
    merged: list[str] = []
    buffer: str | None = None

    for raw_line in lines:
        raw_stripped = (raw_line or "").strip()
        line = _clean_token(raw_line)
        if line is None:
            if buffer is not None:
                merged.append(buffer)
                buffer = None
            continue
        detected_section = _detect_section_name(line)
        if detected_section is not None:
            if buffer is not None:
                merged.append(buffer)
                buffer = None
            if detected_section == "ignore":
                break
            continue

        if _looks_like_skill_category_header_only(raw_stripped):
            if buffer is not None:
                merged.append(buffer)
            buffer = f"{line.rstrip(':–—-')} :"
            continue

        if buffer is None:
            buffer = line
            continue

        if (
            buffer.endswith(":")
            or _skill_buffer_accepts_category_continuation(buffer, line)
            or _should_join_wrapped_skill_line(buffer, line)
        ):
            previous_last = buffer.split()[-1].casefold().strip(".,;:()") if buffer.split() else ""
            joiner = ", " if previous_last in {"materials"} else " "
            buffer = f"{buffer}{joiner}{line}"
            continue

        merged.append(buffer)
        buffer = line

    if buffer is not None:
        merged.append(buffer)

    return merged


def _skill_buffer_accepts_category_continuation(previous: str, current: str) -> bool:
    if " : " not in previous:
        return False
    category, _payload = previous.split(" : ", 1)
    if not _looks_like_skill_category_header(category):
        return False
    if _looks_like_skill_category_header_only(current):
        return False
    if len(previous) + len(current) > 280:
        return False
    # Category payloads in PDFs often wrap every visual line. Keep collecting
    # until the next category header/section.
    return True


def _should_join_wrapped_skill_line(previous: str, current: str) -> bool:
    if not previous or not current:
        return False
    if _looks_like_contact_line(previous) or _looks_like_contact_line(current):
        return False
    if _contains_year_information(previous) or _contains_year_information(current):
        return False
    if _SKILL_CATEGORY_RE.match(previous):
        return False
    if previous.endswith((",", "&", "/", "-", "–", "—")):
        return True

    previous_words = previous.split()
    current_words = current.split()
    if len(previous_words) < 3 or len(current_words) < 2:
        return False
    if len(previous) + len(current) > 90:
        return False

    previous_last = previous_words[-1].casefold().strip(".,;:()")
    current_first = current_words[0].casefold().strip(".,;:()")

    continuation_starters = {
        "and",
        "or",
        "with",
        "for",
        "of",
        "in",
        "management",
        "clients",
        "equipment",
        "software",
    }
    continuation_enders = {
        "data",
        "non-technical",
        "materials",
        "product",
        "cost",
        "estimates",
    }

    if current_first in continuation_starters:
        return True
    if previous_last in continuation_enders:
        return True

    return False


_SKILL_CATEGORY_RE = re.compile(
    r"^(?P<category>[A-Za-zÇĞİÖŞÜçğıöşüÄÖÜäöüß0-9 &/+\-]+?)\s*[:–—]\s*(?P<payload>.+)$"
)


def _iter_skill_tokens_from_line(line: str):
    """Yield cleaned skill tokens from a single skills-section line."""
    payload = line
    category: str | None = None
    match = _SKILL_CATEGORY_RE.match(line)
    if match:
        category_candidate = match.group("category").strip()
        payload_candidate = match.group("payload").strip()
        if payload_candidate and _looks_like_skill_category_header(category_candidate):
            category = category_candidate
            payload = payload_candidate

    if category is not None:
        yield from _iter_skill_tokens_from_category_payload(category, payload)
        return

    for item in _split_top_level_skill_items(payload):
        paren_match = re.match(
            r"^(?P<head>[^()]+?)\s*\((?P<body>[^()]+)\)\s*$",
            item,
        )
        if paren_match:
            head = paren_match.group("head").strip()
            body = paren_match.group("body").strip()
            if head and _parenthetical_is_acronym_for_head(head, body):
                yield from _emit_skill_token(f"{head} ({body})")
                continue
            if head:
                yield from _emit_skill_token(head)
            if _parenthetical_looks_like_skill_list(body):
                for sub in re.split(r"[,/;]", body):
                    yield from _emit_skill_token(sub)
            continue
        yield from _emit_skill_token(item)


def _iter_skill_tokens_from_category_payload(category: str, payload: str):
    category_key = _alias_key(category)
    cleaned_payload = _clean_token(payload)
    if cleaned_payload is None:
        return

    if category_key == "technical":
        yield from _iter_technical_skill_tokens(cleaned_payload)
        return

    if category_key == "presentation":
        for token in ("reports", "presentations"):
            yield from _emit_skill_token(token)
        return

    if category_key in {"analysis & evaluation", "analysis and evaluation", "analysis"}:
        for token in ("data assessment", "solution formulation"):
            yield from _emit_skill_token(token)
        return

    if category_key in {"organisational", "organizational", "organisation", "organization"}:
        for token in ("time management", "task prioritisation"):
            yield from _emit_skill_token(token)
        return

    if category_key == "communication":
        for token in ("team working", "leadership", "communication"):
            yield from _emit_skill_token(token)
        return

    yield from _iter_skill_tokens_from_line(cleaned_payload)


def _iter_technical_skill_tokens(payload: str):
    # Keep compact, source-grounded technical names from prose-like grouped lines.
    known_patterns = (
        r"(?<!\w)C\+\+(?!\w)",
        r"(?<![A-Za-z0-9+])C(?![A-Za-z0-9+])",
        r"\bAccess\b",
        r"\bExcel\b",
        r"\bWord\b",
        r"\bPowerPoint\b",
        r"\bMathematica\b",
        r"\bMatamatica\b",
        r"\bElectronics Workbench\b",
        r"\bHTML\b",
        r"\bVHDL\b",
        r"\bassembly code\b",
        r"\bLINUX\b",
        r"\bLinux\b",
    )
    seen: set[str] = set()
    for pattern in known_patterns:
        for match in re.finditer(pattern, payload, flags=re.IGNORECASE):
            token = match.group(0)
            if token.casefold() == "linux":
                token = "Linux"
            elif token.casefold() == "matamatica":
                token = "Mathematica"
            key = token.casefold()
            if key in seen:
                continue
            seen.add(key)
            yield from _emit_skill_token(token)



def _split_top_level_skill_items(payload: str) -> list[str]:
    """Split a skills payload at top-level separators, respecting parentheses.

    Commas are ambiguous in human-readable skills: ``Python, SQL, FastAPI`` is
    a list, but ``Provide Cost Estimates for Materials, Equipment, or Labor``
    is one skill.  We split on comma only when the resulting chunks look like a
    compact skill list.
    """
    items: list[str] = []
    buffer: list[str] = []
    depth = 0
    for character in payload:
        if character == "(":
            depth += 1
            buffer.append(character)
            continue
        if character == ")":
            depth = max(0, depth - 1)
            buffer.append(character)
            continue
        if depth == 0 and character in "|;/•·\n":
            chunk = "".join(buffer).strip()
            if chunk:
                items.extend(_split_skill_item_on_safe_commas(chunk))
            buffer = []
            continue
        buffer.append(character)
    tail = "".join(buffer).strip()
    if tail:
        items.extend(_split_skill_item_on_safe_commas(tail))

    # Additionally split on runs of 2+ spaces (common in OCR multi-column text).
    expanded: list[str] = []
    for item in items:
        expanded.extend(part for part in re.split(r"\s{2,}", item) if part.strip())
    return expanded


def _split_skill_item_on_safe_commas(item: str) -> list[str]:
    if "," not in item:
        return [item]

    parts: list[str] = []
    buffer: list[str] = []
    depth = 0
    for character in item:
        if character == "(":
            depth += 1
            buffer.append(character)
            continue
        if character == ")":
            depth = max(0, depth - 1)
            buffer.append(character)
            continue
        if depth == 0 and character == ",":
            chunk = "".join(buffer).strip()
            if chunk:
                parts.append(chunk)
            buffer = []
            continue
        buffer.append(character)
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)

    if len(parts) <= 1:
        return [item]

    if _comma_parts_look_like_compact_skill_list(parts):
        return parts
    return [item]


def _comma_parts_look_like_compact_skill_list(parts: list[str]) -> bool:
    for part in parts:
        cleaned = _clean_token(part)
        if cleaned is None:
            return False
        normalized = _alias_key(cleaned)
        if normalized.startswith(("and ", "or ")):
            return False
        if len(cleaned) > 30:
            return False
        if len(cleaned.split()) > 4:
            return False
    return True


def _parenthetical_is_acronym_for_head(head: str, body: str) -> bool:
    acronym = re.sub(r"[^A-Za-z0-9]", "", body).upper()
    if not (2 <= len(acronym) <= 10) or acronym != body.strip().upper():
        return False
    head_words = [word for word in re.split(r"\s+", head.strip()) if word]
    if len(head_words) < 2:
        return False
    initials = "".join(word[0].upper() for word in head_words if word[:1].isalpha())
    return bool(initials and acronym == initials)


def _parenthetical_looks_like_skill_list(body: str) -> bool:
    """Return True when a parenthetical body looks like sub-skills, not prose.

    ``(Django)``, ``(Redshift, S3)``, ``(3.11+)`` — accept short tokens;
    ``(3.11+)`` is a version hint and should not be emitted as a skill,
    so restrict to alphanumeric-ish tokens.
    """
    stripped = body.strip()
    if not stripped:
        return False
    if re.fullmatch(r"[\d.+\-\s]+", stripped):
        return False
    tokens = [token.strip() for token in re.split(r"[,/;]", stripped) if token.strip()]
    if not tokens:
        return False
    for token in tokens:
        if len(token) > 30:
            return False
        if not re.fullmatch(r"[A-Za-z0-9 .+\-/&_]+", token):
            return False
    return True


def _emit_skill_token(token: str):
    cleaned = _clean_token(token)
    if cleaned is None:
        return
    # Strip trailing parenthetical version hints like "Python (3.11+)" when
    # the parenthetical body is pure metadata, not sub-skills.
    base = re.sub(r"\s*\([\d.+\-\s]+\)\s*$", "", cleaned).strip()
    if not base:
        return
    base = base.strip(" -·•")
    if not base:
        return
    normalized_base = _alias_key(base)
    if re.fullmatch(r"[0o]+", normalized_base) or re.fullmatch(r"\d{2,}", normalized_base):
        return
    if len(base) == 1 and normalized_base not in SINGLE_CHARACTER_SKILL_TOKENS:
        return
    if len(base) > 90:
        return
    yield base


_SKILL_CATEGORY_HEADER_KEYWORDS = frozenset(
    {
        "backend",
        "frontend",
        "full stack",
        "fullstack",
        "databases",
        "database",
        "languages",
        "programming languages",
        "frameworks",
        "frameworks & tools",
        "frameworks and tools",
        "libraries",
        "libraries & frameworks",
        "tools",
        "tools & technologies",
        "devops",
        "cloud",
        "infrastructure",
        "infra",
        "data",
        "data & ml",
        "ml",
        "ai",
        "testing",
        "qa",
        "methodologies",
        "methodology",
        "soft skills",
        "hard skills",
        "skills",
        "technical",
        "technical skills",
        "other",
        "general",
        "arka uç",
        "ön uç",
        "veritabanları",
        "diller",
        "araçlar",
        "teknolojiler",
        "çerçeveler",
        "backend-technologien",
        "frontend-technologien",
        "datenbanken",
        "sprachen",
        "werkzeuge",
    }
)


def _looks_like_skill_category_header(value: str) -> bool:
    normalized = _alias_key(value)
    if not normalized:
        return False
    if normalized in _SKILL_CATEGORY_HEADER_KEYWORDS:
        return True
    if len(normalized.split()) > 4:
        return False
    # Short, alphabetic heading with no digits is likely a category label.
    if any(ch.isdigit() for ch in normalized):
        return False
    return len(normalized) <= 30


def _looks_like_skill_category_header_only(value: str) -> bool:
    stripped = (value or "").strip()
    if not stripped.endswith((":", "–", "—")):
        return False
    header = stripped.rstrip(":–—-").strip()
    if not header:
        return False
    return _looks_like_skill_category_header(header)


def _extract_fallback_skills(preamble_lines: list[str]) -> list[str]:
    skills: list[str] = []
    seen: set[str] = set()

    for line in preamble_lines:
        if not _looks_like_skill_line(line):
            continue

        for base_token in _iter_skill_tokens_from_line(line):
            key = base_token.casefold()
            if key in seen:
                continue
            seen.add(key)
            skills.append(base_token)

    return skills


def _extract_headline_from_summary(summary: str | None) -> str | None:
    cleaned = _clean_token(summary)
    if cleaned is None:
        return None

    # Common profile opening: "Professional qualified Electrical Engineer...".
    # Extract only the compact role noun phrase, not the whole sentence.
    patterns = (
        r"\b(?:professional(?:ly)?\s+qualified|qualified|experienced|skilled|results[- ]driven|detail[- ]oriented)\s+([A-Z][A-Za-z /&+-]{2,60}?\b(?:Engineer|Developer|Manager|Coordinator|Analyst|Specialist|Consultant|Technician|Architect|Designer|Researcher))\b",
        r"\b([A-Z][A-Za-z /&+-]{2,60}?\b(?:Engineer|Developer|Manager|Coordinator|Analyst|Specialist|Consultant|Technician|Architect|Designer|Researcher))\b",
    )
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match is None:
            continue
        role = _clean_token(match.group(1))
        if role and _looks_like_role_line(role):
            return role
    return None


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
        lowered = _alias_key(line)
        explicit_preference_signal = any(
            token in lowered
            for token in (
                "remote",
                "hybrid",
                "onsite",
                "on-site",
                "uzaktan",
                "hibrit",
                "location",
                "lokasyon",
                "standort",
            )
        )
        # Do not mine comma-only prose for preferred locations.  CV summaries
        # and achievements often contain commas and numbers; treating those as
        # location preferences pollutes the profile.  Compact header rows such
        # as ``email@example.com | Berlin | Remote`` are still accepted.
        if "|" not in line and ";" not in line and not explicit_preference_signal:
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
            if not _is_valid_spoken_language(language_name):
                continue
            entry = build_cv_draft_language_entry(
                language_name=language_name,
                proficiency_level=proficiency_level,
            )
            if entry is not None:
                language_entries.append(entry)

    return language_entries


def is_valid_spoken_language(language_name: str | None) -> bool:
    """Return True only when language_name is a plausible spoken/human language.

    Rejects:
    - None / empty
    - Known technology names, frameworks, libraries, section headers
    - Names not in KNOWN_LANGUAGE_NAMES (when strict allowlist is appropriate)

    This is the public entry point; internal code may also call it as
    ``_is_valid_spoken_language`` via the alias below.
    """
    if language_name is None:
        return False
    cleaned = language_name.strip()
    if not cleaned:
        return False
    normalized = _alias_key(cleaned)
    if not normalized:
        return False
    # Reject anything on the tech blocklist
    if normalized in _TECH_NAMES_NOT_LANGUAGES:
        return False
    # Reject multi-word names where any token is a known tech term
    tokens = normalized.split()
    if any(token in _TECH_NAMES_NOT_LANGUAGES for token in tokens):
        return False
    # Accept known spoken language names
    if normalized in KNOWN_LANGUAGE_NAMES:
        return True
    # Accept items that contain a known language name as a token
    # e.g. "English (C1)" after cleaning → "english" matches
    if any(token in KNOWN_LANGUAGE_NAMES for token in tokens):
        return True
    # Reject anything else — if the CV has no clearly identifiable spoken language,
    # leave Languages empty rather than polluting it with uncertain entries.
    return False


_is_valid_spoken_language = is_valid_spoken_language


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
            if not _is_valid_spoken_language(language_name):
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




def _extract_certification_entries(sections: dict[str, list[str]]) -> list:
    lines = list(sections.get("certifications", []))
    if not lines:
        lines = [
            line
            for line in sections.get("education", [])
            if _looks_like_certification_line(line)
        ]

    entries = []
    for block in _coalesce_certification_lines(lines):
        issued_year, certificate_text = _split_certification_year(block)
        certificate_name, issuer_name = _split_certification_issuer(certificate_text)
        entry = build_cv_draft_certification_entry(
            certificate_name=certificate_name,
            issuer_name=issuer_name,
            issued_year=issued_year,
        )
        if entry is not None:
            entries.append(entry)
    return entries


def _coalesce_certification_lines(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    current: str | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if current is None or _looks_like_certification_start_line(line):
            if current is not None:
                blocks.append(current)
            current = line
            continue
        current = f"{current} {line}".strip()
    if current is not None:
        blocks.append(current)
    return blocks


def _looks_like_certification_start_line(line: str) -> bool:
    return bool(YEAR_TOKEN_RE.search(line)) or _looks_like_certification_line(line)


def _looks_like_certification_line(line: str) -> bool:
    lowered = line.casefold()
    if "leaving certificate" in lowered:
        return False
    return any(
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


def _split_certification_year(value: str) -> tuple[int | None, str]:
    match = re.match(r"^((?:19|20)\d{2})\s+(.+)$", value.strip())
    if match is None:
        return None, value.strip()
    return int(match.group(1)), match.group(2).strip()


def _split_certification_issuer(value: str) -> tuple[str, str | None]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) < 2:
        return value.strip(), None
    return parts[0], ", ".join(parts[1:])


def _extract_education_entries(sections: dict[str, list[str]]) -> list:
    blocks = _split_education_blocks(sections.get("education", []))
    entries = []

    for block in blocks:
        if _education_block_is_supplemental(block):
            continue
        entry = _parse_education_block(block)
        if entry is not None:
            entries.append(entry)

    for entry in _extract_leaving_certificate_entries(sections.get("education", [])):
        key = (entry.school_name, entry.start_year, entry.end_year)
        if not any((existing.school_name, existing.start_year, existing.end_year) == key for existing in entries):
            entries.append(entry)

    return entries


def _extract_leaving_certificate_entries(lines: list[str]) -> list:
    entries = []
    for index, raw_line in enumerate(lines):
        line = _clean_token(raw_line)
        if line is None or not _alias_key(line).startswith("leaving certificate"):
            continue
        date_line = line
        if not _contains_year_information(date_line) and index + 1 < len(lines):
            maybe_date = _clean_token(lines[index + 1])
            if maybe_date is not None and _contains_year_information(maybe_date):
                date_line = maybe_date
        start_year, end_year = _parse_year_range(date_line)
        entry = build_cv_draft_education_entry(
            school_name=line,
            degree_name=None,
            field_of_study=None,
            start_year=start_year,
            end_year=end_year,
        )
        if entry is not None:
            entries.append(entry)
    return entries


def _education_block_is_supplemental(block: list[str]) -> bool:
    first_line = _clean_token(block[0] if block else None)
    if first_line is None:
        return True
    lowered = _alias_key(first_line)
    if lowered in {
        "final year subjects",
        "final year project",
        "other projects",
        "projects",
    }:
        return True
    return False


def _split_education_blocks(lines: list[str]) -> list[list[str]]:
    """Split education lines by institution starts, ignoring dated honors bullets."""
    blocks: list[list[str]] = []
    current_block: list[str] = []

    def flush() -> None:
        if current_block:
            blocks.append(list(current_block))
            current_block.clear()

    for raw_line in lines:
        (raw_line or "").strip()
        line = _clean_token(raw_line)
        if line is None:
            flush()
            continue

        if _should_start_new_education_block(current_block, raw_line):
            flush()

        if current_block or not _line_starts_with_bullet(raw_line):
            current_block.append(raw_line)

    flush()
    return blocks


def _should_start_new_education_block(
    current_block: list[str],
    candidate_line: str,
) -> bool:
    if not current_block:
        return False

    cleaned_line = _clean_token(candidate_line)
    if cleaned_line is None:
        return False
    if _line_starts_with_bullet(candidate_line):
        return False

    if (
        len([line for line in current_block if _clean_token(line)]) == 1
        and _contains_keyword_signal(current_block[0], INSTITUTION_HINT_KEYWORDS)
        and _contains_year_information(cleaned_line)
        and _looks_like_degree_name_line(_strip_date_range_from_education_line(cleaned_line) or _remove_year_text(cleaned_line))
    ):
        return False

    if _education_block_is_supplemental(current_block) and _looks_like_education_entry_start_line(cleaned_line):
        return True
    if _contains_year_information(cleaned_line) and _looks_like_education_entry_start_line(cleaned_line):
        return True

    current_has_education_core = any(
        _contains_year_information(line)
        or _looks_like_degree_name_line(line)
        or _looks_like_education_entry_start_line(line)
        for line in current_block
    )
    if not current_has_education_core:
        return False

    # Degree line + year line + institution line belongs to one education entry.
    if (
        len([line for line in current_block if _clean_token(line)]) <= 2
        and _contains_keyword_signal(cleaned_line, INSTITUTION_HINT_KEYWORDS)
        and not _contains_keyword_signal(current_block[0], INSTITUTION_HINT_KEYWORDS)
        and any(_looks_like_degree_name_line(line) for line in current_block)
    ):
        return False

    if _contains_year_information(cleaned_line):
        if _looks_like_education_entry_start_line(cleaned_line):
            return True
        return "|" in cleaned_line and len(cleaned_line) <= 140

    return _contains_keyword_signal(cleaned_line, INSTITUTION_HINT_KEYWORDS)


def _looks_like_education_entry_start_line(line: str) -> bool:
    cleaned = _clean_token(line)
    if cleaned is None:
        return False
    if _line_starts_with_bullet(cleaned):
        return False
    if _contains_keyword_signal(cleaned, INSTITUTION_HINT_KEYWORDS):
        return True
    if _looks_like_degree_name_line(_remove_year_text(cleaned)):
        return True
    lowered = _alias_key(cleaned)
    return lowered.startswith(("leaving certificate", "high school", "secondary school"))


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
            # Text-PDF extractors sometimes insert blank lines inside wrapped
            # bullet descriptions. Keep dated timeline blocks open; the next
            # role/company line will split them safely.
            if current_block and not any(_contains_year_information(item) for item in current_block):
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

    if (
        len(current_block) == 1
        and _looks_like_ocr_year_title_line(current_block[0])
        and _looks_like_ocr_end_company_line(line)
    ):
        return False

    current_block_has_year = any(
        _contains_year_information(item) for item in current_block
    )
    if not current_block_has_year:
        return False

    if _contains_year_information(line):
        return True

    cleaned_line = _clean_token(line)
    if cleaned_line is not None and _looks_like_new_timeline_entry_line(cleaned_line):
        return True

    if cleaned_line is None:
        return False

    if "|" in cleaned_line and len(cleaned_line) <= 120:
        return True

    return False


def _looks_like_new_timeline_entry_line(line: str) -> bool:
    """Return True for a fresh experience/education title after a dated block."""
    cleaned_line = _clean_token(line)
    if cleaned_line is None:
        return False
    if _line_starts_with_bullet(line):
        return False
    if _looks_like_contact_line(cleaned_line):
        return False
    if _contains_year_information(cleaned_line):
        return False
    if _detect_section_name(cleaned_line) is not None:
        return False
    if len(cleaned_line) > 80:
        return False

    if _looks_like_role_line(cleaned_line):
        return True
    if _looks_like_company_start_line(cleaned_line):
        return True
    return _contains_keyword_signal(cleaned_line, INSTITUTION_HINT_KEYWORDS)


def _line_starts_with_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*[•·*+«»<>\-¢®©\uf0b7]\s+", line or ""))


def _looks_like_ocr_year_title_line(line: str) -> bool:
    cleaned = _clean_token(line)
    if cleaned is None:
        return False
    match = OCR_YEAR_TITLE_RE.match(cleaned)
    return bool(match and _looks_like_role_line(match.group("title")))


def _looks_like_ocr_end_company_line(line: str) -> bool:
    cleaned = _clean_token(line)
    if cleaned is None:
        return False
    match = OCR_END_COMPANY_RE.match(cleaned)
    if match is None:
        return False
    company = match.group("company")
    if _looks_like_role_line(company):
        return False
    return True


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

OCR_YEAR_TITLE_RE = re.compile(
    r"^(?P<start>(?:19|20)\d{2})\s*[-–—]?\s+(?P<title>.+)$",
    re.IGNORECASE,
)
OCR_END_COMPANY_RE = re.compile(
    r"^(?P<end>(?:19|20)\d{2}|present|current|ongoing|heute|devam)\s*[-–—]?\s+(?P<company>.+)$",
    re.IGNORECASE,
)


def _parse_experience_block(block: list[str]):
    ocr_entry = _parse_ocr_year_title_company_experience(block)
    if ocr_entry is not None:
        return ocr_entry

    inline_entry = _parse_inline_title_company_experience_block(block)
    if inline_entry is not None:
        return inline_entry

    company_first_entry = _parse_company_first_experience_block(block)
    if company_first_entry is not None:
        return company_first_entry

    discrete_entry = _parse_discrete_experience_block(block)
    if discrete_entry is not None:
        return discrete_entry

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
    if parsed is None or parsed.title is None:
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


def _parse_inline_title_company_experience_block(block: list[str]):
    """Parse lines like ``Assistant Engineer - ABC Contractors`` + date."""
    cleaned_lines = [_clean_token(line) for line in block]
    cleaned_lines = [line for line in cleaned_lines if line]
    if len(cleaned_lines) < 2:
        return None

    header = cleaned_lines[0]
    date_index = next(
        (index for index, line in enumerate(cleaned_lines[1:], start=1) if _contains_year_information(line)),
        None,
    )
    if date_index is None:
        return None

    title, company_name = _split_title_company_header(header)
    if title is None or company_name is None:
        return None
    if not _looks_like_role_line(title):
        return None

    start_year, end_year = _parse_year_range(cleaned_lines[date_index])
    summary_lines = _clean_experience_summary_lines(cleaned_lines[date_index + 1 :])
    summary = _clean_token(_normalize_ocr_summary_text(" ".join(summary_lines)))

    return build_cv_draft_experience_entry(
        title=title,
        company_name=company_name,
        start_year=start_year,
        end_year=end_year,
        summary=summary,
    )


def _split_title_company_header(line: str) -> tuple[str | None, str | None]:
    cleaned = _clean_token(line)
    if cleaned is None:
        return None, None
    # Prefer explicit dash separators; they are common in text-PDF CVs.
    parts = re.split(r"\s+[–—-]\s+", cleaned, maxsplit=1)
    if len(parts) == 2:
        title = _clean_token(parts[0])
        company = _clean_token(parts[1])
        if title and company:
            return title, _strip_trailing_location_from_org(company) or company
    return None, None


def _parse_company_first_experience_block(block: list[str]):
    """Parse company/location line followed by title/date line.

    Common OCR export layout:
        Turkish Airlines Technic Inc. Istanbul, Turkey
        Project Coordinator February 2018-
        • ...
    """
    cleaned_lines = [_clean_token(line) for line in block]
    cleaned_lines = [line for line in cleaned_lines if line]
    if len(cleaned_lines) < 2:
        return None

    company_line = cleaned_lines[0]
    title_date_line = cleaned_lines[1]
    if not _looks_like_company_start_line(company_line):
        return None
    if not _contains_year_information(title_date_line):
        return None

    title = _strip_date_range_from_title_line(title_date_line)
    if title is None or not _looks_like_role_line(title):
        return None

    company_name = _strip_trailing_location_from_org(company_line)
    if company_name is None:
        return None

    start_year, end_year = _parse_year_range(title_date_line)
    summary_lines = _clean_experience_summary_lines(cleaned_lines[2:])
    summary = _clean_token(_normalize_ocr_summary_text(" ".join(summary_lines)))

    return build_cv_draft_experience_entry(
        title=title,
        company_name=company_name,
        start_year=start_year,
        end_year=end_year,
        summary=summary,
    )


def _strip_date_range_from_title_line(line: str) -> str | None:
    cleaned = _clean_token(line)
    if cleaned is None:
        return None

    # Remove month/year ranges from the end while preserving commas in titles
    # such as "R&D, Manufacturing Intern Engineer".
    cleaned = re.sub(
        r"\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+(?:19|20)\d{2}\s*[-–—]?\s*"
        r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+)?(?:(?:19|20)\d{2}|present|current|ongoing)?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s+(?:19|20)\d{2}\s*[-–—]\s*"
        r"(?:(?:19|20)\d{2}|present|current|ongoing)?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return _clean_token(cleaned)


def _looks_like_company_start_line(line: str) -> bool:
    cleaned = _clean_token(line)
    if cleaned is None:
        return False
    if _looks_like_role_line(cleaned) or _contains_year_information(cleaned):
        return False
    # New experience blocks often start with a legal/company suffix. Keep this
    # stricter than COMPANY_HINT_KEYWORDS so prose such as "matching systems"
    # does not split a running bullet paragraph.
    if re.search(
        r"\b(?:gmbh|llc|inc\.?|corp\.?|corporation|ltd\.?|limited|tic\.?|sanayi|company|co\.?)\b",
        cleaned,
        re.IGNORECASE,
    ):
        return True
    return _looks_like_company_location_line(cleaned)


def _looks_like_company_location_line(line: str) -> bool:
    cleaned = _clean_token(line)
    if cleaned is None:
        return False
    if _looks_like_role_line(cleaned) or _contains_year_information(cleaned):
        return False
    if len(cleaned) > 100:
        return False
    if not re.search(
        r"\b(?:Istanbul|İstanbul|Ankara|Izmir|İzmir|Mugla|Muğla|Turkey)\b",
        cleaned,
        re.IGNORECASE,
    ):
        return False
    # Require enough words before the location so plain addresses/locations do
    # not become company entries.
    before_location = re.split(
        r"\b(?:Istanbul|İstanbul|Ankara|Izmir|İzmir|Mugla|Muğla|Turkey)\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip(" ,")
    return len(before_location.split()) >= 2


def _strip_trailing_location_from_org(line: str) -> str | None:
    cleaned = _clean_token(line)
    if cleaned is None:
        return None

    # Remove simple trailing city/country fragments while keeping legal suffixes.
    cleaned = re.sub(
        r"\s+(?:Istanbul|İstanbul|Ankara|Izmir|İzmir|Mugla|Muğla|Balikesir|Balıkesir),\s*Turkey\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s+(?:Istanbul|İstanbul|Ankara|Izmir|İzmir|Mugla|Muğla|Balikesir|Balıkesir)\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return _clean_token(cleaned)


def _parse_discrete_experience_block(block: list[str]):
    """Parse OCR blocks laid out as title/company/date/description lines."""
    cleaned_lines = [_clean_token(line) for line in block]
    cleaned_lines = [line for line in cleaned_lines if line]
    if len(cleaned_lines) < 3:
        return None

    year_index = next(
        (index for index, line in enumerate(cleaned_lines) if _contains_year_information(line)),
        None,
    )
    if year_index is None or year_index < 2:
        return None

    title = _clean_token(cleaned_lines[0])
    company_name = _clean_token(cleaned_lines[1])
    if title is None or company_name is None:
        return None
    if not _looks_like_role_line(title):
        return None
    if _looks_like_contact_line(company_name) or _detect_section_name(company_name):
        return None

    start_year, end_year = _parse_year_range(cleaned_lines[year_index])
    summary_lines = _clean_experience_summary_lines(cleaned_lines[year_index + 1 :])
    summary = _clean_token(_normalize_ocr_summary_text(" ".join(summary_lines)))

    return build_cv_draft_experience_entry(
        title=title,
        company_name=company_name,
        start_year=start_year,
        end_year=end_year,
        summary=summary,
    )


def _clean_experience_summary_lines(lines: list[str]) -> list[str]:
    cleaned_lines: list[str] = []
    for line in lines:
        cleaned = _clean_token(line)
        if cleaned is None:
            continue
        markerless = re.sub(r"^\s*[•·*+«»<>\-¢®©\uf0b7]\s*", "", cleaned).strip()
        markerless = re.sub(r"^e\s+(?=[A-Z/])", "", markerless).strip()
        lowered = _alias_key(markerless or cleaned)
        if lowered.startswith(("referans", "reference", "referee")):
            continue
        if lowered.startswith(("telefon", "phone", "tel")):
            continue
        if EMAIL_RE.search(cleaned):
            continue
        cleaned_lines.append(markerless or cleaned)
    return cleaned_lines


def _parse_ocr_year_title_company_experience(block: list[str]):
    cleaned_lines = [_clean_token(line) for line in block]
    cleaned_lines = [line for line in cleaned_lines if line]
    if len(cleaned_lines) < 2:
        return None

    first_match = OCR_YEAR_TITLE_RE.match(cleaned_lines[0])
    second_match = OCR_END_COMPANY_RE.match(cleaned_lines[1])
    if first_match is None or second_match is None:
        return None

    title = _clean_token(first_match.group("title"))
    company_payload = _clean_token(second_match.group("company"))
    if title is None or company_payload is None:
        return None
    if not _looks_like_role_line(title):
        return None

    company_name = _extract_company_name_from_ocr_payload(company_payload)
    start_year = int(first_match.group("start"))
    end_token = second_match.group("end").casefold()
    end_year = None if end_token in {"present", "current", "ongoing", "heute", "devam"} else int(end_token)
    summary_text = " ".join(
        line
        for line in cleaned_lines[2:]
        if not _detect_section_name(line)
    )
    summary = _clean_token(_normalize_ocr_summary_text(summary_text))

    return build_cv_draft_experience_entry(
        title=title,
        company_name=company_name,
        start_year=start_year,
        end_year=end_year,
        summary=summary,
    )


def _normalize_ocr_summary_text(value: str) -> str:
    normalized = re.sub(r"(?i)\bfirst to years\b", "first two years", value)
    normalized = re.sub(r"(?<!\S)[«¢]\s+", "• ", normalized)
    normalized = re.sub(r"(?<!\S)\+\s+", "• ", normalized)
    normalized = re.sub(r"\.\.+", ".", normalized)
    return normalized


def _extract_company_name_from_ocr_payload(payload: str) -> str | None:
    cleaned = _clean_token(payload)
    if cleaned is None:
        return None
    parts = [_clean_token(part) for part in re.split(r"\s*,\s*", cleaned)]
    parts = [part for part in parts if part]
    if not parts:
        return cleaned
    return parts[0]


DEGREE_LINE_RE = re.compile(
    r"^(?:B\.?Sc|M\.?Sc|B\.?A|M\.?A|B\.?Eng|M\.?Eng|PhD|Ph\.?D|MBA|BSc|MSc|BA|MA|"
    r"B\.?S\.?|M\.?S\.?|Bachelor|Master|Doctorate|Associate|Associates|"
    r"Lisans|Yüksek Lisans|Diplom|Diploma)(?=\b|[\s.,])",
    re.IGNORECASE,
)


def _looks_like_degree_name_line(line: str) -> bool:
    if _contains_keyword_signal(line, INSTITUTION_HINT_KEYWORDS):
        return False
    if DEGREE_LINE_RE.match(line):
        return True
    normalized = _alias_key(line)
    # Turkish OCR CVs often produce degree names as
    # ``Proje Mühendisliği Yüksek Lisansı`` or ``İnşaat Mühendisliği Lisansı``.
    return bool(
        re.search(r"\b(lisans|yuksek lisans|yüksek lisans|lisansi|lisansı)\b", normalized)
        and not _contains_keyword_signal(line, INSTITUTION_HINT_KEYWORDS)
    )


def _parse_degree_year_institution_education_block(block: list[str]) -> dict[str, str | int | None] | None:
    """Parse text-PDF education blocks: degree, date range, institution."""
    cleaned_lines = [_clean_token(line) for line in block]
    cleaned_lines = [line for line in cleaned_lines if line]
    if len(cleaned_lines) < 3:
        return None

    first_line = cleaned_lines[0]
    if not (_looks_like_degree_name_line(first_line) or _alias_key(first_line).startswith("leaving certificate")):
        return None

    date_index = next(
        (index for index, line in enumerate(cleaned_lines[1:], start=1) if _contains_year_information(line)),
        None,
    )
    if date_index is None:
        return None

    school_name: str | None = None
    for line in cleaned_lines[date_index + 1 : date_index + 5]:
        if _contains_keyword_signal(line, INSTITUTION_HINT_KEYWORDS):
            school_name = line
            break

    # Leaving Certificate rows may not carry a school in the source text.
    if school_name is None and not _alias_key(first_line).startswith("leaving certificate"):
        return None

    start_year, end_year = _parse_year_range(cleaned_lines[date_index])
    degree_name, field_of_study = _split_degree_and_field(first_line)
    if degree_name is None and field_of_study is None:
        degree_name = first_line

    return {
        "school_name": school_name or "Leaving Certificate",
        "degree_name": degree_name,
        "field_of_study": field_of_study,
        "start_year": start_year,
        "end_year": end_year,
    }


def _parse_education_entry_from_discrete_lines(
    block: list[str],
    year_line: str | None,
) -> dict[str, str | None] | None:
    """Try to interpret an education block whose lines are discrete fields.

    Layouts often look like:
        B.S.
        Computer Science
        UCLA
        2016 - 2020
        Los Angeles, CA

    Returns a mapping of school_name/degree_name/field_of_study when the
    block appears to use this layout, or None when the heuristic does not
    fit (caller should fall back to the inline-separator path).
    """
    pre_year_lines: list[str] = []
    for raw_line in block:
        line = _clean_token(raw_line)
        if line is None:
            continue
        if year_line is not None and line == _clean_token(year_line):
            break
        if _contains_year_information(line) and year_line is None:
            break
        pre_year_lines.append(line)

    if len(pre_year_lines) < 2:
        return None
    # If any pre-year line contains strong inline separators, defer to the
    # inline-splitter path so "B.S. CS | UCLA" still works.
    if any(
        "|" in line or re.search(r"\s+[-–—]\s+", line)
        for line in pre_year_lines
    ):
        return None

    degree_name: str | None = None
    field_of_study: str | None = None
    school_name: str | None = None

    for line in pre_year_lines:
        if degree_name is None and _looks_like_degree_name_line(line):
            degree_name = line
            continue
        if school_name is None and _contains_keyword_signal(
            line, INSTITUTION_HINT_KEYWORDS
        ):
            school_name = line
            continue
        # Acronyms / all-caps short lines are almost always the school.
        if school_name is None and _looks_like_institution_acronym(line):
            school_name = line
            continue
        if field_of_study is None:
            field_of_study = line
            continue
        # Additional lines after we already have degree/field/school are
        # supplementary (location, honors) — ignored here.

    if school_name is None:
        # Assume the last non-degree, non-field line is the institution.
        remaining = [
            line
            for line in pre_year_lines
            if line != degree_name and line != field_of_study
        ]
        if remaining:
            school_name = remaining[-1]

    if school_name is None:
        return None

    return {
        "school_name": school_name,
        "degree_name": degree_name,
        "field_of_study": field_of_study,
    }


def _looks_like_institution_acronym(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > 12:
        return False
    letters = [character for character in stripped if character.isalpha()]
    if len(letters) < 2:
        return False
    # Mostly uppercase acronyms: MIT, UCLA, ETH, IIT, LMU, BOĞAZİÇİ
    uppercase_ratio = sum(1 for character in letters if character.isupper()) / len(letters)
    return uppercase_ratio >= 0.8


def _parse_institution_first_education_block(
    block: list[str],
) -> dict[str, str | int | None] | None:
    """Parse school/location line followed by degree/date line.

    Example:
        Istanbul Technical University Istanbul, Turkey
        Bachelor of Science in Mechanical Engineering September 2011-June 2016
    """
    cleaned_lines = [_clean_token(line) for line in block]
    cleaned_lines = [line for line in cleaned_lines if line]
    if len(cleaned_lines) < 2:
        return None

    institution_line = cleaned_lines[0]
    detail_line = cleaned_lines[1]
    if not _contains_keyword_signal(institution_line, INSTITUTION_HINT_KEYWORDS):
        return None
    if not _contains_year_information(detail_line):
        return None

    start_year, end_year = _parse_year_range(detail_line)
    detail_without_dates = _strip_date_range_from_education_line(detail_line)
    if detail_without_dates is None:
        return None

    degree_name, field_of_study = _split_degree_and_field(detail_without_dates)
    return {
        "school_name": _strip_trailing_location_from_org(institution_line),
        "degree_name": degree_name,
        "field_of_study": field_of_study,
        "start_year": start_year,
        "end_year": end_year,
    }


def _strip_date_range_from_education_line(line: str) -> str | None:
    cleaned = _clean_token(line)
    if cleaned is None:
        return None
    cleaned = re.sub(
        r"\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+(?:19|20)\d{2}\s*[-–—]\s*"
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)?\s*(?:19|20)\d{2}\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return _clean_token(cleaned)


def _split_degree_and_field(value: str) -> tuple[str | None, str | None]:
    cleaned = _clean_token(value)
    if cleaned is None:
        return None, None

    match = re.match(
        r"^(Bachelor of Science|Master of Science|Bachelor|Master|BSc|MSc|BS|MS)"
        r"\s+(?:in|of)\s+(.+)$",
        cleaned,
        re.IGNORECASE,
    )
    if match:
        degree = match.group(1).strip()
        field = match.group(2).strip()
        return degree, field

    # High-school rows often contain only a branch such as "Mathematics".
    if not _looks_like_degree_name_line(cleaned):
        return None, cleaned
    return cleaned, None


def _parse_education_block(block: list[str]):
    entity_line, year_line, _summary = _resolve_entity_year_summary(block)
    if entity_line is None:
        return None

    start_year, end_year = _parse_year_range(year_line or entity_line)

    degree_first = _parse_degree_year_institution_education_block(block)
    if degree_first is not None:
        return build_cv_draft_education_entry(
            school_name=degree_first["school_name"],
            degree_name=degree_first["degree_name"],
            field_of_study=degree_first["field_of_study"],
            start_year=degree_first["start_year"],
            end_year=degree_first["end_year"],
        )

    # Favor the discrete-line layout typical of two-column CVs (name-based
    # resumes, OCR output) where the block has separate lines for degree,
    # field, and institution. Example:
    #   B.S.
    #   Computer Science
    #   UCLA
    #   2016 - 2020
    #   Los Angeles, CA
    institution_first = _parse_institution_first_education_block(block)
    if institution_first is not None:
        return build_cv_draft_education_entry(
            school_name=institution_first["school_name"],
            degree_name=institution_first["degree_name"],
            field_of_study=institution_first["field_of_study"],
            start_year=institution_first["start_year"],
            end_year=institution_first["end_year"],
        )

    line_split = _parse_education_entry_from_discrete_lines(block, year_line)
    if line_split is not None:
        return build_cv_draft_education_entry(
            school_name=line_split["school_name"],
            degree_name=line_split["degree_name"],
            field_of_study=line_split["field_of_study"],
            start_year=start_year,
            end_year=end_year,
        )

    cleaned_entity = _remove_year_text(entity_line)

    # Try to split into school, degree, and field.
    # Prefer stronger separators (|, " - ") when present so institution names
    # that include commas (e.g. "University of California, Los Angeles") are
    # not corrupted by comma-splitting.
    if "|" in cleaned_entity:
        parts = re.split(r"\s*\|\s*", cleaned_entity)
    elif re.search(r"\s+[-–—]\s+", cleaned_entity):
        parts = re.split(r"\s+[-–—]\s+", cleaned_entity)
    else:
        parts = re.split(r"\s*,\s+", cleaned_entity)
    parts = [_clean_token(p) for p in parts]
    parts = [p for p in parts if p]

    school_name: str | None = None
    degree_name: str | None = None
    field_of_study: str | None = None

    if len(parts) >= 3:
        # Common OCR/ResumeLab layout: ``2008 BSc in Mechanical Engineering, MIT, Cambridge, MA``.
        # The first part is the degree and the second part is the school; the
        # remaining parts are usually location fragments and should not become
        # field_of_study.
        if DEGREE_LINE_RE.match(parts[0]) and (
            _contains_keyword_signal(parts[1], INSTITUTION_HINT_KEYWORDS)
            or _looks_like_institution_acronym(parts[1])
        ):
            degree_name = parts[0]
            school_name = parts[1]
        else:
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

    # Separate degree from field only when the degree line uses an explicit
    # connector ("in"/"of") — otherwise "BSc Electrical Engineering" must stay
    # as one degree string so the user-facing field is stable.
    if degree_name and field_of_study is None:
        degree_field_match = re.match(
            r"^((?:B\.?Sc|M\.?Sc|B\.?A|M\.?A|B\.?Eng|M\.?Eng|PhD|MBA|BSc|MSc|BA|MA|"
            r"Bachelor|Master|Doctorate|Lisans|Yüksek Lisans|Diplom)\.?)\s+(?:in|of)\s+(.+)$",
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