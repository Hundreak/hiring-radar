"""Placeholder module for the bootstrap phase."""

from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.db.repository import HiringRadarRepository


@dataclass(slots=True, frozen=True)
class OverallSummary:
    total_jobs: int
    active_jobs: int
    inactive_jobs: int


@dataclass(slots=True, frozen=True)
class SourceSummaryRow:
    source_name: str
    source_type: str
    total_jobs: int
    active_jobs: int
    inactive_jobs: int


@dataclass(slots=True, frozen=True)
class CompanySummaryRow:
    company_name: str
    total_jobs: int
    active_jobs: int
    inactive_jobs: int


@dataclass(slots=True, frozen=True)
class SummaryResult:
    overall: OverallSummary
    by_source: list[SourceSummaryRow]
    by_company: list[CompanySummaryRow]


def build_summary(repository: HiringRadarRepository) -> SummaryResult:
    """
    Build a service-level summary result from repository aggregation queries.
    """
    overall_counts = repository.get_job_counts()
    source_rows = repository.get_source_summary_rows()
    company_rows = repository.get_company_summary_rows()

    overall = OverallSummary(
        total_jobs=overall_counts["total_jobs"],
        active_jobs=overall_counts["active_jobs"],
        inactive_jobs=overall_counts["inactive_jobs"],
    )

    by_source = [
        SourceSummaryRow(
            source_name=row["source_name"],
            source_type=row["source_type"],
            total_jobs=row["total_jobs"],
            active_jobs=row["active_jobs"],
            inactive_jobs=row["inactive_jobs"],
        )
        for row in source_rows
    ]

    by_company = [
        CompanySummaryRow(
            company_name=row["company_name"],
            total_jobs=row["total_jobs"],
            active_jobs=row["active_jobs"],
            inactive_jobs=row["inactive_jobs"],
        )
        for row in company_rows
    ]

    return SummaryResult(
        overall=overall,
        by_source=by_source,
        by_company=by_company,
    )
