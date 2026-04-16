from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.schemas.user_retrieval import (
    UserRetrievalContextItemResponse,
    UserRetrievalContextReferenceResponse,
    UserRetrievalContextRequest,
    UserRetrievalContextResponse,
    UserRetrievalSearchRequest,
    UserRetrievalSearchResponse,
    UserRetrievalSearchResultResponse,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.retrieval import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    DeterministicEmbeddingProvider,
    build_retrieval_context_bundle,
    search_retrieval_chunks,
)
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user/retrieval", tags=["user-retrieval"])

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


@router.post("/search", response_model=UserRetrievalSearchResponse)
def search_user_retrieval(
    payload: UserRetrievalSearchRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserRetrievalSearchResponse:
    _require_authenticated_subscriber(repository, subscriber_id=user_session.subscriber_id)

    provider = payload.provider or DEFAULT_EMBEDDING_PROVIDER
    model = payload.model or DEFAULT_EMBEDDING_MODEL
    search_response = search_retrieval_chunks(
        repository,
        subscriber_id=user_session.subscriber_id,
        query_text=payload.query_text,
        embedding_provider=DeterministicEmbeddingProvider(provider=provider, model=model),
        top_k=payload.top_k,
        minimum_similarity=payload.minimum_similarity,
        provider=provider,
        model=model,
        source_types=payload.source_types,
        document_kinds=payload.document_kinds,
    )

    return UserRetrievalSearchResponse(
        query_text=search_response.query_text,
        query_provider=search_response.query_provider,
        query_model=search_response.query_model,
        total_candidates=search_response.total_candidates,
        result_count=len(search_response.results),
        results=[
            UserRetrievalSearchResultResponse(
                similarity=item.similarity,
                source_id=item.source_id,
                source_type=item.source_type,
                source_ref=item.source_ref,
                source_title=item.source_title,
                source_locale=item.source_locale,
                document_id=item.document_id,
                document_kind=item.document_kind,
                document_title=item.document_title,
                document_version=item.document_version,
                chunk_id=item.chunk_id,
                chunk_index=item.chunk_index,
                content=item.content,
                token_estimate=item.token_estimate,
                chunk_metadata_json=item.chunk_metadata_json,
                embedding_provider=item.embedding_provider,
                embedding_model=item.embedding_model,
            )
            for item in search_response.results
        ],
    )


@router.post("/context", response_model=UserRetrievalContextResponse)
def build_user_retrieval_context(
    payload: UserRetrievalContextRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserRetrievalContextResponse:
    _require_authenticated_subscriber(repository, subscriber_id=user_session.subscriber_id)

    provider = payload.provider or DEFAULT_EMBEDDING_PROVIDER
    model = payload.model or DEFAULT_EMBEDDING_MODEL
    context_bundle = build_retrieval_context_bundle(
        repository,
        subscriber_id=user_session.subscriber_id,
        query_text=payload.query_text,
        embedding_provider=DeterministicEmbeddingProvider(provider=provider, model=model),
        search_top_k=payload.search_top_k,
        result_limit=payload.result_limit,
        minimum_similarity=payload.minimum_similarity,
        provider=provider,
        model=model,
        source_types=payload.source_types,
        document_kinds=payload.document_kinds,
        max_total_characters=payload.max_total_characters,
        max_total_tokens=payload.max_total_tokens,
        max_chars_per_item=payload.max_chars_per_item,
        merge_adjacent_chunks=payload.merge_adjacent_chunks,
        adjacent_window=payload.adjacent_window,
        diversify_sources=payload.diversify_sources,
    )

    return UserRetrievalContextResponse(
        query_text=context_bundle.query_text,
        query_provider=context_bundle.query_provider,
        query_model=context_bundle.query_model,
        total_search_results=context_bundle.total_search_results,
        total_items=context_bundle.total_items,
        total_characters=context_bundle.total_characters,
        total_token_estimate=context_bundle.total_token_estimate,
        truncated=context_bundle.truncated,
        items=[
            UserRetrievalContextItemResponse(
                source_id=item.source_id,
                source_type=item.source_type,
                source_ref=item.source_ref,
                source_title=item.source_title,
                source_locale=item.source_locale,
                document_id=item.document_id,
                document_kind=item.document_kind,
                document_title=item.document_title,
                document_version=item.document_version,
                similarity_max=item.similarity_max,
                similarity_average=item.similarity_average,
                merged_chunk_count=item.merged_chunk_count,
                references=[
                    UserRetrievalContextReferenceResponse(
                        chunk_id=reference.chunk_id,
                        chunk_index=reference.chunk_index,
                        similarity=reference.similarity,
                    )
                    for reference in item.references
                ],
                content=item.content,
                token_estimate=item.token_estimate,
                char_count=item.char_count,
                truncated=item.truncated,
            )
            for item in context_bundle.items
        ],
    )


def _require_authenticated_subscriber(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
) -> None:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )
