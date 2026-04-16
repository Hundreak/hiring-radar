from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from hiring_radar.filtering.engine import (
    KeywordFilterEvaluation,
    evaluate_job_text_against_keyword_filter,
)
from hiring_radar.filtering.models import FilterableJobText, KeywordFilterSettings
from hiring_radar.models import JobRecord


@dataclass(slots=True, frozen=True)
class JobFilterDecision:
    job: JobRecord
    evaluation: KeywordFilterEvaluation


@dataclass(slots=True, frozen=True)
class JobFilterResult:
    total_jobs: int
    passed_decisions: tuple[JobFilterDecision, ...]
    rejected_decisions: tuple[JobFilterDecision, ...]

    @property
    def passed_count(self) -> int:
        return len(self.passed_decisions)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_decisions)

    @property
    def passed_jobs(self) -> tuple[JobRecord, ...]:
        return tuple(decision.job for decision in self.passed_decisions)

    @property
    def rejected_jobs(self) -> tuple[JobRecord, ...]:
        return tuple(decision.job for decision in self.rejected_decisions)


def build_filterable_job_text(*, job: JobRecord) -> FilterableJobText:
    return FilterableJobText(
        title=job.title,
        location=job.location,
        company_name=job.company_name,
    )


def evaluate_job_record_against_keyword_filter(
    *,
    job: JobRecord,
    settings: KeywordFilterSettings,
) -> JobFilterDecision:
    filterable_job_text = build_filterable_job_text(job=job)
    evaluation = evaluate_job_text_against_keyword_filter(
        job=filterable_job_text,
        settings=settings,
    )
    return JobFilterDecision(
        job=job,
        evaluation=evaluation,
    )


def filter_jobs_by_keyword_settings(
    *,
    jobs: Iterable[JobRecord],
    settings: KeywordFilterSettings,
) -> JobFilterResult:
    passed_decisions: list[JobFilterDecision] = []
    rejected_decisions: list[JobFilterDecision] = []

    for job in jobs:
        decision = evaluate_job_record_against_keyword_filter(
            job=job,
            settings=settings,
        )
        if decision.evaluation.passed:
            passed_decisions.append(decision)
        else:
            rejected_decisions.append(decision)

    total_jobs = len(passed_decisions) + len(rejected_decisions)

    return JobFilterResult(
        total_jobs=total_jobs,
        passed_decisions=tuple(passed_decisions),
        rejected_decisions=tuple(rejected_decisions),
    )
