from __future__ import annotations

import csv
from pathlib import Path

from hiring_radar.models import JobRecord
from hiring_radar.services.export import export_jobs_to_csv


def make_job(
    *,
    fingerprint: str,
    source_name: str = "demo-greenhouse",
    title: str = "Backend Engineer",
    company_name: str = "Demo Company",
    location: str | None = "Remote",
    canonical_url: str = "https://boards.greenhouse.io/demo/jobs/123",
    source_type: str = "greenhouse",
    source_job_id: str | None = "123",
    raw_posted_at: str | None = "2026-04-03",
    posted_at: str | None = "2026-04-03",
    first_seen_at: str | None = "2026-04-03T10:00:00Z",
    last_seen_at: str | None = "2026-04-03T11:00:00Z",
    is_active: bool = True,
    scraped_at: str = "2026-04-03T11:00:00Z",
    job_id: int | None = 1,
) -> JobRecord:
    return JobRecord(
        id=job_id,
        source_name=source_name,
        title=title,
        company_name=company_name,
        location=location,
        canonical_url=canonical_url,
        source_type=source_type,
        source_job_id=source_job_id,
        raw_posted_at=raw_posted_at,
        posted_at=posted_at,
        fingerprint=fingerprint,
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
        is_active=is_active,
        scraped_at=scraped_at,
    )


def test_export_jobs_to_csv_writes_expected_file(tmp_path: Path) -> None:
    jobs = [
        make_job(
            fingerprint="fp-1",
            source_name="corelight-greenhouse",
            company_name="Corelight",
            title="Security Engineer",
            location="North America",
            canonical_url="https://boards.greenhouse.io/corelight/jobs/7751102",
            source_job_id="7751102",
            job_id=10,
        ),
        make_job(
            fingerprint="fp-2",
            source_name="trendyol-lever",
            company_name="Trendyol",
            source_type="lever",
            title="Data Engineer",
            location="Istanbul, Turkey",
            canonical_url="https://jobs.lever.co/trendyol/data-engineer-def456",
            source_job_id="data-engineer-def456",
            is_active=False,
            job_id=11,
        ),
    ]

    result = export_jobs_to_csv(
        jobs=jobs,
        output_dir=tmp_path / "exports",
        timestamp_factory=lambda: "2026-04-03T18-00-00Z",
    )

    output_path = Path(result.output_path)

    assert result.row_count == 2
    assert output_path.exists()
    assert output_path.name == "jobs_export_2026-04-03T18-00-00Z.csv"

    with output_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2

    first_row = rows[0]
    second_row = rows[1]

    assert first_row["id"] == "10"
    assert first_row["source_name"] == "corelight-greenhouse"
    assert first_row["company_name"] == "Corelight"
    assert first_row["source_type"] == "greenhouse"
    assert first_row["title"] == "Security Engineer"
    assert first_row["location"] == "North America"
    assert first_row["canonical_url"] == "https://boards.greenhouse.io/corelight/jobs/7751102"
    assert first_row["source_job_id"] == "7751102"
    assert first_row["is_active"] == "true"

    assert second_row["id"] == "11"
    assert second_row["source_name"] == "trendyol-lever"
    assert second_row["company_name"] == "Trendyol"
    assert second_row["source_type"] == "lever"
    assert second_row["title"] == "Data Engineer"
    assert second_row["location"] == "Istanbul, Turkey"
    assert second_row["is_active"] == "false"


def test_export_jobs_to_csv_writes_header_for_empty_dataset(tmp_path: Path) -> None:
    result = export_jobs_to_csv(
        jobs=[],
        output_dir=tmp_path / "exports",
        timestamp_factory=lambda: "2026-04-03T18-05-00Z",
    )

    output_path = Path(result.output_path)

    assert result.row_count == 0
    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8").strip().splitlines()

    assert len(content) == 1
    assert (
        content[0]
        == "id,source_name,company_name,source_type,title,location,canonical_url,"
        "source_job_id,raw_posted_at,posted_at,fingerprint,first_seen_at,last_seen_at,"
        "is_active,scraped_at"
    )