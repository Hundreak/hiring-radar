from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import RetrievalChunk


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "retrieval_repository.db"))
    return HiringRadarRepository(connection), connection


def test_repository_can_upsert_retrieval_domain_and_replace_chunks(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber, _ = repo.upsert_subscriber(
            email="alice@example.com",
            full_name="Alice Example",
            updated_at="2026-04-13T12:00:00Z",
        )
        subscriber_id = subscriber.id or 0

        source = repo.upsert_retrieval_source(
            subscriber_id,
            source_type="profile",
            source_ref="subscriber:1:profile",
            title="Profile aggregate",
            locale="tr",
            status="pending",
            checksum="checksum-v1",
            metadata_json={"origin": "profile_workspace"},
            updated_at="2026-04-13T12:05:00Z",
        )
        assert source.id is not None
        assert source.metadata_json["origin"] == "profile_workspace"
        assert source.status == "pending"

        updated_source = repo.update_retrieval_source_lifecycle(
            source.id or 0,
            status="ready",
            updated_at="2026-04-13T12:06:00Z",
            last_ingested_at="2026-04-13T12:06:00Z",
            error_message=None,
        )
        assert updated_source.status == "ready"
        assert updated_source.last_ingested_at == "2026-04-13T12:06:00Z"

        document = repo.upsert_retrieval_document(
            updated_source.id or 0,
            document_kind="profile_summary",
            title="Profile aggregate",
            body_text="Alice builds resilient platforms.",
            metadata_json={"paragraphs": 1},
            checksum="checksum-v1",
            status="pending",
            version=1,
            updated_at="2026-04-13T12:07:00Z",
        )
        assert document.checksum == "checksum-v1"
        assert document.status == "pending"

        ready_document = repo.update_retrieval_document_lifecycle(
            document.id or 0,
            status="ready",
            updated_at="2026-04-13T12:08:00Z",
            checksum="checksum-v1",
            version=1,
        )
        assert ready_document.status == "ready"

        replaced_chunks = repo.replace_retrieval_chunks(
            ready_document.id or 0,
            chunks=[
                RetrievalChunk(
                    chunk_index=0,
                    content="Alice builds resilient platforms.",
                    token_estimate=4,
                    metadata_json={"section": "summary"},
                    embedding_status="pending",
                ),
                RetrievalChunk(
                    chunk_index=1,
                    content="Experienced in FastAPI and retrieval systems.",
                    token_estimate=6,
                    metadata_json={"section": "skills"},
                    embedding_status="pending",
                ),
            ],
            created_at="2026-04-13T12:09:00Z",
        )
        assert len(replaced_chunks) == 2
        assert replaced_chunks[0].metadata_json["section"] == "summary"
        assert replaced_chunks[1].chunk_index == 1

        listed_sources = repo.list_retrieval_sources(subscriber_id)
        listed_documents = repo.list_retrieval_documents(updated_source.id or 0)
        listed_chunks = repo.list_retrieval_chunks(ready_document.id or 0)

        assert len(listed_sources) == 1
        assert len(listed_documents) == 1
        assert len(listed_chunks) == 2
    finally:
        close_connection(connection)
