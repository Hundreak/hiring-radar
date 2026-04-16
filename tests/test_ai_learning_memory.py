from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.ai.learning_memory import (
    extract_learning_memory_candidates,
    persist_learning_memory_candidates,
)


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "learning_memory.db"))
    return HiringRadarRepository(connection), connection


def test_learning_memory_candidates_are_extracted_and_persisted(tmp_path: Path) -> None:
    repository, connection = _make_repo(tmp_path)
    try:
        subscriber, _ = repository.upsert_subscriber(
            email="memory@example.com",
            full_name="Memory User",
            updated_at="2026-04-15T10:00:00Z",
        )
        subscriber_id = subscriber.id or 0
        candidates = extract_learning_memory_candidates(
            prompt="CV'me göre embedded ve STM32 odaklı rollerde nasıl daha güçlü görünürüm? Hibrit çalışmaya da açığım.",
            locale="tr",
        )
        stored = persist_learning_memory_candidates(
            repository,
            subscriber_id=subscriber_id,
            candidates=candidates,
            observed_at="2026-04-15T10:05:00Z",
        )
        assert stored
        memories = repository.list_subscriber_ai_learned_memories(subscriber_id)
        assert any(item.memory_key == "interest:embedded" for item in memories)
        assert any(item.memory_key == "interest:stm32" for item in memories)
        assert any(item.memory_key == "preference:work_mode" for item in memories)
    finally:
        close_connection(connection)
