from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import RetrievalChunk, RetrievalEmbedding, RetrievalEmbeddingJob

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_PROVIDER = "deterministic"
DEFAULT_EMBEDDING_MODEL = "sha256-16d"
DEFAULT_EMBEDDING_DIMENSIONS = 16

EMBEDDING_JOB_STATUS_QUEUED = "queued"
EMBEDDING_JOB_STATUS_PROCESSING = "processing"
EMBEDDING_JOB_STATUS_COMPLETED = "completed"
EMBEDDING_JOB_STATUS_FAILED = "failed"

CHUNK_EMBEDDING_STATUS_PENDING = "pending"
CHUNK_EMBEDDING_STATUS_QUEUED = "queued"
CHUNK_EMBEDDING_STATUS_PROCESSING = "processing"
CHUNK_EMBEDDING_STATUS_READY = "ready"
CHUNK_EMBEDDING_STATUS_FAILED = "failed"

PROCESS_ACTION_PROCESSED = "processed"
PROCESS_ACTION_FAILED = "failed"
PROCESS_ACTION_IDLE = "idle"


@dataclass(slots=True, frozen=True)
class EmbeddingVectorResult:
    provider: str
    model: str
    vector: tuple[float, ...]
    dimensions: int
    vector_ref: str | None = None


@dataclass(slots=True, frozen=True)
class EmbeddingJobProcessResult:
    action: str
    job: RetrievalEmbeddingJob | None = None
    chunk: RetrievalChunk | None = None
    embedding: RetrievalEmbedding | None = None
    reason: str | None = None
    error_message: str | None = None


class EmbeddingProvider(Protocol):
    def embed_text(self, *, text: str) -> EmbeddingVectorResult:
        """Return a deterministic embedding vector for the supplied text."""


class DeterministicEmbeddingProvider:
    def __init__(
        self,
        *,
        provider: str = DEFAULT_EMBEDDING_PROVIDER,
        model: str = DEFAULT_EMBEDDING_MODEL,
        dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
    ) -> None:
        if dimensions < 1:
            raise ValueError("Embedding dimensions must be >= 1.")
        self.provider = provider
        self.model = model
        self.dimensions = dimensions

    def embed_text(self, *, text: str) -> EmbeddingVectorResult:
        vector = _build_deterministic_vector(text, dimensions=self.dimensions)
        return EmbeddingVectorResult(
            provider=self.provider,
            model=self.model,
            vector=vector,
            dimensions=self.dimensions,
            vector_ref=None,
        )



def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()



def _build_deterministic_vector(text: str, *, dimensions: int) -> tuple[float, ...]:
    if not text.strip():
        return tuple(0.0 for _ in range(dimensions))

    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        payload = f"{counter}:{text}".encode()
        digest = hashlib.sha256(payload).digest()
        for index in range(0, len(digest), 4):
            if len(values) >= dimensions:
                break
            chunk = digest[index : index + 4]
            integer = int.from_bytes(chunk, byteorder="big", signed=False)
            normalized = (integer / 0xFFFFFFFF) * 2.0 - 1.0
            values.append(normalized)
        counter += 1

    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return tuple(0.0 for _ in range(dimensions))
    return tuple(value / norm for value in values)



def enqueue_chunk_embedding_jobs(
    repository: HiringRadarRepository,
    *,
    chunks: list[RetrievalChunk],
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    created_at: str | None = None,
) -> list[RetrievalEmbeddingJob]:
    timestamp = created_at or utc_now_iso()
    jobs: list[RetrievalEmbeddingJob] = []
    for chunk in chunks:
        if chunk.id is None:
            raise RuntimeError("Cannot enqueue retrieval embedding job for chunk without id.")
        job = repository.enqueue_retrieval_embedding_job(
            chunk.id,
            provider=provider,
            model=model,
            created_at=timestamp,
        )
        jobs.append(job)
    return jobs



