from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.job_identity import encode_canonical_job_api_id
from hiring_radar.api.routers import user_ai as user_ai_module
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import CanonicalJob, CanonicalJobLink, JobSource, JobSourceRecord
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.matching.contracts import ExternalSourceInsights, ExternalSourceMetadata
from hiring_radar.services.user_auth import UserSession


class StubRuntime:
    last_request = None

    class config:
        runtime = "ollama"
        default_model = "llama3.1:8b"
        audit_enabled = False
        audit_preview_chars = 120
        max_retries = 0

    def generate_structured(self, request):
        StubRuntime.last_request = request

        class Response:
            content = {
                "answer": "## Uyum özeti\n- Çekirdek beceri örtüşmesi var.\n- Başvuru öncesi eksik alanlarını gözden geçir.",
                "follow_up_suggestions": ["Bu iş için CV'de hangi deneyimi öne çıkarmalıyım?"],
                "warnings": [],
                "confidence_band": "medium",
            }

        return Response()


async def _stub_get_external_source_insights(self, *, source_url: str, observed_at: str, force_refresh: bool = False):
    return ExternalSourceInsights(
        enrichment_status="live",
        site_specific_requirements=("Hands-on work with Kubernetes and AWS.",),
        company_culture_clues=("The company emphasizes autonomy and clear feedback.",),
        responsibility_clues=("Own backend platform services and improve developer productivity.",),
        technology_stack_terms=("python", "fastapi", "kubernetes", "aws"),
        original_source_metadata=ExternalSourceMetadata(
            source_url=source_url,
            final_url=source_url,
            source_domain="boards.greenhouse.io",
            fetch_status="live",
            http_status=200,
            page_title="Senior Backend Engineer",
            site_name="Acme Careers",
            fetched_at=observed_at,
            content_digest="digest-1",
            text_char_count=420,
        ),
    )


def _seed_subscriber(repository: HiringRadarRepository) -> int:
    subscriber, _ = repository.upsert_subscriber(
        email="api@example.com",
        full_name="Api User",
        updated_at="2026-04-15T14:00:00Z",
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=None,
        headline="Backend Engineer",
        summary="Builds Python APIs and platform services.",
        target_roles=("Backend Engineer", "Platform Engineer"),
        skills=("Python", "FastAPI", "Docker", "Kubernetes"),
        preferred_locations=("Remote", "Istanbul"),
        remote_preference="remote",
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
        extracted_text="Python, FastAPI, Docker, Kubernetes, English communication.",
        parse_status="completed",
        uploaded_at="2026-04-15T14:02:00Z",
        parsed_at="2026-04-15T14:03:00Z",
    )
    return subscriber_id


def _seed_canonical_job(repository: HiringRadarRepository) -> int:
    source = repository.upsert_job_source(
        JobSource(
            source_type="greenhouse",
            source_name="acme-greenhouse",
            account_slug="acme",
            base_url="https://boards.greenhouse.io/acme",
            trust_score=0.97,
            country_scope="global",
            is_active=True,
            created_at="2026-04-18T09:00:00Z",
            updated_at="2026-04-18T09:00:00Z",
        )
    )
    source_record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id="backend-1",
            raw_payload_json='{"title":"Senior Backend Engineer"}',
            raw_payload_hash="hash-backend-1",
            canonical_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            title="Senior Backend Engineer",
            company_name="Acme",
            location_text="Remote, Turkey",
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            fetched_at="2026-04-18T09:10:00Z",
            is_active=True,
        )
    )
    job = repository.upsert_canonical_job(
        CanonicalJob(
            canonical_key="acme|senior backend engineer|remote turkey|backend-1",
            normalized_title="senior backend engineer",
            normalized_company_name="acme",
            display_title="Senior Backend Engineer",
            display_company_name="Acme",
            location_city="Remote",
            country="Turkey",
            workplace_type="remote",
            employment_type="full_time",
            seniority="senior",
            category="software_engineering",
            department="engineering",
            description_text="Python FastAPI Docker Kubernetes and English communication required. Minimum 4 years of backend API experience.",
            posted_at="2026-04-18",
            apply_url="https://boards.greenhouse.io/acme/jobs/backend-1",
            trust_score=0.97,
            freshness_score=0.92,
            is_active=True,
            created_at="2026-04-18T09:12:00Z",
            updated_at="2026-04-18T09:12:00Z",
        )
    )
    repository.upsert_canonical_job_link(
        CanonicalJobLink(
            canonical_job_id=job.id or 0,
            source_job_id=source_record.id or 0,
            merge_reason="unit_test_link",
            confidence=0.99,
            created_at="2026-04-18T09:13:00Z",
            updated_at="2026-04-18T09:13:00Z",
        )
    )
    refresh_matching_readiness_features(
        repository,
        refreshed_at="2026-04-18T09:14:00Z",
        canonical_job_ids=[job.id or 0],
    )
    return job.id or 0


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object, int]:
    connection = initialize_database(str(tmp_path / "copilot_job_analysis.db"))
    repository = HiringRadarRepository(connection)
    _seed_subscriber(repository)
    canonical_job_id = _seed_canonical_job(repository)
    return repository, connection, canonical_job_id


def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=1,
        email="api@example.com",
        issued_at="2026-04-05T10:00:00Z",
        expires_at="2026-04-05T12:00:00Z",
    )


