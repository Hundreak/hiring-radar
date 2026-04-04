from __future__ import annotations

from hiring_radar.filtering.models import KeywordFilterSettings
from hiring_radar.services.digest import (
    DigestJobItem,
    DigestResult,
    DigestSourceSection,
    filter_digest_result_by_keyword_settings,
)


def _make_digest(*, titles: list[str]) -> DigestResult:
    jobs = [
        DigestJobItem(
            company_name="Corelight",
            source_name="corelight-greenhouse",
            source_type="greenhouse",
            title=title,
            location="Remote",
            canonical_url=f"https://example.com/jobs/{index}",
            first_seen_at="2026-04-04T10:00:00Z",
        )
        for index, title in enumerate(titles, start=1)
    ]

    sections = []
    if jobs:
        sections = [
            DigestSourceSection(
                source_name="corelight-greenhouse",
                source_type="greenhouse",
                new_jobs_count=len(jobs),
                jobs=jobs,
            )
        ]

    return DigestResult(
        generated_at="2026-04-04T12:00:00Z",
        since="2026-04-04T00:00:00Z",
        total_new_jobs=len(jobs),
        sections=sections,
    )


def test_filter_digest_result_by_keyword_settings_filters_jobs_and_counts() -> None:
    digest = _make_digest(
        titles=[
            "Security Engineer",
            "Security Intern",
            "Growth Marketing Manager",
        ]
    )
    settings = KeywordFilterSettings(
        include_keywords=("engineer",),
        exclude_keywords=("intern",),
        match_title=True,
        match_location=False,
        match_company_name=False,
    )

    result = filter_digest_result_by_keyword_settings(
        digest,
        settings=settings,
    )

    assert result.original_total_new_jobs == 3
    assert result.filtered_total_new_jobs == 1
    assert result.filtered_out_jobs == 2
    assert result.digest.total_new_jobs == 1
    assert len(result.digest.sections) == 1
    assert result.digest.sections[0].new_jobs_count == 1
    assert [job.title for job in result.digest.sections[0].jobs] == [
        "Security Engineer",
    ]


def test_filter_digest_result_by_keyword_settings_returns_original_digest_when_disabled() -> None:
    digest = _make_digest(
        titles=[
            "Security Engineer",
            "Growth Marketing Manager",
        ]
    )
    settings = KeywordFilterSettings()

    result = filter_digest_result_by_keyword_settings(
        digest,
        settings=settings,
    )

    assert result.original_total_new_jobs == 2
    assert result.filtered_total_new_jobs == 2
    assert result.filtered_out_jobs == 0
    assert result.digest == digest