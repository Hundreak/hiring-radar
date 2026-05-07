from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.models import CanonicalJob


def _repo(tmp_path: Path) -> HiringRadarRepository:
    connection = initialize_database(str(tmp_path / "job_catalog.db"))
    return HiringRadarRepository(connection)


def test_list_ranked_canonical_jobs_prefers_quality_score(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    try:
        repo.upsert_canonical_job(
            CanonicalJob(
                canonical_key="alpha",
                normalized_title="backend engineer",
                normalized_company_name="alpha",
                display_title="Backend Engineer",
                display_company_name="Alpha",
                apply_url="https://alpha.example/jobs/1",
                trust_score=0.92,
                freshness_score=0.96,
                is_active=True,
                created_at="2026-04-18T09:00:00Z",
                updated_at="2026-04-18T09:05:00Z",
            )
        )
        repo.upsert_canonical_job(
            CanonicalJob(
                canonical_key="beta",
                normalized_title="backend engineer",
                normalized_company_name="beta",
                display_title="Backend Engineer",
                display_company_name="Beta",
                apply_url="https://beta.example/jobs/1",
                trust_score=0.99,
                freshness_score=0.35,
                is_active=True,
                created_at="2026-04-18T09:00:00Z",
                updated_at="2026-04-18T09:10:00Z",
            )
        )

        ranked = repo.list_ranked_canonical_jobs()

        assert [job.canonical_key for job in ranked] == ["alpha", "beta"]
        assert repo.get_canonical_job_by_id(ranked[0].id or 0) == ranked[0]
    finally:
        repo.close()
