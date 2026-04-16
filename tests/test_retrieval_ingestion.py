from __future__ import annotations

from pathlib import Path

import pytest

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import (
    RetrievalChunk,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageEntry,
)
from hiring_radar.services.retrieval.ingestion import (
    DOCUMENT_KIND_CV_TEXT,
    DOCUMENT_KIND_PROFILE_AGGREGATE,
    SOURCE_TYPE_CV_UPLOAD,
    SOURCE_TYPE_PROFILE,
    build_cv_prepared_document,
    build_profile_prepared_document,
    ingest_prepared_document,
)


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "retrieval_ingestion.db"))
    return HiringRadarRepository(connection), connection



def test_profile_retrieval_ingestion_builds_source_document_chunks_and_jobs(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-13T13:00:00Z",
        )
        subscriber_id = subscriber.id or 0
        repo.upsert_subscriber_profile(
            subscriber_id,
            phone=None,
            headline="Backend Engineer",
            summary="Builds API platforms and data-heavy systems.",
            target_roles=("Backend Engineer", "Platform Engineer"),
            skills=("Python", "FastAPI"),
            preferred_locations=("Remote",),
            remote_preference="remote",
            cv_filename=None,
            cv_uploaded_at=None,
            updated_at="2026-04-13T13:01:00Z",
        )
        repo.upsert_subscriber_skill_detail(
            subscriber_id,
            skill_name="Python",
            category="Software",
            proficiency_hint="Advanced",
            years_hint=6,
            evidence_note="Built APIs and automation pipelines.",
            evidence_file_name=None,
            updated_at="2026-04-13T13:02:00Z",
        )
        repo.replace_subscriber_education_entries(
            subscriber_id,
            entries=[
                SubscriberEducationEntry(
                    subscriber_id=subscriber_id,
                    school_name="Example University",
                    degree_name="BSc",
                    field_of_study="Computer Engineering",
                    start_year=2015,
                    end_year=2019,
                    display_order=0,
                )
            ],
            updated_at="2026-04-13T13:03:00Z",
        )
        repo.replace_subscriber_experience_entries(
            subscriber_id,
            entries=[
                SubscriberExperienceEntry(
                    subscriber_id=subscriber_id,
                    title="Platform Engineer",
                    company_name="Example Corp",
                    start_year=2020,
                    end_year=None,
                    summary="Owns internal developer platform.",
                    display_order=0,
                )
            ],
            updated_at="2026-04-13T13:04:00Z",
        )
        repo.replace_subscriber_language_entries(
            subscriber_id,
            entries=[
                SubscriberLanguageEntry(
                    subscriber_id=subscriber_id,
                    language_name="English",
                    proficiency_level="C1",
                    notes="Used in day-to-day work.",
                    display_order=0,
                )
            ],
            updated_at="2026-04-13T13:05:00Z",
        )

        prepared = build_profile_prepared_document(repo, subscriber_id=subscriber_id, locale="en")
        result = ingest_prepared_document(
            repo,
            prepared,
            now="2026-04-13T13:10:00Z",
        )

        assert result.action == "created"
        assert result.changed is True
        assert result.source is not None
        assert result.document is not None
        assert result.source.status == "ready"
        assert result.document.status == "ready"
        assert result.document.version == 1
        assert result.source.last_ingested_at == "2026-04-13T13:10:00Z"
        assert result.chunk_count >= 1

        source = repo.get_retrieval_source_by_key(
            subscriber_id,
            SOURCE_TYPE_PROFILE,
            f"subscriber:{subscriber_id}:profile",
        )
        assert source is not None and source.id is not None

        document = repo.get_retrieval_document_by_kind(
            source.id,
            DOCUMENT_KIND_PROFILE_AGGREGATE,
        )
        assert document is not None and document.id is not None

        chunks = repo.list_retrieval_chunks(document.id)
        jobs = repo.list_retrieval_embedding_jobs()
        assert len(chunks) == result.chunk_count
        assert len(jobs) == len(chunks)
        assert all(chunk.embedding_status == "queued" for chunk in chunks)

        second = ingest_prepared_document(
            repo,
            prepared,
            now="2026-04-13T13:11:00Z",
        )
        assert second.action == "noop"
        assert second.changed is False
        assert len(repo.list_retrieval_embedding_jobs()) == len(jobs)

        repo.upsert_subscriber_profile(
            subscriber_id,
            phone=None,
            headline="Senior Backend Engineer",
            summary="Builds API platforms and retrieval systems.",
            target_roles=("Backend Engineer", "Platform Engineer"),
            skills=("Python", "FastAPI"),
            preferred_locations=("Remote",),
            remote_preference="remote",
            cv_filename=None,
            cv_uploaded_at=None,
            updated_at="2026-04-13T13:12:00Z",
        )
        changed_prepared = build_profile_prepared_document(repo, subscriber_id=subscriber_id, locale="en")
        changed = ingest_prepared_document(
            repo,
            changed_prepared,
            now="2026-04-13T13:13:00Z",
        )
        assert changed.action == "updated"
        assert changed.changed is True
        assert changed.document is not None
        assert changed.document.version == 2
        changed_jobs = repo.list_retrieval_embedding_jobs()
        assert len(changed_jobs) == changed.chunk_count
    finally:
        close_connection(connection)



