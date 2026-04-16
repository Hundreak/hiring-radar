from __future__ import annotations

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import (
    Subscriber,
    SubscriberCvUpload,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageCertificate,
    SubscriberLanguageEntry,
    SubscriberProfile,
)
from hiring_radar.services.retrieval.ingestion import (
    DOCUMENT_KIND_CV_TEXT,
    DOCUMENT_KIND_PROFILE_AGGREGATE,
    SOURCE_TYPE_CV_UPLOAD,
    SOURCE_TYPE_PROFILE,
)
from hiring_radar.services.retrieval.orchestration import (
    refresh_cv_upload_retrieval,
    refresh_profile_retrieval,
)
from hiring_radar.services.user_auth import UserSession


class TriggerRepository:
    def __init__(self) -> None:
        self.profile = SubscriberProfile(subscriber_id=7)
        self.education_entries: list[SubscriberEducationEntry] = []
        self.experience_entries: list[SubscriberExperienceEntry] = []
        self.language_entries: list[SubscriberLanguageEntry] = []
        self.language_certificates: list[SubscriberLanguageCertificate] = []
        self.latest_cv_upload: SubscriberCvUpload | None = None
        self.subscriber = Subscriber(
            id=7,
            email="alice@example.com",
            full_name="Alice Example",
            is_active=True,
            digest_enabled=True,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

    def get_subscriber_by_id(self, subscriber_id: int):
        return self.subscriber if subscriber_id == 7 else None

    def update_subscriber_fields_by_id(self, subscriber_id: int, *, fields: dict, updated_at: str):
        self.subscriber = Subscriber(
            id=7,
            email="alice@example.com",
            full_name=fields.get("full_name"),
            is_active=True,
            digest_enabled=True,
            created_at="2026-04-05T10:00:00Z",
            updated_at=updated_at,
        )
        return self.subscriber

    def get_subscriber_profile(self, subscriber_id: int):
        return self.profile

    def upsert_subscriber_profile(
        self,
        subscriber_id: int,
        *,
        phone,
        headline,
        summary,
        target_roles,
        skills,
        preferred_locations,
        remote_preference,
        cv_filename,
        cv_uploaded_at,
        updated_at,
        **kwargs,
    ):
        self.profile = SubscriberProfile(
            subscriber_id=subscriber_id,
            phone=phone,
            headline=headline,
            summary=summary,
            target_roles=target_roles,
            skills=skills,
            preferred_locations=preferred_locations,
            remote_preference=remote_preference,
            cv_filename=cv_filename,
            cv_uploaded_at=cv_uploaded_at,
            created_at=self.profile.created_at or updated_at,
            updated_at=updated_at,
        )
        return self.profile

    def list_subscriber_education_entries(self, subscriber_id: int):
        return self.education_entries

    def list_subscriber_experience_entries(self, subscriber_id: int):
        return self.experience_entries

    def list_subscriber_language_entries(self, subscriber_id: int):
        return self.language_entries

    def list_subscriber_language_certificates(self, subscriber_id: int):
        return self.language_certificates

    def get_latest_subscriber_cv_upload(self, subscriber_id: int):
        return self.latest_cv_upload



def _make_user_session() -> UserSession:
    return UserSession(
        subscriber_id=7,
        email="alice@example.com",
        issued_at="2026-04-05T10:00:00Z",
        expires_at="2026-04-05T12:00:00Z",
    )



def test_patch_basic_info_triggers_profile_refresh(monkeypatch) -> None:
    import hiring_radar.api.routers.user_profile as user_profile_router

    called: list[int] = []

    def _record(repository, *, subscriber_id: int) -> None:
        called.append(subscriber_id)

    monkeypatch.setattr(user_profile_router, "_sync_profile_retrieval_safe", _record)

    app = create_app()
    app.dependency_overrides[get_current_user_session] = _make_user_session
    app.dependency_overrides[get_repository] = lambda: TriggerRepository()

    client = TestClient(app)
    response = client.patch(
        "/api/user/profile/basic-info",
        json={
            "full_name": "Alice Example",
            "headline": "Senior Electronics Engineer",
            "summary": "Builds embedded systems.",
            "phone": "+90 555 111 2233",
            "primary_email": "alice@example.com",
        },
    )

    assert response.status_code == 200
    assert called == [7]



def _make_repository(tmp_path) -> tuple[HiringRadarRepository, int]:
    connection = initialize_database(str(tmp_path / "retrieval.db"))
    repository = HiringRadarRepository(connection)
    timestamp = "2026-04-14T10:00:00+00:00"
    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at=timestamp,
    )
    subscriber_id = subscriber.id or 0
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone="+90 555 000 0000",
        headline="Embedded Systems Engineer",
        summary="Designs RF and embedded platforms.",
        target_roles=("Embedded Engineer", "Firmware Engineer"),
        skills=("Python", "C++"),
        preferred_locations=("Istanbul",),
        remote_preference="hybrid",
        cv_filename=None,
        cv_uploaded_at=None,
        updated_at=timestamp,
    )
    repository.upsert_subscriber_skill_detail(
        subscriber_id,
        skill_name="Python",
        category="Programming",
        proficiency_hint="Automation and tooling",
        years_hint=5,
        evidence_note="Built internal data tooling.",
        updated_at=timestamp,
    )
    repository.replace_subscriber_experience_entries(
        subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                title="Embedded Engineer",
                company_name="CoreSift Labs",
                start_year=2021,
                end_year=None,
                summary="Developed BLE and telemetry pipelines.",
            )
        ],
        updated_at=timestamp,
    )
    return repository, subscriber_id



