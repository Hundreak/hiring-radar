from __future__ import annotations

from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import RetrievalChunk


def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "retrieval_embedding_jobs.db"))
    return HiringRadarRepository(connection), connection



def _seed_chunk(repo: HiringRadarRepository) -> RetrievalChunk:
    subscriber, _ = repo.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-14T09:00:00Z",
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
        updated_at="2026-04-14T09:01:00Z",
        last_ingested_at="2026-04-14T09:01:00Z",
    )
    document = repo.upsert_retrieval_document(
        source.id or 0,
        document_kind="profile_aggregate",
        title="Profile aggregate",
        body_text="Alice designs RF systems and embedded platforms.",
        metadata_json={"paragraphs": 1},
        checksum="document-checksum",
        status="ready",
        version=1,
        updated_at="2026-04-14T09:02:00Z",
    )
    return repo.replace_retrieval_chunks(
        document.id or 0,
        chunks=[
            RetrievalChunk(
                chunk_index=0,
                content="Alice designs RF systems and embedded platforms.",
                token_estimate=8,
                metadata_json={"section": "summary"},
                embedding_status="pending",
            )
        ],
        created_at="2026-04-14T09:03:00Z",
    )[0]



def test_enqueue_claim_fail_and_complete_retrieval_embedding_jobs(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        chunk = _seed_chunk(repo)
        assert chunk.id is not None

        queued = repo.enqueue_retrieval_embedding_job(
            chunk.id,
            provider="deterministic",
            model="sha256-16d",
            created_at="2026-04-14T09:04:00Z",
        )
        assert queued.id is not None
        assert queued.status == "queued"
        assert repo.get_retrieval_chunk(chunk.id).embedding_status == "queued"

        duplicate = repo.enqueue_retrieval_embedding_job(
            chunk.id,
            provider="deterministic",
            model="sha256-16d",
            created_at="2026-04-14T09:05:00Z",
        )
        assert duplicate.id == queued.id
        assert len(repo.list_retrieval_embedding_jobs()) == 1

        claimed = repo.claim_next_retrieval_embedding_job(
            provider="deterministic",
            model="sha256-16d",
            claimed_at="2026-04-14T09:06:00Z",
        )
        assert claimed is not None
        assert claimed.id == queued.id
        assert claimed.status == "processing"
        assert claimed.attempt_count == 1
        assert repo.get_retrieval_chunk(chunk.id).embedding_status == "processing"

        failed = repo.fail_retrieval_embedding_job(
            claimed.id or 0,
            error_message="runtime unavailable",
            failed_at="2026-04-14T09:07:00Z",
        )
        assert failed.status == "failed"
        assert failed.last_error == "runtime unavailable"
        assert repo.get_retrieval_chunk(chunk.id).embedding_status == "failed"

        second_job = repo.enqueue_retrieval_embedding_job(
            chunk.id,
            provider="deterministic",
            model="sha256-16d",
            created_at="2026-04-14T09:08:00Z",
        )
        assert second_job.id != claimed.id

        claimed_second = repo.claim_next_retrieval_embedding_job(
            provider="deterministic",
            model="sha256-16d",
            claimed_at="2026-04-14T09:09:00Z",
        )
        assert claimed_second is not None
        assert claimed_second.id == second_job.id
        assert claimed_second.attempt_count == 1

        completed = repo.complete_retrieval_embedding_job(
            claimed_second.id or 0,
            completed_at="2026-04-14T09:10:00Z",
        )
        assert completed.status == "completed"
        assert completed.completed_at == "2026-04-14T09:10:00Z"
    finally:
        close_connection(connection)



def test_claim_next_retrieval_embedding_job_filters_by_provider_and_model(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        chunk = _seed_chunk(repo)
        assert chunk.id is not None

        repo.enqueue_retrieval_embedding_job(
            chunk.id,
            provider="deterministic",
            model="sha256-16d",
            created_at="2026-04-14T09:11:00Z",
        )
        repo.enqueue_retrieval_embedding_job(
            chunk.id,
            provider="custom",
            model="v2",
            created_at="2026-04-14T09:12:00Z",
        )

        claimed = repo.claim_next_retrieval_embedding_job(
            provider="custom",
            model="v2",
            claimed_at="2026-04-14T09:13:00Z",
        )
        assert claimed is not None
        assert claimed.provider == "custom"
        assert claimed.model == "v2"

        remaining = repo.find_active_retrieval_embedding_job(
            chunk.id,
            provider="deterministic",
            model="sha256-16d",
        )
        assert remaining is not None
        assert remaining.status == "queued"
    finally:
        close_connection(connection)
