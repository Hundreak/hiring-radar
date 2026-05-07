from __future__ import annotations

import pytest

from hiring_radar.models import SubscriberProfile
from hiring_radar.services.cv_profile_apply_execution import (
    CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED,
    CV_PARSE_RUN_APPLY_STATUS_PARTIALLY_APPLIED,
    applied_execution_result_to_dict,
    apply_selected_cv_profile_operations,
    build_cv_selected_apply_operations,
    derive_parse_run_apply_status,
    selected_apply_operations_to_dict,
)
from hiring_radar.services.cv_profile_apply_plan import build_cv_profile_apply_plan
from hiring_radar.services.cv_profile_draft import (
    build_cv_draft_certification_entry,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)


def test_apply_selected_cv_profile_operations_updates_selected_fields() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=5,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T16:00:00Z",
        draft=build_cv_profile_draft(
            headline="Senior Backend Engineer",
            summary="Built reliable FastAPI platforms and matching systems.",
            skills=["Python", "FastAPI", "SQL"],
            target_roles=["Staff Backend Engineer"],
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
                )
            ],
        ),
    )

    profile = SubscriberProfile(
        subscriber_id=1,
        headline=None,
        summary="Existing summary to review before overwrite.",
        target_roles=(),
        skills=("Python",),
        preferred_locations=(),
        remote_preference=None,
    )

    apply_plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
    )
    selection = build_cv_selected_apply_operations(
        scalar_fields=["headline", "summary", "remote_preference"],
        list_fields=["skills", "target_roles", "preferred_locations"],
        education_entry_indexes=[0],
        experience_entry_indexes=[0],
        language_entry_indexes=[0],
    )

    result = apply_selected_cv_profile_operations(
        apply_plan=apply_plan,
        selection=selection,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
    )

    assert result.applied_change_count == 9
    assert result.applied_scalar_fields == (
        "headline",
        "summary",
        "remote_preference",
    )
    assert result.applied_list_fields == (
        "skills",
        "target_roles",
        "preferred_locations",
    )

    assert result.profile.headline == "Senior Backend Engineer"
    assert result.profile.summary == (
        "Built reliable FastAPI platforms and matching systems."
    )
    assert result.profile.remote_preference == "remote"
    assert result.profile.skills == ("Python", "FastAPI", "SQL")
    assert result.profile.target_roles == ("Staff Backend Engineer",)
    assert result.profile.preferred_locations == ("Berlin",)

    assert len(result.education_entries) == 1
    assert result.education_entries[0].school_name == "METU"

    assert len(result.experience_entries) == 1
    assert result.experience_entries[0].company_name == "ACME"

    assert len(result.language_entries) == 1
    assert result.language_entries[0].language_name == "English"


def test_apply_selected_cv_profile_operations_rejects_non_applicable_selection() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=6,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T16:05:00Z",
        draft=build_cv_profile_draft(
            headline="Senior Backend Engineer",
            skills=["Python"],
        ),
    )

    profile = SubscriberProfile(
        subscriber_id=1,
        headline="Senior Backend Engineer",
        summary=None,
        target_roles=(),
        skills=("Python",),
        preferred_locations=(),
        remote_preference=None,
    )

    apply_plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
    )
    selection = build_cv_selected_apply_operations(
        scalar_fields=["headline"],
        list_fields=[],
        education_entry_indexes=[],
        experience_entry_indexes=[],
        language_entry_indexes=[],
    )

    with pytest.raises(ValueError, match="Selected scalar field is not applicable"):
        apply_selected_cv_profile_operations(
            apply_plan=apply_plan,
            selection=selection,
            profile=profile,
            education_entries=[],
            experience_entries=[],
            language_entries=[],
        )


def test_build_cv_selected_apply_operations_rejects_empty_selection() -> None:
    with pytest.raises(ValueError, match="At least one CV apply operation must be selected"):
        build_cv_selected_apply_operations(
            scalar_fields=[],
            list_fields=[],
            education_entry_indexes=[],
            experience_entry_indexes=[],
            language_entry_indexes=[],
        )



