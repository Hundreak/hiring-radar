from hiring_radar.services.cv_local_diagnostics import LocalCvInspectionResult
from hiring_radar.services.cv_profile_draft import (
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)


def test_local_cv_inspection_to_dict_exposes_cli_friendly_aliases() -> None:
    draft = build_cv_profile_draft(
        full_name="Cormac Turing",
        email="cormac.c.turing@gmail.com",
        headline="Mechanical Engineer",
        skills=("3D CAD", "Leadership"),
    )
    snapshot = build_cv_profile_draft_snapshot(
        generated_at="1970-01-01T00:00:00Z",
        source_filename="engineering_resumelab.png",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        draft=draft,
    )
    result = LocalCvInspectionResult(
        path="/home/remzi/Desktop/CV/engineering_resumelab.png",
        filename="engineering_resumelab.png",
        supported=True,
        success=True,
        file_format="png",
        content_type="image/png",
        file_size_bytes=104_618,
        parse_status="parsed",
        extraction_method="image_ocr",
        used_ocr=True,
        snapshot=snapshot,
    )

    payload = result.to_dict()

    assert payload["parse_status"] == "parsed"
    assert payload["extraction_method"] == "image_ocr"
    assert payload["snapshot"]["draft"]["full_name"] == "Cormac Turing"
    assert payload["status"] == "parsed"
    assert payload["method"] == "image_ocr"
    assert payload["draft"]["email"] == "cormac.c.turing@gmail.com"
    assert payload["draft"]["skills"] == ["3D CAD", "Leadership"]
