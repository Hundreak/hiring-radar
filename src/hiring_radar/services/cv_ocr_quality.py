"""OCR / extracted-text quality scoring and gibberish detection.

The apply pipeline uses these scores to decide whether an uploaded CV's
extracted text is trustworthy enough to pivot a real profile onto. A low
or unusable score must NEVER pivot or overwrite a populated profile —
garbage-in, garbage-on-profile is the exact failure mode this module
exists to prevent.

Design goals:
  * Deterministic, dependency-free scoring (no ML, no network).
  * Cheap enough to run inline during upload.
  * Works across English, Turkish, and German CV text — the three
    languages this product ships OCR training data for.
  * Produces a single, stable quality band plus human-readable reasons
    so downstream UIs and logs can explain the verdict.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Mapping

CV_OCR_QUALITY_HIGH = "high"
CV_OCR_QUALITY_MEDIUM = "medium"
CV_OCR_QUALITY_LOW = "low"
CV_OCR_QUALITY_UNUSABLE = "unusable"

_QUALITY_ORDER: tuple[str, ...] = (
    CV_OCR_QUALITY_UNUSABLE,
    CV_OCR_QUALITY_LOW,
    CV_OCR_QUALITY_MEDIUM,
    CV_OCR_QUALITY_HIGH,
)

# Small, curated stopword / common-token sets. We deliberately keep each
# set tiny: the signal we want is "does a plausible amount of real-word
# vocabulary appear?" not a full morphological coverage. Bigger lists
# add noise (common English words happen to be valid-looking garbage too).
_EN_STOPWORDS = frozenset(
    {
        "the", "and", "for", "with", "from", "this", "that", "have",
        "has", "are", "was", "were", "will", "would", "been", "being",
        "work", "team", "project", "skills", "experience", "education",
        "summary", "developer", "engineer", "manager", "senior", "years",
        "company", "technologies", "responsible", "developed", "designed",
        "implemented", "managed", "built", "improved", "worked", "using",
        "about", "professional", "role", "roles", "language", "languages",
    }
)

_TR_STOPWORDS = frozenset(
    {
        "ve", "ile", "için", "bir", "bu", "şu", "çok", "daha",
        "gibi", "olarak", "sonra", "önce", "yıl", "yıllık", "yıllar",
        "deneyim", "deneyimi", "deneyimli", "eğitim", "eğitimi",
        "beceri", "beceriler", "diller", "dil", "özet", "iletişim",
        "mühendis", "mühendisi", "mühendislik", "yönetici", "uzman",
        "geliştirici", "proje", "projeler", "şirket", "şirketinde",
        "üniversite", "üniversitesi", "lisans", "yüksek", "lise",
        "çalıştı", "çalıştım", "geliştirdim", "geliştirdi", "tasarladım",
        "yönettim", "kurdum", "oluşturdum", "sorumlu", "sorumluluklar",
    }
)

_DE_STOPWORDS = frozenset(
    {
        "und", "oder", "der", "die", "das", "den", "ein", "eine",
        "einer", "einem", "mit", "für", "von", "bei", "auf", "aus",
        "zum", "zur", "als", "bin", "war", "waren", "ist", "sind",
        "jahr", "jahre", "jahren", "erfahrung", "ausbildung", "studium",
        "kenntnisse", "fähigkeiten", "sprachen", "entwickler",
        "ingenieur", "manager", "leitung", "team", "projekt", "projekte",
        "unternehmen", "universität", "hochschule", "abschluss",
        "entwickelt", "entworfen", "implementiert", "geführt", "gebaut",
        "zuständig", "verantwortlich",
    }
)

_ALL_STOPWORDS = _EN_STOPWORDS | _TR_STOPWORDS | _DE_STOPWORDS

# Characters that should basically never show up in a CV at high frequency.
# Tesseract loves to emit these from noisy backgrounds or inverted text.
_OCR_NOISE_CHARS = frozenset("^`~|<>{}[]\\¢£¥§¶†‡•¤¦¬©®™")

_TOKEN_RE = re.compile(r"[^\W\d_]+(?:[\-'’][^\W\d_]+)*", re.UNICODE)
_WORD_CHAR_RE = re.compile(r"[^\W\d_]", re.UNICODE)


@dataclass(slots=True, frozen=True)
class OcrQualityMetrics:
    character_count: int = 0
    letter_count: int = 0
    token_count: int = 0
    word_like_token_count: int = 0
    mean_token_length: float = 0.0
    alphabetic_ratio: float = 0.0
    word_like_ratio: float = 0.0
    symbol_letter_ratio: float = 0.0
    noise_char_ratio: float = 0.0
    repeat_char_penalty: float = 0.0
    stopword_hit_count: int = 0
    line_count: int = 0
    contains_email: bool = False
    contains_phone: bool = False


@dataclass(slots=True, frozen=True)
class OcrQualityReport:
    band: str
    score: float
    metrics: OcrQualityMetrics
    reasons: tuple[str, ...] = field(default_factory=tuple)
    extraction_method: str | None = None

    @property
    def is_trustworthy_for_apply(self) -> bool:
        """Safe to let the draft mutate the profile at all."""
        return self.band in (CV_OCR_QUALITY_HIGH, CV_OCR_QUALITY_MEDIUM)

    @property
    def is_trustworthy_for_pivot(self) -> bool:
        """Safe to let the draft fully replace CV-derived profile fields.

        Pivot wipes fields on the profile that the draft does not
        carry, so we require the higher bar.
        """
        return self.band == CV_OCR_QUALITY_HIGH

    def to_dict(self) -> dict[str, object]:
        metrics = self.metrics
        return {
            "band": self.band,
            "score": round(self.score, 4),
            "reasons": list(self.reasons),
            "extraction_method": self.extraction_method,
            "metrics": {
                "character_count": metrics.character_count,
                "letter_count": metrics.letter_count,
                "token_count": metrics.token_count,
                "word_like_token_count": metrics.word_like_token_count,
                "mean_token_length": round(metrics.mean_token_length, 3),
                "alphabetic_ratio": round(metrics.alphabetic_ratio, 4),
                "word_like_ratio": round(metrics.word_like_ratio, 4),
                "symbol_letter_ratio": round(metrics.symbol_letter_ratio, 4),
                "noise_char_ratio": round(metrics.noise_char_ratio, 4),
                "repeat_char_penalty": round(metrics.repeat_char_penalty, 4),
                "stopword_hit_count": metrics.stopword_hit_count,
                "line_count": metrics.line_count,
                "contains_email": metrics.contains_email,
                "contains_phone": metrics.contains_phone,
            },
        }


def quality_band_at_least(band: str, minimum: str) -> bool:
    """Return True if ``band`` is at least as strong as ``minimum``."""
    try:
        return _QUALITY_ORDER.index(band) >= _QUALITY_ORDER.index(minimum)
    except ValueError:
        return False


def score_ocr_quality(
    text: str | None,
    *,
    extraction_method: str | None = None,
    strict_for_ocr: bool = True,
) -> OcrQualityReport:
    """Score the extracted text and return a quality report.

    ``strict_for_ocr`` raises the acceptance bar when the text came from
    an OCR pipeline (image CVs or rasterized PDFs): OCR routinely
    produces text that *looks* structured but is actually noise, so the
    quality gate has less margin for error than a pdfminer/python-docx
    extraction.
    """
    metrics = _compute_metrics(text)
    is_ocr = (extraction_method or "").strip().lower() in {"image_ocr", "pdf_ocr"}
    strict = strict_for_ocr and is_ocr

    reasons: list[str] = []
    # --- Hard failure gates --------------------------------------------------
    if metrics.character_count == 0 or metrics.letter_count == 0:
        reasons.append("no_text")
        return OcrQualityReport(
            band=CV_OCR_QUALITY_UNUSABLE,
            score=0.0,
            metrics=metrics,
            reasons=tuple(reasons),
            extraction_method=extraction_method,
        )

    min_letters = 120 if strict else 40
    if metrics.letter_count < min_letters:
        reasons.append("too_few_letters")
    min_tokens = 25 if strict else 10
    if metrics.token_count < min_tokens:
        reasons.append("too_few_tokens")
    if metrics.alphabetic_ratio < 0.45:
        reasons.append("low_alphabetic_ratio")
    if metrics.word_like_ratio < 0.55:
        reasons.append("low_word_like_ratio")
    if metrics.symbol_letter_ratio > (0.35 if strict else 0.6):
        reasons.append("high_symbol_ratio")
    if metrics.noise_char_ratio > 0.03:
        reasons.append("ocr_noise_chars")
    if metrics.repeat_char_penalty > 0.25:
        reasons.append("repeating_noise")
    if metrics.mean_token_length < 2.4 or metrics.mean_token_length > 14.0:
        reasons.append("abnormal_token_length")
    min_stopwords = 3 if strict else 1
    if metrics.stopword_hit_count < min_stopwords:
        reasons.append("no_recognizable_vocabulary")

    # --- Composite score ----------------------------------------------------
    score = _compute_composite_score(metrics)

    # --- Band resolution ----------------------------------------------------
    fatal_reasons = {
        "no_text",
        "too_few_letters",
        "low_alphabetic_ratio",
        "low_word_like_ratio",
        "no_recognizable_vocabulary",
        "repeating_noise",
        "ocr_noise_chars",
    }
    if any(r in fatal_reasons for r in reasons):
        band = CV_OCR_QUALITY_UNUSABLE
    elif reasons:
        band = CV_OCR_QUALITY_LOW
    elif score >= (0.80 if strict else 0.72):
        band = CV_OCR_QUALITY_HIGH
    elif score >= (0.58 if strict else 0.48):
        band = CV_OCR_QUALITY_MEDIUM
    else:
        band = CV_OCR_QUALITY_LOW

    return OcrQualityReport(
        band=band,
        score=score,
        metrics=metrics,
        reasons=tuple(reasons),
        extraction_method=extraction_method,
    )


def is_gibberish_scalar(
    value: str | None,
    *,
    min_letters: int = 3,
    strict: bool = False,
) -> bool:
    """Return True when a scalar looks like OCR noise, not a real value.

    Used to strip individual draft fields even when the overall text
    passed the quality gate. A corrupted headline like ``"@#Ö|\\"`` must
    never land on a profile.

    ``strict=True`` raises the bar for OCR-sourced fields: requires at
    least two word-like tokens, a higher alphabetic ratio, and rejects
    single-character-fragment runs that plain OCR often emits.
    """
    if value is None:
        return True
    cleaned = value.strip()
    if not cleaned:
        return True
    metrics = _compute_metrics(cleaned)
    if metrics.letter_count < min_letters:
        return True
    alpha_threshold = 0.55 if strict else 0.5
    if metrics.alphabetic_ratio < alpha_threshold:
        return True
    noise_threshold = 0.05 if strict else 0.08
    if metrics.noise_char_ratio > noise_threshold:
        return True
    if metrics.symbol_letter_ratio > 0.8:
        return True
    repeat_threshold = 0.25 if strict else 0.35
    if metrics.repeat_char_penalty > repeat_threshold:
        return True
    tokens = _TOKEN_RE.findall(cleaned.lower())
    if not tokens:
        return True
    wordlike = [t for t in tokens if _is_word_like(t)]
    if not wordlike:
        return True
    # Strict mode: for space-separated values (multi-word context), require at
    # least two word-like tokens — a single garbled fragment like "Sftwr Eng"
    # still passes the individual word-like test but indicates broken OCR.
    # Single-token compound words like "JavaScript" are allowed through.
    if strict and " " in cleaned and len(wordlike) < 2:
        return True
    if len(wordlike) == 1 and len(wordlike[0]) < 3:
        return True
    # Reject when the majority of tokens look like single-char OCR fragments:
    # e.g. "S o f t w a r e" emitted by broken column OCR.
    single_char_tokens = sum(1 for t in tokens if len(t) == 1)
    if len(tokens) >= 3 and single_char_tokens / len(tokens) > 0.5:
        return True
    return False


def is_gibberish_scalar_ocr(value: str | None, *, min_letters: int = 3) -> bool:
    """Convenience wrapper for OCR-sourced scalar fields (strict=True)."""
    return is_gibberish_scalar(value, min_letters=min_letters, strict=True)


def filter_gibberish_items(
    values: object,
    *,
    strict: bool = False,
) -> tuple[str, ...]:
    """Drop gibberish items from a list-like draft field."""
    if not values:
        return ()
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:  # type: ignore[union-attr]
        if not isinstance(raw, str):
            continue
        item = raw.strip()
        if not item:
            continue
        if is_gibberish_scalar(item, min_letters=2, strict=strict):
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return tuple(cleaned)


# -- internals ---------------------------------------------------------------


def _compute_metrics(text: str | None) -> OcrQualityMetrics:
    if not text:
        return OcrQualityMetrics()
    normalized = unicodedata.normalize("NFC", text)
    character_count = len(normalized)
    letter_count = sum(1 for ch in normalized if _WORD_CHAR_RE.match(ch))
    non_space_count = sum(1 for ch in normalized if not ch.isspace())
    symbol_count = sum(
        1
        for ch in normalized
        if not ch.isalnum() and not ch.isspace()
    )
    noise_count = sum(1 for ch in normalized if ch in _OCR_NOISE_CHARS)

    tokens = _TOKEN_RE.findall(normalized)
    token_count = len(tokens)
    word_like_tokens = [tok for tok in tokens if _is_word_like(tok)]
    word_like_token_count = len(word_like_tokens)

    if tokens:
        mean_token_length = sum(len(tok) for tok in tokens) / len(tokens)
    else:
        mean_token_length = 0.0

    alphabetic_ratio = letter_count / max(non_space_count, 1)
    word_like_ratio = (
        word_like_token_count / token_count if token_count else 0.0
    )
    symbol_letter_ratio = symbol_count / max(letter_count, 1)
    noise_char_ratio = noise_count / max(character_count, 1)
    repeat_char_penalty = _repeat_char_penalty(normalized)

    lowered_tokens = {tok.lower() for tok in tokens}
    stopword_hits = sum(1 for tok in lowered_tokens if tok in _ALL_STOPWORDS)

    contains_email = bool(
        re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", normalized)
    )
    contains_phone = bool(
        re.search(r"\+?\d[\d\s().\-]{6,}\d", normalized)
    )

    line_count = sum(1 for line in normalized.splitlines() if line.strip())

    return OcrQualityMetrics(
        character_count=character_count,
        letter_count=letter_count,
        token_count=token_count,
        word_like_token_count=word_like_token_count,
        mean_token_length=mean_token_length,
        alphabetic_ratio=alphabetic_ratio,
        word_like_ratio=word_like_ratio,
        symbol_letter_ratio=symbol_letter_ratio,
        noise_char_ratio=noise_char_ratio,
        repeat_char_penalty=repeat_char_penalty,
        stopword_hit_count=stopword_hits,
        line_count=line_count,
        contains_email=contains_email,
        contains_phone=contains_phone,
    )


def _is_word_like(token: str) -> bool:
    """A token passes if it looks like a plausible human-language word.

    Tesseract garbage tends to produce single-character runs, tokens
    with internal symbols, or extreme vowel/consonant ratios. A good
    real-world CV token is 2-20 letters, has at least one vowel unless
    it's a short acronym, and contains no odd punctuation interior.
    """
    length = len(token)
    if length < 2 or length > 22:
        return False
    lowered = token.lower()
    if any(ch in _OCR_NOISE_CHARS for ch in lowered):
        return False
    vowels = sum(1 for ch in lowered if ch in "aeıioöuüâêîôûaeiou")
    if length >= 4 and vowels == 0:
        return False
    # Reject anything with more than two identical consecutive letters.
    for i in range(len(lowered) - 2):
        if lowered[i] == lowered[i + 1] == lowered[i + 2]:
            return False
    return True


def _repeat_char_penalty(text: str) -> float:
    """Fraction of characters that sit inside a 3+ identical-run streak."""
    if not text:
        return 0.0
    total = len(text)
    streak_chars = 0
    i = 0
    while i < total:
        if text[i].isspace():
            i += 1
            continue
        j = i + 1
        while j < total and text[j] == text[i]:
            j += 1
        run = j - i
        if run >= 3:
            streak_chars += run
        i = j
    return streak_chars / total


def _compute_composite_score(metrics: OcrQualityMetrics) -> float:
    """Weighted 0..1 score combining the main quality metrics."""
    if metrics.letter_count == 0:
        return 0.0

    alpha_component = min(metrics.alphabetic_ratio / 0.9, 1.0)
    wordlike_component = min(metrics.word_like_ratio / 0.9, 1.0)
    length_component = 1.0
    if metrics.mean_token_length < 3.0:
        length_component = max(metrics.mean_token_length / 3.0, 0.0)
    elif metrics.mean_token_length > 10.0:
        length_component = max(1.0 - (metrics.mean_token_length - 10.0) / 10.0, 0.0)
    stopword_component = min(metrics.stopword_hit_count / 8.0, 1.0)
    volume_component = min(metrics.letter_count / 800.0, 1.0)
    symbol_penalty = max(1.0 - metrics.symbol_letter_ratio, 0.0)
    noise_penalty = max(1.0 - metrics.noise_char_ratio * 10.0, 0.0)
    repeat_penalty = max(1.0 - metrics.repeat_char_penalty * 4.0, 0.0)

    # Weights intentionally favor word-likeness + stopword hits over
    # raw volume, because OCR garbage can produce lots of letters too.
    score = (
        alpha_component * 0.18
        + wordlike_component * 0.22
        + length_component * 0.10
        + stopword_component * 0.25
        + volume_component * 0.10
        + symbol_penalty * 0.05
        + noise_penalty * 0.05
        + repeat_penalty * 0.05
    )
    return max(0.0, min(1.0, score))


def quality_report_metrics_summary(report: OcrQualityReport) -> Mapping[str, object]:
    """Return a flat summary useful for logging and telemetry."""
    metrics = report.metrics
    return {
        "band": report.band,
        "score": round(report.score, 4),
        "letter_count": metrics.letter_count,
        "token_count": metrics.token_count,
        "word_like_ratio": round(metrics.word_like_ratio, 4),
        "stopword_hits": metrics.stopword_hit_count,
        "alphabetic_ratio": round(metrics.alphabetic_ratio, 4),
        "reasons": list(report.reasons),
    }
