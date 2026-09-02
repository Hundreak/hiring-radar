from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.retrieval.chunking import estimate_token_count
from hiring_radar.services.retrieval.embedding_jobs import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    EmbeddingProvider,
)
from hiring_radar.services.retrieval.search import (
    RetrievalSearchResponse,
    RetrievalSearchResult,
    search_retrieval_chunks,
)

DEFAULT_CONTEXT_SEARCH_TOP_K = 12
DEFAULT_CONTEXT_RESULT_LIMIT = 5
DEFAULT_CONTEXT_MAX_TOTAL_CHARACTERS = 4000
DEFAULT_CONTEXT_MAX_TOTAL_TOKENS = 800
DEFAULT_CONTEXT_MAX_CHARS_PER_ITEM = 1200
DEFAULT_CONTEXT_ADJACENT_WINDOW = 1
MIN_CONTEXT_ITEM_CHARACTERS = 32


@dataclass(slots=True, frozen=True)
class RetrievalContextReference:
    chunk_id: int
    chunk_index: int
    similarity: float


@dataclass(slots=True, frozen=True)
class RetrievalContextItem:
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
    references: tuple[RetrievalContextReference, ...]
    content: str
    token_estimate: int
    char_count: int
    truncated: bool


@dataclass(slots=True, frozen=True)
class RetrievalContextBundle:
    query_text: str
    query_provider: str
    query_model: str
    total_search_results: int
    total_items: int
    total_characters: int
    total_token_estimate: int
    truncated: bool
    items: tuple[RetrievalContextItem, ...]



def build_retrieval_context_bundle(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    query_text: str,
    embedding_provider: EmbeddingProvider,
    search_top_k: int = DEFAULT_CONTEXT_SEARCH_TOP_K,
    result_limit: int = DEFAULT_CONTEXT_RESULT_LIMIT,
    minimum_similarity: float | None = None,
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    model: str = DEFAULT_EMBEDDING_MODEL,
    source_types: Iterable[str] | None = None,
    document_kinds: Iterable[str] | None = None,
    max_total_characters: int = DEFAULT_CONTEXT_MAX_TOTAL_CHARACTERS,
    max_total_tokens: int = DEFAULT_CONTEXT_MAX_TOTAL_TOKENS,
    max_chars_per_item: int = DEFAULT_CONTEXT_MAX_CHARS_PER_ITEM,
    merge_adjacent_chunks: bool = True,
    adjacent_window: int = DEFAULT_CONTEXT_ADJACENT_WINDOW,
    diversify_sources: bool = True,
) -> RetrievalContextBundle:
    search_response = search_retrieval_chunks(
        repository,
        subscriber_id=subscriber_id,
        query_text=query_text,
        embedding_provider=embedding_provider,
        top_k=search_top_k,
        minimum_similarity=minimum_similarity,
        provider=provider,
        model=model,
        source_types=source_types,
        document_kinds=document_kinds,
    )
    return assemble_retrieval_context_bundle(
        search_response,
        result_limit=result_limit,
        max_total_characters=max_total_characters,
        max_total_tokens=max_total_tokens,
        max_chars_per_item=max_chars_per_item,
        merge_adjacent_chunks=merge_adjacent_chunks,
        adjacent_window=adjacent_window,
        diversify_sources=diversify_sources,
    )



def assemble_retrieval_context_bundle(
    search_response: RetrievalSearchResponse,
    *,
    result_limit: int = DEFAULT_CONTEXT_RESULT_LIMIT,
    max_total_characters: int = DEFAULT_CONTEXT_MAX_TOTAL_CHARACTERS,
    max_total_tokens: int = DEFAULT_CONTEXT_MAX_TOTAL_TOKENS,
    max_chars_per_item: int = DEFAULT_CONTEXT_MAX_CHARS_PER_ITEM,
    merge_adjacent_chunks: bool = True,
    adjacent_window: int = DEFAULT_CONTEXT_ADJACENT_WINDOW,
    diversify_sources: bool = True,
) -> RetrievalContextBundle:
    _validate_context_options(
        result_limit=result_limit,
        max_total_characters=max_total_characters,
        max_total_tokens=max_total_tokens,
        max_chars_per_item=max_chars_per_item,
        adjacent_window=adjacent_window,
    )

    if not search_response.results:
        return RetrievalContextBundle(
            query_text=search_response.query_text,
            query_provider=search_response.query_provider,
            query_model=search_response.query_model,
            total_search_results=0,
            total_items=0,
            total_characters=0,
            total_token_estimate=0,
            truncated=False,
            items=(),
        )

    candidates = _build_context_candidates(
        search_response.results,
        merge_adjacent_chunks=merge_adjacent_chunks,
        adjacent_window=adjacent_window,
    )
    candidates = _deduplicate_context_candidates(candidates)
    ordered_candidates = _order_context_candidates(candidates, diversify_sources=diversify_sources)

    selected: list[RetrievalContextItem] = []
    total_characters = 0
    total_tokens = 0
    truncated = False

    for candidate in ordered_candidates:
        if len(selected) >= result_limit:
            truncated = True
            break

        remaining_characters = max_total_characters - total_characters
        remaining_tokens = max_total_tokens - total_tokens
        fitted = _fit_context_candidate(
            candidate,
            max_characters=min(max_chars_per_item, remaining_characters),
            max_tokens=remaining_tokens,
        )
        if fitted is None:
            truncated = True
            continue

        selected.append(fitted)
        total_characters += fitted.char_count
        total_tokens += fitted.token_estimate
        if fitted.truncated:
            truncated = True

    if len(selected) < len(ordered_candidates):
        truncated = True

    return RetrievalContextBundle(
        query_text=search_response.query_text,
        query_provider=search_response.query_provider,
        query_model=search_response.query_model,
        total_search_results=len(search_response.results),
        total_items=len(selected),
        total_characters=total_characters,
        total_token_estimate=total_tokens,
        truncated=truncated,
        items=tuple(selected),
    )



