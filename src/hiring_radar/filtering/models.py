from __future__ import annotations

from dataclasses import dataclass
from typing import Final

_VALID_MATCH_FIELDS: Final[tuple[str, ...]] = (
    "title",
    "location",
    "company_name",
)


def _normalize_keyword(keyword: str) -> str:
    return keyword.strip().casefold()


def _clean_keywords(keywords: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    cleaned: list[str] = []

    for keyword in keywords:
        stripped = keyword.strip()
        if not stripped:
            continue

        normalized = _normalize_keyword(stripped)
        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned.append(stripped)

    return tuple(cleaned)


@dataclass(slots=True, frozen=True)
class KeywordFilterSettings:
    include_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    match_title: bool = True
    match_location: bool = True
    match_company_name: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "include_keywords",
            _clean_keywords(self.include_keywords),
        )
        object.__setattr__(
            self,
            "exclude_keywords",
            _clean_keywords(self.exclude_keywords),
        )

        if not self.active_fields():
            raise ValueError(
                "KeywordFilterSettings requires at least one enabled match field."
            )

    def is_enabled(self) -> bool:
        return bool(self.include_keywords or self.exclude_keywords)

    def active_fields(self) -> tuple[str, ...]:
        fields: list[str] = []

        if self.match_title:
            fields.append("title")
        if self.match_location:
            fields.append("location")
        if self.match_company_name:
            fields.append("company_name")

        return tuple(fields)

    def to_dict(self) -> dict[str, object]:
        return {
            "include_keywords": list(self.include_keywords),
            "exclude_keywords": list(self.exclude_keywords),
            "match_title": self.match_title,
            "match_location": self.match_location,
            "match_company_name": self.match_company_name,
        }


@dataclass(slots=True, frozen=True)
class FilterableJobText:
    title: str
    location: str | None
    company_name: str

    def field_map(self) -> dict[str, str]:
        values = {
            "title": self.title,
            "location": self.location or "",
            "company_name": self.company_name,
        }

        return {
            field_name: values[field_name]
            for field_name in _VALID_MATCH_FIELDS
        }

    def selected_field_values(
        self,
        *,
        settings: KeywordFilterSettings,
    ) -> tuple[str, ...]:
        fields = self.field_map()
        return tuple(fields[field_name] for field_name in settings.active_fields())