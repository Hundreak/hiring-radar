from __future__ import annotations

import json
import math
from collections.abc import Iterable
from dataclasses import dataclass

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import RetrievalSearchCandidate
from hiring_radar.services.retrieval.embedding_jobs import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    EmbeddingProvider,
)


@dataclass(slots=True, frozen=True)
class RetrievalSearchResult:
    similarity: float
    source_id: int
    source_type: str
    source_ref: str
    source_title: str | None
    source_locale: str | None
    document_id: int
    document_kind: str
    document_title: str | None
    document_version: int
    chunk_id: int
    chunk_index: int
    content: str
    token_estimate: int | None
    chunk_metadata_json: dict[str, object]
    embedding_provider: str
    embedding_model: str


@dataclass(slots=True, frozen=True)
class RetrievalSearchResponse:
    query_text: str
    query_provider: str
    query_model: str
    total_candidates: int
    results: tuple[RetrievalSearchResult, ...]



def search_retrieval_chunks(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    query_text: str,
    embedding_provider: EmbeddingProvider,
    top_k: int = 5,
    minimum_similarity: float | None = None,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    source_types: Iterable[str] | None = None,
    document_kinds: Iterable[str] | None = None,
) -> RetrievalSearchResponse:
    if top_k < 1:
        raise ValueError("Retrieval search top_k must be >= 1.")

    normalized_query = query_text.strip()
    if not normalized_query:
        return RetrievalSearchResponse(
            query_text=query_text,
            query_provider=provider,
            query_model=model,
            total_candidates=0,
            results=(),
        )

    query_embedding = embedding_provider.embed_text(text=normalized_query)
    candidates = repository.list_retrieval_search_candidates(
        subscriber_id=subscriber_id,
        provider=provider,
        model=model,
        source_types=source_types,
        document_kinds=document_kinds,
    )

    ranked: list[RetrievalSearchResult] = []
    query_vector = tuple(query_embedding.vector)

    for candidate in candidates:
        candidate_vector = _parse_embedding_vector(candidate)
        if candidate_vector is None:
            continue
        if len(candidate_vector) != len(query_vector):
            continue

        similarity = _cosine_similarity(query_vector, candidate_vector)
        if minimum_similarity is not None and similarity < minimum_similarity:
            continue

        ranked.append(
            RetrievalSearchResult(
                similarity=similarity,
                source_id=candidate.source_id,
                source_type=candidate.source_type,
                source_ref=candidate.source_ref,
                source_title=candidate.source_title,
                source_locale=candidate.source_locale,
                document_id=candidate.document_id,
                document_kind=candidate.document_kind,
                document_title=candidate.document_title,
                document_version=candidate.document_version,
                chunk_id=candidate.chunk_id,
                chunk_index=candidate.chunk_index,
                content=candidate.content,
                token_estimate=candidate.token_estimate,
                chunk_metadata_json=dict(candidate.chunk_metadata_json),
                embedding_provider=candidate.embedding_provider,
                embedding_model=candidate.embedding_model,
            )
        )

    ranked.sort(key=lambda item: (-item.similarity, item.chunk_id))
    results = tuple(ranked[:top_k])
    return RetrievalSearchResponse(
        query_text=query_text,
        query_provider=query_embedding.provider,
        query_model=query_embedding.model,
        total_candidates=len(candidates),
        results=results,
    )



def _parse_embedding_vector(candidate: RetrievalSearchCandidate) -> tuple[float, ...] | None:
    raw_vector = candidate.embedding_vector_json
    if raw_vector is None:
        return None

    payload = json.loads(raw_vector)
    if not isinstance(payload, list):
        return None

    values: list[float] = []
    for item in payload:
        if not isinstance(item, (int, float)):
            return None
        values.append(float(item))
    return tuple(values)



def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0

    dot = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=False))
    return dot / (left_norm * right_norm)