def test_derive_parse_run_apply_status_distinguishes_partial_and_full() -> None:
    assert (
        derive_parse_run_apply_status(remaining_actionable_change_count=0)
        == CV_PARSE_RUN_APPLY_STATUS_FULLY_APPLIED
    )
    assert (
        derive_parse_run_apply_status(remaining_actionable_change_count=2)
        == CV_PARSE_RUN_APPLY_STATUS_PARTIALLY_APPLIED
    )


def test_apply_execution_serializers_return_json_ready_payloads() -> None:
    selection = build_cv_selected_apply_operations(
        scalar_fields=["headline"],
        list_fields=["skills"],
        education_entry_indexes=[0],
        experience_entry_indexes=[1],
        language_entry_indexes=[2],
    )

    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=7,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T17:10:00Z",
        draft=build_cv_profile_draft(
            headline="Senior Backend Engineer",
            skills=["Python", "FastAPI"],
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
                ),
                build_cv_draft_experience_entry(
                    title="Backend Engineer",
                    company_name="Example GmbH",
                    start_year=2018,
                    end_year=2021,
                ),
            ],
            language_entries=[
                build_cv_draft_language_entry(
                    language_name="English",
                    proficiency_level="C1",
                ),
                build_cv_draft_language_entry(
                    language_name="German",
                    proficiency_level="B1",
                ),
                build_cv_draft_language_entry(
                    language_name="Turkish",
                    proficiency_level="Native",
                ),
            ],
        ),
    )
    profile = SubscriberProfile(
        subscriber_id=1,
        headline=None,
        summary=None,
        target_roles=(),
        skills=(),
        preferred_locations=(),
        remote_preference=None,
    )
    apply_plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
    )
    result = apply_selected_cv_profile_operations(
        apply_plan=apply_plan,
        selection=selection,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
    )

    selection_payload = selected_apply_operations_to_dict(selection)
    result_payload = applied_execution_result_to_dict(result)

    assert selection_payload == {
        "scalar_fields": ["headline"],
        "list_fields": ["skills"],
        "education_entry_indexes": [0],
        "experience_entry_indexes": [1],
        "language_entry_indexes": [2],
    }
    assert result_payload["applied_scalar_fields"] == ["headline"]
    assert result_payload["applied_list_fields"] == ["skills"]
    assert result_payload["applied_education_entry_indexes"] == [0]
    assert result_payload["applied_experience_entry_indexes"] == [1]
    assert result_payload["applied_language_entry_indexes"] == [2]
    assert result_payload["applied_change_count"] == 5

def test_apply_selected_cv_profile_operations_persists_selected_certification() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=8,
        source_filename="cert_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T18:00:00Z",
        draft=build_cv_profile_draft(
            certification_entries=[
                build_cv_draft_certification_entry(
                    certificate_name="Certified Reliability Engineer",
                    issuer_name="American Society for Quality",
                    issued_year=2013,
                )
            ],
        ),
    )
    profile = SubscriberProfile(subscriber_id=1)
    apply_plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
        certification_entries=[],
    )
    selection = build_cv_selected_apply_operations(
        scalar_fields=[],
        list_fields=[],
        education_entry_indexes=[],
        experience_entry_indexes=[],
        language_entry_indexes=[],
        certification_entry_indexes=[0],
    )

    result = apply_selected_cv_profile_operations(
        apply_plan=apply_plan,
        selection=selection,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
        certification_entries=[],
    )

    assert result.applied_certification_entry_indexes == (0,)
    assert result.applied_change_count == 1
    assert len(result.certification_entries) == 1
    assert (
        result.certification_entries[0].certificate_name
        == "Certified Reliability Engineer"
    )
    assert result.certification_entries[0].issued_year == 2013
    assert selected_apply_operations_to_dict(selection)[
        "certification_entry_indexes"
    ] == [0]
    assert applied_execution_result_to_dict(result)[
        "applied_certification_entry_indexes"
    ] == [0]
