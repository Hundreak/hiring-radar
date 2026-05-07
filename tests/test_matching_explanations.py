from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import (
    CanonicalJob,
    CanonicalJobLink,
    JobSource,
    JobSourceRecord,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
)
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.matching import ExplanationGenerator, rank_canonical_jobs_for_subscriber
from hiring_radar.services.matching.profile_features import refresh_subscriber_profile_features


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / "matching_explanations.db"))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


def _seed_ranked_match(repository: HiringRadarRepository):
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-18T09:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Senior Backend Engineer",
        summary="Python backend engineer focused on FastAPI, Docker and cloud delivery.",
        target_roles=("Backend Engineer", "Platform Engineer"),
        skills=("Python", "FastAPI", "Docker", "Kubernetes"),
        preferred_locations=("Istanbul", "Remote"),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T09:01:00Z",
    )
    repository.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                title="Backend Engineer",
                company_name="Acme",
                start_year=2019,
                end_year=None,
                summary="Built Python and FastAPI services deployed with Docker.",
            )
        ],
        updated_at="2026-04-18T09:02:00Z",
    )
    repository.replace_subscriber_education_entries(
        subscriber_id,
        entries=[
            SubscriberEducationEntry(
                school_name="Example University",
                degree_name="Bachelor of Science",
                field_of_study="Computer Engineering",
                start_year=2014,
                end_year=2018,
            )
        ],
        updated_at="2026-04-18T09:03:00Z",
    )
    repository.replace_subscriber_language_entries(
        subscriber_id,
        entries=[SubscriberLanguageEntry(language_name="English", proficiency_level="C1")],
        updated_at="2026-04-18T09:04:00Z",
    )
    refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:05:00Z",
    )

    source = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme",
            trust_score=0.97,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T08:00:00Z",
            updated_at="2026-04-18T08:00:00Z",
        )
    )
    source_record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="backend-1",
            raw_payload_json='{"title":"Senior Backend Engineer"}',
            raw_payload_hash="hash-backend-1",
            canonical_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            title="Senior Backend Engineer",
            company_name="Acme",
            location_text="Remote, Turkey",
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            fetched_at="2026-04-18T08:10:00Z",
            is_active=True,
        )
    )
    job = repository.upsert_canonical_job(
        CanonicalJob(
            canonical_key="acme|senior-backend-engineer|remote|backend-1",
            normalized_title="senior backend engineer",
            normalized_company_name="acme",
            display_title="Senior Backend Engineer",
            display_company_name="Acme",
            location_city="Remote",
            country="Turkey",
            workplace_type="remote",
            employment_type="full_time",
            seniority="senior",
            category="software_engineering",
            department="engineering",
            description_text=(
                "We are hiring a Senior Backend Engineer with Python, FastAPI, Docker, Kubernetes and English communication skills. "
                "GraphQL is a plus. Minimum 5 years of experience required."
            ),
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            trust_score=0.97,
            freshness_score=0.94,
            is_active=True,
            created_at="2026-04-18T08:12:00Z",
            updated_at="2026-04-18T08:12:00Z",
        )
    )
    repository.upsert_canonical_job_link(
        CanonicalJobLink(
            canonical_job_id=job.id or 0,
            source_job_id=source_record.id or 0,
            merge_reason="unit_test_link",
            confidence=0.99,
            created_at="2026-04-18T08:13:00Z",
            updated_at="2026-04-18T08:13:00Z",
        )
    )
    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:06:00Z",
        canonical_job_ids=[job.id or 0],
    )

    ranked = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:07:00Z",
        limit=10,
    )
    assert ranked
    return ranked[0]


def test_explanation_generator_builds_structured_payload(repository: HiringRadarRepository) -> None:
    ranked_match = _seed_ranked_match(repository)

    payload = ExplanationGenerator().generate_for_ranked_match(ranked_match)

    assert payload.top_reasons
    assert payload.matching_score_breakdown
    assert payload.key_evidence_points
    assert payload.gap_analysis
    assert payload.summary == payload.top_reasons[0]
    assert any(item.component_key == "skill_alignment" for item in payload.matching_score_breakdown)
    assert any(point.code == "skill_overlap_high" for point in payload.key_evidence_points)
    assert any(gap.code == "skill_gap_detected" for gap in payload.gap_analysis)
    assert "Python" in payload.key_evidence_points[0].detail or "python" in payload.key_evidence_points[0].detail.lower()
    assert payload.external_source_insights.enrichment_status == "unavailable"


def test_explanation_generator_produces_safe_legacy_fallback() -> None:
    payload = ExplanationGenerator().generate_for_legacy_job(
        title="Security Engineer",
        company_name="Trendyol",
        matched=True,
        match_score=67,
        matched_keywords=("security", "python"),
    )

    assert payload.top_reasons
    assert payload.matching_score_breakdown[0].component_key == "legacy_keyword_alignment"
    assert payload.key_evidence_points[0].code == "legacy_keywords_matched"
    assert payload.final_score == pytest.approx(0.67)
    assert payload.external_source_insights.enrichment_status == "unavailable"


def test_explanation_generator_caps_legacy_scores_below_deterministic_perfect_match() -> None:
    payload = ExplanationGenerator().generate_for_legacy_job(
        title="Platform Engineer",
        company_name="Acme",
        matched=True,
        match_score=100,
        matched_keywords=("platform",),
    )

    assert payload.final_score == pytest.approx(0.78)
    assert payload.fit_score == pytest.approx(0.78)

def test_explanation_generator_mentions_source_enriched_skill_context(repository: HiringRadarRepository) -> None:
    ranked_match = _seed_ranked_match(repository)
    repository.upsert_job_external_context_snapshot(
        __import__('hiring_radar.models', fromlist=['JobExternalContextSnapshot']).JobExternalContextSnapshot(
            source_url=ranked_match.job.apply_url,
            final_url=ranked_match.job.apply_url,
            source_domain="boards.greenhouse.io",
            fetch_status="ok",
            http_status=200,
            page_title="Senior Backend Engineer – Acme",
            clean_text="Python FastAPI Docker Kubernetes required. Own backend services.",
            site_specific_requirements=("Python", "FastAPI", "Docker", "Kubernetes"),
            responsibility_clues=("Own backend services",),
            technology_stack_terms=("python", "fastapi", "docker", "kubernetes"),
            fetched_at="2026-04-18T09:08:00Z",
            expires_at="2026-04-19T09:08:00Z",
            updated_at="2026-04-18T09:08:00Z",
        )
    )
    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:09:00Z",
        canonical_job_ids=[ranked_match.job.id or 0],
    )
    ranked_match = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=ranked_match.profile_feature.subscriber_id,
        refreshed_at="2026-04-18T09:10:00Z",
        limit=1,
    )[0]

    payload = ExplanationGenerator().generate_for_ranked_match(ranked_match)

    skill_point = next(point for point in payload.key_evidence_points if point.code == "skill_overlap_high")
    assert "source-enriched job page" in skill_point.detail
    assert payload.analysis_coverage.level == "strong"
    assert "original_source_page" in payload.analysis_coverage.content_sources
    assert any(point.code == "job_content_verified" for point in payload.key_evidence_points)

