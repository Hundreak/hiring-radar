from __future__ import annotations

from hiring_radar.services.cv_engine.extraction.normalization import (
    normalize_extracted_text,
)



def test_normalize_extracted_text_removes_bullets_zero_width_and_noise() -> None:
    raw_text = (
        "\ufeffAlice Example\u200b\n"
        "Senior Backend Engineer\n"
        "•• Python\n"
        "----\n"
        "Page 1 of 2\n"
        "  FastAPI   PostgreSQL  \n"
    )

    artifact = normalize_extracted_text(raw_text)

    assert artifact.lines == [
        "Alice Example",
        "Senior Backend Engineer",
        "Python",
        "FastAPI PostgreSQL",
    ]
    assert artifact.removed_noise_fragments == ["----", "Page 1 of 2"]
    assert artifact.metadata["removed_noise_count"] == 2



def test_normalize_extracted_text_preserves_single_blank_line_blocks() -> None:
    raw_text = "Summary\n\n\nBuilt APIs\n\n\nSkills\nPython\n"

    artifact = normalize_extracted_text(raw_text)

    assert artifact.lines == ["Summary", "", "Built APIs", "", "Skills", "Python"]
    assert artifact.text == "Summary\n\nBuilt APIs\n\nSkills\nPython"
