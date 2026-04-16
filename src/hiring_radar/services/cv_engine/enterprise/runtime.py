from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from hiring_radar.services.cv_engine.ats.scoring import score_ats_compatibility
from hiring_radar.services.cv_engine.cache.incremental import plan_incremental_parse
from hiring_radar.services.cv_engine.cache.keys import (
    build_config_fingerprint,
    build_parse_cache_key,
    build_section_hashes,
)
from hiring_radar.services.cv_engine.cache.models import ParseCacheEntry, ParseReuseMode
from hiring_radar.services.cv_engine.cache.store import InMemoryParseCacheStore
from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.enterprise.fingerprints import build_document_fingerprints
from hiring_radar.services.cv_engine.enterprise.models import (
    DocumentFingerprints,
    DocumentRelationKind,
    VersionMatchResult,
)
from hiring_radar.services.cv_engine.enterprise.versioning import resolve_document_relation
from hiring_radar.services.cv_engine.models import ParseContext, ParserResult, SectionBlock
from hiring_radar.services.cv_engine.redaction.engine import redact_cv_text

FOUNDATION_PARSER_VERSION = "cv_engine_v2"
_PARSE_CACHE_STORE = InMemoryParseCacheStore()


def get_parse_cache_store() -> InMemoryParseCacheStore:
    """Return the singleton in-memory cache used by the foundation runtime."""
    return _PARSE_CACHE_STORE


def build_cache_key_for_text(
    *,
    extracted_text: str,
    config: ParserRuntimeConfig,
) -> tuple[str, str, Any]:
    """Build cache identity values for a normalized text payload."""
    fingerprints = build_document_fingerprints(
        text=extracted_text,
        simhash_bits=config.document_versioning.simhash_bits,
    )
    config_fingerprint = build_config_fingerprint(config)
    cache_key = build_parse_cache_key(
        parser_version=FOUNDATION_PARSER_VERSION,
        content_sha256=fingerprints.content_sha256,
        config_fingerprint=config_fingerprint,
        document_sha256=fingerprints.document_sha256,
        cache_config=config.parse_cache,
    )
    return fingerprints.content_sha256, config_fingerprint, cache_key


def get_cached_parser_result_for_text(
    *,
    extracted_text: str,
    config: ParserRuntimeConfig,
) -> ParserResult | None:
    """Return a cached parser result for an exact text/config match, if available."""
    if not config.parse_cache.enabled:
        return None

    _, _, cache_key = build_cache_key_for_text(
        extracted_text=extracted_text,
        config=config,
    )
    entry = _PARSE_CACHE_STORE.get(cache_key)
    if entry is None:
        return None

    payload = entry.payload.get("parser_result")
    if not isinstance(payload, dict):
        return None

    result = ParserResult.model_validate(payload)
    enterprise_metadata = dict(result.context.metadata.get("enterprise", {}))
    enterprise_metadata["cache"] = {
        **dict(enterprise_metadata.get("cache", {})),
        "cache_key": cache_key.as_storage_key(),
        "status": ParseReuseMode.EXACT_HIT.value,
        "exact_reusable": True,
        "partial_reusable": False,
        "reusable_section_names": list(
            dict(enterprise_metadata.get("cache", {})).get(
                "reusable_section_names",
                [],
            )
        ),
        "changed_section_names": [],
    }
    result.context.metadata["enterprise"] = enterprise_metadata
    return result