def _validate_context_options(
    *,
    result_limit: int,
    max_total_characters: int,
    max_total_tokens: int,
    max_chars_per_item: int,
    adjacent_window: int,
) -> None:
    if result_limit < 1:
        raise ValueError("Retrieval context result_limit must be >= 1.")
    if max_total_characters < MIN_CONTEXT_ITEM_CHARACTERS:
        raise ValueError("Retrieval context max_total_characters is too small.")
    if max_total_tokens < 1:
        raise ValueError("Retrieval context max_total_tokens must be >= 1.")
    if max_chars_per_item < MIN_CONTEXT_ITEM_CHARACTERS:
        raise ValueError("Retrieval context max_chars_per_item is too small.")
    if adjacent_window < 0:
        raise ValueError("Retrieval context adjacent_window must be >= 0.")



def _build_context_candidates(
    results: tuple[RetrievalSearchResult, ...],
    *,
    merge_adjacent_chunks: bool,
    adjacent_window: int,
) -> list[RetrievalContextItem]:
    by_document: dict[int, list[RetrievalSearchResult]] = {}
    for result in results:
        by_document.setdefault(result.document_id, []).append(result)

    for document_results in by_document.values():
        document_results.sort(key=lambda item: item.chunk_index)

    consumed_chunk_ids: set[int] = set()
    candidates: list[RetrievalContextItem] = []

    for result in results:
        if result.chunk_id in consumed_chunk_ids:
            continue

        merged_results = [result]
        if merge_adjacent_chunks:
            merged_results = _collect_adjacent_results(
                result,
                by_document.get(result.document_id, []),
                consumed_chunk_ids=consumed_chunk_ids,
                adjacent_window=adjacent_window,
            )

        for merged in merged_results:
            consumed_chunk_ids.add(merged.chunk_id)
        candidates.append(_build_context_item(merged_results))

    return candidates



def _collect_adjacent_results(
    seed: RetrievalSearchResult,
    document_results: list[RetrievalSearchResult],
    *,
    consumed_chunk_ids: set[int],
    adjacent_window: int,
) -> list[RetrievalSearchResult]:
    if adjacent_window == 0:
        return [seed]

    position = next((index for index, item in enumerate(document_results) if item.chunk_id == seed.chunk_id), None)
    if position is None:
        return [seed]

    collected: list[RetrievalSearchResult] = [seed]
    left_index = position - 1
    while left_index >= 0:
        candidate = document_results[left_index]
        if candidate.chunk_id in consumed_chunk_ids:
            break
        nearest_index = collected[0].chunk_index
        if nearest_index - candidate.chunk_index > adjacent_window:
            break
        collected.insert(0, candidate)
        left_index -= 1

    right_index = position + 1
    while right_index < len(document_results):
        candidate = document_results[right_index]
        if candidate.chunk_id in consumed_chunk_ids:
            break
        nearest_index = collected[-1].chunk_index
        if candidate.chunk_index - nearest_index > adjacent_window:
            break
        collected.append(candidate)
        right_index += 1

    return collected



