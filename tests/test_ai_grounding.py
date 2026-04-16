from __future__ import annotations

from pathlib import Path

from hiring_radar.api.schemas.profile_contract import UserProfileAggregateResponse
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.ai.grounding import build_copilot_grounding_bundle
from hiring_radar.services.profile_aggregate import build_user_profile_aggregate_response


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object, int]:
    connection = initialize_database(str(tmp_path / "grounding.db"))
    repository = HiringRadarRepository(connection)
    subscriber, _ = repository.upsert_subscriber(
        email="ground@example.com",
        full_name="Ground User",
        updated_at="2026-04-15T12:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Embedded Systems Engineer",
        summary="Builds firmware and telemetry systems.",
        target_roles=("Embedded Engineer", "Firmware Engineer"),
        skills=("Python", "STM32", "C"),
        preferred_locations=("Remote",),
        remote_preference="hybrid",
        cv_filename="cv.pdf",
        cv_uploaded_at="2026-04-15T12:01:00Z",
        updated_at="2026-04-15T12:01:00Z",
    )
    repository.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="cv.txt",
        storage_path="/tmp/cv.txt",
        content_type="text/plain",
        file_size_bytes=100,
        extracted_text="STM32 firmware development, Python automation, telemetry pipeline design.",
        parse_status="completed",
        uploaded_at="2026-04-15T12:02:00Z",
        parsed_at="2026-04-15T12:03:00Z",
    )
    return repository, connection, subscriber_id


def test_grounding_bundle_combines_profile_cv_memory_and_knowledge(tmp_path: Path) -> None:
    repository, connection, subscriber_id = _make_repo(tmp_path)
    try:
        aggregate: UserProfileAggregateResponse = build_user_profile_aggregate_response(
            user_id=str(subscriber_id),
            email="ground@example.com",
            full_name="Ground User",
            legacy_profile=repository.get_subscriber_profile(subscriber_id),
            experience_entries=repository.list_subscriber_experience_entries(subscriber_id),
            education_entries=repository.list_subscriber_education_entries(subscriber_id),
            language_entries=repository.list_subscriber_language_entries(subscriber_id),
        )
        repository.upsert_subscriber_ai_learned_memory(
            subscriber_id,
            memory_key="workflow:cv_improvement",
            memory_note="User frequently asks for CV strengthening guidance.",
            source_type="conversation",
            confidence=0.7,
            observed_at="2026-04-15T12:10:00Z",
        )
        bundle = build_copilot_grounding_bundle(
            repository,
            subscriber_id=subscriber_id,
            profile=aggregate.profile,
            query="STM32 ve Python deneyimimi CV'mde nasıl daha iyi anlatırım?",
            locale="tr",
        )
        assert bundle.profile_summary
        assert "STM32" in bundle.cv_summary
        assert bundle.memory_summary
        assert bundle.career_knowledge_summary
        assert any(item.source_type == "career_knowledge" for item in bundle.sources)
    finally:
        close_connection(connection)
