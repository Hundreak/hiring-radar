from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import (
    CanonicalJob,
    JobSource,
    JobSourceRecord,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
)
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.matching.engine import rank_canonical_jobs_for_subscriber
from hiring_radar.services.matching.profile_features import refresh_subscriber_profile_features


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "matching_engine.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)
    yield repo
    repo.close()


def _create_source(repository: HiringRadarRepository) -> JobSource:
    return repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme",
            trust_score=0.96,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T08:00:00Z",
            updated_at="2026-04-18T08:00:00Z",
        )
    )


def _persist_job(repository: HiringRadarRepository, source: JobSource, *, external_job_id: str, title: str, location_text: str, description_text: str, canonical_key: str, category: str | None = None, department: str | None = None, workplace_type: str | None = None, employment_type: str | None = None, seniority: str | None = None, trust_score: float = 0.95, freshness_score: float = 0.9) -> CanonicalJob:
    source_record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id=external_job_id,
            raw_payload_json='{"title": "placeholder"}',
            raw_payload_hash=f"hash-{external_job_id}",
            canonical_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
            title=title,
            company_name="Acme",
            location_text=location_text,
            posted_at="2026-04-18",
            apply_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
            fetched_at="2026-04-18T08:10:00Z",
            is_active=True,
        )
    )
    job = repository.upsert_canonical_job(
        CanonicalJob(
            canonical_key=canonical_key,
            normalized_title=title.casefold(),
            normalized_company_name="acme",
            display_title=title,
            display_company_name="Acme",
            location_city=location_text.split(',')[0],
            country="Turkey" if "Istanbul" in location_text else "Germany" if "Berlin" in location_text else None,
            workplace_type=workplace_type,
            employment_type=employment_type,
            seniority=seniority,
            category=category,
            department=department,
            description_text=description_text,
            posted_at="2026-04-18",
            apply_url=f"https://boards.greenhouse.io/acme/jobs/{external_job_id}",
            trust_score=trust_score,
            freshness_score=freshness_score,
            is_active=True,
            created_at="2026-04-18T08:12:00Z",
            updated_at="2026-04-18T08:12:00Z",
        )
    )
    repository.upsert_canonical_job_link(
        link=__import__('hiring_radar.models', fromlist=['CanonicalJobLink']).CanonicalJobLink(
            canonical_job_id=job.id or 0,
            source_job_id=source_record.id or 0,
            merge_reason="unit_test_link",
            confidence=0.99,
            created_at="2026-04-18T08:13:00Z",
            updated_at="2026-04-18T08:13:00Z",
        )
    )
    return job


def test_rank_canonical_jobs_for_subscriber_orders_high_fit_jobs_first(repository: HiringRadarRepository) -> None:
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
        summary="Python backend engineer focused on distributed APIs and platform systems.",
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
                start_year=2018,
                end_year=2021,
                summary="Built Python/FastAPI services on AWS.",
            ),
            SubscriberExperienceEntry(
                title="Senior Platform Engineer",
                company_name="Beta",
                start_year=2021,
                end_year=None,
                summary="Managed Docker and Kubernetes-based deployment platforms.",
            ),
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
        entries=[
            SubscriberLanguageEntry(language_name="English", proficiency_level="C1"),
        ],
        updated_at="2026-04-18T09:04:00Z",
    )
    refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:05:00Z",
    )

    source = _create_source(repository)
    strong_job = _persist_job(
        repository,
        source,
        external_job_id="backend-1",
        title="Senior Backend Engineer",
        location_text="Remote, Turkey",
        description_text="We are hiring a Senior Backend Engineer with Python, FastAPI, Docker, Kubernetes and English communication skills. At least 5 years of experience required.",
        canonical_key="acme|senior-backend-engineer|remote|backend-1",
        category="software_engineering",
        department="engineering",
        workplace_type="remote",
        employment_type="full_time",
        seniority="senior",
        trust_score=0.96,
        freshness_score=0.94,
    )
    weak_job = _persist_job(
        repository,
        source,
        external_job_id="sales-1",
        title="Retail Sales Associate",
        location_text="Berlin, Germany",
        description_text="Looking for retail sales experience, customer support and cash handling. German language required. On-site position.",
        canonical_key="acme|retail-sales-associate|berlin|sales-1",
        category="sales",
        department="commercial",
        workplace_type="onsite",
        employment_type="full_time",
        seniority="junior",
        trust_score=0.90,
        freshness_score=0.90,
    )

    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:06:00Z",
        canonical_job_ids=[strong_job.id or 0, weak_job.id or 0],
    )

    ranked = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:07:00Z",
        limit=10,
    )

    assert len(ranked) == 2
    assert ranked[0].job.display_title == "Senior Backend Engineer"
    assert ranked[0].result.final_score > ranked[1].result.final_score
    assert ranked[0].result.final_score >= 0.75
    assert "python" in ranked[0].result.matched_skill_terms
    assert ranked[1].result.final_score < 0.5


