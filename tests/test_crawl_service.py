from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import initialize_database
from hiring_radar.scrapers.base import ScraperSourceConfig
from hiring_radar.services.crawl import CrawlFetchError, run_single_source_crawl


@pytest.fixture()
def repository(tmp_path: Path) -> HiringRadarRepository:
    db_path = tmp_path / "test_crawl_service.db"
    connection = initialize_database(str(db_path))
    repo = HiringRadarRepository(connection)

    yield repo

    repo.close()


def test_run_single_source_crawl_success(repository: HiringRadarRepository) -> None:
    fixture_path = Path("tests/fixtures/greenhouse_sample.html")
    html = fixture_path.read_text(encoding="utf-8")

    config = ScraperSourceConfig(
        source_name="demo-greenhouse",
        company_name="Demo Company",
        source_type="greenhouse",
        url="https://boards.greenhouse.io/demo-company",
    )

    def fake_fetch_html(url: str) -> str:
        assert url == "https://boards.greenhouse.io/demo-company"
        return html

    result = run_single_source_crawl(
        source_config=config,
        repository=repository,
        fetch_html=fake_fetch_html,
        started_at="2026-04-03T17:00:00Z",
    )

    active_jobs = repository.list_active_jobs(source_name="demo-greenhouse")
    crawl_run = repository.get_crawl_run(result.crawl_run_id or -1)

    assert result.success is True
    assert result.source_name == "demo-greenhouse"
    assert result.source_type == "greenhouse"
    assert result.started_at == "2026-04-03T17:00:00Z"
    assert result.finished_at
    assert result.total_parsed_jobs == 2
    assert result.new_jobs == 2
    assert result.updated_jobs == 0
    assert result.deactivated_jobs == 0
    assert result.crawl_run_id is not None
    assert result.error_message is None

    assert len(active_jobs) == 2
    assert {job.title for job in active_jobs} == {"Backend Engineer", "Data Engineer"}

    assert crawl_run is not None
    assert crawl_run.source_name == "demo-greenhouse"
    assert crawl_run.started_at == "2026-04-03T17:00:00Z"
    assert crawl_run.finished_at is not None
    assert crawl_run.success is True
    assert crawl_run.notes is None


def test_run_single_source_crawl_failure(repository: HiringRadarRepository) -> None:
    config = ScraperSourceConfig(
        source_name="demo-greenhouse",
        company_name="Demo Company",
        source_type="greenhouse",
        url="https://boards.greenhouse.io/demo-company",
    )

    def failing_fetch_html(url: str) -> str:
        assert url == "https://boards.greenhouse.io/demo-company"
        raise CrawlFetchError("simulated fetch failure")

    result = run_single_source_crawl(
        source_config=config,
        repository=repository,
        fetch_html=failing_fetch_html,
        started_at="2026-04-03T17:05:00Z",
    )

    crawl_run = repository.get_crawl_run(result.crawl_run_id or -1)
    active_jobs = repository.list_active_jobs(source_name="demo-greenhouse")

    assert result.success is False
    assert result.source_name == "demo-greenhouse"
    assert result.source_type == "greenhouse"
    assert result.started_at == "2026-04-03T17:05:00Z"
    assert result.finished_at
    assert result.total_parsed_jobs == 0
    assert result.new_jobs == 0
    assert result.updated_jobs == 0
    assert result.deactivated_jobs == 0
    assert result.crawl_run_id is not None
    assert result.error_message == "simulated fetch failure"

    assert crawl_run is not None
    assert crawl_run.source_name == "demo-greenhouse"
    assert crawl_run.started_at == "2026-04-03T17:05:00Z"
    assert crawl_run.finished_at is not None
    assert crawl_run.success is False
    assert crawl_run.notes == "simulated fetch failure"

    assert active_jobs == []