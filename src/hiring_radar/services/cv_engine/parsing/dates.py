from __future__ import annotations

import re
from dataclasses import dataclass

from hiring_radar.services.cv_engine.language.month_names import get_month_map
from hiring_radar.services.cv_engine.models import ParsedDateRange

_YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")
_MONTH_YEAR_NUMERIC_RE = re.compile(
    r"(?<!\d)(?P<month>0?[1-9]|1[0-2])[./-](?P<year>19\d{2}|20\d{2})(?!\d)"
)
_DATE_SEPARATOR_RE = re.compile(
    r"\s*(?:-|–|—|to|until|through|bis|\bbis\b|\bto\b)\s*",
    re.IGNORECASE,
)
_PRESENT_TERMS = {
    "present",
    "current",
    "ongoing",
    "now",
    "today",
    "devam",
    "devam ediyor",
    "halen",
    "su an",
    "şu an",
    "guncel",
    "güncel",
    "bugun",
    "bugün",
    "heute",
    "bis heute",
    "aktuell",
    "laufend",
    "gegenwart",
}


@dataclass(frozen=True, slots=True)
class DateFragment:
    """Intermediate normalized date fragment."""

    year: int | None
    month: int | None
    is_present: bool
    confidence: float



def parse_date_range(text: str, language: str) -> ParsedDateRange | None:
    """Parse a localized date range into a normalized model.

    Supports Turkish, English, and German month names, numeric month/year
    formats, year-only ranges, and open-ended present-tense expressions.
    """
    cleaned = _normalize_date_text(text)
    if not cleaned:
        return None

    parts = [part.strip() for part in _DATE_SEPARATOR_RE.split(cleaned) if part.strip()]
    if len(parts) >= 2:
        start_fragment = parse_date_fragment(parts[0], language)
        end_fragment = parse_date_fragment(parts[1], language)
        if start_fragment is not None and end_fragment is not None:
            confidence = min(1.0, (start_fragment.confidence + end_fragment.confidence) / 2.0)
            return ParsedDateRange(
                start_year=start_fragment.year,
                start_month=start_fragment.month,
                end_year=end_fragment.year,
                end_month=end_fragment.month,
                is_present=end_fragment.is_present,
                raw_text=text,
                confidence=confidence,
            )
        if start_fragment is not None and _looks_present_like(parts[1]):
            return ParsedDateRange(
                start_year=start_fragment.year,
                start_month=start_fragment.month,
                end_year=None,
                end_month=None,
                is_present=True,
                raw_text=text,
                confidence=min(1.0, start_fragment.confidence + 0.08),
            )

    single_fragment = parse_date_fragment(cleaned, language)
    if single_fragment is None:
        return None

    return ParsedDateRange(
        start_year=single_fragment.year,
        start_month=single_fragment.month,
        end_year=None,
        end_month=None,
        is_present=single_fragment.is_present,
        raw_text=text,
        confidence=single_fragment.confidence,
    )



def parse_date_fragment(text: str, language: str) -> DateFragment | None:
    """Parse one localized date fragment such as ``Jan 2020`` or ``2020``."""
    cleaned = _normalize_date_text(text)
    if not cleaned:
        return None
    if _looks_present_like(cleaned):
        return DateFragment(year=None, month=None, is_present=True, confidence=0.94)

    numeric_match = _MONTH_YEAR_NUMERIC_RE.search(cleaned)
    if numeric_match is not None:
        return DateFragment(
            year=int(numeric_match.group("year")),
            month=int(numeric_match.group("month")),
            is_present=False,
            confidence=0.88,
        )

    month_name = _extract_month_name(cleaned, language)
    year_match = _YEAR_RE.search(cleaned)
    if month_name is not None and year_match is not None:
        return DateFragment(
            year=int(year_match.group(0)),
            month=month_name,
            is_present=False,
            confidence=0.9,
        )

    if year_match is not None:
        return DateFragment(
            year=int(year_match.group(0)),
            month=None,
            is_present=False,
            confidence=0.7,
        )

    return None



def contains_date_range(text: str, language: str) -> bool:
    """Return whether a line appears to contain a parseable date expression."""
    return parse_date_range(text, language) is not None



def _extract_month_name(text: str, language: str) -> int | None:
    month_map = get_month_map(language)
    folded_text = _fold_text(text)
    for token, month_number in month_map.items():
        pattern = rf"(?<!\w){re.escape(token)}(?!\w)"
        if re.search(pattern, folded_text, re.IGNORECASE):
            return month_number
    return None



def _looks_present_like(text: str) -> bool:
    folded = _fold_text(text)
    return folded in _PRESENT_TERMS



def _normalize_date_text(text: str) -> str:
    cleaned = text.replace("•", " ").replace("|", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:/")
    return cleaned



def _fold_text(text: str) -> str:
    replacements = str.maketrans({
        "ş": "s",
        "Ş": "s",
        "ı": "i",
        "İ": "i",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
        # Almancaya özgü olanlar; ö/Ö/ü/Ü yukarıdaki Türkçe blokta aynı
        # karşılıklarla zaten tanımlı.
        "ä": "a",
        "Ä": "a",
        "ß": "ss",
    })
    return text.translate(replacements).casefold().strip()
