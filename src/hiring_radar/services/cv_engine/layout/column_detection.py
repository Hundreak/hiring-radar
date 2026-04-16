from __future__ import annotations

from hiring_radar.services.cv_engine.config import LayoutAnalysisConfig
from hiring_radar.services.cv_engine.models import LayoutColumn, LayoutPage, LayoutTextBlock


def detect_columns_for_page(
    *,
    page_number: int,
    page_width: float,
    page_height: float,
    blocks: list[LayoutTextBlock],
    config: LayoutAnalysisConfig,
) -> LayoutPage:
    """Cluster page blocks into reading columns.

    The implementation intentionally stays lightweight and deterministic:
    sorted blocks are scanned left-to-right and merged into the same column when
    their horizontal centers are close enough. This is robust for the vast
    majority of résumé layouts without introducing an ML dependency.
    """
    if not blocks:
        return LayoutPage(
            page_number=page_number,
            width=page_width,
            height=page_height,
            blocks=[],
            columns=[],
            is_multi_column=False,
        )

    threshold = max(page_width * config.column_merge_gap_ratio, 36.0)
    sorted_blocks = sorted(blocks, key=lambda item: (item.center_x, item.y0, item.block_index))
    clusters: list[list[LayoutTextBlock]] = []

    for block in sorted_blocks:
        if not clusters:
            clusters.append([block])
            continue

        previous_cluster = clusters[-1]
        previous_centers = [item.center_x for item in previous_cluster]
        previous_center = sum(previous_centers) / len(previous_centers)
        if abs(block.center_x - previous_center) <= threshold:
            previous_cluster.append(block)
        elif len(clusters) < config.max_columns:
            clusters.append([block])
        else:
            previous_cluster.append(block)

    columns: list[LayoutColumn] = []
    for index, cluster in enumerate(clusters):
        column_x0 = min(item.x0 for item in cluster)
        column_x1 = max(item.x1 for item in cluster)
        sorted_cluster = sorted(cluster, key=lambda item: (item.y0, item.x0, item.block_index))
        column_width = max(column_x1 - column_x0, 0.0)
        columns.append(
            LayoutColumn(
                index=index,
                x0=column_x0,
                x1=column_x1,
                blocks=sorted_cluster,
                is_sidebar=(column_width / max(page_width, 1.0)) <= config.sidebar_width_ratio,
                metadata={"block_count": len(sorted_cluster)},
            )
        )

    columns.sort(key=lambda item: item.x0)
    for index, column in enumerate(columns):
        column.index = index

    return LayoutPage(
        page_number=page_number,
        width=page_width,
        height=page_height,
        blocks=sorted(blocks, key=lambda item: (item.y0, item.x0, item.block_index)),
        columns=columns,
        is_multi_column=len(columns) > 1,
        metadata={"column_count": len(columns), "threshold": threshold},
    )
