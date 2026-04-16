from __future__ import annotations

from hiring_radar.services.cv_engine.enterprise.fingerprints import (
    build_document_fingerprints,
    compute_content_sha256,
    compute_document_sha256,
    compute_person_fingerprint,
    compute_simhash,
    normalize_text_for_content_fingerprint,
)
from hiring_radar.services.cv_engine.enterprise.models import (
    DocumentFingerprints,
    DocumentRelationKind,
    SimilarityResult,
    VersionMatchResult,
)
from hiring_radar.services.cv_engine.enterprise.versioning import (
    resolve_document_relation,
)

__all__ = [
    "FOUNDATION_PARSER_VERSION",
    "enrich_and_store_parser_result",
    "get_cached_parser_result_for_text",
    "get_parse_cache_store",
    "DocumentFingerprints",
    "DocumentRelationKind",
    "SimilarityResult",
    "VersionMatchResult",
    "build_document_fingerprints",
    "compute_content_sha256",
    "compute_document_sha256",
    "compute_person_fingerprint",
    "compute_simhash",
    "normalize_text_for_content_fingerprint",
    "resolve_document_relation",
]

from hiring_radar.services.cv_engine.enterprise.runtime import (
    FOUNDATION_PARSER_VERSION,
    enrich_and_store_parser_result,
    get_cached_parser_result_for_text,
    get_parse_cache_store,
)
