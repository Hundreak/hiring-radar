from __future__ import annotations

from hiring_radar.services.cv_profile_confidence import (
    CV_CONFIDENCE_HIGH,
    CV_CONFIDENCE_LOW,
    CV_CONFIDENCE_MEDIUM,
    build_cv_profile_confidence_report,
)
from hiring_radar.services.cv_profile_draft import (
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)


def test_build_cv_profile_confidence_report_scores_rich_snapshot_high() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=10,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T22:00:00Z",
        draft=build_cv_profile_draft(
            headline="Senior Backend Engineer",
            summary=(
                "Backend engineer with 8+ years of experience building "
                "FastAPI services, data platforms and recruiter tooling."
            ),
            skills=["Python", "FastAPI", "SQL", "Docker", "AWS"],
            target_roles=["Staff Backend Engineer", "Platform Engineer"],
            preferred_locations=["Berlin"],
            remote_preference="remote",
            education_entries=[
                build_cv_draft_education_entry(
                    school_name="METU",
                    degree_name="BSc Electrical Engineering",
                    start_year=2012,
                    end_year=2017,
                )
            ],
            experience_entries=[
                build_cv_draft_experience_entry(
                    title="Senior Backend Engineer",
                    company_name="ACME",
                    start_year=2021,
                    end_year=None,
                    summary="Built matching systems.",
                )
            ],
            language_entries=[
                build_cv_draft_language_entry(
                    language_name="English",
                    proficiency_level="C1",
                ),
                build_cv_draft_language_entry(
                    language_name="Turkish",
                    proficiency_level="Native",
                ),
            ],
        ),
    )

    report = build_cv_profile_confidence_report(snapshot)

    assert report.headline.level == CV_CONFIDENCE_HIGH
    assert report.summary.level == CV_CONFIDENCE_HIGH
    assert report.skills.level == CV_CONFIDENCE_HIGH
    assert report.target_roles.level == CV_CONFIDENCE_HIGH
    assert report.preferred_locations.level == CV_CONFIDENCE_MEDIUM
    assert report.remote_preference.level == CV_CONFIDENCE_MEDIUM
    assert report.education_entries.level == CV_CONFIDENCE_HIGH
    assert report.experience_entries.level == CV_CONFIDENCE_HIGH
    assert report.language_entries.level == CV_CONFIDENCE_HIGH
    assert report.high_confidence_field_count() >= 6
    assert report.low_confidence_field_names() == ()


def test_build_cv_profile_confidence_report_marks_sparse_snapshot_low() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=11,
        source_filename="sparse_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T22:05:00Z",
        draft=build_cv_profile_draft(
            headline="Developer",
            skills=["Python"],
            education_entries=[],
            experience_entries=[],
            language_entries=[
                build_cv_draft_language_entry(language_name="English")
            ],
        ),
    )

    report = build_cv_profile_confidence_report(snapshot)

    assert report.headline.level == CV_CONFIDENCE_MEDIUM
    assert report.summary.level == CV_CONFIDENCE_LOW
    assert report.skills.level == CV_CONFIDENCE_LOW
    assert report.target_roles.level == CV_CONFIDENCE_LOW
    assert report.preferred_locations.level == CV_CONFIDENCE_LOW
    assert report.remote_preference.level == CV_CONFIDENCE_LOW
    assert report.education_entries.level == CV_CONFIDENCE_LOW
    assert report.experience_entries.level == CV_CONFIDENCE_LOW
    assert report.language_entries.level == CV_CONFIDENCE_LOW
    assert "summary" in report.low_confidence_field_names()
    assert "experience_entries" in report.low_confidence_field_names()