def _build_context_item(results: list[RetrievalSearchResult]) -> RetrievalContextItem:
    ordered_results = sorted(results, key=lambda item: item.chunk_index)
    merged_content = _merge_chunk_contents(item.content for item in ordered_results)
    similarities = [item.similarity for item in ordered_results]
    references = tuple(
        RetrievalContextReference(
            chunk_id=item.chunk_id,
            chunk_index=item.chunk_index,
            similarity=item.similarity,
        )
        for item in ordered_results
    )
    seed = ordered_results[0]
    return RetrievalContextItem(
        source_id=seed.source_id,
        source_type=seed.source_type,
        source_ref=seed.source_ref,
        source_title=seed.source_title,
        source_locale=seed.source_locale,
        document_id=seed.document_id,
        document_kind=seed.document_kind,
        document_title=seed.document_title,
        document_version=seed.document_version,
        similarity_max=max(similarities),
        similarity_average=sum(similarities) / len(similarities),
        merged_chunk_count=len(ordered_results),
        references=references,
        content=merged_content,
        token_estimate=estimate_token_count(merged_content),
        char_count=len(merged_content),
        truncated=False,
    )



def _merge_chunk_contents(contents: Iterable[str]) -> str:
    merged = ""
    for content in contents:
        normalized = content.strip()
        if not normalized:
            continue
        if not merged:
            merged = normalized
            continue
        merged = _merge_two_content_blocks(merged, normalized)
    return merged.strip()



def _merge_two_content_blocks(left: str, right: str) -> str:
    left_normalized = left.rstrip()
    right_normalized = right.lstrip()
    if not left_normalized:
        return right_normalized
    if not right_normalized:
        return left_normalized
    if _normalize_content_signature(left_normalized) == _normalize_content_signature(right_normalized):
        return left_normalized

    max_overlap = min(240, len(left_normalized), len(right_normalized))
    for overlap_length in range(max_overlap, 31, -1):
        if left_normalized.endswith(right_normalized[:overlap_length]):
            return left_normalized + right_normalized[overlap_length:]

    return f"{left_normalized}\n\n{right_normalized}"



def _normalize_content_signature(content: str) -> str:
    return " ".join(content.lower().split())



def _deduplicate_context_candidates(candidates: list[RetrievalContextItem]) -> list[RetrievalContextItem]:
    deduplicated: list[RetrievalContextItem] = []
    seen_signatures: set[str] = set()

    for candidate in sorted(candidates, key=lambda item: (-item.similarity_max, item.document_id, item.references[0].chunk_index)):
        signature = _normalize_content_signature(candidate.content)
        if not signature or signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        deduplicated.append(candidate)

    return deduplicated



def _order_context_candidates(
    candidates: list[RetrievalContextItem],
    *,
    diversify_sources: bool,
) -> list[RetrievalContextItem]:
    ordered = sorted(
        candidates,
        key=lambda item: (-item.similarity_max, item.source_id, item.document_id, item.references[0].chunk_index),
    )
    if not diversify_sources:
        return ordered

    diversified: list[RetrievalContextItem] = []
    deferred: list[RetrievalContextItem] = []
    seen_sources: set[int] = set()

    for candidate in ordered:
        if candidate.source_id not in seen_sources:
            diversified.append(candidate)
            seen_sources.add(candidate.source_id)
        else:
            deferred.append(candidate)

    diversified.extend(deferred)
    return diversified



def _fit_context_candidate(
    candidate: RetrievalContextItem,
    *,
    max_characters: int,
    max_tokens: int,
) -> RetrievalContextItem | None:
    if max_characters < MIN_CONTEXT_ITEM_CHARACTERS or max_tokens < 1:
        return None
    if candidate.char_count <= max_characters and candidate.token_estimate <= max_tokens:
        return candidate

    original_content = candidate.content
    trimmed_content = _trim_content(original_content, max_characters)
    trimmed_tokens = estimate_token_count(trimmed_content)

    while trimmed_content and trimmed_tokens > max_tokens:
        target_length = max(
            MIN_CONTEXT_ITEM_CHARACTERS,
            int(len(trimmed_content) * (max_tokens / max(trimmed_tokens, 1))),
        )
        if target_length >= len(trimmed_content):
            target_length = max(MIN_CONTEXT_ITEM_CHARACTERS, len(trimmed_content) - 16)
        if target_length < MIN_CONTEXT_ITEM_CHARACTERS:
            return None
        trimmed_content = _trim_content(trimmed_content, target_length)
        trimmed_tokens = estimate_token_count(trimmed_content)
        if len(trimmed_content) <= MIN_CONTEXT_ITEM_CHARACTERS and trimmed_tokens > max_tokens:
            return None

    if not trimmed_content:
        return None

    return replace(
        candidate,
        content=trimmed_content,
        token_estimate=trimmed_tokens,
        char_count=len(trimmed_content),
        truncated=trimmed_content != original_content,
    )



def _trim_content(content: str, max_characters: int) -> str:
    normalized = content.strip()
    if len(normalized) <= max_characters:
        return normalized
    if max_characters <= 1:
        return normalized[:max_characters]

    reserved = max(1, max_characters - 1)
    trimmed = normalized[:reserved].rstrip()
    if len(trimmed) < MIN_CONTEXT_ITEM_CHARACTERS - 1:
        return ""
    return f"{trimmed}…"
