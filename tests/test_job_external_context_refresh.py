from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import JobExternalContextSnapshot, JobRecord
from hiring_radar.services.jobs.external_context_refresh import hydrate_job_url


def _make_repository(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / 'external_context_refresh.db'))
    return HiringRadarRepository(connection), connection


async def _fake_get_external_source_insights(self, *, source_url: str, observed_at: str, force_refresh: bool = False):
    return SimpleNamespace(
        enrichment_status='live',
        original_source_metadata=SimpleNamespace(final_url=source_url),
    )


def test_hydrate_job_url_bootstraps_source_records_and_canonical_jobs_from_legacy_job(tmp_path: Path, monkeypatch) -> None:
    repository, connection = _make_repository(tmp_path)
    try:
        source_url = 'https://jobs.lever.co/trendyol/ed8259be-930e-487a-9560-cd0da4a6e2db'
        repository.upsert_job(
            JobRecord(
                source_name='trendyol-lever',
                title='Database Engineer - NoSQL',
                company_name='Trendyol',
                location='Istanbul / Maslak',
                canonical_url=source_url,
                source_type='lever',
                source_job_id='ed8259be-930e-487a-9560-cd0da4a6e2db',
                raw_posted_at='2026-04-20',
                posted_at='2026-04-20',
                fingerprint='trendyol-nosql-1',
                first_seen_at='2026-04-20T10:00:00Z',
                last_seen_at='2026-04-20T10:00:00Z',
                is_active=True,
                scraped_at='2026-04-20T10:00:00Z',
            )
        )
        repository.upsert_job_external_context_snapshot(
            JobExternalContextSnapshot(
                source_url=source_url,
                final_url=source_url,
                source_domain='jobs.lever.co',
                fetch_status='live',
                http_status=200,
                page_title='Trendyol - Database Engineer - NoSQL',
                site_name='trendyol',
                meta_description='NoSQL platform role',
                clean_text='About the Role\nOperate Redis, Cassandra, MongoDB.\nWhat We Offer\nHybrid working model.',
                content_digest='digest-1',
                site_specific_requirements=(
                    'Extensive experience (4+ years) in administering and optimizing NoSQL systems.',
                    'Hands-on experience with at least three of: Elasticsearch, Redis, Cassandra, Couchbase, MongoDB.',
                ),
                company_culture_clues=(
                    'Hybrid working model with flexibility.',
                ),
                responsibility_clues=(
                    'Maintain and optimize database capacity.',
                ),
                technology_stack_terms=('redis', 'cassandra', 'mongodb', 'python'),
                source_metadata_json={'provider_name': 'lever'},
                fetched_at='2026-04-20T10:05:00Z',
                expires_at='2026-04-21T10:05:00Z',
                updated_at='2026-04-20T10:05:00Z',
            )
        )
        monkeypatch.setattr(
            'hiring_radar.services.ai.web_context.WebContextService.get_external_source_insights',
            _fake_get_external_source_insights,
        )

        result = hydrate_job_url(
            repository,
            source_url=source_url,
            observed_at='2026-04-20T10:06:00Z',
            force_refresh=True,
        )

        assert result.matched_legacy_job_ids
        assert result.bootstrap_created_sources == 1
        assert result.bootstrap_created_source_records == 1
        assert result.bootstrap_created_canonical_jobs == 1
        assert result.matched_canonical_jobs == 1
        assert result.refreshed_feature_count == 1
        assert 'BOOTSTRAP_CANONICAL_CREATED' in result.linkage_reason_codes

        assert len(repository.list_job_sources(active_only=True)) == 1
        source = repository.list_job_sources(active_only=True)[0]
        assert len(repository.list_job_source_records(source_id=source.id or 0, active_only=True)) == 1
        assert len(repository.list_canonical_jobs(active_only=True)) == 1
    finally:
        close_connection(connection)
