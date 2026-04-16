from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from hiring_radar.services import cv_extraction
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_EMPTY,
    CV_PARSE_STATUS_PARSED,
    CvExtractionError,
    derive_cv_parse_status,
    extract_text_from_cv_file,
    normalize_extracted_text,
)

SIMPLE_TEXT_PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144]
/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 55 >>
stream
BT
/F1 18 Tf
50 100 Td
(Hello Alice CV) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000063 00000 n 
0000000122 00000 n 
0000000248 00000 n 
0000000353 00000 n 
trailer
<< /Root 1 0 R /Size 6 >>
startxref
423
%%EOF
"""


def test_normalize_extracted_text_collapses_whitespace() -> None:
    raw_text = "  Alice\r\n\r\n\r\nPython\t FastAPI  "
    assert normalize_extracted_text(raw_text) == "Alice\n\nPython FastAPI"
    assert normalize_extracted_text("   ") is None


def test_derive_cv_parse_status_distinguishes_text_and_empty() -> None:
    assert derive_cv_parse_status("Alice Example") == CV_PARSE_STATUS_PARSED
    assert derive_cv_parse_status(None) == CV_PARSE_STATUS_EMPTY


def test_extract_text_from_pdf_returns_parsed_status_for_text_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "alice_cv.pdf"
    pdf_path.write_bytes(SIMPLE_TEXT_PDF_BYTES)

    result = extract_text_from_cv_file(pdf_path)

    assert result.parse_status == CV_PARSE_STATUS_PARSED
    assert result.page_count == 1
    assert result.extracted_text == "Hello Alice CV"


def test_extract_text_from_pdf_returns_empty_status_for_blank_pdf(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "blank_cv.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=144)
    with pdf_path.open("wb") as handle:
        writer.write(handle)

    result = extract_text_from_cv_file(pdf_path)

    assert result.parse_status == CV_PARSE_STATUS_EMPTY
    assert result.page_count == 1
    assert result.extracted_text is None


def test_extract_text_from_docx_returns_parsed_status(tmp_path: Path) -> None:
    from docx import Document

    docx_path = tmp_path / "alice_cv.docx"
    document = Document()
    document.add_paragraph("Alice Example")
    document.add_paragraph("Senior Backend Engineer")
    document.add_paragraph("Python, FastAPI, SQL")
    document.save(docx_path)

    result = extract_text_from_cv_file(docx_path)

    assert result.parse_status == CV_PARSE_STATUS_PARSED
    assert result.page_count == 1
    assert result.extracted_text is not None
    assert "Alice Example" in result.extracted_text
    assert "Senior Backend Engineer" in result.extracted_text
    assert "Python, FastAPI, SQL" in result.extracted_text


def test_extract_text_from_png_returns_parsed_status(tmp_path: Path, monkeypatch) -> None:
    from PIL import Image

    png_path = tmp_path / "alice_cv.png"
    Image.new("RGB", (240, 120), color="white").save(png_path)

    monkeypatch.setattr(
        cv_extraction,
        "_ocr_image_to_text",
        lambda _image, *, lang: "Alice Example\nSenior Backend Engineer\nPython",
    )

    result = extract_text_from_cv_file(png_path)

    assert result.parse_status == CV_PARSE_STATUS_PARSED
    assert result.page_count == 1
    assert result.extracted_text == "Alice Example\nSenior Backend Engineer\nPython"


def test_extract_text_from_cv_file_rejects_legacy_doc_files(tmp_path: Path) -> None:
    doc_path = tmp_path / "alice_cv.doc"
    doc_path.write_bytes(b"fake-doc")

    with pytest.raises(CvExtractionError, match="Supported formats"):
        extract_text_from_cv_file(doc_path)


def test_normalize_extracted_text_uses_foundation_cleanup_rules() -> None:
    raw_text = "\ufeffAlice\u200b Example\r\n\r\n•••\r\nPython\t FastAPI\r\nPage 1 of 1"
    assert normalize_extracted_text(raw_text) == "Alice Example\n\nPython FastAPI"



def test_extract_text_from_pdf_prefers_layout_aware_reading_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = tmp_path / "alice_cv.pdf"
    pdf_path.write_bytes(SIMPLE_TEXT_PDF_BYTES)

    ordered_text = "Alice Example\n\nSenior Backend Engineer\n\nPython"
    monkeypatch.setattr(
        cv_extraction,
        "_extract_pdf_text_with_layout",
        lambda _path: cv_extraction.CvExtractionResult(
            extracted_text=ordered_text,
            parse_status=CV_PARSE_STATUS_PARSED,
            page_count=1,
        ),
    )

    result = extract_text_from_cv_file(pdf_path)

    assert result.extracted_text == ordered_text
    assert result.parse_status == CV_PARSE_STATUS_PARSED


def test_extract_text_from_pdf_falls_back_to_pypdf_when_layout_is_unavailable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = tmp_path / "alice_cv.pdf"
    pdf_path.write_bytes(SIMPLE_TEXT_PDF_BYTES)

    monkeypatch.setattr(cv_extraction, "_extract_pdf_text_with_layout", lambda _path: None)

    result = extract_text_from_cv_file(pdf_path)

    assert result.extracted_text == "Hello Alice CV"
    assert result.page_count == 1