def enqueue_document_embedding_jobs(
    repository: HiringRadarRepository,
    *,
    document_id: int,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    created_at: str | None = None,
) -> list[RetrievalEmbeddingJob]:
    chunks = repository.list_retrieval_chunks(document_id)
    if not chunks:
        return []
    return enqueue_chunk_embedding_jobs(
        repository,
        chunks=chunks,
        provider=provider,
        model=model,
        created_at=created_at,
    )



def process_next_embedding_job(
    repository: HiringRadarRepository,
    *,
    embedding_provider: EmbeddingProvider,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    now: str | None = None,
) -> EmbeddingJobProcessResult:
    timestamp = now or utc_now_iso()
    job = repository.claim_next_retrieval_embedding_job(
        provider=provider,
        model=model,
        claimed_at=timestamp,
    )
    if job is None:
        return EmbeddingJobProcessResult(
            action=PROCESS_ACTION_IDLE,
            reason="no_queued_jobs",
        )

    chunk = repository.get_retrieval_chunk(job.chunk_id)
    if chunk is None or chunk.id is None:
        failed_job = repository.fail_retrieval_embedding_job(
            job.id or 0,
            error_message="Retrieval chunk not found for embedding job.",
            failed_at=timestamp,
        )
        return EmbeddingJobProcessResult(
            action=PROCESS_ACTION_FAILED,
            job=failed_job,
            reason="missing_chunk",
            error_message="Retrieval chunk not found for embedding job.",
        )

    try:
        vector_result = embedding_provider.embed_text(text=chunk.content)
        repository.delete_retrieval_embeddings_for_chunk(chunk.id)
        embedding = repository.create_retrieval_embedding(
            chunk.id,
            provider=vector_result.provider,
            model=vector_result.model,
            vector_ref=vector_result.vector_ref,
            vector_json=json.dumps(vector_result.vector),
            dimensions=vector_result.dimensions,
            created_at=timestamp,
        )
        repository.update_retrieval_chunk_embedding_status(
            chunk.id,
            embedding_status=CHUNK_EMBEDDING_STATUS_READY,
        )
        completed_job = repository.complete_retrieval_embedding_job(
            job.id or 0,
            completed_at=timestamp,
        )
        return EmbeddingJobProcessResult(
            action=PROCESS_ACTION_PROCESSED,
            job=completed_job,
            chunk=repository.get_retrieval_chunk(chunk.id),
            embedding=embedding,
        )
    except Exception as exc:
        failed_job = repository.fail_retrieval_embedding_job(
            job.id or 0,
            error_message=str(exc),
            failed_at=timestamp,
        )
        return EmbeddingJobProcessResult(
            action=PROCESS_ACTION_FAILED,
            job=failed_job,
            chunk=repository.get_retrieval_chunk(chunk.id),
            reason="provider_error",
            error_message=str(exc),
        )



def process_next_embedding_job_safe(
    repository: HiringRadarRepository,
    *,
    embedding_provider: EmbeddingProvider,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    now: str | None = None,
) -> EmbeddingJobProcessResult:
    try:
        return process_next_embedding_job(
            repository,
            embedding_provider=embedding_provider,
            provider=provider,
            model=model,
            now=now,
        )
    except Exception as exc:
        logger.exception("Retrieval embedding job processing failed unexpectedly.")
        return EmbeddingJobProcessResult(
            action=PROCESS_ACTION_FAILED,
            reason="unexpected_error",
            error_message=str(exc),
        )



def run_embedding_job_batch(
    repository: HiringRadarRepository,
    *,
    embedding_provider: EmbeddingProvider,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    limit: int = 1,
    now: str | None = None,
    stop_on_error: bool = False,
) -> list[EmbeddingJobProcessResult]:
    if limit < 1:
        raise ValueError("Embedding batch limit must be >= 1.")

    results: list[EmbeddingJobProcessResult] = []
    for _ in range(limit):
        result = process_next_embedding_job_safe(
            repository,
            embedding_provider=embedding_provider,
            provider=provider,
            model=model,
            now=now,
        )
        results.append(result)
        if result.action == PROCESS_ACTION_IDLE:
            break
        if stop_on_error and result.action == PROCESS_ACTION_FAILED:
            break
    return results
