"""CV extraction regression tests.

These tests verify that CV extraction quality scoring, parse status derivation,
review requirement logic, and OCR fallback detection behave correctly across
different CV formats and content types.
"""
from __future__ import annotations

import pytest

from hiring_radar.services.cv_extraction import (
    CV_EXTRACTION_FALLBACK_REASON_EXTRACTION_FAILED,
    CV_EXTRACTION_FALLBACK_REASON_LOW_QUALITY_OCR,
    CV_EXTRACTION_FALLBACK_REASON_LOW_TEXT_VOLUME,
    CV_EXTRACTION_FALLBACK_REASON_NO_TEXT_DETECTED,
    CV_EXTRACTION_FALLBACK_REASON_OCR_NO_TEXT_DETECTED,
    CV_EXTRACTION_FALLBACK_REASON_OCR_REVIEW_RECOMMENDED,
    CV_EXTRACTION_METHOD_DOC_TEXT,
    CV_EXTRACTION_METHOD_DOCX_TEXT,
    CV_EXTRACTION_METHOD_IMAGE_OCR,
    CV_EXTRACTION_METHOD_PDF_TEXT,
    CV_EXTRACTION_METHOD_UNKNOWN,
    CV_EXTRACTION_NEXT_ACTION_REUPLOAD_AS_DOCUMENT,
    CV_EXTRACTION_NEXT_ACTION_REUPLOAD_OR_EDIT_MANUALLY,
    CV_EXTRACTION_NEXT_ACTION_REVIEW_BEFORE_APPLY,
    CV_EXTRACTION_NEXT_ACTION_SAFE_TO_APPLY,
    CV_EXTRACTION_QUALITY_HIGH,
    CV_EXTRACTION_QUALITY_LOW,
    CV_EXTRACTION_QUALITY_MEDIUM,
    CV_FILE_FORMAT_DOC,
    CV_FILE_FORMAT_DOCX,
    CV_FILE_FORMAT_JPEG,
    CV_FILE_FORMAT_JPG,
    CV_FILE_FORMAT_PDF,
    CV_FILE_FORMAT_PNG,
    CV_FILE_FORMAT_UNKNOWN,
    CV_FILE_FORMAT_WEBP,
    CV_PARSE_STATUS_EMPTY,
    CV_PARSE_STATUS_FAILED,
    CV_PARSE_STATUS_PARSED,
    CV_PARSE_STATUS_PENDING,
    CvExtractionResult,
    derive_cv_extraction_fallback_reason,
    derive_cv_extraction_quality,
    derive_cv_extraction_recommended_next_action,
    derive_cv_extraction_review_hints,
    derive_cv_parse_status,
    derive_cv_parse_status_detail,
    infer_cv_extraction_method,
    infer_cv_file_format,
    is_cv_extraction_safe_for_default_apply,
    normalize_extracted_text,
    should_cv_extraction_require_manual_review,
)


class TestCvFileFormatInference:
    """Test CV file format inference from filename and content type."""

    @pytest.mark.parametrize(
        ("filename", "content_type", "expected"),
        [
            ("cv.pdf", "application/pdf", CV_FILE_FORMAT_PDF),
            ("resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", CV_FILE_FORMAT_DOCX),
            ("document.doc", "application/msword", CV_FILE_FORMAT_DOC),
            ("scan.png", "image/png", CV_FILE_FORMAT_PNG),
            ("photo.jpg", "image/jpeg", CV_FILE_FORMAT_JPG),
            ("photo.jpeg", "image/jpeg", CV_FILE_FORMAT_JPEG),
            ("image.webp", "image/webp", CV_FILE_FORMAT_WEBP),
            ("unknown.xyz", None, CV_FILE_FORMAT_UNKNOWN),
            ("unknown", None, CV_FILE_FORMAT_UNKNOWN),
        ],
    )
    def test_infer_format(self, filename, content_type, expected):
        assert infer_cv_file_format(filename, content_type) == expected

    def test_content_type_fallback_when_no_extension(self):
        assert infer_cv_file_format("cv", "application/pdf") == CV_FILE_FORMAT_PDF
        assert infer_cv_file_format("", "image/png") == CV_FILE_FORMAT_PNG


