from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.routers import user_ai as user_ai_module
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.ai.contracts import AiCopilotChatResponse, AiCopilotSource
from hiring_radar.services.user_auth import UserSession


class StubRuntime:
    class config:
        runtime = "ollama"
        default_model = "llama3.1:8b"
        audit_enabled = False
        audit_preview_chars = 120
        max_retries = 0


class StubTask:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def run(self, *, conversation_id: int, latest_user_message: str, locale: str = "tr", **_: object) -> AiCopilotChatResponse:
        assert latest_user_message == "Merhaba"
        return AiCopilotChatResponse(
            conversation_id=str(conversation_id),
            answer="Merhaba, headline ve summary alanlarını birlikte iyileştirebiliriz.",
            sources=[AiCopilotSource(source_type="profile", label="Profile grounding")],
            warnings=[],
        )


def _make_user_session() -> UserSession:
    return UserSession(subscriber_id=1, email="alice@example.com", issued_at="2026-04-05T10:00:00Z", expires_at="2026-04-05T12:00:00Z")


def _make_repository(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "copilot_repo.db"))
    repository = HiringRadarRepository(connection)
    subscriber, _ = repository.upsert_subscriber(email="alice@example.com", full_name="Alice Example", updated_at="2026-04-05T10:00:00Z")
    repository.upsert_subscriber_profile(subscriber.id or 0, phone=None, headline="RF Systems Engineer", summary="Designs embedded and RF systems.", target_roles=(), skills=(), preferred_locations=(), remote_preference=None, cv_filename=None, cv_uploaded_at=None, updated_at="2026-04-05T10:00:00Z")
    return repository, connection


def test_user_ai_copilot_chat_works_with_real_repository(tmp_path: Path, monkeypatch) -> None:
    repository, connection = _make_repository(tmp_path)
    try:
        app = create_app()
        app.dependency_overrides[get_current_user_session] = _make_user_session
        app.dependency_overrides[get_repository] = lambda: repository
        monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: StubRuntime())
        monkeypatch.setattr(user_ai_module, "CopilotChatTask", StubTask)

        client = TestClient(app)
        response = client.post("/api/user/ai/copilot/chat", json={"locale": "tr", "message": "Merhaba", "conversation_id": None})

        assert response.status_code == 200
        payload = response.json()
        assert payload["answer"].startswith("Merhaba")
        assert payload["conversation_id"] is not None
        conversations = repository.list_subscriber_ai_copilot_conversations(1)
        assert len(conversations) == 1
        messages = repository.list_subscriber_ai_copilot_messages(1, conversation_id=conversations[0].id or 0, limit=20)
        assert len(messages) == 2
    finally:
        close_connection(connection)
