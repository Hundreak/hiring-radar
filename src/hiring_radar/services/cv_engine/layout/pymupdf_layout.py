from __future__ import annotations

from pathlib import Path
from typing import Any

from hiring_radar.services.cv_engine.config import LayoutAnalysisConfig
from hiring_radar.services.cv_engine.exceptions import RecoverableStageError
from hiring_radar.services.cv_engine.layout.column_detection import detect_columns_for_page
from hiring_radar.services.cv_engine.layout.reading_order import reconstruct_reading_order
from hiring_radar.services.cv_engine.models import LayoutAnalysisArtifact, LayoutTextBlock, ParserStageName


class PyMuPdfLayoutAnalyzer:
    """Lightweight PDF layout analyzer backed by PyMuPDF blocks."""

    def analyze_pdf(
        self,
        *,
        file_path: str | Path,
        config: LayoutAnalysisConfig,
    ) -> LayoutAnalysisArtifact:
        path = Path(file_path)
        if not config.enabled:
            return LayoutAnalysisArtifact()

        try:
            import fitz  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on optional backend
            raise RecoverableStageError(
                ParserStageName.LAYOUT_ANALYSIS,
                "PyMuPDF is not installed; layout-aware PDF parsing is unavailable.",
            ) from exc

        try:
            document = fitz.open(path)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise RecoverableStageError(
                ParserStageName.LAYOUT_ANALYSIS,
                f"Failed to open PDF layout source: {path.name}",
            ) from exc

        pages = []
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            width = float(page.rect.width)
            height = float(page.rect.height)
            raw = page.get_text("dict")
            blocks = _convert_raw_blocks(
                raw_blocks=raw.get("blocks", []),
                page_number=page_index,
                config=config,
            )
            pages.append(
                detect_columns_for_page(
                    page_number=page_index,
                    page_width=width,
                    page_height=height,
                    blocks=blocks,
                    config=config,
                )
            )

        return reconstruct_reading_order(pages=pages, config=config)


def _convert_raw_blocks(
    *,
    raw_blocks: list[dict[str, Any]],
    page_number: int,
    config: LayoutAnalysisConfig,
) -> list[LayoutTextBlock]:
    converted: list[LayoutTextBlock] = []

    for block_index, block in enumerate(raw_blocks):
        if block.get("type") != 0:
            continue

        bbox = block.get("bbox") or [0.0, 0.0, 0.0, 0.0]
        lines = block.get("lines") or []
        text_fragments: list[str] = []
        max_font_size = 0.0
        font_names: set[str] = set()

        for line in lines:
            spans = line.get("spans") or []
            line_fragments: list[str] = []
            for span in spans:
                span_text = str(span.get("text") or "").strip()
                if not span_text:
                    continue
                line_fragments.append(span_text)
                max_font_size = max(max_font_size, float(span.get("size") or 0.0))
                font_name = str(span.get("font") or "").strip()
                if font_name:
                    font_names.add(font_name)
            if line_fragments:
                text_fragments.append(" ".join(line_fragments))

        text = "\n".join(fragment for fragment in text_fragments if fragment).strip()
        if len(text) < config.minimum_block_text_length:
            continue

        x0, y0, x1, y1 = [float(value) for value in bbox]
        if (y1 - y0) < config.minimum_block_height:
            continue

        converted.append(
            LayoutTextBlock(
                page_number=page_number,
                text=text,
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                block_index=block_index,
                metadata={
                    "font_names": sorted(font_names),
                    "max_font_size": max_font_size,
                },
            )
        )

    return converted
