from __future__ import annotations

import re

from hiring_radar.services.cv_engine.config import ExperienceParsingConfig, ParserRuntimeConfig
from hiring_radar.services.cv_engine.models import ParsedDateRange, ParsedExperienceLine
from hiring_radar.services.cv_engine.parsing.dates import parse_date_range
from hiring_radar.services.cv_engine.scoring.confidence import combine_confidence_components
from hiring_radar.services.cv_engine.semantic.location_resolution import (
    resolve_location_candidate,
)
from hiring_radar.services.cv_engine.semantic.organization_resolution import (
    resolve_organization_candidate,
)
from hiring_radar.services.cv_engine.semantic.role_resolution import resolve_role_candidate

_ROLE_HINT_RE = re.compile(
    r"\b(?:engineer|developer|analyst|manager|scientist|architect|consultant|specialist|lead|administrator|designer|intern|technician|researcher|mühendis|geliştirici|analist|uzman|yönetici|tasarımcı|ingenieur|entwickler|berater|leiter|spezialist|forscher)\b",
    re.IGNORECASE,
)
_COMPANY_HINT_RE = re.compile(
    r"\b(?:llc|inc\.?|corp\.?|corporation|ltd\.?|limited|company|co\.?|holding|holdings|solutions|systems|software|technologies|technology|labs|group|gmbh|ag|plc|a\.ş\.?|oy|ab)\b",
    re.IGNORECASE,
)
_LOCATION_SPLIT_RE = re.compile(r"\s*[|,;/]\s*")


def parse_experience_block(
    lines: list[str],
    *,
    language: str = "en",
    config: ExperienceParsingConfig | None = None,
) -> ParsedExperienceLine | None:
    """Parse one experience entry block into structured semantic fields."""
    runtime_config = config or ExperienceParsingConfig()
    normalized_lines = [
        _clean_line(item)
        for item in lines[: runtime_config.max_candidate_lines + 4]
        if _clean_line(item) is not None
    ]
    if not normalized_lines:
        return None

    date_index, date_range = _find_date_line(normalized_lines, language)
    non_date_lines: list[str] = []
    for index, line in enumerate(normalized_lines):
        if index == date_index:
            stripped_line = _strip_date_text(line, language)
            if stripped_line:
                non_date_lines.append(stripped_line)
            continue
        if _looks_like_date_only_line(line, language):
            continue
        non_date_lines.append(line)
    if not non_date_lines:
        non_date_lines = [line for line in normalized_lines if line]

    title: str | None = None
    company_name: str | None = None
    location: str | None = None

    inline_result = _parse_inline_title_company(non_date_lines[0], language)
    if inline_result is not None:
        title, company_name, location = inline_result
        summary_lines = non_date_lines[1:]
    else:
        title, company_name, location = _parse_multiline_candidates(non_date_lines)
        consumed_prefix = sum(value is not None for value in (title, company_name, location))
        summary_lines = non_date_lines[min(consumed_prefix, len(non_date_lines)) :]

    resolved_role = resolve_role_candidate(title or "", section_name="experience")
    if resolved_role is not None:
        title = resolved_role.title
    resolved_company = resolve_organization_candidate(company_name or "")
    if resolved_company is not None:
        company_name = resolved_company.organization_name
    resolved_location = resolve_location_candidate(location or "") if location else None
    if resolved_location is not None:
        location = resolved_location.location_name

    bonuses: list[tuple[str, float]] = []
    reasons: list[str] = []
    if resolved_role is not None:
        bonuses.append(("resolved_role", 0.16))
        reasons.append("resolved_role")
    elif title:
        bonuses.append(("role_candidate", 0.08))
        reasons.append("role_candidate")
    if resolved_company is not None:
        bonuses.append(("resolved_company", 0.14))
        reasons.append("resolved_company")
    elif company_name:
        bonuses.append(("company_candidate", 0.08))
        reasons.append("company_candidate")
    if date_range is not None:
        bonuses.append(("date_range", 0.14))
        reasons.append("date_range")
    if resolved_location is not None:
        bonuses.append(("resolved_location", 0.08))
        reasons.append("resolved_location")
    if summary_lines:
        bonuses.append(("summary_lines", 0.06))
        reasons.append("summary_lines")

    assessment = combine_confidence_components(
        base_score=ParserRuntimeConfig().confidence_scoring.base_score,
        bonuses=bonuses,
        penalties=(),
        config=ParserRuntimeConfig().confidence_scoring,
        reasons=reasons,
    )

    if date_range is not None and date_range.confidence_assessment is None:
        date_range.confidence_assessment = assessment

    return ParsedExperienceLine(
        title=title,
        company_name=company_name,
        location=location,
        date_range=date_range,
        summary_lines=summary_lines,
        confidence=assessment.score,
        confidence_assessment=assessment,
        title_provenance=(resolved_role.provenance if resolved_role is not None else None),
        company_provenance=(
            resolved_company.provenance if resolved_company is not None else None
        ),
        location_provenance=(
            resolved_location.provenance if resolved_location is not None else None
        ),
        metadata={
            "language": language,
            "line_count": len(normalized_lines),
        },
    )