def test_refresh_profile_retrieval_is_idempotent_and_updates_versions(tmp_path) -> None:
    repository, subscriber_id = _make_repository(tmp_path)
    try:
        first = refresh_profile_retrieval(repository, subscriber_id=subscriber_id, locale="tr")
        assert first.action == "created"
        assert first.source_status == "ready"
        assert first.document_status == "ready"
        assert first.chunk_count > 0

        source = repository.get_retrieval_source_by_key(
            subscriber_id,
            SOURCE_TYPE_PROFILE,
            f"subscriber:{subscriber_id}:profile",
        )
        assert source is not None and source.id is not None
        document = repository.get_retrieval_document_by_kind(
            source.id,
            DOCUMENT_KIND_PROFILE_AGGREGATE,
        )
        assert document is not None
        original_version = document.version
        original_chunks = repository.list_retrieval_chunks(document.id or 0)
        original_jobs = repository.list_retrieval_embedding_jobs()
        assert len(original_jobs) == len(original_chunks)
        assert all(chunk.embedding_status == "queued" for chunk in original_chunks)

        second = refresh_profile_retrieval(repository, subscriber_id=subscriber_id, locale="tr")
        assert second.action == "noop"
        source = repository.get_retrieval_source_by_key(
            subscriber_id,
            SOURCE_TYPE_PROFILE,
            f"subscriber:{subscriber_id}:profile",
        )
        document = repository.get_retrieval_document_by_kind(
            source.id or 0,
            DOCUMENT_KIND_PROFILE_AGGREGATE,
        )
        assert document is not None
        assert document.version == original_version
        second_jobs = repository.list_retrieval_embedding_jobs()
        assert len(second_jobs) == len(original_jobs)

        repository.upsert_subscriber_profile(
            subscriber_id,
            phone="+90 555 000 0000",
            headline="Principal Embedded Engineer",
            summary="Designs RF, firmware and AI-assisted telemetry platforms.",
            target_roles=("Embedded Engineer", "Firmware Engineer"),
            skills=("Python", "C++", "DSP"),
            preferred_locations=("Istanbul",),
            remote_preference="hybrid",
            cv_filename=None,
            cv_uploaded_at=None,
            updated_at="2026-04-14T10:30:00+00:00",
        )

        third = refresh_profile_retrieval(repository, subscriber_id=subscriber_id, locale="tr")
        assert third.action == "updated"
        source = repository.get_retrieval_source_by_key(
            subscriber_id,
            SOURCE_TYPE_PROFILE,
            f"subscriber:{subscriber_id}:profile",
        )
        document = repository.get_retrieval_document_by_kind(
            source.id or 0,
            DOCUMENT_KIND_PROFILE_AGGREGATE,
        )
        assert document is not None
        assert document.version == original_version + 1
        updated_chunks = repository.list_retrieval_chunks(document.id or 0)
        updated_jobs = repository.list_retrieval_embedding_jobs()
        assert len(updated_jobs) == len(updated_chunks)
        assert all(chunk.embedding_status == "queued" for chunk in updated_chunks)
    finally:
        close_connection(repository.connection)



def test_refresh_cv_upload_retrieval_transitions_from_failed_to_ready(tmp_path) -> None:
    repository, subscriber_id = _make_repository(tmp_path)
    try:
        upload = repository.create_subscriber_cv_upload(
            subscriber_id,
            original_filename="alice_cv.pdf",
            storage_path="uploads/cv/alice_cv.pdf",
            content_type="application/pdf",
            file_size_bytes=1024,
            extracted_text=None,
            parse_status="failed",
            uploaded_at="2026-04-14T11:00:00+00:00",
            parsed_at="2026-04-14T11:00:10+00:00",
        )
        assert upload.id is not None

        first = refresh_cv_upload_retrieval(
            repository,
            subscriber_id=subscriber_id,
            cv_upload_id=upload.id,
            locale="tr",
        )
        assert first.action == "skipped"
        assert first.source_status == "failed"

        repository.update_subscriber_cv_upload_parse_result(
            upload.id,
            extracted_text="Alice Example\nEmbedded Systems Engineer\nPython C++ BLE DSP",
            parse_status="parsed",
            parsed_at="2026-04-14T11:05:00+00:00",
            updated_at="2026-04-14T11:05:00+00:00",
        )

        second = refresh_cv_upload_retrieval(
            repository,
            subscriber_id=subscriber_id,
            cv_upload_id=upload.id,
            locale="tr",
        )
        assert second.action in {"created", "updated"}
        assert second.source_status == "ready"
        assert second.document_status == "ready"
        assert second.chunk_count > 0

        source = repository.get_retrieval_source_by_key(
            subscriber_id,
            SOURCE_TYPE_CV_UPLOAD,
            f"cv_upload:{upload.id}",
        )
        assert source is not None and source.id is not None
        document = repository.get_retrieval_document_by_kind(
            source.id,
            DOCUMENT_KIND_CV_TEXT,
        )
        assert document is not None
        assert "Embedded Systems Engineer" in document.body_text
        chunks = repository.list_retrieval_chunks(document.id or 0)
        jobs = repository.list_retrieval_embedding_jobs()
        assert len(jobs) >= len(chunks)
        assert all(job.chunk_id in {chunk.id for chunk in chunks if chunk.id is not None} for job in jobs)
    finally:
        close_connection(repository.connection)