def test_user_ai_copilot_chat_includes_job_analysis_grounding(tmp_path: Path, monkeypatch) -> None:
    repository, connection, canonical_job_id = _make_repo(tmp_path)
    try:
        app = create_app()
        app.dependency_overrides[get_current_user_session] = _make_user_session
        app.dependency_overrides[get_repository] = lambda: repository
        monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: StubRuntime())
        monkeypatch.setattr(
            "hiring_radar.services.ai.web_context.WebContextService.get_external_source_insights",
            _stub_get_external_source_insights,
        )
        monkeypatch.setattr(
            "hiring_radar.services.ai.web_context.WebContextService.get_external_source_insights",
            _stub_get_external_source_insights,
        )

        client = TestClient(app)
        response = client.post(
            "/api/user/ai/copilot/chat",
            json={
                "locale": "tr",
                "message": "Bu iş için ne kadar uygunum?",
                "job_analysis_context": {
                    "api_job_id": encode_canonical_job_api_id(canonical_job_id),
                    "source_surface": "matches",
                    "analysis_mode": "job_fit",
                },
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["answer"]
        assert any(source["label"] == "Job analysis context" for source in payload["sources"])
        assert any(source["label"] == "Deterministic match evidence" for source in payload["sources"])
        request_message = StubRuntime.last_request.messages[1].content
        assert "Task mode: job_fit" in request_message
        assert "Senior Backend Engineer" in request_message
        assert "Deterministic fit score" in request_message
        assert "External source context:" in request_message
        assert "Culture clues" in request_message
        assert any(source["label"] == "External source context" for source in payload["sources"])
    finally:
        close_connection(connection)


def test_user_ai_copilot_chat_returns_404_for_missing_job_analysis_context(tmp_path: Path, monkeypatch) -> None:
    repository, connection, _ = _make_repo(tmp_path)
    try:
        app = create_app()
        app.dependency_overrides[get_current_user_session] = _make_user_session
        app.dependency_overrides[get_repository] = lambda: repository
        monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: StubRuntime())

        client = TestClient(app)
        response = client.post(
            "/api/user/ai/copilot/chat",
            json={
                "locale": "tr",
                "message": "Bu iş için ne kadar uygunum?",
                "job_analysis_context": {
                    "api_job_id": encode_canonical_job_api_id(999),
                    "source_surface": "jobs",
                    "analysis_mode": "job_fit",
                },
            },
        )

        assert response.status_code == 404
        assert "Job could not be found" in response.json()["detail"]
    finally:
        close_connection(connection)


def test_user_ai_copilot_chat_reuses_latest_job_analysis_context_in_same_conversation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository, connection, canonical_job_id = _make_repo(tmp_path)
    try:
        app = create_app()
        app.dependency_overrides[get_current_user_session] = _make_user_session
        app.dependency_overrides[get_repository] = lambda: repository
        monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: StubRuntime())
        monkeypatch.setattr(
            "hiring_radar.services.ai.web_context.WebContextService.get_external_source_insights",
            _stub_get_external_source_insights,
        )

        client = TestClient(app)
        first = client.post(
            "/api/user/ai/copilot/chat",
            json={
                "locale": "tr",
                "message": "Bu iş için ne kadar uygunum?",
                "display_message": '"Senior Backend Engineer" ilanını profilime göre analiz et.',
                "job_analysis_context": {
                    "api_job_id": encode_canonical_job_api_id(canonical_job_id),
                    "source_surface": "matches",
                    "analysis_mode": "job_fit",
                },
            },
        )
        assert first.status_code == 200
        conversation_id = first.json()["conversation_id"]

        second = client.post(
            "/api/user/ai/copilot/chat",
            json={
                "locale": "tr",
                "message": "CV'de özellikle neyi öne çıkarmalıyım?",
                "conversation_id": conversation_id,
            },
        )
        assert second.status_code == 200
        request_message = StubRuntime.last_request.messages[1].content
        assert "Task mode: job_fit" in request_message
        assert "Senior Backend Engineer" in request_message
    finally:
        close_connection(connection)


class WeakJobAnalysisRuntime:
    last_request = None

    class config:
        runtime = "ollama"
        default_model = "llama3.1:8b"
        audit_enabled = False
        audit_preview_chars = 120
        max_retries = 0

    def generate_structured(self, request):
        WeakJobAnalysisRuntime.last_request = request

        class Response:
            content = {
                "answer": "Bu işin size uygun olup olmadığını kanıta dayalı olarak açıklayacağım.",
                "follow_up_suggestions": [],
                "warnings": [],
                "confidence_band": "medium",
            }

        return Response()


def test_user_ai_copilot_chat_replaces_weak_job_analysis_with_deterministic_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository, connection, canonical_job_id = _make_repo(tmp_path)
    try:
        app = create_app()
        app.dependency_overrides[get_current_user_session] = _make_user_session
        app.dependency_overrides[get_repository] = lambda: repository
        monkeypatch.setattr(user_ai_module, "build_local_ai_runtime_service", lambda: WeakJobAnalysisRuntime())
        monkeypatch.setattr(
            "hiring_radar.services.ai.web_context.WebContextService.get_external_source_insights",
            _stub_get_external_source_insights,
        )

        client = TestClient(app)
        response = client.post(
            "/api/user/ai/copilot/chat",
            json={
                "locale": "tr",
                "message": "Bu iş için ne kadar uygunum?",
                "job_analysis_context": {
                    "api_job_id": encode_canonical_job_api_id(canonical_job_id),
                    "source_surface": "matches",
                    "analysis_mode": "job_fit",
                },
            },
        )

        assert response.status_code == 200
        answer = response.json()["answer"]
        assert "## Genel değerlendirme" in answer
        assert "## Neden uygun görünüyor" in answer
        assert "## Başvuru öncesi öneriler" in answer
    finally:
        close_connection(connection)
