from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.routers import user_ai as user_ai_module
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.services.user_auth import UserSession


class StubRuntime:
    class config:
        runtime = "ollama"
        default_model = "llama3.1:8b"
        audit_enabled = False
        audit_preview_chars = 120
        max_retries = 0

    def generate_structured(self, request):
        class Response:
            content = {
                "answer": "**Güçlü yönlerin**\n- Gömülü sistem deneyimin görünür.\n- Python desteğin profilini güçlendiriyor.",
                "follow_up_suggestions": ["Projelerini ölçülebilir çıktılarla yazalım."],
                "warnings": [],
                "confidence_band": "medium",
            }

        return Response()


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "copilot_api.db"))
    repository = HiringRadarRepository(connection)
    subscriber, _ = repository.upsert_subscriber(
        email="api@example.com",
        full_name="Api User",
        updated_at="2026-04-15T14:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Embedded Systems Engineer",
        summary="Builds reliable firmware systems.",
        target_roles=("Embedded Engineer",),
        skills=("STM32", "Python"),
        preferred_locations=("Remote",),
        remote_preference="hybrid",
        cv_filename="cv.pdf",
        cv_uploaded_at="2026-04-15T14:01:00Z",
        updated_at="2026-04-15T14:01:00Z",
    )
    repository.create_subscriber_cv_upload(
        subscriber_id,
        original_filename="cv.txt",
        storage_path="/tmp/cv.txt",
        content_type="text/plain",
        file_size_bytes=100,
        extracted_text="STM32, embedded Linux, Python automation.",
        parse_status="completed",
        uploaded_at="2026-04-15T14:02:00Z",
        parsed_at="2026-04-15T14:03:00Z",
    )
    return repository, connection


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=1,
        email="api@example.com",
        issued_at="2026-04-05T10:00:00Z",
        expires_at="2026-04-05T12:00:00Z",
    )


def test_user_ai_copilot_chat_endpoint_returns_grounded_reply(tmp_path: Path, monkeypatch) -> None:
    repository, connection = _make_repo(tmp_path)
    try:
        app = create_app()
        app.dependency_overrides[get_current_user_session] = _make_user_session
        app.dependency_overrides[get_repository] = lambda: repository
        monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: StubRuntime())

        client = TestClient(app)
        response = client.post(
            "/api/user/ai/copilot/chat",
            json={"locale": "tr", "message": "CV'me göre en güçlü iki yönüm ne?"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["answer"]
        assert payload["conversation_id"] is not None
        assert payload["sources"]
        conversations = repository.list_subscriber_ai_copilot_conversations(1)
        assert len(conversations) == 1
        messages = repository.list_subscriber_ai_copilot_messages(1, conversation_id=conversations[0].id or 0)
        assert len(messages) == 2
    finally:
        close_connection(connection)