def test_behavioral_affinity_softly_boosts_ranking_without_overwriting_core_fit(repository: HiringRadarRepository) -> None:
    subscriber, _ = repository.upsert_subscriber(
        email="bob@example.com",
        full_name="Bob Example",
        updated_at="2026-04-18T09:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Data Engineer",
        summary="Python and SQL data engineer open to hybrid work in Istanbul.",
        target_roles=("Data Engineer",),
        skills=("Python", "SQL"),
        preferred_locations=("Istanbul",),
        remote_preference="hybrid",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T09:01:00Z",
    )
    repository.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[SubscriberExperienceEntry(title="Data Engineer", start_year=2020, end_year=None, summary="Built SQL pipelines.")],
        updated_at="2026-04-18T09:02:00Z",
    )
    refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:03:00Z",
    )
    source = _create_source(repository)
    first_job = _persist_job(
        repository,
        source,
        external_job_id="data-1",
        title="Data Engineer",
        location_text="Istanbul, Turkey",
        description_text="Python SQL ETL role. At least 3 years of experience.",
        canonical_key="acme|data-engineer|istanbul|data-1",
        category="data",
        department="data",
        workplace_type="hybrid",
        employment_type="full_time",
        seniority="mid",
        trust_score=0.95,
        freshness_score=0.95,
    )
    second_job = _persist_job(
        repository,
        source,
        external_job_id="data-2",
        title="Data Engineer",
        location_text="Istanbul, Turkey",
        description_text="Python SQL ETL role. At least 3 years of experience.",
        canonical_key="acme|data-engineer|istanbul|data-2",
        category="data",
        department="data",
        workplace_type="hybrid",
        employment_type="full_time",
        seniority="mid",
        trust_score=0.95,
        freshness_score=0.95,
    )
    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:04:00Z",
        canonical_job_ids=[first_job.id or 0, second_job.id or 0],
    )

    ranked = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:05:00Z",
        behavioral_affinity_by_job_id={second_job.id or 0: 1.0},
    )

    assert ranked[0].job.id == second_job.id
    assert ranked[0].result.final_score >= ranked[1].result.final_score
    assert ranked[0].result.fit_score == pytest.approx(ranked[1].result.fit_score, abs=0.03)


