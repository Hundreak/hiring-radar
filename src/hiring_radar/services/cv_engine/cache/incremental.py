from __future__ import annotations

from collections.abc import Sequence

from hiring_radar.services.cv_engine.cache.models import (
    IncrementalParsePlan,
    ParseCacheEntry,
    ParseCacheKey,
    ParseReuseMode,
    SectionHash,
)
from hiring_radar.services.cv_engine.config import (
    DocumentVersioningConfig,
    ParseCacheConfig,
)
from hiring_radar.services.cv_engine.enterprise.models import DocumentFingerprints
from hiring_radar.services.cv_engine.enterprise.versioning import resolve_document_relation


def plan_incremental_parse(
    *,
    key: ParseCacheKey,
    incoming_fingerprints: DocumentFingerprints,
    incoming_section_hashes: Sequence[SectionHash],
    candidates: Sequence[ParseCacheEntry],
    cache_config: ParseCacheConfig | None = None,
    versioning_config: DocumentVersioningConfig | None = None,
) -> IncrementalParsePlan:
    """Return a cache reuse plan for an incoming parse request."""
    runtime_cache_config = cache_config or ParseCacheConfig()
    runtime_versioning_config = versioning_config or DocumentVersioningConfig()

    for candidate in candidates:
        if candidate.key.as_storage_key() != key.as_storage_key():
            continue
        return IncrementalParsePlan(
            mode=ParseReuseMode.EXACT_HIT,
            reusable_section_names=[item.section_name for item in incoming_section_hashes],
            changed_section_names=[],
            matched_entry_key=candidate.key,
            matched_similarity=1.0,
            reason_codes=["exact_cache_key_match"],
        )

    best_candidate: ParseCacheEntry | None = None
    best_similarity = -1.0
    best_reason_codes: list[str] = []
    incoming_section_map = {item.section_name: item for item in incoming_section_hashes}

    for candidate in candidates[: runtime_cache_config.max_candidates_per_lookup]:
        if candidate.content_simhash is None:
            continue
        candidate_fingerprints = DocumentFingerprints(
            document_sha256=candidate.key.document_sha256,
            content_sha256=candidate.key.content_sha256,
            content_simhash=candidate.content_simhash,
            normalized_character_count=0,
            normalized_token_count=0,
            person_fingerprint=candidate.person_fingerprint,
        )
        relation = resolve_document_relation(
            existing=candidate_fingerprints,
            incoming=incoming_fingerprints,
            config=runtime_versioning_config,
        )
        if runtime_cache_config.prefer_same_person_candidates:
            if incoming_fingerprints.person_fingerprint and not relation.same_person:
                continue
        if relation.similarity.similarity > best_similarity:
            best_candidate = candidate
            best_similarity = relation.similarity.similarity
            best_reason_codes = list(relation.reason_codes)

    if best_candidate is None:
        return IncrementalParsePlan(
            mode=ParseReuseMode.MISS,
            reason_codes=["no_compatible_cache_candidate"],
        )

    if best_similarity < runtime_cache_config.minimum_similarity_for_partial_reuse:
        return IncrementalParsePlan(
            mode=ParseReuseMode.MISS,
            matched_entry_key=best_candidate.key,
            matched_similarity=best_similarity,
            reason_codes=best_reason_codes or ["candidate_similarity_below_threshold"],
        )

    candidate_section_map = best_candidate.section_hash_map()
    reusable: list[str] = []
    changed: list[str] = []
    for section_name, section_hash in incoming_section_map.items():
        cached_section = candidate_section_map.get(section_name)
        if cached_section is not None and cached_section.sha256 == section_hash.sha256:
            reusable.append(section_name)
        else:
            changed.append(section_name)

    if reusable and not changed:
        return IncrementalParsePlan(
            mode=ParseReuseMode.EXACT_HIT,
            reusable_section_names=reusable,
            changed_section_names=[],
            matched_entry_key=best_candidate.key,
            matched_similarity=best_similarity,
            reason_codes=best_reason_codes + ["all_section_hashes_match"],
        )

    if reusable and runtime_cache_config.allow_section_level_reuse:
        return IncrementalParsePlan(
            mode=ParseReuseMode.PARTIAL_REUSE,
            reusable_section_names=reusable,
            changed_section_names=changed,
            matched_entry_key=best_candidate.key,
            matched_similarity=best_similarity,
            reason_codes=best_reason_codes + ["section_level_reuse"],
        )

    return IncrementalParsePlan(
        mode=ParseReuseMode.MISS,
        matched_entry_key=best_candidate.key,
        matched_similarity=best_similarity,
        reason_codes=best_reason_codes or ["no_reusable_sections"],
    )
