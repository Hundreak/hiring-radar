from __future__ import annotations

from typing import Any

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import SubscriberCvUpload
from hiring_radar.services.cv_engine.ats.scoring import score_ats_compatibility
from hiring_radar.services.cv_engine.cache.incremental import plan_incremental_parse
from hiring_radar.services.cv_engine.cache.keys import (
    build_config_fingerprint,
    build_parse_cache_key,
    build_section_hashes,
)
from hiring_radar.services.cv_engine.compliance.audit import (
    extract_enterprise_metadata_from_parse_run_metadata_json,
)
from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.enterprise.fingerprints import build_document_fingerprints
from hiring_radar.services.cv_engine.enterprise.models import (
    DocumentFingerprints,
    DocumentRelationKind,
    VersionMatchResult,
)
from hiring_radar.services.cv_engine.enterprise.runtime import (
    FOUNDATION_PARSER_VERSION,
    get_parse_cache_store,
)
from hiring_radar.services.cv_engine.enterprise.versioning import resolve_document_relation
from hiring_radar.services.cv_engine.legacy_runtime import build_foundation_parser_result_from_text
from hiring_radar.services.cv_engine.models import ParserResult
from hiring_radar.services.cv_engine.redaction.engine import redact_cv_text
from hiring_radar.services.cv_extraction import CV_PARSE_STATUS_PARSED, normalize_extracted_text


