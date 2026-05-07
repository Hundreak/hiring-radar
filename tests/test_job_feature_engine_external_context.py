from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import CanonicalJob, JobExternalContextSnapshot
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features


def _repo(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / 'job_feature_external.db'))
    return HiringRadarRepository(connection)


def test_refresh_matching_readiness_features_merges_external_context_terms(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    try:
        job = repo.upsert_canonical_job(
            CanonicalJob(
                canonical_key='acme|platform-engineer|remote',
                normalized_title='platform engineer',
                normalized_company_name='acme',
                display_title='Platform Engineer',
                display_company_name='Acme',
                location_city='Remote',
                workplace_type='remote',
                employment_type='full_time',
                seniority='senior',
                description_text='Senior platform engineer role. Build internal platforms and maintain Kubernetes infrastructure.',
                apply_url='https://jobs.example.com/platform-engineer',
                trust_score=0.95,
                freshness_score=0.92,
                is_active=True,
                created_at='2026-04-19T09:00:00Z',
                updated_at='2026-04-19T09:00:00Z',
            )
        )
        repo.upsert_job_external_context_snapshot(
            JobExternalContextSnapshot(
                source_url='https://jobs.example.com/platform-engineer',
                final_url='https://jobs.example.com/platform-engineer',
                source_domain='jobs.example.com',
                fetch_status='cached',
                http_status=200,
                page_title='Platform Engineer',
                clean_text='Requirements: Terraform, AWS, Kubernetes. Responsibilities: own reliability and drive architecture.',
                site_specific_requirements=('Terraform experience', 'AWS production systems', 'Kubernetes operations'),
                responsibility_clues=('Own platform reliability', 'Drive architecture decisions'),
                technology_stack_terms=('terraform', 'aws', 'kubernetes'),
                source_metadata_json={
                    'raw_capture_metadata': {
                        'quantitative_signals': {
                            'min_experience_years': 4,
                            'required_scripting_languages': ['python'],
                            'requires_linux': True,
                            'preferred_cloud_platforms': ['aws'],
                            'preferred_virtualization_terms': ['openstack'],
                            'support_model_terms': ['on-call'],
                        }
                    }
                },
                fetched_at='2026-04-19T08:55:00Z',
                expires_at='2026-04-19T12:00:00Z',
                updated_at='2026-04-19T08:55:00Z',
            )
        )

        result = refresh_matching_readiness_features(
            repo,
            refreshed_at='2026-04-19T09:05:00Z',
            canonical_job_ids=[job.id or 0],
        )

        feature = result.features[0]
        assert 'terraform' in feature.external_requirement_terms
        assert 'linux' in feature.external_requirement_terms
        assert 'aws' in feature.external_technology_terms
        assert 'openstack' in feature.preferred_skill_terms
        assert feature.years_experience_min == 4
        assert feature.external_context_status == 'cached'
        assert feature.external_context_updated_at == '2026-04-19T08:55:00Z'
        assert 'terraform' in feature.skill_terms
        assert feature.responsibility_scope in {'architect', 'senior-ic', 'tech-lead'}
    finally:
        repo.close()
