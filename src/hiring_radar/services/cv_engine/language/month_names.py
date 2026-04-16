from __future__ import annotations

from collections.abc import Iterable

MONTH_NAMES_BY_LANGUAGE: dict[str, dict[str, int]] = {
    "en": {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    },
    "tr": {
        "oca": 1,
        "ocak": 1,
        "sub": 2,
        "subat": 2,
        "şubat": 2,
        "mar": 3,
        "mart": 3,
        "nis": 4,
        "nisan": 4,
        "may": 5,
        "mayis": 5,
        "mayıs": 5,
        "haz": 6,
        "haziran": 6,
        "tem": 7,
        "temmuz": 7,
        "agu": 8,
        "agustos": 8,
        "ağu": 8,
        "ağustos": 8,
        "eyl": 9,
        "eylul": 9,
        "eylül": 9,
        "eki": 10,
        "ekim": 10,
        "kas": 11,
        "kasim": 11,
        "kasım": 11,
        "ara": 12,
        "aralik": 12,
        "aralık": 12,
    },
    "de": {
        "jan": 1,
        "januar": 1,
        "feb": 2,
        "februar": 2,
        "mar": 3,
        "mär": 3,
        "maerz": 3,
        "märz": 3,
        "apr": 4,
        "april": 4,
        "mai": 5,
        "jun": 6,
        "juni": 6,
        "jul": 7,
        "juli": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "okt": 10,
        "oktober": 10,
        "nov": 11,
        "november": 11,
        "dez": 12,
        "dezember": 12,
    },
}

PRESENT_TOKENS_BY_LANGUAGE: dict[str, tuple[str, ...]] = {
    "en": ("present", "current", "ongoing", "now"),
    "tr": ("devam", "halen", "guncel", "güncel", "su an", "şu an"),
    "de": ("heute", "aktuell", "derzeit", "bis heute"),
}


def get_month_map(language: str) -> dict[str, int]:
    """Return the month-name map for one supported language."""
    return MONTH_NAMES_BY_LANGUAGE.get(language, MONTH_NAMES_BY_LANGUAGE["en"])



def get_present_tokens(language: str) -> tuple[str, ...]:
    """Return localized tokens representing an open-ended current date."""
    return PRESENT_TOKENS_BY_LANGUAGE.get(language, PRESENT_TOKENS_BY_LANGUAGE["en"])



def iter_all_month_tokens(language: str) -> Iterable[str]:
    """Yield localized month-name tokens for one language."""
    return get_month_map(language).keys()



def resolve_month_name(value: str, language: str) -> int | None:
    """Resolve a localized month token into its integer representation."""
    normalized = value.casefold().strip()
    if not normalized:
        return None
    return get_month_map(language).get(normalized)
