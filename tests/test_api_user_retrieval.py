from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from hiring_radar.api.app import create_app
from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.db.sqlite import close_connection, initialize_database
from hiring_radar.models import RetrievalChunk
from hiring_radar.services.retrieval.embedding_jobs import DeterministicEmbeddingProvider
from hiring_radar.services.user_auth import UserSession


class RetrievalApiFixture:
    def __init__(self, repository: HiringRadarRepository, subscriber_id: int) -> None:
        self.repository = repository
        self.subscriber_id = subscriber_id

    def make_session(self) -> UserSession:
        return UserSession(
            subscriber_id=self.subscriber_id,
            email="alice@example.com",
            issued_at="2026-04-05T10:00:00Z",
            expires_at="2026-04-05T12:00:00Z",
        )


def _build_fixture(db_path: Path) -> RetrievalApiFixture:
    connection = initialize_database(str(db_path))
    repository = HiringRadarRepository(connection)
    provider = DeterministicEmbeddingProvider()

    subscriber, _ = repository.upsert_subscriber(
        email="alice@example.com",
        full_name="Alice Example",
        updated_at="2026-04-05T10:00:00Z",
    )
    assert subscriber.id is not None

    source = repository.upsert_retrieval_source(
        subscriber.id,
        source_type="profile",
        source_ref=f"profile:{subscriber.id}",
        title="Alice Profile",
        locale="tr",
        status="ready",
        checksum="source-checksum",
        metadata_json={"kind": "profile"},
        updated_at="2026-04-05T10:01:00Z",
        last_ingested_at="2026-04-05T10:01:00Z",
    )
    assert source.id is not None

    document = repository.upsert_retrieval_document(
        source.id,
        document_kind="profile_aggregate",
        title="Alice Aggregate",
        body_text="python backend fastapi retrieval embeddings testing context assembly",
        metadata_json={"section": "aggregate"},
        checksum="document-checksum",
        status="ready",
        version=1,
        updated_at="2026-04-05T10:02:00Z",
    )
    assert document.id is not None

    chunks = repository.replace_retrieval_chunks(
        document.id,
        chunks=[
            RetrievalChunk(
                document_id=document.id,
                chunk_index=0,
                content="python backend fastapi retrieval",
                token_estimate=4,
                metadata_json={"section": "headline"},
                embedding_status="ready",
            ),
            RetrievalChunk(
                document_id=document.id,
                chunk_index=1,
                content="embeddings testing context assembly",
                token_estimate=4,
                metadata_json={"section": "summary"},
                embedding_status="ready",
            ),
        ],
        created_at="2026-04-05T10:03:00Z",
    )

    for chunk in chunks:
        vector = provider.embed_text(text=chunk.content)
        repository.delete_retrieval_embeddings_for_chunk(chunk.id or 0)
        repository.create_retrieval_embedding(
            chunk.id or 0,
            provider=vector.provider,
            model=vector.model,
            vector_ref=None,
            vector_json=json.dumps(vector.vector),
            dimensions=vector.dimensions,
            created_at="2026-04-05T10:04:00Z",
        )
        repository.update_retrieval_chunk_embedding_status(chunk.id or 0, embedding_status="ready")

    return RetrievalApiFixture(repository=repository, subscriber_id=subscriber.id)


def test_user_retrieval_search_endpoint_returns_ranked_results(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path / "retrieval_search.db")
    app = create_app()
    app.dependency_overrides[get_current_user_session] = fixture.make_session
    app.dependency_overrides[get_repository] = lambda: fixture.repository

    client = TestClient(app)
    response = client.post(
        "/api/user/retrieval/search",
        json={
            "query_text": "python backend fastapi retrieval",
            "top_k": 2,
            "document_kinds": ["profile_aggregate"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result_count"] == 2
    assert payload["query_provider"] == "deterministic"
    assert payload["query_model"] == "sha256-16d"
    assert payload["results"][0]["chunk_index"] == 0
    assert payload["results"][0]["document_kind"] == "profile_aggregate"
    assert payload["results"][0]["embedding_provider"] == "deterministic"

    close_connection(fixture.repository.connection)



def test_user_retrieval_context_endpoint_returns_structured_bundle(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path / "retrieval_context.db")
    app = create_app()
    app.dependency_overrides[get_current_user_session] = fixture.make_session
    app.dependency_overrides[get_repository] = lambda: fixture.repository

    client = TestClient(app)
    response = client.post(
        "/api/user/retrieval/context",
        json={
            "query_text": "testing context assembly",
            "search_top_k": 4,
            "result_limit": 2,
            "max_total_characters": 300,
            "max_total_tokens": 120,
            "max_chars_per_item": 180,
            "adjacent_window": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] >= 1
    assert payload["query_model"] == "sha256-16d"
    assert payload["items"][0]["document_kind"] == "profile_aggregate"
    assert payload["items"][0]["references"]

    close_connection(fixture.repository.connection)



def test_user_retrieval_endpoint_requires_authentication() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/user/retrieval/search",
        json={"query_text": "python backend"},
    )

    assert response.status_code == 401
