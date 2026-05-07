from __future__ import annotations

import os
import re
import shutil
import unicodedata
import subprocess
import tempfile
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
    {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".webp"}
)

CV_FILE_FORMAT_PDF = "pdf"
CV_FILE_FORMAT_DOCX = "docx"
CV_FILE_FORMAT_DOC = "doc"
CV_FILE_FORMAT_PNG = "png"
CV_FILE_FORMAT_JPG = "jpg"
CV_FILE_FORMAT_JPEG = "jpeg"
CV_FILE_FORMAT_WEBP = "webp"
CV_FILE_FORMAT_UNKNOWN = "unknown"

CV_EXTRACTION_METHOD_PDF_TEXT = "pdf_text"
CV_EXTRACTION_METHOD_DOCX_TEXT = "docx_text"
CV_EXTRACTION_METHOD_DOC_TEXT = "doc_text"
CV_EXTRACTION_METHOD_PDF_OCR = "pdf_ocr"
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
    extraction_method: str = CV_EXTRACTION_METHOD_UNKNOWN
    used_ocr: bool = False


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
    if extension == ".doc":
        return CV_FILE_FORMAT_DOC
    if extension == ".png":
        return CV_FILE_FORMAT_PNG
    if extension == ".jpg":
        return CV_FILE_FORMAT_JPG
    if extension == ".jpeg":
        return CV_FILE_FORMAT_JPEG
    if extension == ".webp":
        return CV_FILE_FORMAT_WEBP

    normalized_content_type = (content_type or "").strip().lower()
    if normalized_content_type == "application/pdf":
        return CV_FILE_FORMAT_PDF
    if (
        normalized_content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return CV_FILE_FORMAT_DOCX
    if normalized_content_type == "application/msword":
        return CV_FILE_FORMAT_DOC
    if normalized_content_type == "image/png":
        return CV_FILE_FORMAT_PNG
    if normalized_content_type == "image/jpeg":
        return CV_FILE_FORMAT_JPEG
    if normalized_content_type == "image/webp":
        return CV_FILE_FORMAT_WEBP
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
    if file_format == CV_FILE_FORMAT_DOC:
        return CV_EXTRACTION_METHOD_DOC_TEXT
    if file_format in {
        CV_FILE_FORMAT_PNG,
        CV_FILE_FORMAT_JPG,
        CV_FILE_FORMAT_JPEG,
        CV_FILE_FORMAT_WEBP,
    }:
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
    if extension == ".doc":
        return extract_text_from_doc(path)
    if extension in {".png", ".jpg", ".jpeg", ".webp"}:
        return extract_text_from_image(path)
    raise CvExtractionError(
        "Unsupported CV extraction format. Supported formats: PDF, DOCX, DOC, PNG, JPG, JPEG, WEBP."
    )


_PDF_TEXT_QUALITY_MIN_LENGTH = 120
_PDF_TEXT_GARBLED_RATIO_THRESHOLD = 0.55


def extract_text_from_pdf(file_path: str | Path) -> CvExtractionResult:
    """Extract text from a PDF CV.

    The extractor prefers a layout-aware PyMuPDF reading order when the optional
    dependency is available. If that path is unavailable or yields low-quality
    text, the legacy ``pypdf`` extractor serves as a safety fallback. Finally,
    if both text paths produce thin or garbled output, the extractor renders
    the PDF pages as images and OCRs them before picking the best candidate.
    """
    path = Path(file_path)
    layout_attempt = _extract_pdf_text_with_layout(path)
    if _is_high_quality_pdf_text(layout_attempt):
        return layout_attempt  # type: ignore[return-value]

    pypdf_attempt = _extract_pdf_text_with_pypdf(path)
    if _is_high_quality_pdf_text(pypdf_attempt):
        return pypdf_attempt

    ocr_attempt = _extract_pdf_text_with_ocr(path)
    candidates: list[CvExtractionResult] = []
    if layout_attempt is not None:
        candidates.append(layout_attempt)
    candidates.append(pypdf_attempt)
    if ocr_attempt is not None:
        candidates.append(ocr_attempt)

    return _pick_best_pdf_candidate(candidates) or pypdf_attempt


def _is_high_quality_pdf_text(result: CvExtractionResult | None) -> bool:
    if result is None or result.extracted_text is None:
        return False
    text = result.extracted_text
    if len(text) < _PDF_TEXT_QUALITY_MIN_LENGTH:
        return False
    return not _looks_like_garbled_pdf_text(text)


def _looks_like_garbled_pdf_text(text: str) -> bool:
    """Detect obviously broken text output (mostly non-letters, CID artifacts)."""
    if not text:
        return True
    sample = text[:2000]
    if "\uFFFD" in sample or sample.count("(cid:") >= 3:
        return True
    letters = sum(ch.isalpha() for ch in sample)
    if letters == 0:
        return True
    non_alnum = sum(not ch.isalnum() and not ch.isspace() for ch in sample)
    non_alnum_ratio = non_alnum / max(len(sample), 1)
    letter_ratio = letters / max(len(sample), 1)
    if non_alnum_ratio > _PDF_TEXT_GARBLED_RATIO_THRESHOLD and letter_ratio < 0.3:
        return True
    return False


def _pick_best_pdf_candidate(
    candidates: list[CvExtractionResult],
) -> CvExtractionResult | None:
    """Choose the most useful extraction candidate among PDF attempts."""
    best: CvExtractionResult | None = None
    best_score = -1
    for candidate in candidates:
        if candidate.extracted_text is None:
            continue
        text = candidate.extracted_text
        score = len(text)
        if _looks_like_garbled_pdf_text(text):
            score = score // 4
        if score > best_score:
            best_score = score
            best = candidate
    return best


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
            extraction_method=CV_EXTRACTION_METHOD_PDF_TEXT,
            used_ocr=False,
        )

    return CvExtractionResult(
        extracted_text=ordered_text,
        parse_status=derive_cv_parse_status(ordered_text),
        page_count=page_count,
        extraction_method=CV_EXTRACTION_METHOD_PDF_TEXT,
        used_ocr=False,
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
        extraction_method=CV_EXTRACTION_METHOD_PDF_TEXT,
        used_ocr=False,
    )