class TestCvExtractionMethodInference:
    """Test extraction method inference from filename."""

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("cv.pdf", CV_EXTRACTION_METHOD_PDF_TEXT),
            ("resume.docx", CV_EXTRACTION_METHOD_DOCX_TEXT),
            ("document.doc", CV_EXTRACTION_METHOD_DOC_TEXT),
            ("scan.png", CV_EXTRACTION_METHOD_IMAGE_OCR),
            ("photo.jpg", CV_EXTRACTION_METHOD_IMAGE_OCR),
            ("image.webp", CV_EXTRACTION_METHOD_IMAGE_OCR),
            ("unknown.xyz", CV_EXTRACTION_METHOD_UNKNOWN),
        ],
    )
    def test_infer_method(self, filename, expected):
        assert infer_cv_extraction_method(filename) == expected


class TestParseStatusDerivation:
    """Test parse status derivation from extracted text."""

    def test_parsed_when_text_present(self):
        assert derive_cv_parse_status("Valid CV content here.") == CV_PARSE_STATUS_PARSED

    def test_empty_when_none(self):
        assert derive_cv_parse_status(None) == CV_PARSE_STATUS_EMPTY

    def test_empty_when_empty_string(self):
        assert derive_cv_parse_status("") == CV_PARSE_STATUS_EMPTY

    def test_whitespace_only_after_normalization_is_empty(self):
        # derive_cv_parse_status does not normalize; upstream normalize_extracted_text does
        assert derive_cv_parse_status("   \n\t  ") == CV_PARSE_STATUS_PARSED
        assert normalize_extracted_text("   \n\t  ") is None


class TestParseStatusDetailDerivation:
    """Test user-facing parse status detail codes."""

    def test_pending_detail(self):
        result = derive_cv_parse_status_detail(
            parse_status=CV_PARSE_STATUS_PENDING, filename="cv.pdf"
        )
        assert result == "awaiting_extraction"

    def test_failed_detail(self):
        result = derive_cv_parse_status_detail(
            parse_status=CV_PARSE_STATUS_FAILED, filename="cv.pdf"
        )
        assert result == "extraction_failed"

    def test_empty_ocr_detail(self):
        result = derive_cv_parse_status_detail(
            parse_status=CV_PARSE_STATUS_EMPTY, filename="scan.png"
        )
        assert result == "ocr_no_text_detected"

    def test_empty_docx_detail(self):
        result = derive_cv_parse_status_detail(
            parse_status=CV_PARSE_STATUS_EMPTY, filename="cv.docx"
        )
        assert result == "no_text_detected"

    def test_parsed_pdf_detail(self):
        result = derive_cv_parse_status_detail(
            parse_status=CV_PARSE_STATUS_PARSED, filename="cv.pdf"
        )
        assert result == "pdf_text_extracted"

    def test_parsed_ocr_detail(self):
        result = derive_cv_parse_status_detail(
            parse_status=CV_PARSE_STATUS_PARSED, filename="scan.png"
        )
        assert result == "ocr_text_extracted"


