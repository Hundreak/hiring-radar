from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.filtering.models import FilterableJobText, KeywordFilterSettings


@dataclass(slots=True, frozen=True)
class KeywordFieldMatch:
    field_name: str
    keyword: str
    field_value: str


@dataclass(slots=True, frozen=True)
class KeywordFilterEvaluation:
    passed: bool
    include_matched: bool
    exclude_matched: bool
    include_matches: tuple[KeywordFieldMatch, ...] = ()
    exclude_matches: tuple[KeywordFieldMatch, ...] = ()


def _keyword_in_text(*, keyword: str, text: str) -> bool:
    return keyword.casefold() in text.casefold()


def _collect_matches(
    *,
    job: FilterableJobText,
    keywords: tuple[str, ...],
    settings: KeywordFilterSettings,
) -> tuple[KeywordFieldMatch, ...]:
    if not keywords:
        return ()

    field_map = job.field_map()
    matches: list[KeywordFieldMatch] = []

    for field_name in settings.active_fields():
        field_value = field_map[field_name]
        if not field_value:
            continue

        for keyword in keywords:
            if _keyword_in_text(keyword=keyword, text=field_value):
                matches.append(
                    KeywordFieldMatch(
                        field_name=field_name,
                        keyword=keyword,
                        field_value=field_value,
                    )
                )

    return tuple(matches)


def evaluate_job_text_against_keyword_filter(
    *,
    job: FilterableJobText,
    settings: KeywordFilterSettings,
) -> KeywordFilterEvaluation:
    if not settings.is_enabled():
        return KeywordFilterEvaluation(
            passed=True,
            include_matched=False,
            exclude_matched=False,
            include_matches=(),
            exclude_matches=(),
        )

    include_matches = _collect_matches(
        job=job,
        keywords=settings.include_keywords,
        settings=settings,
    )
    exclude_matches = _collect_matches(
        job=job,
        keywords=settings.exclude_keywords,
        settings=settings,
    )

    include_matched = bool(include_matches)
    exclude_matched = bool(exclude_matches)

    include_passed = True if not settings.include_keywords else include_matched
    passed = include_passed and not exclude_matched

    return KeywordFilterEvaluation(
        passed=passed,
        include_matched=include_matched,
        exclude_matched=exclude_matched,
        include_matches=include_matches,
        exclude_matches=exclude_matches,
    )