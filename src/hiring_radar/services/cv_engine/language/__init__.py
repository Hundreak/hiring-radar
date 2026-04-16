from __future__ import annotations

from hiring_radar.services.cv_engine.language.aliases import (
    SECTION_ALIASES_BY_LANGUAGE,
    best_section_alias_match,
    fold_for_matching,
    get_section_aliases,
    normalize_alias_text,
    tokenize_alias_text,
)
from hiring_radar.services.cv_engine.language.detection import (
    LightweightLanguageDetectionStrategy,
    detect_supported_language,
)
from hiring_radar.services.cv_engine.language.month_names import (
    MONTH_NAMES_BY_LANGUAGE,
    PRESENT_TOKENS_BY_LANGUAGE,
    get_month_map,
    get_present_tokens,
    resolve_month_name,
)

__all__ = [
    "MONTH_NAMES_BY_LANGUAGE",
    "PRESENT_TOKENS_BY_LANGUAGE",
    "SECTION_ALIASES_BY_LANGUAGE",
    "LightweightLanguageDetectionStrategy",
    "best_section_alias_match",
    "detect_supported_language",
    "fold_for_matching",
    "get_month_map",
    "get_present_tokens",
    "get_section_aliases",
    "normalize_alias_text",
    "resolve_month_name",
    "tokenize_alias_text",
]