class TestExtractionQuality:
    """Test extraction quality scoring."""

    def test_high_quality_pdf_long_text(self):
        text = "A" * 500
        result = derive_cv_extraction_quality(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text=text,
        )
        assert result == CV_EXTRACTION_QUALITY_HIGH

    def test_medium_quality_pdf_medium_text(self):
        text = "A" * 200
        result = derive_cv_extraction_quality(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text=text,
        )
        assert result == CV_EXTRACTION_QUALITY_MEDIUM

    def test_low_quality_pdf_short_text(self):
        text = "Short text"
        result = derive_cv_extraction_quality(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text=text,
        )
        assert result == CV_EXTRACTION_QUALITY_LOW

    def test_low_quality_ocr_short_text(self):
        text = "OCR short"
        result = derive_cv_extraction_quality(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text=text,
        )
        assert result == CV_EXTRACTION_QUALITY_LOW

    def test_medium_quality_ocr_acceptable_text(self):
        text = "A" * 500
        result = derive_cv_extraction_quality(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text=text,
        )
        assert result == CV_EXTRACTION_QUALITY_MEDIUM

    def test_empty_always_low(self):
        result = derive_cv_extraction_quality(
            parse_status=CV_PARSE_STATUS_EMPTY,
            filename="cv.pdf",
            extracted_text=None,
        )
        assert result == CV_EXTRACTION_QUALITY_LOW

    def test_failed_always_low(self):
        result = derive_cv_extraction_quality(
            parse_status=CV_PARSE_STATUS_FAILED,
            filename="cv.pdf",
            extracted_text=None,
        )
        assert result == CV_EXTRACTION_QUALITY_LOW


class TestExtractionReviewHints:
    """Test deterministic review hint generation."""

    def test_ocr_source_hint(self):
        hints = derive_cv_extraction_review_hints(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text="Some OCR text that is long enough to pass volume check",
        )
        assert "ocr_source" in hints
        assert "manual_review_recommended" in hints

    def test_low_text_volume_hint(self):
        hints = derive_cv_extraction_review_hints(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="Short",
        )
        assert "low_text_volume" in hints

    def test_medium_text_volume_hint(self):
        hints = derive_cv_extraction_review_hints(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="A" * 200,
        )
        assert "medium_text_volume" in hints

    def test_failed_extraction_hint(self):
        hints = derive_cv_extraction_review_hints(
            parse_status=CV_PARSE_STATUS_FAILED,
            filename="cv.pdf",
            extracted_text=None,
        )
        assert hints == ("extraction_failed",)

    def test_no_text_detected_hint(self):
        hints = derive_cv_extraction_review_hints(
            parse_status=CV_PARSE_STATUS_EMPTY,
            filename="cv.pdf",
            extracted_text=None,
        )
        assert hints == ("no_text_detected",)

    def test_ocr_no_text_detected_hint(self):
        hints = derive_cv_extraction_review_hints(
            parse_status=CV_PARSE_STATUS_EMPTY,
            filename="scan.png",
            extracted_text=None,
        )
        assert hints == ("ocr_no_text_detected",)


class TestExtractionFallbackReason:
    """Test fallback reason derivation."""

    def test_extraction_failed(self):
        reason = derive_cv_extraction_fallback_reason(
            parse_status=CV_PARSE_STATUS_FAILED, filename="cv.pdf", extracted_text=None
        )
        assert reason == CV_EXTRACTION_FALLBACK_REASON_EXTRACTION_FAILED

    def test_no_text_detected(self):
        reason = derive_cv_extraction_fallback_reason(
            parse_status=CV_PARSE_STATUS_EMPTY, filename="cv.pdf", extracted_text=None
        )
        assert reason == CV_EXTRACTION_FALLBACK_REASON_NO_TEXT_DETECTED

    def test_ocr_no_text_detected(self):
        reason = derive_cv_extraction_fallback_reason(
            parse_status=CV_PARSE_STATUS_EMPTY, filename="scan.png", extracted_text=None
        )
        assert reason == CV_EXTRACTION_FALLBACK_REASON_OCR_NO_TEXT_DETECTED

    def test_low_quality_ocr(self):
        reason = derive_cv_extraction_fallback_reason(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text="Short",
        )
        assert reason == CV_EXTRACTION_FALLBACK_REASON_LOW_QUALITY_OCR

    def test_low_text_volume(self):
        reason = derive_cv_extraction_fallback_reason(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="Short",
        )
        assert reason == CV_EXTRACTION_FALLBACK_REASON_LOW_TEXT_VOLUME

    def test_ocr_review_recommended(self):
        reason = derive_cv_extraction_fallback_reason(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text="A" * 500,
        )
        assert reason == CV_EXTRACTION_FALLBACK_REASON_OCR_REVIEW_RECOMMENDED

    def test_no_fallback_for_good_pdf(self):
        reason = derive_cv_extraction_fallback_reason(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="A" * 500,
        )
        assert reason is None