def enrich_and_store_parser_result(
    *,
    result: ParserResult,
    extracted_text: str,
    config: ParserRuntimeConfig,
) -> ParserResult:
    """Attach enterprise metadata to a parser result and store it in cache."""
    fingerprints = _build_runtime_fingerprints(
        extracted_text=extracted_text,
        result=result,
        config=config,
    )
    config_fingerprint = build_config_fingerprint(config)
    cache_key = build_parse_cache_key(
        parser_version=FOUNDATION_PARSER_VERSION,
        content_sha256=fingerprints.content_sha256,
        config_fingerprint=config_fingerprint,
        document_sha256=fingerprints.document_sha256,
        cache_config=config.parse_cache,
    )
    candidates = _PARSE_CACHE_STORE.find_candidates(
        parser_version=FOUNDATION_PARSER_VERSION,
        config_fingerprint=config_fingerprint,
    )
    section_hashes = _build_section_hashes_from_context(result.context)
    incremental_plan = plan_incremental_parse(
        key=cache_key,
        incoming_fingerprints=fingerprints,
        incoming_section_hashes=section_hashes,
        candidates=candidates,
        cache_config=config.parse_cache,
        versioning_config=config.document_versioning,
    )
    version_match = _resolve_best_version_match(
        fingerprints=fingerprints,
        candidates=candidates,
        config=config,
    )
    ats_report = score_ats_compatibility(
        result.context.parsed_data,
        sections=(
            result.context.sections.sections if result.context.sections is not None else []
        ),
        extraction=result.context.extraction,
        quality=result.context.quality,
        config=config.ats_scoring,
    )
    redaction_result = redact_cv_text(
        extracted_text,
        parsed_data=result.context.parsed_data,
        config=config.redaction,
    )
    enterprise_metadata = {
        "fingerprints": fingerprints.model_dump(mode="json"),
        "versioning": _serialize_version_match(version_match),
        "cache": {
            "cache_key": cache_key.as_storage_key(),
            "status": (
                incremental_plan.mode.value
                if config.parse_cache.enabled
                else "disabled"
            ),
            "exact_reusable": incremental_plan.mode == ParseReuseMode.EXACT_HIT,
            "partial_reusable": (
                incremental_plan.mode == ParseReuseMode.PARTIAL_REUSE
            ),
            "reusable_section_names": list(incremental_plan.reusable_section_names),
            "changed_section_names": list(incremental_plan.changed_section_names),
            "reason_codes": list(incremental_plan.reason_codes),
        },
        "ats": {
            "score": ats_report.score,
            "level": ats_report.level.value,
            "issue_codes": [item.code for item in ats_report.issues],
            "recommendations": list(ats_report.recommendations),
        },
        "redaction": {
            "available": True,
            "pii_findings_count": len(redaction_result.findings),
            "pii_types": sorted({item.pii_type.value for item in redaction_result.findings}),
            "warnings": list(redaction_result.warnings),
        },
    }
    result.context.metadata["enterprise"] = enterprise_metadata

    if config.parse_cache.enabled:
        _PARSE_CACHE_STORE.put(
            ParseCacheEntry(
                key=cache_key,
                content_simhash=fingerprints.content_simhash,
                person_fingerprint=fingerprints.person_fingerprint,
                section_hashes=section_hashes,
                payload={
                    "parser_result": result.model_dump(mode="json"),
                },
                metadata={
                    "cache_status": incremental_plan.mode.value,
                    "version_relation": enterprise_metadata["versioning"]["relation"],
                },
            )
        )

    return result


def _build_runtime_fingerprints(
    *,
    extracted_text: str,
    result: ParserResult,
    config: ParserRuntimeConfig,
) -> DocumentFingerprints:
    parsed_data = result.context.parsed_data
    full_name = parsed_data.full_name if parsed_data is not None else None
    email = parsed_data.emails[0] if parsed_data is not None and parsed_data.emails else None
    phone = (
        parsed_data.phone_numbers[0]
        if parsed_data is not None and parsed_data.phone_numbers
        else None
    )
    return build_document_fingerprints(
        text=extracted_text,
        full_name=full_name,
        email=email,
        phone=phone,
        simhash_bits=config.document_versioning.simhash_bits,
    )


def _build_section_hashes_from_context(context: ParseContext) -> list[Any]:
    sections = context.sections.sections if context.sections is not None else []
    if sections:
        return build_section_hashes(
            [
                (section.name.value, "\n".join(line for line in section.lines if line.strip()))
                for section in sections
            ]
        )
    normalized_text = context.normalized.text if context.normalized is not None else ""
    return build_section_hashes({"document": normalized_text})


def _resolve_best_version_match(
    *,
    fingerprints: DocumentFingerprints,
    candidates: Sequence[ParseCacheEntry],
    config: ParserRuntimeConfig,
) -> VersionMatchResult | None:
    best_match: VersionMatchResult | None = None
    best_rank = -1
    best_similarity = -1.0
    for candidate in candidates:
        if candidate.content_simhash is None:
            continue
        existing = DocumentFingerprints(
            document_sha256=candidate.key.document_sha256,
            content_sha256=candidate.key.content_sha256,
            content_simhash=candidate.content_simhash,
            normalized_character_count=0,
            normalized_token_count=0,
            person_fingerprint=candidate.person_fingerprint,
        )
        match = resolve_document_relation(
            existing=existing,
            incoming=fingerprints,
            config=config.document_versioning,
        )
        rank = _relation_rank(match.relation)
        similarity = match.similarity.similarity
        if rank > best_rank or (rank == best_rank and similarity > best_similarity):
            best_match = match
            best_rank = rank
            best_similarity = similarity
    return best_match


def _relation_rank(relation: DocumentRelationKind) -> int:
    if relation == DocumentRelationKind.EXACT_DUPLICATE:
        return 4
    if relation == DocumentRelationKind.UPDATED_VERSION:
        return 3
    if relation == DocumentRelationKind.RELATED_VARIANT:
        return 2
    return 1


def _serialize_version_match(match: VersionMatchResult | None) -> dict[str, Any]:
    if match is None:
        return {
            "relation": "first_observed",
            "similarity": None,
            "same_person": False,
            "reason_codes": [],
        }
    return {
        "relation": match.relation.value,
        "similarity": match.similarity.similarity,
        "same_person": match.same_person,
        "reason_codes": list(match.reason_codes),
    }
