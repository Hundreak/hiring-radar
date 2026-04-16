from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.layout import (
    PyMuPdfLayoutAnalyzer,
    layout_artifact_to_text,
)
from hiring_radar.services.cv_engine.extraction.normalization import (
    normalize_extracted_text as normalize_engine_text,
)

CV_PARSE_STATUS_PENDING = "pending"
CV_PARSE_STATUS_PARSED = "parsed"
CV_PARSE_STATUS_FAILED = "failed"
CV_PARSE_STATUS_EMPTY = "empty"

CV_OCR_LANG_ENV_VAR = "HIRING_RADAR_CV_OCR_LANG"

SUPPORTED_CV_EXTRACTION_EXTENSIONS = frozenset(
    {".pdf", ".docx", ".png", ".jpg", ".jpeg"}
)

CV_FILE_FORMAT_PDF = "pdf"
CV_FILE_FORMAT_DOCX = "docx"
CV_FILE_FORMAT_PNG = "png"
CV_FILE_FORMAT_JPG = "jpg"
CV_FILE_FORMAT_JPEG = "jpeg"
CV_FILE_FORMAT_UNKNOWN = "unknown"

CV_EXTRACTION_METHOD_PDF_TEXT = "pdf_text"
CV_EXTRACTION_METHOD_DOCX_TEXT = "docx_text"
CV_EXTRACTION_METHOD_IMAGE_OCR = "image_ocr"
CV_EXTRACTION_METHOD_UNKNOWN = "unknown"

CV_EXTRACTION_QUALITY_HIGH = "high"
CV_EXTRACTION_QUALITY_MEDIUM = "medium"
CV_EXTRACTION_QUALITY_LOW = "low"

CV_EXTRACTION_FALLBACK_REASON_EXTRACTION_FAILED = "extraction_failed"
CV_EXTRACTION_FALLBACK_REASON_NO_TEXT_DETECTED = "no_text_detected"
CV_EXTRACTION_FALLBACK_REASON_OCR_NO_TEXT_DETECTED = "ocr_no_text_detected"
CV_EXTRACTION_FALLBACK_REASON_LOW_QUALITY_OCR = "low_quality_ocr"
CV_EXTRACTION_FALLBACK_REASON_LOW_TEXT_VOLUME = "low_text_volume"
CV_EXTRACTION_FALLBACK_REASON_OCR_REVIEW_RECOMMENDED = "ocr_review_recommended"

CV_EXTRACTION_NEXT_ACTION_SAFE_TO_APPLY = "safe_to_apply"
CV_EXTRACTION_NEXT_ACTION_REVIEW_BEFORE_APPLY = "review_before_apply"
CV_EXTRACTION_NEXT_ACTION_REUPLOAD_OR_EDIT_MANUALLY = "reupload_or_edit_manually"
CV_EXTRACTION_NEXT_ACTION_REUPLOAD_AS_DOCUMENT = "reupload_as_document"


class CvExtractionError(RuntimeError):
    """Raised when a CV file cannot be extracted safely."""


@dataclass(slots=True, frozen=True)
class CvExtractionResult:
    extracted_text: str | None
    parse_status: str
    page_count: int


def normalize_extracted_text(text: str | None) -> str | None:
    """Normalize extracted text for downstream parsing."""
    if text is None:
        return None

    normalized = normalize_engine_text(text).text
    return normalized or None


def derive_cv_parse_status(extracted_text: str | None) -> str:
    """Derive parse status from normalized extracted text."""
    return CV_PARSE_STATUS_PARSED if extracted_text else CV_PARSE_STATUS_EMPTY