def test_experience_description_evidence_improves_deterministic_fit(repository: HiringRadarRepository) -> None:
    source = _create_source(repository)
    job = _persist_job(
        repository,
        source,
        external_job_id="platform-1",
        title="Senior Platform Engineer",
        location_text="Remote, Turkey",
        description_text=(
            "We need a Senior Platform Engineer with Python, Kubernetes, Docker and observability. "
            "The role owns platform reliability, incident response, automation and technical direction. "
            "At least 5 years of experience required."
        ),
        canonical_key="acme|senior-platform-engineer|remote|platform-1",
        category="software_engineering",
        department="engineering",
        workplace_type="remote",
        employment_type="full_time",
        seniority="senior",
    )
    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:06:00Z",
        canonical_job_ids=[job.id or 0],
    )

    strong_subscriber, _ = repository.upsert_subscriber(
        email="rich-evidence@example.com",
        full_name="Rich Evidence",
        updated_at="2026-04-18T10:00:00Z",
    )
    strong_id = strong_subscriber.id or 0
    repository.upsert_subscriber_profile(
        strong_id,
        phone=None,
        headline="Senior Platform Engineer",
        summary="Python platform engineer focused on reliability and automation.",
        target_roles=("Platform Engineer",),
        skills=("Python", "Kubernetes", "Docker"),
        preferred_locations=("Remote",),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T10:01:00Z",
    )
    repository.replace_subscriber_experience_entries(
        strong_id,
        entries=[
            SubscriberExperienceEntry(
                title="Senior Platform Engineer",
                company_name="Acme",
                start_year=2020,
                end_year=None,
                summary=(
                    "Owned Kubernetes platform reliability, incident response, observability and automation. "
                    "Led technical direction for Docker-based deployment workflows."
                ),
            )
        ],
        updated_at="2026-04-18T10:02:00Z",
    )
    refresh_subscriber_profile_features(
        repository,
        subscriber_id=strong_id,
        refreshed_at="2026-04-18T10:03:00Z",
    )

    weak_subscriber, _ = repository.upsert_subscriber(
        email="flat-evidence@example.com",
        full_name="Flat Evidence",
        updated_at="2026-04-18T10:10:00Z",
    )
    weak_id = weak_subscriber.id or 0
    repository.upsert_subscriber_profile(
        weak_id,
        phone=None,
        headline="Senior Platform Engineer",
        summary="Interested in platform roles.",
        target_roles=("Platform Engineer",),
        skills=("Python", "Kubernetes", "Docker"),
        preferred_locations=("Remote",),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T10:11:00Z",
    )
    repository.replace_subscriber_experience_entries(
        weak_id,
        entries=[
            SubscriberExperienceEntry(
                title="Engineer",
                company_name="Beta",
                start_year=2020,
                end_year=None,
                summary="Worked on engineering tasks across the team.",
            )
        ],
        updated_at="2026-04-18T10:12:00Z",
    )
    refresh_subscriber_profile_features(
        repository,
        subscriber_id=weak_id,
        refreshed_at="2026-04-18T10:13:00Z",
    )

    strong_ranked = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=strong_id,
        refreshed_at="2026-04-18T10:14:00Z",
        limit=1,
    )
    weak_ranked = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=weak_id,
        refreshed_at="2026-04-18T10:15:00Z",
        limit=1,
    )

    assert strong_ranked and weak_ranked
    assert strong_ranked[0].result.final_score > weak_ranked[0].result.final_score
    assert strong_ranked[0].result.fit_score > weak_ranked[0].result.fit_score
    assert strong_ranked[0].result.components[0].raw_score > weak_ranked[0].result.components[0].raw_score

def test_external_job_context_increases_catalog_confidence_for_same_role(repository: HiringRadarRepository) -> None:
    subscriber, _ = repository.upsert_subscriber(
        email="context-aware@example.com",
        full_name="Context Aware",
        updated_at="2026-04-18T11:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Senior Platform Engineer",
        summary="Platform engineer focused on Python, Docker, Kubernetes and AWS.",
        target_roles=("Platform Engineer",),
        skills=("Python", "Docker", "Kubernetes", "AWS"),
        preferred_locations=("Remote",),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T11:01:00Z",
    )
    repository.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                title="Senior Platform Engineer",
                company_name="Acme",
                start_year=2019,
                end_year=None,
                summary="Owned AWS-based platform reliability with Docker and Kubernetes.",
            )
        ],
        updated_at="2026-04-18T11:02:00Z",
    )
    refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T11:03:00Z",
    )

    source = _create_source(repository)
    baseline_job = _persist_job(
        repository,
        source,
        external_job_id="platform-baseline",
        title="Senior Platform Engineer",
        location_text="Remote, Turkey",
        description_text="Senior Platform Engineer role with Python, Docker, Kubernetes and AWS. Minimum 5 years.",
        canonical_key="acme|senior-platform-engineer|remote|baseline",
        category="software_engineering",
        department="engineering",
        workplace_type="remote",
        employment_type="full_time",
        seniority="senior",
        trust_score=0.95,
        freshness_score=0.92,
    )
    enriched_job = _persist_job(
        repository,
        source,
        external_job_id="platform-enriched",
        title="Senior Platform Engineer",
        location_text="Remote, Turkey",
        description_text="Senior Platform Engineer role with Python, Docker, Kubernetes and AWS. Minimum 5 years.",
        canonical_key="acme|senior-platform-engineer|remote|enriched",
        category="software_engineering",
        department="engineering",
        workplace_type="remote",
        employment_type="full_time",
        seniority="senior",
        trust_score=0.95,
        freshness_score=0.92,
    )

    repository.upsert_job_external_context_snapshot(
        __import__('hiring_radar.models', fromlist=['JobExternalContextSnapshot']).JobExternalContextSnapshot(
            source_url=enriched_job.apply_url,
            final_url=enriched_job.apply_url,
            source_domain="boards.greenhouse.io",
            fetch_status="ok",
            http_status=200,
            page_title="Senior Platform Engineer – Acme",
            clean_text=(
                "Requirements: Python, Docker, Kubernetes, AWS. "
                "Responsibilities: own platform reliability, drive architecture, and mentor engineers."
            ),
            site_specific_requirements=("Python", "Docker", "Kubernetes", "AWS"),
            responsibility_clues=("Own platform reliability", "Drive architecture", "Mentor engineers"),
            technology_stack_terms=("python", "docker", "kubernetes", "aws"),
            fetched_at="2026-04-18T11:04:00Z",
            expires_at="2026-04-19T11:04:00Z",
            updated_at="2026-04-18T11:04:00Z",
        )
    )

    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T11:05:00Z",
        canonical_job_ids=[baseline_job.id or 0, enriched_job.id or 0],
    )

    ranked = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T11:06:00Z",
        limit=10,
    )

    by_title = {item.job.id: item for item in ranked}
    baseline_match = by_title[baseline_job.id]
    enriched_match = by_title[enriched_job.id]

    assert enriched_match.result.catalog_score > baseline_match.result.catalog_score
    assert enriched_match.result.final_score >= baseline_match.result.final_score - 0.01