def extract_text_from_docx(file_path: str | Path) -> CvExtractionResult:
    """Extract text from a DOCX CV.

    Reads body content in document order (paragraphs and top-level tables mixed)
    plus section headers, section footers, and nested tables. Cells are joined
    with ``" | "`` so downstream parsers can still split pipe-separated layouts.
    """
    path = Path(file_path)
    try:
        from docx import Document
        from docx.document import Document as _DocumentType
        from docx.oxml.ns import qn
        from docx.table import Table, _Cell
        from docx.text.paragraph import Paragraph
    except ImportError as exc:  # pragma: no cover
        raise CvExtractionError(
            "DOCX extraction requires the 'python-docx' package to be installed."
        ) from exc

    try:
        document = Document(str(path))
    except Exception as exc:  # pragma: no cover
        raise CvExtractionError(f"Failed to read DOCX file: {path.name}") from exc

    blocks: list[str] = []
    seen_blocks: set[str] = set()

    def push(value: str | None) -> None:
        cleaned = normalize_extracted_text(value)
        if not cleaned:
            return
        if cleaned in seen_blocks:
            return
        seen_blocks.add(cleaned)
        blocks.append(cleaned)

    def render_cell(cell: "_Cell") -> str:
        parts: list[str] = []
        for child in _iter_block_items(cell, Paragraph, Table, qn):
            if isinstance(child, Paragraph):
                text = normalize_extracted_text(child.text)
                if text:
                    parts.append(text)
            elif isinstance(child, Table):
                nested_rows = _render_table_rows(child, render_cell)
                if nested_rows:
                    parts.append("\n".join(nested_rows))
        return " ".join(part for part in parts if part)

    def _render_table_rows(table: "Table", renderer) -> list[str]:
        rendered: list[str] = []
        seen_keys: set[tuple[str, ...]] = set()
        for row in table.rows:
            cells = [renderer(cell) for cell in row.cells]
            cells = [cell for cell in cells if cell]
            if not cells:
                continue
            key = tuple(cells)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            rendered.append(" | ".join(cells))
        return rendered

    # Body content in document order so paragraphs and tables stay interleaved.
    for block in _iter_block_items(document, Paragraph, Table, qn):
        if isinstance(block, Paragraph):
            push(block.text)
        elif isinstance(block, Table):
            for row_line in _render_table_rows(block, render_cell):
                push(row_line)

    # Section headers and footers (often contain name, contact, and page labels).
    for section in getattr(document, "sections", []):
        for part in _iter_header_footer_parts(section):
            for block in _iter_block_items(part, Paragraph, Table, qn):
                if isinstance(block, Paragraph):
                    push(block.text)
                elif isinstance(block, Table):
                    for row_line in _render_table_rows(block, render_cell):
                        push(row_line)

    combined_text = normalize_extracted_text("\n\n".join(blocks))
    return CvExtractionResult(
        extracted_text=combined_text,
        parse_status=derive_cv_parse_status(combined_text),
        page_count=1,
        extraction_method=CV_EXTRACTION_METHOD_DOCX_TEXT,
        used_ocr=False,
    )


