from __future__ import annotations

from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.enterprise.runtime import (
    get_parse_cache_store,
)
from hiring_radar.services.cv_engine.legacy_runtime import (
    build_foundation_parser_result_from_text,
)


def test_foundation_runtime_uses_exact_cache_hit_on_second_parse() -> None:
    store = get_parse_cache_store()
    store.clear()

    text = """
Alice Example
Senior Backend Engineer
alice@example.com

Professional Summary
Backend engineer with strong FastAPI experience.

Technical Skills
Python
FastAPI
SQL
"""
    config = ParserRuntimeConfig()

    first_result = build_foundation_parser_result_from_text(
        extracted_text=text,
        filename="alice_cv.pdf",
        config=config,
    )
    second_result = build_foundation_parser_result_from_text(
        extracted_text=text,
        filename="alice_cv.pdf",
        config=config,
    )

    first_cache = first_result.context.metadata["enterprise"]["cache"]
    second_cache = second_result.context.metadata["enterprise"]["cache"]

    assert first_cache["status"] == "miss"
    assert second_cache["status"] == "exact_hit"
    assert second_cache["exact_reusable"] is True
