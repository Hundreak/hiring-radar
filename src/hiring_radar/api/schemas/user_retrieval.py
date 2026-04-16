from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserRetrievalSearchRequest(BaseModel):
    query_text: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=25)
    minimum_similarity: float | None = Field(default=None, ge=-1.0, le=1.0)
    provider: str | None = Field(default=None, min_length=1, max_length=200)
    model: str | None = Field(default=None, min_length=1, max_length=200)
    source_types: list[str] | None = None
    document_kinds: list[str] | None = None


class UserRetrievalSearchResultResponse(BaseModel):
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
    chunk_metadata_json: dict[str, Any]
    embedding_provider: str
    embedding_model: str


class UserRetrievalSearchResponse(BaseModel):
    query_text: str
    query_provider: str
    query_model: str
    total_candidates: int
    result_count: int
    results: list[UserRetrievalSearchResultResponse]


class UserRetrievalContextRequest(BaseModel):
    query_text: str = Field(min_length=1, max_length=4000)
    search_top_k: int = Field(default=12, ge=1, le=50)
    result_limit: int = Field(default=5, ge=1, le=20)
    minimum_similarity: float | None = Field(default=None, ge=-1.0, le=1.0)
    provider: str | None = Field(default=None, min_length=1, max_length=200)
    model: str | None = Field(default=None, min_length=1, max_length=200)
    source_types: list[str] | None = None
    document_kinds: list[str] | None = None
    max_total_characters: int = Field(default=4000, ge=32, le=20000)
    max_total_tokens: int = Field(default=800, ge=1, le=8000)
    max_chars_per_item: int = Field(default=1200, ge=32, le=8000)
    merge_adjacent_chunks: bool = True
    adjacent_window: int = Field(default=1, ge=0, le=10)
    diversify_sources: bool = True


class UserRetrievalContextReferenceResponse(BaseModel):
    chunk_id: int
    chunk_index: int
    similarity: float


class UserRetrievalContextItemResponse(BaseModel):
    source_id: int
    source_type: str
    source_ref: str
    source_title: str | None
    source_locale: str | None
    document_id: int
    document_kind: str
    document_title: str | None
    document_version: int
    similarity_max: float
    similarity_average: float
    merged_chunk_count: int
    references: list[UserRetrievalContextReferenceResponse]
    content: str
    token_estimate: int
    char_count: int
    truncated: bool


class UserRetrievalContextResponse(BaseModel):
    query_text: str
    query_provider: str
    query_model: str
    total_search_results: int
    total_items: int
    total_characters: int
    total_token_estimate: int
    truncated: bool
    items: list[UserRetrievalContextItemResponse]