def extract_text_from_doc(file_path: str | Path) -> CvExtractionResult:
    """Extract text from a legacy binary Word ``.doc`` CV when host tools exist.

    Python's ``python-docx`` only reads modern OOXML ``.docx`` files. For older
    ``.doc`` files we deliberately use local, shell-free command invocations in
    this order: ``antiword``, ``catdoc``, then LibreOffice/soffice conversion.
    If none are installed the caller receives a clear ``CvExtractionError``.
    """
    path = Path(file_path)
    word_kind = _detect_legacy_word_container(path)
    if word_kind == "docx_zip":
        return extract_text_from_docx(path)
    if word_kind == "unknown":
        raise CvExtractionError(
            f"Legacy .doc file does not look like a Word binary/RTF document: {path.name}"
        )

    attempts: list[str] = []

    for tool in ("antiword", "catdoc"):
        executable = shutil.which(tool)
        if executable is None:
            continue
        attempts.append(tool)
        try:
            completed = subprocess.run(
                [executable, str(path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except Exception:
            continue
        if completed.returncode == 0 and completed.stdout.strip():
            text = normalize_extracted_text(completed.stdout)
            return CvExtractionResult(
                extracted_text=text,
                parse_status=derive_cv_parse_status(text),
                page_count=1,
                extraction_method=CV_EXTRACTION_METHOD_DOC_TEXT,
                used_ocr=False,
            )

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is not None:
        attempts.append("soffice")
        try:
            with tempfile.TemporaryDirectory(prefix="hiring_radar_doc_") as tmpdir:
                completed = subprocess.run(
                    [
                        soffice,
                        "--headless",
                        "--convert-to",
                        "txt:Text",
                        "--outdir",
                        tmpdir,
                        str(path),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                if completed.returncode == 0:
                    text_files = sorted(Path(tmpdir).glob("*.txt"))
                    if text_files:
                        raw_text = text_files[0].read_text(encoding="utf-8", errors="ignore")
                        text = normalize_extracted_text(raw_text)
                        return CvExtractionResult(
                            extracted_text=text,
                            parse_status=derive_cv_parse_status(text),
                            page_count=1,
                            extraction_method=CV_EXTRACTION_METHOD_DOC_TEXT,
                            used_ocr=False,
                        )
        except Exception:
            pass

    attempted = ", ".join(attempts) if attempts else "none available"
    raise CvExtractionError(
        "Legacy .doc extraction requires antiword, catdoc, or LibreOffice/soffice "
        f"on the host system (attempted: {attempted})."
    )


def _detect_legacy_word_container(path: Path) -> str:
    """Return a coarse container kind for files uploaded with a ``.doc`` suffix."""
    try:
        header = path.read_bytes()[:16]
    except Exception:
        return "unknown"
    if header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"):
        return "ole_doc"
    if header.lstrip().startswith(b"{\\rtf"):
        return "rtf"
    if header.startswith(b"PK\x03\x04"):
        return "docx_zip"
    return "unknown"


def _iter_block_items(parent, Paragraph, Table, qn):
    """Yield paragraphs and tables in document order from a docx container.

    Accepts a Document, _Cell, or _Header/_Footer — anything with an underlying
    ``element`` exposing a body of ``w:p``/``w:tbl`` children.
    """
    try:
        from docx.document import Document as _DocumentType
        from docx.oxml.table import CT_Tbl
        from docx.oxml.text.paragraph import CT_P
        from docx.table import _Cell
    except ImportError:  # pragma: no cover
        return

    element = getattr(parent, "element", None)
    if element is None:
        element = getattr(parent, "_element", None)
    if element is None:
        return

    body = element.body if hasattr(element, "body") else element
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _iter_header_footer_parts(section):
    """Yield unique header/footer parts attached to a docx section."""
    seen_ids: set[int] = set()
    for attr in ("header", "first_page_header", "even_page_header",
                 "footer", "first_page_footer", "even_page_footer"):
        part = getattr(section, attr, None)
        if part is None:
            continue
        if getattr(part, "is_linked_to_previous", False):
            continue
        part_id = id(part)
        if part_id in seen_ids:
            continue
        seen_ids.add(part_id)
        yield part


def extract_text_from_image(file_path: str | Path) -> CvExtractionResult:
    """Extract text from an image CV using OCR with layout-aware preprocessing."""
    path = Path(file_path)
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise CvExtractionError(
            "Image extraction requires the 'Pillow' package to be installed."
        ) from exc

    try:
        image = Image.open(path)
    except Exception as exc:  # pragma: no cover
        raise CvExtractionError(f"Failed to read image file: {path.name}") from exc

    try:
        prepared_image = _prepare_image_for_ocr(image)
        ocr_lang = _resolve_ocr_languages()
        extracted_text = _ocr_image_to_text(prepared_image, lang=ocr_lang)
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
        extraction_method=CV_EXTRACTION_METHOD_IMAGE_OCR,
        used_ocr=True,
    )


_OSD_MIN_CONFIDENCE = 6.0


def _prepare_image_for_ocr(image):
    """Normalize an image for OCR.

    Pipeline order matters: convert to grayscale and scale up BEFORE running
    OSD orientation detection. Running OSD on a palette-mode (P) or RGB image
    that has a coloured background can produce false orientation signals because
    the colour palette looks like inverted text to Tesseract's classifier.
    Converting to grayscale first eliminates that false signal.

    Steps:
      1. EXIF transpose (physical camera rotation embedded in metadata)
      2. Grayscale conversion (removes colour palette / channel confusion)
      3. Upscale to ≥1500 px on the short side (better OSD + OCR accuracy)
      4. OSD-based orientation correction with confidence gate
      5. Auto-contrast normalisation
      6. Gentle sharpening
    """
    from PIL import Image, ImageFilter, ImageOps

    prepared = ImageOps.exif_transpose(image) if image is not None else image
    prepared = ImageOps.grayscale(prepared)

    min_dimension = min(prepared.width, prepared.height) if prepared else 0
    if min_dimension and min_dimension < 1500:
        scale_factor = max(2, 1500 // min_dimension)
        prepared = prepared.resize(
            (prepared.width * scale_factor, prepared.height * scale_factor),
            Image.LANCZOS,
        )

    # Run OSD only on the clean grayscale image so colour palettes cannot
    # produce a false orientation signal.
    prepared = _correct_image_orientation(prepared)
    prepared = ImageOps.autocontrast(prepared, cutoff=1)
    prepared = prepared.filter(ImageFilter.SHARPEN)
    return prepared


def _correct_image_orientation(image):
    """Detect and correct coarse page rotation using Tesseract OSD.

    Only applies the rotation when OSD reports a confidence above
    ``_OSD_MIN_CONFIDENCE``.  Low-confidence signals (< 6.0) are common on
    decorative or colourful page backgrounds and are unreliable — acting on
    them rotates correctly-oriented images and destroys OCR quality.
    """
    try:
        import pytesseract
    except ImportError:
        return image

    try:
        osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
    except Exception:
        return image

    conf = float(osd.get("orientation_conf", 0) or 0)
    if conf < _OSD_MIN_CONFIDENCE:
        return image

    rotate = int(osd.get("rotate", 0) or 0) % 360
    if rotate in {90, 180, 270}:
        try:
            return image.rotate(-rotate, expand=True)
        except Exception:
            return image
    return image


def _resolve_ocr_languages() -> str:
    ocr_lang = os.environ.get(CV_OCR_LANG_ENV_VAR, "").strip()
    if ocr_lang:
        return ocr_lang
    return _detect_ocr_languages()


def _extract_pdf_text_with_ocr(file_path: Path) -> CvExtractionResult | None:
    """Render each PDF page as an image and OCR it.

    Requires the optional PyMuPDF dependency (``fitz``). Returns ``None`` when
    the dependency is unavailable so the caller can gracefully fall back to a
    text-only result rather than raising.
    """
    try:
        import fitz  # type: ignore
    except ImportError:
        return None

    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return None

    try:
        document = fitz.open(file_path)
    except Exception:
        return None

    ocr_lang = _resolve_ocr_languages()
    page_count = 0
    page_texts: list[str] = []

    try:
        for page_index in range(document.page_count):
            page_count += 1
            try:
                page = document.load_page(page_index)
                matrix = fitz.Matrix(2.0, 2.0)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes(
                    "RGB",
                    (pixmap.width, pixmap.height),
                    pixmap.samples,
                )
            except Exception:
                continue

            try:
                prepared = _prepare_image_for_ocr(image)
                page_text = _ocr_image_to_text(prepared, lang=ocr_lang)
            except CvExtractionError:
                continue
            except Exception:
                continue

            normalized_page = normalize_extracted_text(page_text)
            if normalized_page:
                page_texts.append(normalized_page)
    finally:
        try:
            document.close()
        except Exception:
            pass

    combined_text = normalize_extracted_text("\n\n".join(page_texts))
    return CvExtractionResult(
        extracted_text=combined_text,
        parse_status=derive_cv_parse_status(combined_text),
        page_count=page_count or 1,
        extraction_method=CV_EXTRACTION_METHOD_PDF_OCR,
        used_ocr=True,
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
    """Run OCR over a prepared image.

    Primary strategy: bounding-box-based column-aware reconstruction using
    ``image_to_data``. For multi-column CVs this produces correctly ordered
    text (left column first, then right) instead of interleaved lines that
    confuse downstream parsers.

    Fallback: if the bounding-box path fails or produces no output, the
    function retries with PSM 3/4/6 and returns the highest-scoring result.
    """
    try:
        import pytesseract
        from pytesseract import TesseractNotFoundError
    except ImportError as exc:  # pragma: no cover
        raise CvExtractionError(
            "Image OCR requires the 'pytesseract' package to be installed."
        ) from exc

    # --- Primary: column-aware bounding-box reconstruction -----------------
    try:
        column_text = _ocr_image_column_aware(image, lang=lang)
        if column_text and _score_ocr_output(column_text) > 0:
            return column_text
    except TesseractNotFoundError as exc:
        raise CvExtractionError(
            "Image OCR requires the Tesseract binary to be installed on the host system."
        ) from exc
    except Exception:
        pass

    # --- Fallback: PSM sweep ------------------------------------------------
    results: list[str] = []
    for psm in (6, 4, 3):
        try:
            text = pytesseract.image_to_string(
                image,
                lang=lang,
                config=f"--psm {psm}",
            )
        except TesseractNotFoundError as exc:
            raise CvExtractionError(
                "Image OCR requires the Tesseract binary to be installed on the host system."
            ) from exc
        except Exception:
            continue
        if text:
            results.append(text)

    if not results:
        return ""

    return max(results, key=_score_ocr_output)


# -- Column-aware OCR helpers ------------------------------------------------

_MIN_WORD_CONF = 30
_TWO_COLUMN_MIN_WORDS_PER_SIDE = 8
_TWO_COLUMN_MIN_BALANCE_RATIO = 0.07
_COL_SPLIT_SEARCH_RANGE = (0.25, 0.82)


def _ocr_image_column_aware(image, *, lang: str) -> str:
    """Extract text respecting multi-column layout via bounding-box analysis.

    Uses Tesseract's ``image_to_data`` to obtain per-word bounding boxes,
    then detects whether the document is likely two-column by looking for a
    significant horizontal gap in the middle portion of the page. If two
    columns are found the text is reconstructed as left column → blank line
    → right column so downstream parsers receive correctly ordered content.

    Some CV templates keep the header/profile as a full-width single column
    and switch to two columns only from a paired heading such as
    ``İŞ DENEYİMİ`` + ``EĞİTİM``.  A full-page split would cut the profile
    paragraph in half, so detect that late two-column start first.
    """
    import pytesseract

    data = pytesseract.image_to_data(
        image,
        lang=lang,
        config="--psm 3",
        output_type=pytesseract.Output.DICT,
    )
    words = _parse_ocr_word_data(data)
    if not words:
        return ""

    page_width = image.width

    late_column_text = _reconstruct_late_two_column_text(words, page_width)
    if late_column_text:
        return late_column_text

    col_split, is_two_column = _detect_column_split(words, page_width)

    if not is_two_column:
        return _words_to_ordered_text(words)

    left_words = [
        w for w in words if w["cx"] < col_split
    ]
    right_words = [
        w for w in words if w["cx"] >= col_split
    ]
    left_text = _words_to_ordered_text(left_words)
    right_text = _words_to_ordered_text(right_words)
    if left_text and right_text:
        return f"{left_text}\n\n{right_text}"
    return left_text or right_text


def _parse_ocr_word_data(data: dict) -> list[dict]:
    """Convert Tesseract image_to_data output into a filtered word list."""
    words: list[dict] = []
    text_list = data.get("text", [])
    for i in range(len(text_list)):
        text = str(text_list[i]).strip()
        if not text:
            continue
        try:
            conf = int(data["conf"][i])
        except (ValueError, TypeError, IndexError):
            conf = -1
        if conf < _MIN_WORD_CONF:
            continue
        left = int(data["left"][i])
        top = int(data["top"][i])
        width = int(data["width"][i])
        height = int(data["height"][i])
        words.append(
            {
                "text": text,
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "cx": left + width // 2,
            }
        )
    return words


def _detect_column_split(
    words: list[dict], page_width: int
) -> tuple[int, bool]:
    """Return (split_x, is_two_column) by finding the largest X gap in the
    middle third of the page.  Returns (page_width//2, False) when the
    layout doesn't look two-column.
    """
    if not words:
        return page_width // 2, False

    x_starts = sorted({w["left"] for w in words})
    lo = int(page_width * _COL_SPLIT_SEARCH_RANGE[0])
    hi = int(page_width * _COL_SPLIT_SEARCH_RANGE[1])

    max_gap = 0
    col_split = page_width // 2
    for i in range(1, len(x_starts)):
        gap = x_starts[i] - x_starts[i - 1]
        mid = (x_starts[i] + x_starts[i - 1]) // 2
        if lo < mid < hi and gap > max_gap:
            max_gap = gap
            col_split = mid

    left_count = sum(1 for w in words if w["cx"] < col_split)
    right_count = sum(1 for w in words if w["cx"] >= col_split)
    total = len(words)
    balance = min(left_count, right_count) / max(total, 1)

    is_two_column = (
        max_gap > page_width * 0.04
        and left_count >= _TWO_COLUMN_MIN_WORDS_PER_SIDE
        and right_count >= _TWO_COLUMN_MIN_WORDS_PER_SIDE
        and balance >= _TWO_COLUMN_MIN_BALANCE_RATIO
    )
    return col_split, is_two_column


def _reconstruct_late_two_column_text(words: list[dict], page_width: int) -> str | None:
    """Reconstruct templates that become two-column only after the profile.

    Detects a paired section-header line (for example ``İŞ DENEYİMİ`` on the
    left and ``EĞİTİM`` on the right).  Lines above that header remain in
    normal reading order; words from the paired header down are reconstructed
    as left column followed by right column.
    """
    grouped_lines = _group_ocr_words_into_lines(words)
    if len(grouped_lines) < 3:
        return None

    for line in grouped_lines:
        split_x = _detect_dual_section_header_split(line, page_width)
        if split_x is None:
            continue

        cut_top = max(0, int(line["top"] - line["height"] * 0.5))
        preamble_words = [word for word in words if word["top"] < cut_top]
        column_words = [word for word in words if word["top"] >= cut_top]
        left_words = [word for word in column_words if word["cx"] < split_x]
        right_words = [word for word in column_words if word["cx"] >= split_x]

        if len(left_words) < _TWO_COLUMN_MIN_WORDS_PER_SIDE:
            continue
        if len(right_words) < _TWO_COLUMN_MIN_WORDS_PER_SIDE:
            continue

        parts = [
            _words_to_ordered_text(preamble_words),
            _words_to_ordered_text(left_words),
            _words_to_ordered_text(right_words),
        ]
        parts = [part for part in parts if part]
        if len(parts) >= 2:
            return "\n\n".join(parts)

    return None


def _detect_dual_section_header_split(line: dict, page_width: int) -> int | None:
    line_words = sorted(line.get("words", []), key=lambda word: word["left"])
    if len(line_words) < 3:
        return None

    text = _normalize_ocr_header_text(" ".join(word["text"] for word in line_words))
    if not (
        _contains_any_header_marker(text, _EXPERIENCE_HEADER_MARKERS)
        and _contains_any_header_marker(text, _EDUCATION_HEADER_MARKERS)
    ):
        return None

    gaps: list[tuple[int, int, int]] = []
    for index in range(1, len(line_words)):
        previous_right = line_words[index - 1]["left"] + line_words[index - 1]["width"]
        current_left = line_words[index]["left"]
        gap = current_left - previous_right
        if gap <= 0:
            continue
        split_x = (previous_right + current_left) // 2
        if page_width * 0.25 < split_x < page_width * 0.85:
            gaps.append((gap, index, split_x))

    if not gaps:
        return None

    gap, index, split_x = max(gaps, key=lambda item: item[0])
    if gap < max(24, int(page_width * 0.035)):
        return None

    left_text = _normalize_ocr_header_text(
        " ".join(word["text"] for word in line_words[:index])
    )
    right_text = _normalize_ocr_header_text(
        " ".join(word["text"] for word in line_words[index:])
    )

    left_is_experience = _contains_any_header_marker(
        left_text, _EXPERIENCE_HEADER_MARKERS
    )
    left_is_education = _contains_any_header_marker(left_text, _EDUCATION_HEADER_MARKERS)
    right_is_experience = _contains_any_header_marker(
        right_text, _EXPERIENCE_HEADER_MARKERS
    )
    right_is_education = _contains_any_header_marker(right_text, _EDUCATION_HEADER_MARKERS)

    if (left_is_experience and right_is_education) or (
        left_is_education and right_is_experience
    ):
        return split_x
    return None


_EXPERIENCE_HEADER_MARKERS = frozenset(
    {
        "experience",
        "work experience",
        "is deneyimi",
        "is deneyim",
        "deneyimi",
        "deneyim",
    }
)
_EDUCATION_HEADER_MARKERS = frozenset(
    {
        "education",
        "egitim",
        "ogrenim",
        "akademik gecmis",
    }
)


def _normalize_ocr_header_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    # Turkish dotless i is not a combining-mark variant of ``i``; normalize it
    # explicitly so OCR text like ``İŞ`` / ``IS`` / ``IŞ`` share one key.
    without_marks = without_marks.replace("ı", "i").replace("I", "i")
    without_marks = without_marks.casefold()
    without_marks = re.sub(r"[^a-z0-9çğıöşü\s]", " ", without_marks)
    without_marks = re.sub(r"\s+", " ", without_marks).strip()
    return without_marks


def _contains_any_header_marker(text: str, markers: frozenset[str]) -> bool:
    return any(marker in text for marker in markers)


def _group_ocr_words_into_lines(words: list[dict]) -> list[dict]:
    """Group OCR word boxes into line dictionaries with text and geometry."""
    if not words:
        return []

    avg_height = sum(w["height"] for w in words) / len(words)
    line_threshold = max(avg_height * 0.6, 4)

    sorted_words = sorted(words, key=lambda w: (w["top"], w["left"]))
    grouped: list[dict] = []
    current_words: list[dict] = [sorted_words[0]]
    current_top = sorted_words[0]["top"]

    def flush() -> None:
        if not current_words:
            return
        current_words.sort(key=lambda word: word["left"])
        grouped.append(
            {
                "words": list(current_words),
                "text": " ".join(word["text"] for word in current_words),
                "top": min(word["top"] for word in current_words),
                "height": max(word["height"] for word in current_words),
                "left": min(word["left"] for word in current_words),
                "right": max(word["left"] + word["width"] for word in current_words),
            }
        )

    for word in sorted_words[1:]:
        if abs(word["top"] - current_top) <= line_threshold:
            current_words.append(word)
            continue
        flush()
        current_words = [word]
        current_top = word["top"]

    flush()
    return grouped


def _words_to_ordered_text(words: list[dict]) -> str:
    """Reconstruct text from a list of words by grouping into lines."""
    return "\n".join(
        line["text"] for line in _group_ocr_words_into_lines(words) if line["text"]
    )


def _score_ocr_output(text: str) -> int:
    """Rough quality score for OCR output — rewards letters over noise."""
    if not text:
        return 0
    letters = sum(ch.isalpha() for ch in text)
    words = sum(1 for token in text.split() if any(ch.isalpha() for ch in token))
    return letters + words * 2
