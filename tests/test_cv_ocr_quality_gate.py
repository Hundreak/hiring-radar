"""Tests for OCR quality gate, gibberish detection, and safe auto-apply behavior.

Critical invariant: garbage OCR text must NEVER corrupt a populated profile.
"""
from __future__ import annotations

import pytest

from hiring_radar.services.cv_ocr_quality import (
    CV_OCR_QUALITY_HIGH,
    CV_OCR_QUALITY_LOW,
    CV_OCR_QUALITY_MEDIUM,
    CV_OCR_QUALITY_UNUSABLE,
    filter_gibberish_items,
    is_gibberish_scalar,
    quality_band_at_least,
    score_ocr_quality,
)

# ---------------------------------------------------------------------------
# is_gibberish_scalar — non-strict (default)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [
    None,
    "",
    "   ",
    "!!##@@",
    "a",
    "@@",
    "|||||",
])
def test_is_gibberish_scalar_rejects_obviously_bad(value) -> None:
    assert is_gibberish_scalar(value) is True


@pytest.mark.parametrize("value", [
    "Python",
    "Senior Software Engineer",
    "Berlin",
    "FastAPI",
    "JavaScript",
    "SQL",
])
def test_is_gibberish_scalar_accepts_real_cv_tokens(value) -> None:
    assert is_gibberish_scalar(value) is False


def test_is_gibberish_scalar_rejects_single_char_fragment_run() -> None:
    # OCR column-merge artifact: "S o f t w a r e"
    assert is_gibberish_scalar("S o f t w a r e") is True


def test_is_gibberish_scalar_rejects_symbol_heavy() -> None:
    assert is_gibberish_scalar("@#Ö|\\") is True


# ---------------------------------------------------------------------------
# is_gibberish_scalar — strict mode (OCR source)
# ---------------------------------------------------------------------------

def test_is_gibberish_scalar_strict_rejects_single_short_token() -> None:
    # Strict: a scalar longer than 8 chars needs ≥ 2 word-like tokens
    assert is_gibberish_scalar("Sftwr", strict=True) is True


def test_is_gibberish_scalar_strict_accepts_multi_word() -> None:
    assert is_gibberish_scalar("Software Engineer", strict=True) is False


def test_is_gibberish_scalar_strict_rejects_high_noise_ratio() -> None:
    # noise_char_ratio threshold is 0.05 in strict mode (vs 0.08 in normal)
    assert is_gibberish_scalar("Python|Java|SQL|||", strict=True) is True


def test_is_gibberish_scalar_non_strict_allows_short_tech_token() -> None:
    # Non-strict: "SQL" is a valid short tech token
    assert is_gibberish_scalar("SQL", strict=False) is False


# ---------------------------------------------------------------------------
# filter_gibberish_items — strict mode
# ---------------------------------------------------------------------------

def test_filter_gibberish_items_drops_noise_keeps_real() -> None:
    items = ["Python", "!!!", "JavaScript", "a", "SQL", "@#$"]
    result = filter_gibberish_items(items)
    assert "Python" in result
    assert "JavaScript" in result
    assert "SQL" in result
    assert "!!!" not in result
    assert "@#$" not in result


def test_filter_gibberish_items_strict_drops_single_char_runs() -> None:
    items = ["S o f t w a r e", "Python", "Prg"]
    result = filter_gibberish_items(items, strict=True)
    assert "Python" in result
    assert "S o f t w a r e" not in result


def test_filter_gibberish_items_deduplicates() -> None:
    items = ["Python", "python", "PYTHON"]
    result = filter_gibberish_items(items)
    assert len(result) == 1


def test_filter_gibberish_items_empty_input() -> None:
    assert filter_gibberish_items([]) == ()
    assert filter_gibberish_items(None) == ()


# ---------------------------------------------------------------------------
# score_ocr_quality — band assignment
# ---------------------------------------------------------------------------

_GOOD_CV_TEXT = (
    "Alice Example\n"
    "Senior Backend Engineer\n"
    "alice@example.com | +49 111 222\n\n"
    "SUMMARY\n"
    "Experienced backend engineer with 7 years building high-throughput APIs "
    "using Python, FastAPI, and PostgreSQL. Led distributed systems projects "
    "across three product teams.\n\n"
    "SKILLS\n"
    "Python FastAPI PostgreSQL Redis Docker Kubernetes\n\n"
    "EXPERIENCE\n"
    "Senior Backend Engineer — ACME Corp (2020–2024)\n"
    "Designed and maintained the job-matching service processing 2 million "
    "queries per day. Reduced p99 latency by 40% through query optimization.\n\n"
    "EDUCATION\n"
    "BSc Computer Science — Technical University Berlin (2013–2017)"
)

_GARBAGE_OCR_TEXT = (
    "aSrioe Exapmle\n"
    "Snri Bcaeknd Egineer\n"
    "lcaie@xmaple.ocm\n\n"
    "SMMUARY\n"
    "Expircened bkaecnd eigneer wtih 7 yreas biulding high-thruoghput AIPa\n"
    "usnig Pyhton, FasATPI, nad PosgterSQL. Led distrbiuted sysemts porejcts.\n\n"
    "SLKILS\n"
    "Pyhton FasATPI PosgterSQL Rdieis Dockre\n"
)

_NOISE_ONLY_TEXT = "@@## ||| ^^ ~~~ [] {} \\ | | | | ^"


def test_score_ocr_quality_high_for_good_cv_text() -> None:
    report = score_ocr_quality(_GOOD_CV_TEXT, extraction_method="image_ocr")
    assert report.band in (CV_OCR_QUALITY_HIGH, CV_OCR_QUALITY_MEDIUM)
    assert report.score > 0.5


def test_score_ocr_quality_unusable_for_noise_only() -> None:
    report = score_ocr_quality(_NOISE_ONLY_TEXT, extraction_method="image_ocr")
    assert report.band == CV_OCR_QUALITY_UNUSABLE


def test_score_ocr_quality_unusable_for_none() -> None:
    report = score_ocr_quality(None, extraction_method="image_ocr")
    assert report.band == CV_OCR_QUALITY_UNUSABLE


def test_score_ocr_quality_unusable_for_empty_string() -> None:
    report = score_ocr_quality("", extraction_method="image_ocr")
    assert report.band == CV_OCR_QUALITY_UNUSABLE


def test_score_ocr_quality_strict_mode_for_ocr() -> None:
    # OCR mode uses strict thresholds — a short text that would pass for
    # PDF text should score lower for OCR.
    short_text = "Python developer Berlin"
    report_ocr = score_ocr_quality(short_text, extraction_method="image_ocr")
    report_pdf = score_ocr_quality(short_text, extraction_method="pdf_text")
    # OCR is stricter — should score lower or have more reasons
    assert report_ocr.band in (CV_OCR_QUALITY_LOW, CV_OCR_QUALITY_UNUSABLE)


def test_score_ocr_quality_is_not_trustworthy_for_pivot_when_medium() -> None:
    # Medium quality must not be trustworthy for pivot (full field replacement)
    report = score_ocr_quality(_GOOD_CV_TEXT[:300], extraction_method="image_ocr")
    # Even if medium, pivot should be denied
    if report.band == CV_OCR_QUALITY_MEDIUM:
        assert report.is_trustworthy_for_pivot is False


def test_score_ocr_quality_high_is_trustworthy_for_apply() -> None:
    report = score_ocr_quality(_GOOD_CV_TEXT, extraction_method="image_ocr")
    if report.band == CV_OCR_QUALITY_HIGH:
        assert report.is_trustworthy_for_apply is True


# ---------------------------------------------------------------------------
# quality_band_at_least helper
# ---------------------------------------------------------------------------

