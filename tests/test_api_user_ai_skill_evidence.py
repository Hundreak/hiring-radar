from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.routers import user_ai as user_ai_module
from hiring_radar.models import Subscriber, SubscriberProfile
from hiring_radar.services.ai.contracts import SkillEvidenceSuggestionResponse
from hiring_radar.services.user_auth import UserSession


class FakeRepository:
    def __init__(self) -> None:
        self.subscriber = Subscriber(
            id=7,
            email="alice@example.com",
            full_name="Alice Example",
            is_active=True,
            digest_enabled=True,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )
        self.profile = SubscriberProfile(subscriber_id=7, headline="Engineer", summary="Short summary")

    def get_subscriber_by_id(self, subscriber_id: int):
        return self.subscriber if subscriber_id == 7 else None

    def get_subscriber_profile(self, subscriber_id: int):
        return self.profile

    def list_subscriber_experience_entries(self, subscriber_id: int):
        return []

    def list_subscriber_education_entries(self, subscriber_id: int):
        return []

    def list_subscriber_language_entries(self, subscriber_id: int):
        return []

    def list_subscriber_skill_entries(self, subscriber_id: int):
        return []

    def list_subscriber_cv_uploads(self, subscriber_id: int):
        return []

    def get_subscriber_keyword_preferences(self, subscriber_id: int):
        return None


class StubTask:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def run(self, *, profile, locale: str, skill_name: str, category: str | None, existing_evidence_note: str | None):
        assert locale == "tr"
        assert skill_name == "Python"
        assert category == "Yazılım"
        assert existing_evidence_note == "Veri işleme ve otomasyon projelerinde kullandım."
        return SkillEvidenceSuggestionResponse(
            description_suggestions=[
                "Python becerisini veri işleme ve otomasyon bağlamında daha net konumlandır."
            ],
            evidence_note_suggestions=[
                "Python ile veri temizleme ve otomasyon akışları geliştirerek manuel operasyon ihtiyacını azalttım."
            ],
            proof_ideas=[
                "Bu beceriyi desteklemek için proje adı, çıktı ve varsa GitHub bağlantısı ekle."
            ],
            missing_signals=["Ölçülebilir çıktı belirtilmemiş."],
            strengthening_note="Bu beceriyi daha güçlü göstermek için proje bağlamı ekle.",
            warnings=[],
            confidence_band="medium",
        )


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=7,
        email="alice@example.com",
        issued_at="2026-04-05T10:00:00Z",
        expires_at="2026-04-05T12:00:00Z",
    )


def test_user_ai_skill_evidence_endpoint_returns_structured_suggestions(monkeypatch) -> None:
    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: object())
    monkeypatch.setattr(user_ai_module, "SkillEvidenceSuggestionTask", StubTask)

    client = TestClient(app)
    response = client.post(
        "/api/user/ai/profile/skill-evidence",
        json={
            "locale": "tr",
            "skill_name": "Python",
            "category": "Yazılım",
            "existing_evidence_note": "Veri işleme ve otomasyon projelerinde kullandım.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["description_suggestions"][0].startswith("Python becerisini")
    assert payload["proof_ideas"][0].startswith("Bu beceriyi desteklemek")
    assert payload["strengthening_note"] == "Bu beceriyi daha güçlü göstermek için proje bağlamı ekle."