def test_cv_retrieval_document_builder_returns_empty_body_when_not_parsed(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="bob@example.com",
            full_name="Bob Example",
            updated_at="2026-04-13T14:00:00Z",
        )
        subscriber_id = subscriber.id or 0
        upload = repo.create_subscriber_cv_upload(
            subscriber_id,
            original_filename="resume.pdf",
            storage_path="/tmp/resume.pdf",
            content_type="application/pdf",
            file_size_bytes=1200,
            extracted_text=None,
            parse_status="pending",
            uploaded_at="2026-04-13T14:01:00Z",
            parsed_at=None,
        )
        prepared = build_cv_prepared_document(
            repo,
            subscriber_id=subscriber_id,
            cv_upload_id=upload.id or 0,
            locale="en",
        )
        assert prepared is not None
        assert prepared.body_text == ""
    finally:
        close_connection(connection)



def test_cv_ingestion_creates_jobs_only_for_parsed_text(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="carol@example.com",
            full_name="Carol Example",
            updated_at="2026-04-13T15:00:00Z",
        )
        subscriber_id = subscriber.id or 0
        upload = repo.create_subscriber_cv_upload(
            subscriber_id,
            original_filename="cv.txt",
            storage_path="/tmp/cv.txt",
            content_type="text/plain",
            file_size_bytes=100,
            extracted_text=None,
            parse_status="failed",
            uploaded_at="2026-04-13T15:03:00Z",
            parsed_at="2026-04-13T15:03:30Z",
        )
        prepared = build_cv_prepared_document(
            repo,
            subscriber_id=subscriber_id,
            cv_upload_id=upload.id or 0,
            locale="en",
        )
        assert prepared is not None

        skipped = ingest_prepared_document(
            repo,
            prepared,
            now="2026-04-13T15:04:00Z",
        )
        assert skipped.action == "skipped"
        assert skipped.reason == "empty_body"
        assert repo.list_retrieval_embedding_jobs() == []

        repo.update_subscriber_cv_upload_parse_result(
            upload.id or 0,
            extracted_text="Carol builds ranking systems. She maintains retrieval pipelines.",
            parse_status="parsed",
            parsed_at="2026-04-13T15:05:00Z",
            updated_at="2026-04-13T15:05:00Z",
        )
        prepared = build_cv_prepared_document(
            repo,
            subscriber_id=subscriber_id,
            cv_upload_id=upload.id or 0,
            locale="en",
        )
        created = ingest_prepared_document(
            repo,
            prepared,
            now="2026-04-13T15:06:00Z",
        )
        assert created.action in {"created", "updated"}
        assert created.document is not None and created.document.id is not None

        source = repo.get_retrieval_source_by_key(
            subscriber_id,
            SOURCE_TYPE_CV_UPLOAD,
            f"cv_upload:{upload.id}",
        )
        assert source is not None and source.id is not None
        document = repo.get_retrieval_document_by_kind(source.id, DOCUMENT_KIND_CV_TEXT)
        assert document is not None and document.id is not None
        assert repo.list_retrieval_embedding_jobs() != []
    finally:
        close_connection(connection)



def test_ingestion_marks_source_and_document_failed_when_chunk_replace_crashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="dora@example.com",
            full_name="Dora Example",
            updated_at="2026-04-13T16:00:00Z",
        )
        subscriber_id = subscriber.id or 0
        repo.upsert_subscriber_profile(
            subscriber_id,
            phone=None,
            headline="Platform Engineer",
            summary="Builds resilient APIs.",
            target_roles=("Platform Engineer",),
            skills=("Python",),
            preferred_locations=("Remote",),
            remote_preference="remote",
            cv_filename=None,
            cv_uploaded_at=None,
            updated_at="2026-04-13T16:01:00Z",
        )
        prepared = build_profile_prepared_document(repo, subscriber_id=subscriber_id, locale="en")

        def _boom(document_id: int, *, chunks: list[RetrievalChunk], created_at: str):
            raise RuntimeError("chunk replace failed")

        monkeypatch.setattr(repo, "replace_retrieval_chunks", _boom)

        with pytest.raises(RuntimeError, match="chunk replace failed"):
            ingest_prepared_document(
                repo,
                prepared,
                now="2026-04-13T16:02:00Z",
            )

        source = repo.get_retrieval_source_by_key(
            subscriber_id,
            SOURCE_TYPE_PROFILE,
            f"subscriber:{subscriber_id}:profile",
        )
        assert source is not None and source.id is not None
        assert source.status == "failed"

        document = repo.get_retrieval_document_by_kind(source.id, DOCUMENT_KIND_PROFILE_AGGREGATE)
        assert document is not None
        assert document.status == "failed"
    finally:
        close_connection(connection)
