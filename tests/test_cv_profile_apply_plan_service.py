from __future__ import annotations

from hiring_radar.models import (
    SubscriberCertificationEntry,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
    SubscriberProfile,
)
from hiring_radar.services.cv_profile_apply_plan import (
    CV_APPLY_ACTION_ADD_UNIQUE,
    CV_APPLY_ACTION_FILL_MISSING,
    CV_APPLY_ACTION_NOOP,
    CV_APPLY_ACTION_REVIEW_REQUIRED,
    build_cv_profile_apply_plan,
)
from hiring_radar.services.cv_profile_draft import (
    build_cv_draft_certification_entry,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)


def test_build_cv_profile_apply_plan_prefers_safe_non_destructive_changes() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=5,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T15:00:00Z",
        draft=build_cv_profile_draft(
            headline="Senior Backend Engineer",
            summary="Built reliable FastAPI platforms and matching systems.",
            skills=["Python", "FastAPI", "SQL"],
            target_roles=["Staff Backend Engineer"],
            preferred_locations=["Berlin", "Remote"],
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
        phone=None,
        headline=None,
        summary="Existing summary that should not be overwritten automatically.",
        target_roles=("Backend Engineer",),
        skills=("Python",),
        preferred_locations=("Berlin",),
        remote_preference=None,
    )

    plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=profile,
        education_entries=[],
        experience_entries=[],
        language_entries=[],
    )

    assert plan.source_parse_status == "parsed"

    assert plan.headline.action == CV_APPLY_ACTION_FILL_MISSING
    assert plan.headline.default_selected is True
    assert plan.headline.suggested_value == "Senior Backend Engineer"

    assert plan.summary.action == CV_APPLY_ACTION_REVIEW_REQUIRED
    assert plan.summary.default_selected is False

    assert plan.remote_preference.action == CV_APPLY_ACTION_FILL_MISSING
    assert plan.remote_preference.default_selected is True
    assert plan.remote_preference.suggested_value == "remote"

    assert plan.skills.action == CV_APPLY_ACTION_ADD_UNIQUE
    assert plan.skills.items_to_add == ("FastAPI", "SQL")
    assert plan.skills.default_selected is True

    assert plan.target_roles.action == CV_APPLY_ACTION_ADD_UNIQUE
    assert plan.target_roles.items_to_add == ("Staff Backend Engineer",)

    assert plan.preferred_locations.action == CV_APPLY_ACTION_ADD_UNIQUE
    assert plan.preferred_locations.items_to_add == ("Remote",)

    assert len(plan.education_entries) == 1
    assert plan.education_entries[0].action == CV_APPLY_ACTION_ADD_UNIQUE
    assert plan.education_entries[0].default_selected is True

    assert len(plan.experience_entries) == 1
    assert plan.experience_entries[0].action == CV_APPLY_ACTION_ADD_UNIQUE
    assert plan.experience_entries[0].default_selected is True

    assert len(plan.language_entries) == 1
    assert plan.language_entries[0].action == CV_APPLY_ACTION_ADD_UNIQUE
    assert plan.language_entries[0].default_selected is True

    assert plan.has_actionable_changes() is True
    assert plan.default_selected_change_count() == 8


def test_build_cv_profile_apply_plan_skips_duplicate_entries_and_tokens() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=6,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T15:05:00Z",
        draft=build_cv_profile_draft(
            headline="Senior Backend Engineer",
            skills=["Python", "FastAPI"],
            target_roles=["Backend Engineer"],
            preferred_locations=["Berlin"],
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
        headline="Senior Backend Engineer",
        summary=None,
        target_roles=("Backend Engineer",),
        skills=("Python", "FastAPI"),
        preferred_locations=("Berlin",),
        remote_preference=None,
    )

    education_entries = [
        SubscriberEducationEntry(
            id=11,
            subscriber_id=1,
            school_name="METU",
            degree_name="BSc Electrical Engineering",
            field_of_study=None,
            start_year=2012,
            end_year=2017,
        )
    ]
    experience_entries = [
        SubscriberExperienceEntry(
            id=12,
            subscriber_id=1,
            title="Senior Backend Engineer",
            company_name="ACME",
            start_year=2021,
            end_year=None,
            summary=None,
        )
    ]
    language_entries = [
        SubscriberLanguageEntry(
            id=13,
            subscriber_id=1,
            language_name="English",
            proficiency_level="B2",
            notes=None,
        )
    ]

    plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=language_entries,
    )

    assert plan.headline.action == CV_APPLY_ACTION_NOOP
    assert plan.skills.action == CV_APPLY_ACTION_NOOP
    assert plan.target_roles.action == CV_APPLY_ACTION_NOOP
    assert plan.preferred_locations.action == CV_APPLY_ACTION_NOOP

    assert len(plan.education_entries) == 1
    assert plan.education_entries[0].action == CV_APPLY_ACTION_NOOP
    assert plan.education_entries[0].matched_existing_id == 11

    assert len(plan.experience_entries) == 1
    assert plan.experience_entries[0].action == CV_APPLY_ACTION_NOOP
    assert plan.experience_entries[0].matched_existing_id == 12

    assert len(plan.language_entries) == 1
    assert plan.language_entries[0].action == CV_APPLY_ACTION_NOOP
    assert plan.language_entries[0].matched_existing_id == 13

    assert plan.has_actionable_changes() is False
    assert plan.default_selected_change_count() == 0

def test_build_cv_profile_apply_plan_adds_and_deduplicates_certifications() -> None:
    snapshot = build_cv_profile_draft_snapshot(
        source_upload_id=8,
        source_filename="alice_cv.pdf",
        source_parse_status="parsed",
        parser_version="heuristic-v0",
        generated_at="2026-04-06T15:20:00Z",
        draft=build_cv_profile_draft(
            certification_entries=[
                build_cv_draft_certification_entry(
                    certificate_name="Certified Reliability Engineer",
                    issuer_name="American Society for Quality",
                    issued_year=2013,
                ),
                build_cv_draft_certification_entry(
                    certificate_name="GD&T Professional",
                    issuer_name="ASME International",
                    issued_year=2018,
                ),
            ],
        ),
    )

    plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=SubscriberProfile(subscriber_id=1),
        education_entries=[],
        experience_entries=[],
        language_entries=[],
        certification_entries=[
            SubscriberCertificationEntry(
                id=21,
                subscriber_id=1,
                certificate_name="Certified Reliability Engineer",
                issuer_name="American Society for Quality",
                issued_year=2013,
            )
        ],
    )

    assert len(plan.certification_entries) == 2
    assert plan.certification_entries[0].action == CV_APPLY_ACTION_NOOP
    assert plan.certification_entries[0].matched_existing_id == 21
    assert plan.certification_entries[1].action == CV_APPLY_ACTION_ADD_UNIQUE
    assert plan.certification_entries[1].default_selected is True
