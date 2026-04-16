from __future__ import annotations

import json
from pathlib import Path

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import RetrievalChunk
from hiring_radar.services.retrieval.context import build_retrieval_context_bundle
from hiring_radar.services.retrieval.embedding_jobs import EmbeddingVectorResult


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
    connection = initialize_database(str(tmp_path / "retrieval_context.db"))
    return HiringRadarRepository(connection), connection



def _create_subscriber(repo: HiringRadarRepository, email: str, subscriber_number: int) -> int:
    subscriber, _ = repo.upsert_subscriber(
        email=email,
        full_name=f"Subscriber {subscriber_number}",
        updated_at=f"2026-04-14T15:00:0{subscriber_number}Z",
    )
    return subscriber.id or 0



def _create_search_document(
    repo: HiringRadarRepository,
    *,
    subscriber_id: int,
    ref_suffix: str,
    chunks: list[tuple[int, str, tuple[float, ...]]],
    source_type: str = "profile",
    document_kind: str = "profile_aggregate",
    provider: str = "test",
    model: str = "test-2d",
) -> tuple[int, list[int]]:
    timestamp = f"2026-04-14T16:00:{ref_suffix[-2:].zfill(2)}Z"
    source = repo.upsert_retrieval_source(
        subscriber_id,
        source_type=source_type,
        source_ref=f"subscriber:{subscriber_id}:{ref_suffix}",
        title=f"Source {ref_suffix}",
        locale="tr",
        status="ready",
        checksum=f"source-{ref_suffix}",
        metadata_json={"ref": ref_suffix},
        updated_at=timestamp,
    )
    document = repo.upsert_retrieval_document(
        source.id or 0,
        document_kind=document_kind,
        title=f"Document {ref_suffix}",
        body_text="\n\n".join(content for _, content, _ in chunks),
        metadata_json={"ref": ref_suffix},
        checksum=f"document-{ref_suffix}",
        status="ready",
        version=1,
        updated_at=timestamp,
    )
    stored_chunks = repo.replace_retrieval_chunks(
        document.id or 0,
        chunks=[
            RetrievalChunk(
                chunk_index=chunk_index,
                content=content,
                token_estimate=len(content.split()),
                metadata_json={"ref": ref_suffix, "chunk_index": chunk_index},
                embedding_status="ready",
            )
            for chunk_index, content, _ in chunks
        ],
        created_at=timestamp,
    )
    stored_chunk_ids: list[int] = []
    for stored_chunk, (_, _, vector) in zip(stored_chunks, chunks, strict=True):
        repo.create_retrieval_embedding(
            stored_chunk.id or 0,
            provider=provider,
            model=model,
            vector_ref=None,
            vector_json=json.dumps(vector),
            dimensions=len(vector),
            created_at=timestamp,
        )
        stored_chunk_ids.append(stored_chunk.id or 0)
    return source.id or 0, stored_chunk_ids



def test_build_retrieval_context_bundle_merges_adjacent_chunks_from_same_document(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "alice@example.com", 1)
        _, chunk_ids = _create_search_document(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="41",
            chunks=[
                (0, "Built a retrieval orchestration layer for profile syncing.", (1.0, 0.0)),
                (1, "Implemented safe trigger wiring and additive ingestion updates.", (0.98, 0.02)),
                (3, "Unrelated appendix note.", (0.1, 0.99)),
            ],
        )

        bundle = build_retrieval_context_bundle(
            repo,
            subscriber_id=subscriber_id,
            query_text="retrieval orchestration",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
            search_top_k=3,
            result_limit=3,
        )

        assert bundle.total_search_results == 3
        assert bundle.total_items == 2
        first_item = bundle.items[0]
        assert first_item.merged_chunk_count == 2
        assert tuple(reference.chunk_id for reference in first_item.references) == tuple(chunk_ids[:2])
        assert tuple(reference.chunk_index for reference in first_item.references) == (0, 1)
        assert "retrieval orchestration layer" in first_item.content
        assert "safe trigger wiring" in first_item.content
    finally:
        close_connection(connection)



def test_build_retrieval_context_bundle_applies_budget_and_marks_truncation(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "bob@example.com", 2)
        _create_search_document(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="42",
            chunks=[
                (
                    0,
                    " ".join(["production-grade retrieval context"] * 40),
                    (1.0, 0.0),
                )
            ],
        )

        bundle = build_retrieval_context_bundle(
            repo,
            subscriber_id=subscriber_id,
            query_text="production retrieval",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
            search_top_k=1,
            result_limit=1,
            max_total_characters=120,
            max_total_tokens=20,
            max_chars_per_item=120,
        )

        assert bundle.total_items == 1
        assert bundle.truncated is True
        assert bundle.items[0].truncated is True
        assert bundle.total_characters <= 120
        assert bundle.total_token_estimate <= 20
        assert bundle.items[0].content.endswith("…")
    finally:
        close_connection(connection)



def test_build_retrieval_context_bundle_prefers_source_diversity_before_fallback(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "carol@example.com", 3)
        first_source_id, _ = _create_search_document(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="43",
            chunks=[
                (0, "Primary source strongest match.", (1.0, 0.0)),
                (2, "Primary source second strongest match.", (0.99, 0.01)),
            ],
        )
        second_source_id, _ = _create_search_document(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="44",
            chunks=[
                (0, "Secondary source strong match.", (0.97, 0.03)),
            ],
        )

        bundle = build_retrieval_context_bundle(
            repo,
            subscriber_id=subscriber_id,
            query_text="strong match",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
            search_top_k=3,
            result_limit=2,
            diversify_sources=True,
        )

        assert bundle.total_items == 2
        assert bundle.items[0].source_id == first_source_id
        assert bundle.items[1].source_id == second_source_id
    finally:
        close_connection(connection)



def test_build_retrieval_context_bundle_deduplicates_identical_context_content(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "dave@example.com", 4)
        duplicate_content = "Designed a deterministic retrieval ingestion pipeline for profile data."
        _create_search_document(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="45",
            chunks=[(0, duplicate_content, (1.0, 0.0))],
        )
        _create_search_document(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="46",
            chunks=[(0, duplicate_content, (0.99, 0.01))],
            source_type="cv_upload",
            document_kind="cv_text",
        )

        bundle = build_retrieval_context_bundle(
            repo,
            subscriber_id=subscriber_id,
            query_text="retrieval ingestion pipeline",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
            search_top_k=4,
            result_limit=4,
            diversify_sources=False,
        )

        assert bundle.total_search_results == 2
        assert bundle.total_items == 1
        assert bundle.items[0].content == duplicate_content
    finally:
        close_connection(connection)



def test_build_retrieval_context_bundle_returns_empty_bundle_for_blank_query(tmp_path: Path) -> None:
    repo, connection = _make_repo(tmp_path)

    try:
        subscriber_id = _create_subscriber(repo, "eve@example.com", 5)
        _create_search_document(
            repo,
            subscriber_id=subscriber_id,
            ref_suffix="47",
            chunks=[(0, "Stored profile evidence.", (1.0, 0.0))],
        )

        bundle = build_retrieval_context_bundle(
            repo,
            subscriber_id=subscriber_id,
            query_text="   ",
            embedding_provider=FakeQueryEmbeddingProvider((1.0, 0.0)),
            provider="test",
            model="test-2d",
        )

        assert bundle.total_search_results == 0
        assert bundle.total_items == 0
        assert bundle.items == ()
        assert bundle.truncated is False
    finally:
        close_connection(connection)