class TestRecommendedNextAction:
    """Test recommended next action derivation."""

    def test_safe_to_apply_for_good_pdf(self):
        action = derive_cv_extraction_recommended_next_action(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="A" * 500,
        )
        assert action == CV_EXTRACTION_NEXT_ACTION_SAFE_TO_APPLY

    def test_reupload_for_failed_extraction(self):
        action = derive_cv_extraction_recommended_next_action(
            parse_status=CV_PARSE_STATUS_FAILED, filename="cv.pdf", extracted_text=None
        )
        assert action == CV_EXTRACTION_NEXT_ACTION_REUPLOAD_OR_EDIT_MANUALLY

    def test_reupload_for_low_quality_ocr(self):
        action = derive_cv_extraction_recommended_next_action(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text="Short",
        )
        assert action == CV_EXTRACTION_NEXT_ACTION_REUPLOAD_AS_DOCUMENT

    def test_review_before_apply_for_ocr_review(self):
        action = derive_cv_extraction_recommended_next_action(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text="A" * 500,
        )
        assert action == CV_EXTRACTION_NEXT_ACTION_REVIEW_BEFORE_APPLY


class TestManualReviewRequirement:
    """Test manual review requirement logic."""

    def test_requires_review_for_empty(self):
        assert should_cv_extraction_require_manual_review(
            parse_status=CV_PARSE_STATUS_EMPTY, filename="cv.pdf", extracted_text=None
        )

    def test_requires_review_for_failed(self):
        assert should_cv_extraction_require_manual_review(
            parse_status=CV_PARSE_STATUS_FAILED, filename="cv.pdf", extracted_text=None
        )

    def test_requires_review_for_ocr(self):
        assert should_cv_extraction_require_manual_review(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text="A" * 500,
        )

    def test_no_review_for_good_pdf(self):
        assert not should_cv_extraction_require_manual_review(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="A" * 500,
        )

    def test_requires_review_for_low_text_volume(self):
        assert should_cv_extraction_require_manual_review(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="Short",
        )


class TestSafeForDefaultApply:
    """Test safe-for-default-apply logic."""

    def test_safe_for_good_pdf(self):
        assert is_cv_extraction_safe_for_default_apply(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="cv.pdf",
            extracted_text="A" * 500,
        )

    def test_not_safe_for_empty(self):
        assert not is_cv_extraction_safe_for_default_apply(
            parse_status=CV_PARSE_STATUS_EMPTY, filename="cv.pdf", extracted_text=None
        )

    def test_not_safe_for_ocr(self):
        assert not is_cv_extraction_safe_for_default_apply(
            parse_status=CV_PARSE_STATUS_PARSED,
            filename="scan.png",
            extracted_text="A" * 500,
        )


class TestNormalizeExtractedText:
    """Test text normalization."""

    def test_returns_none_for_none(self):
        assert normalize_extracted_text(None) is None

    def test_normalizes_whitespace(self):
        result = normalize_extracted_text("  hello   world  \n\n  ")
        assert result == "hello world"

    def test_returns_none_for_empty_after_normalization(self):
        assert normalize_extracted_text("   \n\t  ") is None


class TestCvExtractionResult:
    """Test extraction result dataclass."""

    def test_default_values(self):
        result = CvExtractionResult(
            extracted_text="test",
            parse_status=CV_PARSE_STATUS_PARSED,
            page_count=2,
        )
        assert result.extraction_method == CV_EXTRACTION_METHOD_UNKNOWN
        assert result.used_ocr is False

    def test_custom_values(self):
        result = CvExtractionResult(
            extracted_text="test",
            parse_status=CV_PARSE_STATUS_PARSED,
            page_count=1,
            extraction_method=CV_EXTRACTION_METHOD_PDF_TEXT,
            used_ocr=True,
        )
        assert result.extraction_method == CV_EXTRACTION_METHOD_PDF_TEXT
        assert result.used_ocr is True
