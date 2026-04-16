from __future__ import annotations

from collections import Counter
from typing import Any

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.language.aliases import iter_all_section_aliases
from hiring_radar.services.cv_engine.language.month_names import iter_all_month_tokens
from hiring_radar.services.cv_engine.models import ParseContext
from hiring_radar.services.cv_engine.protocols import LanguageDetectionStrategy


class LightweightLanguageDetectionStrategy(LanguageDetectionStrategy):
    """Detect the dominant CV language with a library backend and safe fallback."""

    def detect(
        self,
        *,
        context: ParseContext,
        config: ParserRuntimeConfig,
    ) -> str:
        text = context.normalized.text if context.normalized else ""
        if not text.strip():
            return config.language_detection.fallback_language

        if config.language_detection.enable_library_backend:
            detected = _detect_with_optional_library(
                text=text,
                supported_languages=config.language_detection.supported_languages,
            )
            if detected is not None:
                return detected

        return detect_supported_language(
            text=text,
            supported_languages=config.language_detection.supported_languages,
            fallback_language=config.language_detection.fallback_language,
        )



def _detect_with_optional_library(
    *,
    text: str,
    supported_languages: tuple[str, ...],
) -> str | None:
    """Use ftlangdetect when available and return a supported language or None."""
    try:
        from ftlangdetect import detect  # type: ignore
    except ImportError:
        return None

    try:
        result: dict[str, Any] = detect(text=text)
    except Exception:
        return None

    language = str(result.get("lang") or "").strip().lower()
    if language in supported_languages:
        return language
    return None



def detect_supported_language(
    *,
    text: str,
    supported_languages: tuple[str, ...],
    fallback_language: str,
) -> str:
    """Score supported languages with lightweight heuristic signals."""
    lowered = text.casefold()
    scores: Counter[str] = Counter()

    for language in supported_languages:
        scores[language] += _score_section_alias_hits(lowered, language)
        scores[language] += _score_month_name_hits(lowered, language)
        scores[language] += _score_character_markers(lowered, language)
        scores[language] += _score_stopword_markers(lowered, language)

    if not scores:
        return fallback_language

    best_language, best_score = scores.most_common(1)[0]
    if best_score <= 0:
        return fallback_language
    return best_language



def _score_section_alias_hits(text: str, language: str) -> int:
    score = 0
    for _, alias in iter_all_section_aliases(language):
        if alias.casefold() in text:
            score += 3
    return score



def _score_month_name_hits(text: str, language: str) -> int:
    score = 0
    for month_token in iter_all_month_tokens(language):
        if month_token.casefold() in text:
            score += 1
    return score



def _score_character_markers(text: str, language: str) -> int:
    if language == "tr":
        return sum(text.count(character) for character in ("ş", "ğ", "ı", "ç", "ö", "ü"))
    if language == "de":
        return sum(text.count(character) for character in ("ä", "ö", "ü", "ß"))
    return 0



def _score_stopword_markers(text: str, language: str) -> int:
    stopwords = {
        "en": ("with", "and", "work", "experience", "skills"),
        "tr": ("ve", "deneyim", "yetenekler", "eğitim", "özet"),
        "de": ("und", "berufserfahrung", "fähigkeiten", "ausbildung", "profil"),
    }
    score = 0
    padded_text = f" {text} "
    for token in stopwords.get(language, ()):
        if f" {token} " in padded_text:
            score += 1
    return score
