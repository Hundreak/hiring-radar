from __future__ import annotations

from pathlib import Path

from hiring_radar.api.schemas.profile_contract import UserProfileAggregateResponse
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.ai.tasks.copilot_chat_task import CopilotChatTask
from hiring_radar.services.profile_aggregate import build_user_profile_aggregate_response


class StubRuntime:
    class config:
        default_model = "llama3.1:8b"
        max_retries = 0

    def generate_structured(self, request):
        class Response:
            content = {
                "answer": "**Öne çıkan yönlerin**\n- STM32 ve gömülü sistem deneyimin güçlü görünüyor.\n- Python ile otomasyon tarafında destekleyici sinyal var.",
                "follow_up_suggestions": [
                    "Bu deneyimi proje çıktılarıyla güçlendirelim.",
                    "CV başlığını hedef role göre netleştirelim.",
                ],
                "warnings": [],
                "confidence_band": "medium",
            }

        return Response()


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object, int]:
    connection = initialize_database(str(tmp_path / "copilot_task.db"))
    repository = HiringRadarRepository(connection)
    subscriber, _ = repository.upsert_subscriber(
        email="task@example.com",
        full_name="Task User",
        updated_at="2026-04-15T13:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Embedded Engineer",
        summary="Designs firmware and electronics systems.",
        target_roles=("Embedded Engineer",),
        skills=("STM32", "Python"),
        preferred_locations=("Ankara",),
        remote_preference="hybrid",
        cv_filename="cv.pdf",
        cv_uploaded_at="2026-04-15T13:01:00Z",
        updated_at="2026-04-15T13:01:00Z",
    )
    repository.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="cv.txt",
        storage_path="/tmp/cv.txt",
        content_type="text/plain",
        file_size_bytes=100,
        extracted_text="Embedded systems, STM32 development, Python tooling.",
        parse_status="completed",
        uploaded_at="2026-04-15T13:02:00Z",
        parsed_at="2026-04-15T13:03:00Z",
    )
    return repository, connection, subscriber_id


def test_copilot_chat_task_returns_grounded_response_and_persists_memories(tmp_path: Path) -> None:
    repository, connection, subscriber_id = _make_repo(tmp_path)
    try:
        aggregate: UserProfileAggregateResponse = build_user_profile_aggregate_response(
            user_id=str(subscriber_id),
            email="task@example.com",
            full_name="Task User",
            legacy_profile=repository.get_subscriber_profile(subscriber_id),
            experience_entries=repository.list_subscriber_experience_entries(subscriber_id),
            education_entries=repository.list_subscriber_education_entries(subscriber_id),
            language_entries=repository.list_subscriber_language_entries(subscriber_id),
        )
        task = CopilotChatTask(StubRuntime())
        result = task.run(
            repository=repository,
            subscriber_id=subscriber_id,
            profile=aggregate.profile,
            locale="tr",
            user_message="STM32 ve Python deneyimimi CV'mde daha güçlü göstermek istiyorum.",
            recent_messages=[("user", "Merhaba")],
            observed_at="2026-04-15T13:04:00Z",
        )
        assert "STM32" in result.answer
        assert result.sources
        memories = repository.list_subscriber_ai_learned_memories(subscriber_id)
        assert memories
    finally:
        close_connection(connection)
