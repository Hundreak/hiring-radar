from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.services.cv_engine.semantic.skill_catalog import (
    SkillCatalogEntry,
    iter_skill_catalog_entries,
)


@dataclass(frozen=True, slots=True)
class SkillLexiconEntry:
    """Backward-compatible skill lexicon entry."""

    canonical_name: str
    aliases: tuple[str, ...]
    category: str
    ambiguous: bool = False


SKILL_LEXICON: tuple[SkillLexiconEntry, ...] = tuple(
    SkillLexiconEntry(
        canonical_name=entry.canonical_name,
        aliases=entry.aliases,
        category=entry.category,
        ambiguous=entry.ambiguous,
    )
    for entry in iter_skill_catalog_entries()
)


def iter_skill_entries() -> tuple[SkillLexiconEntry, ...]:
    """Return the bundled skill lexicon."""
    return SKILL_LEXICON


def iter_skill_catalog() -> tuple[SkillCatalogEntry, ...]:
    """Return the richer semantic skill catalog."""
    return iter_skill_catalog_entries()