def build_cv_enterprise_metadata(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload: SubscriberCvUpload,
) -> dict[str, Any] | None:
    """Build additive enterprise metadata for one persisted CV upload."""
    extracted_text = normalize_extracted_text(cv_upload.extracted_text)
    if cv_upload.parse_status != CV_PARSE_STATUS_PARSED or extracted_text is None:
        return None

    if cv_upload.id is not None:
        latest_parse_run = repository.get_latest_subscriber_cv_parse_run_for_upload(
            cv_upload.id
        )
        if latest_parse_run is not None:
            stored_metadata = extract_enterprise_metadata_from_parse_run_metadata_json(
                latest_parse_run.metadata_json
            )
            if stored_metadata is not None:
                return stored_metadata

    runtime_config = ParserRuntimeConfig()
    foundation_result = build_foundation_parser_result_from_text(
        extracted_text=extracted_text,
        filename=cv_upload.original_filename,
        used_ocr=bool(cv_upload.content_type and cv_upload.content_type.startswith("image/")),
        extraction_method="enterprise_api_metadata",
        page_count=1,
        config=runtime_config,
    )
    parsed_data = foundation_result.context.parsed_data
    if parsed_data is None:
        return None

    subscriber = repository.get_subscriber_by_id(subscriber_id)
    profile = repository.get_subscriber_profile(subscriber_id)
    fingerprints = build_document_fingerprints(
        text=extracted_text,
        full_name=parsed_data.full_name or (subscriber.full_name if subscriber else None),
        email=subscriber.email if subscriber is not None else None,
        phone=profile.phone if profile is not None else None,
        simhash_bits=runtime_config.document_versioning.simhash_bits,
    )
    cache_key, cache_status = _build_cache_metadata(
        result=foundation_result,
        fingerprints=fingerprints,
        config=runtime_config,
    )
    version_match = _resolve_repository_version_match(
        repository=repository,
        subscriber_id=subscriber_id,
        current_upload_id=cv_upload.id,
        incoming_fingerprints=fingerprints,
        config=runtime_config,
        subscriber_full_name=(parsed_data.full_name or (subscriber.full_name if subscriber else None)),
        subscriber_email=subscriber.email if subscriber is not None else None,
        subscriber_phone=profile.phone if profile is not None else None,
    )
    ats_report = score_ats_compatibility(
        parsed_data,
        sections=(
            foundation_result.context.sections.sections
            if foundation_result.context.sections is not None
            else []
        ),
        extraction=foundation_result.context.extraction,
        quality=foundation_result.context.quality,
        config=runtime_config.ats_scoring,
    )
    redaction_result = redact_cv_text(
        extracted_text,
        parsed_data=parsed_data,
        config=runtime_config.redaction,
    )

    return {
        "fingerprint": {
            "document_sha256": fingerprints.document_sha256,
            "content_sha256": fingerprints.content_sha256,
            "person_fingerprint_available": fingerprints.person_fingerprint is not None,
            "relation": _relation_name(version_match),
            "similarity": (
                None if version_match is None else version_match.similarity.similarity
            ),
            "reason_codes": [] if version_match is None else list(version_match.reason_codes),
        },
        "cache": {
            "cache_key": cache_key,
            "status": cache_status["status"],
            "exact_reusable": cache_status["exact_reusable"],
            "partial_reusable": cache_status["partial_reusable"],
            "reusable_section_names": list(cache_status["reusable_section_names"]),
            "changed_section_names": list(cache_status["changed_section_names"]),
            "reason_codes": list(cache_status["reason_codes"]),
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


def _build_cache_metadata(
    *,
    result: ParserResult,
    fingerprints: DocumentFingerprints,
    config: ParserRuntimeConfig,
) -> tuple[str, dict[str, Any]]:
    config_fingerprint = build_config_fingerprint(config)
    cache_key = build_parse_cache_key(
        parser_version=FOUNDATION_PARSER_VERSION,
        content_sha256=fingerprints.content_sha256,
        config_fingerprint=config_fingerprint,
        document_sha256=fingerprints.document_sha256,
        cache_config=config.parse_cache,
    )
    store = get_parse_cache_store()
    candidates = store.find_candidates(
        parser_version=FOUNDATION_PARSER_VERSION,
        config_fingerprint=config_fingerprint,
    )
    section_hashes = _build_section_hashes_from_result(result)
    plan = plan_incremental_parse(
        key=cache_key,
        incoming_fingerprints=fingerprints,
        incoming_section_hashes=section_hashes,
        candidates=candidates,
        cache_config=config.parse_cache,
        versioning_config=config.document_versioning,
    )
    return (
        cache_key.as_storage_key(),
        {
            "status": plan.mode.value,
            "exact_reusable": plan.mode.value == "exact_hit",
            "partial_reusable": plan.mode.value == "partial_reuse",
            "reusable_section_names": list(plan.reusable_section_names),
            "changed_section_names": list(plan.changed_section_names),
            "reason_codes": list(plan.reason_codes),
        },
    )


def _build_section_hashes_from_result(result: ParserResult) -> list[Any]:
    sections = result.context.sections.sections if result.context.sections is not None else []
    if sections:
        return build_section_hashes(
            [
                (section.name.value, "\n".join(line for line in section.lines if line.strip()))
                for section in sections
            ]
        )
    normalized_text = result.context.normalized.text if result.context.normalized is not None else ""
    return build_section_hashes({"document": normalized_text})


def _resolve_repository_version_match(
    *,
    repository: HiringRadarRepository,
    subscriber_id: int,
    current_upload_id: int | None,
    incoming_fingerprints: DocumentFingerprints,
    config: ParserRuntimeConfig,
    subscriber_full_name: str | None,
    subscriber_email: str | None,
    subscriber_phone: str | None,
) -> VersionMatchResult | None:
    uploads = repository.list_subscriber_cv_uploads(subscriber_id)
    best_match: VersionMatchResult | None = None
    best_rank = -1
    best_similarity = -1.0
    for upload in uploads:
        if upload.id == current_upload_id or not upload.extracted_text:
            continue
        normalized_text = normalize_extracted_text(upload.extracted_text)
        if normalized_text is None:
            continue
        existing = build_document_fingerprints(
            text=normalized_text,
            full_name=subscriber_full_name,
            email=subscriber_email,
            phone=subscriber_phone,
            simhash_bits=config.document_versioning.simhash_bits,
        )
        match = resolve_document_relation(
            existing=existing,
            incoming=incoming_fingerprints,
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


def _relation_name(match: VersionMatchResult | None) -> str:
    if match is None:
        return "first_observed"
    return match.relation.value