def test_sparse_job_content_is_ranked_more_cautiously_than_rich_equivalent_role(repository: HiringRadarRepository) -> None:
    subscriber, _ = repository.upsert_subscriber(
        email="calibration@example.com",
        full_name="Calibration Example",
        updated_at="2026-04-18T09:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Senior Backend Engineer",
        summary="Python backend engineer focused on FastAPI, Docker and Kubernetes.",
        target_roles=("Backend Engineer",),
        skills=("Python", "FastAPI", "Docker", "Kubernetes"),
        preferred_locations=("Remote",),
        remote_preference="remote",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at="2026-04-18T09:01:00Z",
    )
    repository.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                title="Senior Backend Engineer",
                company_name="Acme",
                start_year=2018,
                end_year=None,
                summary="Built Python, FastAPI, Docker and Kubernetes systems in production.",
            )
        ],
        updated_at="2026-04-18T09:02:00Z",
    )
    refresh_subscriber_profile_features(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:03:00Z",
    )

    source = _create_source(repository)
    sparse_job = _persist_job(
        repository,
        source,
        external_job_id="backend-sparse",
        title="Senior Backend Engineer",
        location_text="Remote, Turkey",
        description_text="Senior Backend Engineer. Python required.",
        canonical_key="acme|senior-backend-engineer|remote|backend-sparse",
        category="software_engineering",
        department="engineering",
        workplace_type="remote",
        employment_type="full_time",
        seniority="senior",
    )
    rich_job = _persist_job(
        repository,
        source,
        external_job_id="backend-rich",
        title="Senior Backend Engineer",
        location_text="Remote, Turkey",
        description_text=(
            "We are hiring a Senior Backend Engineer to build Python and FastAPI services with Docker and Kubernetes. "
            "Required skills include Python, FastAPI, Docker, Kubernetes and English communication. "
            "You will own backend APIs, partner with product and design, and work on distributed systems. "
            "At least 5 years of experience required."
        ),
        canonical_key="acme|senior-backend-engineer|remote|backend-rich",
        category="software_engineering",
        department="engineering",
        workplace_type="remote",
        employment_type="full_time",
        seniority="senior",
    )

    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:04:00Z",
        canonical_job_ids=[sparse_job.id or 0, rich_job.id or 0],
    )

    ranked = rank_canonical_jobs_for_subscriber(
        repository,
        subscriber_id=subscriber_id,
        refreshed_at="2026-04-18T09:05:00Z",
        limit=10,
    )

    by_title = {item.job.apply_url.rsplit('/', 1)[-1]: item for item in ranked}
    assert by_title["backend-rich"].result.catalog_score > by_title["backend-sparse"].result.catalog_score
    assert by_title["backend-sparse"].result.final_score - by_title["backend-rich"].result.final_score < 0.05