def infer_cv_file_format(
    filename: str | None,
    content_type: str | None = None,
) -> str:
    """Infer the uploaded CV file format from filename/content type."""
    extension = Path(filename or "").suffix.lower()
    if extension == ".pdf":
        return CV_FILE_FORMAT_PDF
    if extension == ".docx":
        return CV_FILE_FORMAT_DOCX
    if extension == ".png":
        return CV_FILE_FORMAT_PNG
    if extension == ".jpg":
        return CV_FILE_FORMAT_JPG
    if extension == ".jpeg":
        return CV_FILE_FORMAT_JPEG

    normalized_content_type = (content_type or "").strip().lower()
    if normalized_content_type == "application/pdf":
        return CV_FILE_FORMAT_PDF
    if (
        normalized_content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return CV_FILE_FORMAT_DOCX
    if normalized_content_type == "image/png":
        return CV_FILE_FORMAT_PNG
    if normalized_content_type == "image/jpeg":
        return CV_FILE_FORMAT_JPEG
    return CV_FILE_FORMAT_UNKNOWN


def infer_cv_extraction_method(
    filename: str | None,
    content_type: str | None = None,
) -> str:
    """Infer the extraction method used for a CV upload."""
    file_format = infer_cv_file_format(filename, content_type)
    if file_format == CV_FILE_FORMAT_PDF:
        return CV_EXTRACTION_METHOD_PDF_TEXT
    if file_format == CV_FILE_FORMAT_DOCX:
        return CV_EXTRACTION_METHOD_DOCX_TEXT
    if file_format in {CV_FILE_FORMAT_PNG, CV_FILE_FORMAT_JPG, CV_FILE_FORMAT_JPEG}:
        return CV_EXTRACTION_METHOD_IMAGE_OCR
    return CV_EXTRACTION_METHOD_UNKNOWN


def cv_extraction_uses_ocr(
    filename: str | None,
    content_type: str | None = None,
) -> bool:
    """Return whether the upload is processed via OCR."""
    return infer_cv_extraction_method(filename, content_type) == CV_EXTRACTION_METHOD_IMAGE_OCR


def derive_cv_parse_status_detail(
    *,
    parse_status: str,
    filename: str | None,
    content_type: str | None = None,
) -> str:
    """Derive a user-facing parse status detail code."""
    extraction_method = infer_cv_extraction_method(filename, content_type)

    if parse_status == CV_PARSE_STATUS_PENDING:
        return "awaiting_extraction"
    if parse_status == CV_PARSE_STATUS_FAILED:
        return "extraction_failed"
    if parse_status == CV_PARSE_STATUS_EMPTY:
        if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
            return "ocr_no_text_detected"
        return "no_text_detected"
    if parse_status == CV_PARSE_STATUS_PARSED:
        if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
            return "ocr_text_extracted"
        if extraction_method == CV_EXTRACTION_METHOD_DOCX_TEXT:
            return "docx_text_extracted"
        if extraction_method == CV_EXTRACTION_METHOD_PDF_TEXT:
            return "pdf_text_extracted"
        return "text_extracted"
    return "unknown"


def derive_cv_extraction_quality(
    *,
    parse_status: str,
    filename: str | None,
    content_type: str | None = None,
    extracted_text: str | None = None,
) -> str:
    """Derive a coarse extraction quality level."""
    extraction_method = infer_cv_extraction_method(filename, content_type)
    normalized_text = normalize_extracted_text(extracted_text)

    if parse_status in {CV_PARSE_STATUS_FAILED, CV_PARSE_STATUS_EMPTY}:
        return CV_EXTRACTION_QUALITY_LOW
    if parse_status != CV_PARSE_STATUS_PARSED:
        return CV_EXTRACTION_QUALITY_LOW

    text_length = len(normalized_text or "")
    if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
        return (
            CV_EXTRACTION_QUALITY_MEDIUM
            if text_length >= 400
            else CV_EXTRACTION_QUALITY_LOW
        )
    if text_length >= 400:
        return CV_EXTRACTION_QUALITY_HIGH
    if text_length >= 120:
        return CV_EXTRACTION_QUALITY_MEDIUM
    return CV_EXTRACTION_QUALITY_LOW


def derive_cv_extraction_review_hints(
    *,
    parse_status: str,
    filename: str | None,
    content_type: str | None = None,
    extracted_text: str | None = None,
) -> tuple[str, ...]:
    """Derive deterministic review hint codes for extraction output."""
    extraction_method = infer_cv_extraction_method(filename, content_type)
    normalized_text = normalize_extracted_text(extracted_text)
    text_length = len(normalized_text or "")

    hints: list[str] = []
    if parse_status == CV_PARSE_STATUS_FAILED:
        return ("extraction_failed",)
    if parse_status == CV_PARSE_STATUS_EMPTY:
        if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
            return ("ocr_no_text_detected",)
        return ("no_text_detected",)

    if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
        hints.append("ocr_source")
    if text_length < 120:
        hints.append("low_text_volume")
    elif text_length < 400:
        hints.append("medium_text_volume")
    if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
        hints.append("manual_review_recommended")
    return tuple(hints)


def derive_cv_extraction_fallback_reason(
    *,
    parse_status: str,
    filename: str | None,
    content_type: str | None = None,
    extracted_text: str | None = None,
) -> str | None:
    """Derive a coarse fallback reason for extraction/operator flows."""
    extraction_method = infer_cv_extraction_method(filename, content_type)
    quality = derive_cv_extraction_quality(
        parse_status=parse_status,
        filename=filename,
        content_type=content_type,
        extracted_text=extracted_text,
    )

    if parse_status == CV_PARSE_STATUS_FAILED:
        return CV_EXTRACTION_FALLBACK_REASON_EXTRACTION_FAILED
    if parse_status == CV_PARSE_STATUS_EMPTY:
        if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
            return CV_EXTRACTION_FALLBACK_REASON_OCR_NO_TEXT_DETECTED
        return CV_EXTRACTION_FALLBACK_REASON_NO_TEXT_DETECTED
    if quality == CV_EXTRACTION_QUALITY_LOW:
        if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
            return CV_EXTRACTION_FALLBACK_REASON_LOW_QUALITY_OCR
        return CV_EXTRACTION_FALLBACK_REASON_LOW_TEXT_VOLUME
    if extraction_method == CV_EXTRACTION_METHOD_IMAGE_OCR:
        return CV_EXTRACTION_FALLBACK_REASON_OCR_REVIEW_RECOMMENDED
    return None


def derive_cv_extraction_recommended_next_action(
    *,
    parse_status: str,
    filename: str | None,
    content_type: str | None = None,
    extracted_text: str | None = None,
) -> str:
    """Derive the next recommended operator action for extraction output."""
    fallback_reason = derive_cv_extraction_fallback_reason(
        parse_status=parse_status,
        filename=filename,
        content_type=content_type,
        extracted_text=extracted_text,
    )
    if fallback_reason in {
        CV_EXTRACTION_FALLBACK_REASON_EXTRACTION_FAILED,
        CV_EXTRACTION_FALLBACK_REASON_NO_TEXT_DETECTED,
        CV_EXTRACTION_FALLBACK_REASON_OCR_NO_TEXT_DETECTED,
    }:
        return CV_EXTRACTION_NEXT_ACTION_REUPLOAD_OR_EDIT_MANUALLY
    if fallback_reason == CV_EXTRACTION_FALLBACK_REASON_LOW_QUALITY_OCR:
        return CV_EXTRACTION_NEXT_ACTION_REUPLOAD_AS_DOCUMENT
    if fallback_reason in {
        CV_EXTRACTION_FALLBACK_REASON_LOW_TEXT_VOLUME,
        CV_EXTRACTION_FALLBACK_REASON_OCR_REVIEW_RECOMMENDED,
    }:
        return CV_EXTRACTION_NEXT_ACTION_REVIEW_BEFORE_APPLY
    return CV_EXTRACTION_NEXT_ACTION_SAFE_TO_APPLY


def should_cv_extraction_require_manual_review(
    *,
    parse_status: str,
    filename: str | None,
    content_type: str | None = None,
    extracted_text: str | None = None,
) -> bool:
    """Return whether the extraction output should require manual review."""
    if parse_status != CV_PARSE_STATUS_PARSED:
        return True
    fallback_reason = derive_cv_extraction_fallback_reason(
        parse_status=parse_status,
        filename=filename,
        content_type=content_type,
        extracted_text=extracted_text,
    )
    return fallback_reason is not None


def is_cv_extraction_safe_for_default_apply(
    *,
    parse_status: str,
    filename: str | None,
    content_type: str | None = None,
    extracted_text: str | None = None,
) -> bool:
    """Return whether extraction output is safe for default apply behavior."""
    return not should_cv_extraction_require_manual_review(
        parse_status=parse_status,
        filename=filename,
        content_type=content_type,
        extracted_text=extracted_text,
    )


def extract_text_from_cv_file(file_path: str | Path) -> CvExtractionResult:
    """Extract normalized text from a supported CV file."""
    path = Path(file_path)
    extension = path.suffix.lower()
    if extension == ".pdf":
        return extract_text_from_pdf(path)
    if extension == ".docx":
        return extract_text_from_docx(path)
    if extension in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(path)
    raise CvExtractionError(
        "Unsupported CV extraction format. Supported formats: PDF, DOCX, PNG, JPG, JPEG."
    )


def extract_text_from_pdf(file_path: str | Path) -> CvExtractionResult:
    """Extract text from a PDF CV.

    The extractor prefers a layout-aware PyMuPDF reading order when the optional
    dependency is available. If that path is unavailable or yields no usable
    text, the legacy ``pypdf`` extractor remains the safety fallback.

    If both text extraction methods yield low quality text (under 120 chars),
    the extractor falls back to rendering PDF pages as images and OCRing them.
    """
    path = Path(file_path)
    layout_attempt = _extract_pdf_text_with_layout(path)
    if layout_attempt is not None and layout_attempt.extracted_text is not None:
        if len(layout_attempt.extracted_text) >= 120:
            return layout_attempt

    pypdf_attempt = _extract_pdf_text_with_pypdf(path)
    if pypdf_attempt.extracted_text is not None and len(pypdf_attempt.extracted_text) >= 120:
        return pypdf_attempt

    # Text extraction yielded poor results — try OCR on rendered pages
    ocr_attempt = _extract_pdf_text_with_ocr(path)
    if ocr_attempt is not None and ocr_attempt.extracted_text is not None:
        if len(ocr_attempt.extracted_text) > len(pypdf_attempt.extracted_text or ""):
            return ocr_attempt

    # Return best available
    if layout_attempt is not None and layout_attempt.extracted_text is not None:
        return layout_attempt
    return pypdf_attempt


def _extract_pdf_text_with_layout(file_path: Path) -> CvExtractionResult | None:
    """Attempt layout-aware PDF extraction using PyMuPDF blocks."""
    try:
        analyzer = PyMuPdfLayoutAnalyzer()
        layout = analyzer.analyze_pdf(
            file_path=file_path,
            config=ParserRuntimeConfig().layout_analysis,
        )
    except Exception:
        return None

    ordered_text = normalize_extracted_text(layout_artifact_to_text(layout))
    page_count = len(layout.pages)
    if ordered_text is None:
        return CvExtractionResult(
            extracted_text=None,
            parse_status=CV_PARSE_STATUS_EMPTY,
            page_count=page_count,
        )

    return CvExtractionResult(
        extracted_text=ordered_text,
        parse_status=derive_cv_parse_status(ordered_text),
        page_count=page_count,
    )


def _extract_pdf_text_with_pypdf(file_path: Path) -> CvExtractionResult:
    """Fallback PDF extraction using ``pypdf`` only."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise CvExtractionError(
            "PDF extraction requires the 'pypdf' package to be installed."
        ) from exc

    try:
        reader = PdfReader(str(file_path))
    except Exception as exc:  # pragma: no cover
        raise CvExtractionError(f"Failed to read PDF file: {file_path.name}") from exc

    page_texts: list[str] = []
    for page in reader.pages:
        try:
            extracted_text = page.extract_text()
        except Exception as exc:  # pragma: no cover
            raise CvExtractionError(
                f"Failed to extract text from a page in PDF file: {file_path.name}"
            ) from exc
        normalized_text = normalize_extracted_text(extracted_text)
        if normalized_text:
            page_texts.append(normalized_text)

    combined_text = normalize_extracted_text("\n\n".join(page_texts))
    return CvExtractionResult(
        extracted_text=combined_text,
        parse_status=derive_cv_parse_status(combined_text),
        page_count=len(reader.pages),
    )


def extract_text_from_docx(file_path: str | Path) -> CvExtractionResult:
    """Extract text from a DOCX CV."""
    path = Path(file_path)
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover
        raise CvExtractionError(
            "DOCX extraction requires the 'python-docx' package to be installed."
        ) from exc

    try:
        document = Document(str(path))
    except Exception as exc:  # pragma: no cover
        raise CvExtractionError(f"Failed to read DOCX file: {path.name}") from exc

    blocks: list[str] = []
    for paragraph in document.paragraphs:
        normalized_text = normalize_extracted_text(paragraph.text)
        if normalized_text:
            blocks.append(normalized_text)
    for table in document.tables:
        for row in table.rows:
            cells = [
                cleaned
                for cell in row.cells
                if (cleaned := normalize_extracted_text(cell.text)) is not None
            ]
            if cells:
                blocks.append(" | ".join(cells))

    combined_text = normalize_extracted_text("\n\n".join(blocks))
    return CvExtractionResult(
        extracted_text=combined_text,
        parse_status=derive_cv_parse_status(combined_text),
        page_count=1,
    )


def extract_text_from_image(file_path: str | Path) -> CvExtractionResult:
    """Extract text from an image CV using OCR.

    Preprocessing pipeline:
    1. EXIF transpose (fix phone rotation)
    2. Grayscale conversion
    3. Upscale small images to improve OCR accuracy
    4. Autocontrast to normalize exposure
    5. Adaptive sharpening for scanned documents
    """
    path = Path(file_path)
    try:
        from PIL import Image, ImageFilter, ImageOps
    except ImportError as exc:  # pragma: no cover
        raise CvExtractionError(
            "Image extraction requires the 'Pillow' package to be installed."
        ) from exc

    try:
        image = Image.open(path)
    except Exception as exc:  # pragma: no cover
        raise CvExtractionError(f"Failed to read image file: {path.name}") from exc

    try:
        prepared_image = ImageOps.exif_transpose(image)
        prepared_image = ImageOps.grayscale(prepared_image)

        # Upscale small images — Tesseract works best at 300+ DPI equivalent
        min_dimension = min(prepared_image.width, prepared_image.height)
        if min_dimension < 1500:
            scale_factor = max(2, 1500 // min_dimension)
            prepared_image = prepared_image.resize(
                (prepared_image.width * scale_factor, prepared_image.height * scale_factor),
                Image.LANCZOS,
            )

        prepared_image = ImageOps.autocontrast(prepared_image, cutoff=1)

        # Sharpen to counteract blurriness in scanned/photographed documents
        prepared_image = prepared_image.filter(ImageFilter.SHARPEN)

        # Build language string: try multi-language if available
        ocr_lang = os.environ.get(CV_OCR_LANG_ENV_VAR, "").strip()
        if not ocr_lang:
            ocr_lang = _detect_ocr_languages()

        extracted_text = _ocr_image_to_text(
            prepared_image,
            lang=ocr_lang,
        )
    except CvExtractionError:
        raise
    except Exception as exc:  # pragma: no cover
        raise CvExtractionError(
            f"Failed to extract text from image file: {path.name}"
        ) from exc

    combined_text = normalize_extracted_text(extracted_text)
    return CvExtractionResult(
        extracted_text=combined_text,
        parse_status=derive_cv_parse_status(combined_text),
        page_count=1,
    )


def _detect_ocr_languages() -> str:
    """Detect available Tesseract languages and return a combined string.

    Falls back to 'eng' if detection fails.
    """
    try:
        import pytesseract
        available = pytesseract.get_languages()
    except Exception:
        return "eng"

    # Prefer eng+tur+deu for this platform's target languages
    preferred = ["eng", "tur", "deu"]
    found = [lang for lang in preferred if lang in available]
    return "+".join(found) if found else "eng"


def _ocr_image_to_text(image, *, lang: str) -> str:
    """Run OCR over a prepared image."""
    try:
        import pytesseract
        from pytesseract import TesseractNotFoundError
    except ImportError as exc:  # pragma: no cover
        raise CvExtractionError(
            "Image OCR requires the 'pytesseract' package to be installed."
        ) from exc

    try:
        return pytesseract.image_to_string(image, lang=lang)
    except TesseractNotFoundError as exc:
        raise CvExtractionError(
            "Image OCR requires the Tesseract binary to be installed on the host system."
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise CvExtractionError("Image OCR failed.") from exc
