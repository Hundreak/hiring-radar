from __future__ import annotations

from hiring_radar.services.cv_engine.config import LayoutAnalysisConfig
from hiring_radar.services.cv_engine.layout.column_detection import detect_columns_for_page
from hiring_radar.services.cv_engine.layout.reading_order import (
    layout_artifact_to_text,
    reconstruct_reading_order,
)
from hiring_radar.services.cv_engine.models import LayoutTextBlock


def test_reconstruct_reading_order_prefers_main_column_before_left_sidebar() -> None:
    config = LayoutAnalysisConfig()
    blocks = [
        LayoutTextBlock(
            page_number=0,
            text="Alice Example",
            x0=20.0,
            y0=10.0,
            x1=560.0,
            y1=60.0,
            block_index=0,
        ),
        LayoutTextBlock(
            page_number=0,
            text="Python\nFastAPI\nSQL",
            x0=20.0,
            y0=80.0,
            x1=150.0,
            y1=200.0,
            block_index=1,
        ),
        LayoutTextBlock(
            page_number=0,
            text="Senior Backend Engineer",
            x0=210.0,
            y0=90.0,
            x1=550.0,
            y1=120.0,
            block_index=2,
        ),
        LayoutTextBlock(
            page_number=0,
            text="ACME Corp\n2021 - Present",
            x0=210.0,
            y0=130.0,
            x1=550.0,
            y1=220.0,
            block_index=3,
        ),
    ]
    page = detect_columns_for_page(
        page_number=0,
        page_width=600.0,
        page_height=800.0,
        blocks=blocks,
        config=config,
    )

    artifact = reconstruct_reading_order(pages=[page], config=config)
    ordered_text = [item.text for item in artifact.reading_order_blocks]

    assert ordered_text == [
        "Alice Example",
        "Senior Backend Engineer",
        "ACME Corp\n2021 - Present",
        "Python\nFastAPI\nSQL",
    ]
    assert layout_artifact_to_text(artifact).startswith("Alice Example")
