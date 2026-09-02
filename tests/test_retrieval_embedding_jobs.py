from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import RetrievalChunk
from hiring_radar.services.retrieval.embedding_jobs import (
    CHUNK_EMBEDDING_STATUS_FAILED,
    CHUNK_EMBEDDING_STATUS_READY,
    PROCESS_ACTION_FAILED,
    PROCESS_ACTION_IDLE,
    PROCESS_ACTION_PROCESSED,
    DeterministicEmbeddingProvider,
    EmbeddingVectorResult,
    enqueue_chunk_embedding_jobs,
    process_next_embedding_job,
    run_embedding_job_batch,
)


class ExplodingEmbeddingProvider:
    def embed_text(self, *, text: str) -> EmbeddingVectorResult:
        raise RuntimeError("embedding runtime offline")



def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "retrieval_embedding_processor.db"))
    return HiringRadarRepository(connection), connection



def _seed_chunks(repo: HiringRadarRepository) -> list[RetrievalChunk]:
    subscriber, _ = repo.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-14T10:00:00Z",
    )
    source = repo.upsert_retrieval_source(
        subscriber.id or 0,
        source_type="profile",
        source_ref=f"subscriber:{subscriber.id}:profile",
        title="Profile aggregate",
        locale="tr",
        status="ready",
        checksum="source-checksum",
        metadata_json={"origin": "test"},
        updated_at="2026-04-14T10:01:00Z",
        last_ingested_at="2026-04-14T10:01:00Z",
    )
    document = repo.upsert_retrieval_document(
        source.id or 0,
        document_kind="profile_aggregate",
        title="Profile aggregate",
        body_text="Alice builds retrieval systems. Alice deploys APIs.",
        metadata_json={"paragraphs": 2},
        checksum="document-checksum",
        status="ready",
        version=1,
        updated_at="2026-04-14T10:02:00Z",
    )
    return repo.replace_retrieval_chunks(
        document.id or 0,
        chunks=[
            RetrievalChunk(
                chunk_index=0,
                content="Alice builds retrieval systems.",
                token_estimate=4,
                metadata_json={"section": "summary"},
                embedding_status="pending",
            ),
            RetrievalChunk(
                chunk_index=1,
                content="Alice deploys APIs.",
                token_estimate=3,
                metadata_json={"section": "experience"},
                embedding_status="pending",
            ),
        ],
        created_at="2026-04-14T10:03:00Z",
    )



def test_process_next_embedding_job_persists_embedding_and_marks_chunk_ready(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        chunks = _seed_chunks(repo)
        enqueue_chunk_embedding_jobs(repo, chunks=chunks, created_at="2026-04-14T10:04:00Z")

        result = process_next_embedding_job(
            repo,
            embedding_provider=DeterministicEmbeddingProvider(),
            now="2026-04-14T10:05:00Z",
        )

        assert result.action == PROCESS_ACTION_PROCESSED
        assert result.job is not None
        assert result.job.status == "completed"
        assert result.chunk is not None
        assert result.chunk.embedding_status == CHUNK_EMBEDDING_STATUS_READY
        assert result.embedding is not None
        assert result.embedding.dimensions == 16
        embeddings = repo.list_retrieval_embeddings(result.chunk.id or 0)
        assert len(embeddings) == 1
    finally:
        close_connection(connection)



def test_process_next_embedding_job_replaces_existing_embedding(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        chunks = _seed_chunks(repo)
        first_chunk = chunks[0]
        assert first_chunk.id is not None
        repo.create_retrieval_embedding(
            first_chunk.id,
            provider="deterministic",
            model="sha256-16d",
            vector_ref=None,
            vector_json="[0.1, 0.2]",
            dimensions=2,
            created_at="2026-04-14T10:04:30Z",
        )
        enqueue_chunk_embedding_jobs(repo, chunks=[first_chunk], created_at="2026-04-14T10:05:00Z")

        result = process_next_embedding_job(
            repo,
            embedding_provider=DeterministicEmbeddingProvider(),
            now="2026-04-14T10:06:00Z",
        )

        assert result.action == PROCESS_ACTION_PROCESSED
        embeddings = repo.list_retrieval_embeddings(first_chunk.id)
        assert len(embeddings) == 1
        assert embeddings[0].dimensions == 16
    finally:
        close_connection(connection)



def test_process_next_embedding_job_marks_failure_when_provider_raises(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        chunks = _seed_chunks(repo)
        enqueue_chunk_embedding_jobs(repo, chunks=chunks[:1], created_at="2026-04-14T10:07:00Z")

        result = process_next_embedding_job(
            repo,
            embedding_provider=ExplodingEmbeddingProvider(),
            now="2026-04-14T10:08:00Z",
        )

        assert result.action == PROCESS_ACTION_FAILED
        assert result.job is not None
        assert result.job.status == "failed"
        assert result.error_message == "embedding runtime offline"
        assert result.chunk is not None
        assert result.chunk.embedding_status == CHUNK_EMBEDDING_STATUS_FAILED
    finally:
        close_connection(connection)



def test_run_embedding_job_batch_processes_until_idle(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        chunks = _seed_chunks(repo)
        enqueue_chunk_embedding_jobs(repo, chunks=chunks, created_at="2026-04-14T10:09:00Z")

        results = run_embedding_job_batch(
            repo,
            embedding_provider=DeterministicEmbeddingProvider(),
            limit=4,
            now="2026-04-14T10:10:00Z",
        )

        assert [result.action for result in results] == [
            PROCESS_ACTION_PROCESSED,
            PROCESS_ACTION_PROCESSED,
            PROCESS_ACTION_IDLE,
        ]
        assert all(
            repo.get_retrieval_chunk(chunk.id or 0).embedding_status == CHUNK_EMBEDDING_STATUS_READY
            for chunk in chunks
        )
    finally:
        close_connection(connection)