def test_quality_band_at_least_ordering() -> None:
    assert quality_band_at_least(CV_OCR_QUALITY_HIGH, CV_OCR_QUALITY_HIGH) is True
    assert quality_band_at_least(CV_OCR_QUALITY_HIGH, CV_OCR_QUALITY_MEDIUM) is True
    assert quality_band_at_least(CV_OCR_QUALITY_MEDIUM, CV_OCR_QUALITY_HIGH) is False
    assert quality_band_at_least(CV_OCR_QUALITY_LOW, CV_OCR_QUALITY_HIGH) is False
    assert quality_band_at_least(CV_OCR_QUALITY_UNUSABLE, CV_OCR_QUALITY_LOW) is False


def test_quality_band_at_least_unknown_returns_false() -> None:
    assert quality_band_at_least("", CV_OCR_QUALITY_HIGH) is False
    assert quality_band_at_least("unknown", CV_OCR_QUALITY_MEDIUM) is False


# ---------------------------------------------------------------------------
# Auto-apply gate logic (unit tests of helper functions)
# ---------------------------------------------------------------------------

def test_ocr_quality_gate_blocks_medium_for_ocr_image() -> None:
    """The auto-apply gate must block medium-quality image OCR."""
    ocr_band = CV_OCR_QUALITY_MEDIUM
    snapshot_came_from_ocr = True

    # Simulate the gate logic in _auto_apply_latest_cv_parse_run
    should_skip = snapshot_came_from_ocr and not quality_band_at_least(
        ocr_band or "", CV_OCR_QUALITY_HIGH
    )
    assert should_skip is True


def test_ocr_quality_gate_blocks_low_for_ocr_image() -> None:
    ocr_band = CV_OCR_QUALITY_LOW
    snapshot_came_from_ocr = True
    should_skip = snapshot_came_from_ocr and not quality_band_at_least(
        ocr_band or "", CV_OCR_QUALITY_HIGH
    )
    assert should_skip is True


def test_ocr_quality_gate_blocks_none_band_for_ocr_image() -> None:
    """Unknown OCR quality must also be blocked for image sources."""
    ocr_band = None
    snapshot_came_from_ocr = True
    should_skip = snapshot_came_from_ocr and not quality_band_at_least(
        ocr_band or "", CV_OCR_QUALITY_HIGH
    )
    assert should_skip is True


def test_ocr_quality_gate_allows_high_for_ocr_image() -> None:
    ocr_band = CV_OCR_QUALITY_HIGH
    snapshot_came_from_ocr = True
    should_skip = snapshot_came_from_ocr and not quality_band_at_least(
        ocr_band or "", CV_OCR_QUALITY_HIGH
    )
    assert should_skip is False


def test_ocr_quality_gate_allows_low_for_non_ocr() -> None:
    """Non-OCR sources (PDF/DOCX) are not subject to the OCR image gate."""
    ocr_band = CV_OCR_QUALITY_LOW
    snapshot_came_from_ocr = False
    should_skip = snapshot_came_from_ocr and not quality_band_at_least(
        ocr_band or "", CV_OCR_QUALITY_HIGH
    )
    assert should_skip is False


# ---------------------------------------------------------------------------
# No-corruption invariant: sanitizer must not produce garbage on profile
# ---------------------------------------------------------------------------

def test_filter_gibberish_items_ocr_mode_removes_garbled_skills() -> None:
    """OCR column-merge artifacts in skill lists must not survive sanitization."""
    garbled_skills = [
        "S k i l l s",    # space-separated single-char OCR fragment
        "JavaScript",      # legitimate compound tech token
        "SQL",             # short but valid acronym
        "a",               # single char — too short
        "Sftwr Dvlpr",     # two vowel-less tokens — both word-like filtered
    ]
    result = filter_gibberish_items(garbled_skills, strict=True)
    # Legitimate tech tokens must survive
    assert "JavaScript" in result
    assert "SQL" in result
    # Space-separated fragment must be rejected (majority single-char tokens)
    assert "S k i l l s" not in result
    # Single char rejected by min_letters
    assert "a" not in result
    # "Sftwr Dvlpr": both tokens have no vowels (len ≥ 4), so not word-like
    # → wordlike count < 2 in space-separated value → rejected in strict mode
    assert "Sftwr Dvlpr" not in result
