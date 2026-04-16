from __future__ import annotations

import json
from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import RetrievalChunk
from hiring_radar.services.retrieval.embedding_jobs import EmbeddingVectorResult
from hiring_radar.services.retrieval.search import search_retrieval_chunks


class FakeQueryEmbeddingProvider:
    def __init__(self, vector: tuple[float, ...], *, provider: str = "test", model: str = "test-2d") -> None:
        self.vector = vector
        self.provider = provider
        self.model = model

    def embed_text(self, *, text: str) -> EmbeddingVectorResult:
        return EmbeddingVectorResult(
            provider=self.provider,
            model=self.model,
            vector=self.vector,
            dimensions=len(self.vector),
            vector_ref=None,
        )



def _make_repo(tmp_path: Path) -> tuple[HiringRadarRepository, object]:
    connection = initialize_database(str(tmp_path / "retrieval_search.db"))
    return HiringRadarRepository(connection), connection



def _create_subscriber(repo: HiringRadarRepository, email: str, subscriber_number: int) -> int:
    subscriber, _ = repo.upsert_subscriber(
        email=email,
        full_name=f"Subscriber {subscriber_number}",
        updated_at=f"2026-04-14T10:00:0{subscriber_number}Z",
    )
    return subscriber.id or 0



def _create_search_chunk(
    repo: HiringRadarRepository,
    *,
    subscriber_id: int,
    ref_suffix: str,
    content: str,
    vector: tuple[float, ...],
    source_type: str = "profile",
    document_kind: str = "profile_aggregate",
    source_status: str = "ready",
    document_status: str = "ready",
    embedding_status: str = "ready",
    provider: str = "test",
    model: str = "test-2d",
) -> int:
    timestamp_prefix = f"2026-04-14T12:00:{ref_suffix[-2:].zfill(2)}Z"
    source = repo.upsert_retrieval_source(
        subscriber_id,
        source_type=source_type,
        source_ref=f"subscriber:{subscriber_id}:{ref_suffix}",
        title=f"Source {ref_suffix}",
        locale="tr",
        status=source_status,
        checksum=f"source-{ref_suffix}",
        metadata_json={"ref": ref_suffix},
        updated_at=timestamp_prefix,
    )
    document = repo.upsert_retrieval_document(
        source.id or 0,
        document_kind=document_kind,
        title=f"Document {ref_suffix}",
        body_text=content,
        metadata_json={"ref": ref_suffix},
        checksum=f"document-{ref_suffix}",
        status=document_status,
        version=1,
        updated_at=timestamp_prefix,
    )
    chunks = repo.replace_retrieval_chunks(
        document.id or 0,
        chunks=[
            RetrievalChunk(
                chunk_index=0,
                content=content,
                token_estimate=len(content.split()),
                metadata_json={"ref": ref_suffix},
                embedding_status=embedding_status,
            )
        ],
        created_at=timestamp_prefix,
    )
    chunk = chunks[0]
    if embedding_status == "ready":
        repo.create_retrieval_embedding(
            chunk.id or 0,
            provider=provider,
            model=model,
            vector_ref=None,
            vector_json=json.dumps(vector),
            dimensions=len(vector),
            created_at=timestamp_prefix,
        )
    return chunk.id or 0



def test_search_retrieval_chunks_ranks_results_by_similarity(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "alice@example.com", 1)
        first_chunk_id = _create_search_chunk(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="01",
            content="Exact profile match.",
            vector=(1.0, 0.0),
        )
        second_chunk_id = _create_search_chunk(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="02",
            content="Nearby semantic match.",
            vector=(0.8, 0.2),
        )
        _create_search_chunk(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="03",
            content="Opposite direction.",
            vector=(-1.0, 0.0),
        )

        response = search_retrieval_chunks(
            repo,
            subscriber_id=subscriber_id,
            query_text="match query",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
            top_k=2,
        )

        assert response.total_candidates == 3
        assert len(response.results) == 2
        assert response.results[0].chunk_id == first_chunk_id
        assert response.results[1].chunk_id == second_chunk_id
        assert response.results[0].similarity > response.results[1].similarity
    finally:
        close_connection(connection)



def test_search_retrieval_chunks_applies_filters_and_threshold(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "bob@example.com", 2)
        kept_chunk_id = _create_search_chunk(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="10",
            content="Profile summary result.",
            vector=(1.0, 0.0),
            source_type="profile",
            document_kind="profile_aggregate",
        )
        _create_search_chunk(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="11",
            content="CV text result.",
            vector=(1.0, 0.0),
            source_type="cv_upload",
            document_kind="cv_text",
        )
        _create_search_chunk(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="12",
            content="Weak profile result.",
            vector=(0.1, 0.995),
            source_type="profile",
            document_kind="profile_aggregate",
        )

        response = search_retrieval_chunks(
            repo,
            subscriber_id=subscriber_id,
            query_text="profile",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
            top_k=5,
            source_types=("profile",),
            document_kinds=("profile_aggregate",),
            minimum_similarity=0.5,
        )

        assert response.total_candidates == 2
        assert [result.chunk_id for result in response.results] == [kept_chunk_id]
        assert response.results[0].document_kind == "profile_aggregate"
        assert response.results[0].source_type == "profile"
    finally:
        close_connection(connection)



def test_search_retrieval_chunks_is_subscriber_scoped_and_skips_non_ready_records(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        first_subscriber_id = _create_subscriber(repo, "carol@example.com", 3)
        second_subscriber_id = _create_subscriber(repo, "dave@example.com", 4)
        ready_chunk_id = _create_search_chunk(
            repo,
            subscriber_id=first_subscriber_id,
            ref_suffix="20",
            content="Ready profile record.",
            vector=(1.0, 0.0),
        )
        _create_search_chunk(
            repo,
            subscriber_id=first_subscriber_id,
            ref_suffix="21",
            content="Failed source record.",
            vector=(1.0, 0.0),
            source_status="failed",
        )
        _create_search_chunk(
            repo,
            subscriber_id=first_subscriber_id,
            ref_suffix="22",
            content="Failed chunk record.",
            vector=(1.0, 0.0),
            embedding_status="failed",
        )
        _create_search_chunk(
            repo,
            subscriber_id=second_subscriber_id,
            ref_suffix="23",
            content="Other subscriber record.",
            vector=(1.0, 0.0),
        )

        response = search_retrieval_chunks(
            repo,
            subscriber_id=first_subscriber_id,
            query_text="profile",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
        )

        assert [result.chunk_id for result in response.results] == [ready_chunk_id]
    finally:
        close_connection(connection)



def test_search_retrieval_chunks_returns_empty_for_blank_query(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "eve@example.com", 5)
        _create_search_chunk(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="30",
            content="Stored profile record.",
            vector=(1.0, 0.0),
        )

        response = search_retrieval_chunks(
            repo,
            subscriber_id=subscriber_id,
            query_text="   ",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
        )

        assert response.total_candidates == 0
        assert response.results == ()
    finally:
        close_connection(connection)
