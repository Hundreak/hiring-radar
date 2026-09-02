from __future__ import annotations

from hiring_radar.services.cv_engine.config import LayoutAnalysisConfig
from hiring_radar.services.cv_engine.models import (
    LayoutAnalysisArtifact,
    LayoutPage,
    LayoutTextBlock,
)


def reconstruct_reading_order(
    *,
    pages: list[LayoutPage],
    config: LayoutAnalysisConfig,
) -> LayoutAnalysisArtifact:
    """Create a document-level reading order from analyzed pages.

    Full-width header blocks are emitted first, then main content columns, and
    finally narrow sidebars. This reduces the classic issue where left sidebars
    (skills, tools, contact) get interleaved before the main experience stream.
    """
    ordered_blocks: list[LayoutTextBlock] = []
    document_multi_column = False

    for page in sorted(pages, key=lambda item: item.page_number):
        if page.is_multi_column:
            document_multi_column = True

        full_width_blocks: list[LayoutTextBlock] = []
        column_blocks: list[LayoutTextBlock] = []
        page_width = max(page.width, 1.0)

        for block in sorted(page.blocks, key=lambda item: (item.y0, item.x0, item.block_index)):
            if (block.width / page_width) >= config.full_width_ratio:
                full_width_blocks.append(block)
            else:
                column_blocks.append(block)

        ordered_blocks.extend(full_width_blocks)
        if not page.columns:
            ordered_blocks.extend(column_blocks)
            continue

        main_columns = [column for column in page.columns if not column.is_sidebar]
        sidebar_columns = [column for column in page.columns if column.is_sidebar]

        if not main_columns:
            main_columns = page.columns
            sidebar_columns = []

        ordered_columns = sorted(main_columns, key=lambda item: item.x0) + sorted(
            sidebar_columns,
            key=lambda item: item.x0,
        )

        seen_ids = {id(block) for block in full_width_blocks}
        for column in ordered_columns:
            for block in column.blocks:
                if id(block) in seen_ids:
                    continue
                ordered_blocks.append(block)
                seen_ids.add(id(block))

    return LayoutAnalysisArtifact(
        pages=pages,
        reading_order_blocks=ordered_blocks,
        is_multi_column_document=document_multi_column,
        metadata={"page_count": len(pages), "ordered_block_count": len(ordered_blocks)},
    )


def layout_artifact_to_text(layout: LayoutAnalysisArtifact) -> str:
    """Flatten a layout artifact into reading-order text."""
    lines = [block.text.strip() for block in layout.reading_order_blocks if block.text.strip()]
    return "\n\n".join(lines)
