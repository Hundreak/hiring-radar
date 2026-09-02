from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.ai.career_knowledge import (
    ensure_foundation_career_knowledge,
    search_career_knowledge,
)


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "career_knowledge.db"))
    return HiringRadarRepository(connection), connection


def test_career_knowledge_seed_and_search(tmp_path: Path) -> None:
    repository, connection = _make_repo(tmp_path)
    try:
        seeded = ensure_foundation_career_knowledge(repository, updated_at="2026-04-15T11:00:00Z")
        assert len(seeded) >= 3
        matches = search_career_knowledge(
            repository,
            query="CV ve profil sinyallerimi daha güçlü nasıl anlatırım?",
            locale="tr",
            limit=3,
        )
        assert matches
        assert any("CV" in item.document.title or "CV" in item.snippet or "profil" in item.snippet.lower() for item in matches)
    finally:
        close_connection(connection)
