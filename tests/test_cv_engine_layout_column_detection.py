from __future__ import annotations

from hiring_radar.services.cv_engine.config import LayoutAnalysisConfig
from hiring_radar.services.cv_engine.layout.column_detection import detect_columns_for_page
from hiring_radar.services.cv_engine.models import LayoutTextBlock


def test_detect_columns_for_page_splits_sidebar_and_main_column() -> None:
    config = LayoutAnalysisConfig()
    blocks = [
        LayoutTextBlock(
            page_number=0,
            text="Python\nFastAPI\nSQL",
            x0=20.0,
            y0=80.0,
            x1=150.0,
            y1=200.0,
            block_index=0,
        ),
        LayoutTextBlock(
            page_number=0,
            text="Senior Backend Engineer",
            x0=210.0,
            y0=90.0,
            x1=550.0,
            y1=130.0,
            block_index=1,
        ),
        LayoutTextBlock(
            page_number=0,
            text="Built distributed systems.",
            x0=210.0,
            y0=150.0,
            x1=550.0,
            y1=250.0,
            block_index=2,
        ),
    ]

    page = detect_columns_for_page(
        page_number=0,
        page_width=600.0,
        page_height=800.0,
        blocks=blocks,
        config=config,
    )

    assert page.is_multi_column is True
    assert len(page.columns) == 2
    assert page.columns[0].is_sidebar is True
    assert page.columns[1].is_sidebar is False
    assert [item.text for item in page.columns[1].blocks] == [
        "Senior Backend Engineer",
        "Built distributed systems.",
    ]