def _find_date_line(
    lines: list[str],
    language: str,
) -> tuple[int, ParsedDateRange | None]:
    best_index = -1
    best_range: ParsedDateRange | None = None
    for index, line in enumerate(lines):
        parsed = parse_date_range(line, language)
        if parsed is not None:
            best_index = index
            best_range = parsed
            break
    return best_index, best_range



def _parse_inline_title_company(
    line: str,
    language: str,
) -> tuple[str | None, str | None, str | None] | None:
    lowered = line.casefold()
    if " at " in lowered:
        title, company = _split_once_case_insensitive(line, " at ")
        return title.strip() or None, company.strip() or None, None
    if " @ " in line:
        title, company = line.split(" @ ", maxsplit=1)
        return title.strip() or None, company.strip() or None, None

    parts = [part.strip() for part in _LOCATION_SPLIT_RE.split(line) if part.strip()]
    non_date_parts = [part for part in parts if parse_date_range(part, language) is None]
    if (
        len(non_date_parts) >= 2
        and _looks_like_role(non_date_parts[0])
        and _looks_like_company(non_date_parts[1])
    ):
        location = None
        if len(non_date_parts) >= 3 and _looks_like_location(non_date_parts[2]):
            location = non_date_parts[2]
        return non_date_parts[0], non_date_parts[1], location
    return None


def _strip_date_text(line: str, language: str) -> str:
    if _looks_like_date_only_line(line, language):
        return ""
    parsed = parse_date_range(line, language)
    if parsed is None:
        return line
    stripped = line
    if parsed.raw_text and parsed.raw_text != line:
        stripped = line.replace(parsed.raw_text, " ")
    else:
        pipe_parts = [part.strip() for part in line.split("|")]
        if len(pipe_parts) >= 2 and parse_date_range(pipe_parts[-1], language) is not None:
            stripped = " | ".join(pipe_parts[:-1])
        else:
            stripped = re.sub(
                r"(?i)(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december|ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik|januar|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)\s+\d{4}\s*(?:-|–|—|to)\s*(?:present|current|ongoing|heute|devam|\d{4})",
                " ",
                line,
            )
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped.strip(" |-–—,:;")


def _parse_multiline_candidates(
    lines: list[str],
) -> tuple[str | None, str | None, str | None]:
    if not lines:
        return None, None, None
    if len(lines) == 1:
        first = lines[0]
        return (first, None, None) if _looks_like_role(first) else (None, first, None)

    first = lines[0]
    second = lines[1]
    if _looks_like_role(first) and _looks_like_company(second):
        location = lines[2] if len(lines) >= 3 and _looks_like_location(lines[2]) else None
        return first, second, location
    if _looks_like_company(first) and _looks_like_role(second):
        location = lines[2] if len(lines) >= 3 and _looks_like_location(lines[2]) else None
        return second, first, location
    return first, second, None



def _looks_like_role(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if _COMPANY_HINT_RE.search(stripped):
        return False
    return bool(_ROLE_HINT_RE.search(stripped)) or _alpha_ratio(stripped) >= 0.65



def _looks_like_company(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if _COMPANY_HINT_RE.search(stripped):
        return True
    words = stripped.split()
    if len(words) <= 5 and all(word[:1].isupper() for word in words if word[:1].isalpha()):
        return True
    return False



def _looks_like_location(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if len(stripped.split()) > 4:
        return False
    return "," in stripped or all(
        token[:1].isupper() for token in stripped.split() if token[:1].isalpha()
    )



def _looks_like_date_only_line(value: str, language: str) -> bool:
    del language
    cleaned = value.strip()
    if not cleaned:
        return False
    if re.search(r"[|@]", cleaned):
        return False
    return bool(
        re.fullmatch(
            r"(?i)(?:"
            r"(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december|"
            r"ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik|"
            r"januar|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)?"
            r"\s*\d{4}"
            r"(?:\s*(?:-|–|—|to)\s*(?:present|current|ongoing|heute|devam|\d{4}))?"
            r"|\d{1,2}/\d{4}\s*(?:-|–|—|to)\s*(?:\d{1,2}/\d{4}|present|current|ongoing|heute|devam)"
            r")",
            cleaned,
        )
    )



def _clean_line(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip(" |-–—,:;")
    return cleaned or None



def _alpha_ratio(value: str) -> float:
    characters = [character for character in value if not character.isspace()]
    if not characters:
        return 0.0
    alpha_count = sum(character.isalpha() for character in characters)
    return alpha_count / len(characters)



def _split_once_case_insensitive(value: str, separator: str) -> tuple[str, str]:
    lowered = value.casefold()
    lowered_separator = separator.casefold()
    index = lowered.find(lowered_separator)
    if index < 0:
        return value, ""
    return value[:index], value[index + len(separator) :]
