from __future__ import annotations

from hiring_radar.services.cv_engine.config import DocumentVersioningConfig
from hiring_radar.services.cv_engine.enterprise.models import (
    DocumentFingerprints,
    DocumentRelationKind,
    SimilarityResult,
    VersionMatchResult,
)
from hiring_radar.services.cv_engine.enterprise.similarity import (
    compare_content_fingerprints,
)


def resolve_document_relation(
    *,
    existing: DocumentFingerprints,
    incoming: DocumentFingerprints,
    config: DocumentVersioningConfig | None = None,
) -> VersionMatchResult:
    """Classify whether an incoming CV is a duplicate or a newer version."""
    runtime_config = config or DocumentVersioningConfig()
    exact_binary_match = (
        existing.document_sha256 is not None
        and incoming.document_sha256 is not None
        and existing.document_sha256 == incoming.document_sha256
    )
    exact_text_match = existing.content_sha256 == incoming.content_sha256
    similarity = compare_content_fingerprints(
        left_simhash=existing.content_simhash,
        right_simhash=incoming.content_simhash,
        bit_count=runtime_config.simhash_bits,
        exact_text_match=exact_text_match,
    )
    same_person = (
        existing.person_fingerprint is not None
        and existing.person_fingerprint == incoming.person_fingerprint
    )

    reason_codes: list[str] = []
    if exact_binary_match:
        reason_codes.append("same_binary_hash")
    if exact_text_match:
        reason_codes.append("same_content_hash")
    if same_person:
        reason_codes.append("same_person_fingerprint")
    if similarity.similarity >= runtime_config.updated_version_similarity_threshold:
        reason_codes.append("high_content_similarity")
    elif similarity.similarity >= runtime_config.related_variant_similarity_threshold:
        reason_codes.append("related_content_similarity")

    if exact_binary_match or similarity.similarity >= runtime_config.exact_duplicate_similarity_threshold:
        return VersionMatchResult(
            relation=DocumentRelationKind.EXACT_DUPLICATE,
            similarity=similarity,
            confidence=_derive_confidence(similarity, same_person, 0.98),
            same_person=same_person,
            reason_codes=reason_codes,
        )

    if same_person and similarity.similarity >= runtime_config.updated_version_similarity_threshold:
        return VersionMatchResult(
            relation=DocumentRelationKind.UPDATED_VERSION,
            similarity=similarity,
            confidence=_derive_confidence(similarity, same_person, 0.9),
            same_person=same_person,
            reason_codes=reason_codes,
        )

    if similarity.similarity >= runtime_config.related_variant_similarity_threshold:
        return VersionMatchResult(
            relation=DocumentRelationKind.RELATED_VARIANT,
            similarity=similarity,
            confidence=_derive_confidence(similarity, same_person, 0.72),
            same_person=same_person,
            reason_codes=reason_codes,
        )

    return VersionMatchResult(
        relation=DocumentRelationKind.UNRELATED,
        similarity=similarity,
        confidence=_derive_confidence(similarity, same_person, 0.28),
        same_person=same_person,
        reason_codes=reason_codes or ["low_content_similarity"],
    )


def _derive_confidence(
    similarity: SimilarityResult,
    same_person: bool,
    ceiling: float,
) -> float:
    base = min(similarity.similarity, ceiling)
    if same_person:
        base += 0.08
    if similarity.exact_text_match:
        base += 0.04
    return max(0.0, min(1.0, base))
