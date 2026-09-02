from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DocumentRelationKind(StrEnum):
    """Relationship classification between two CV documents."""

    EXACT_DUPLICATE = "exact_duplicate"
    UPDATED_VERSION = "updated_version"
    RELATED_VARIANT = "related_variant"
    UNRELATED = "unrelated"


class SimilarityResult(BaseModel):
    """Content similarity details derived from normalized fingerprints."""

    model_config = ConfigDict(extra="forbid")

    similarity: float = Field(ge=0.0, le=1.0)
    hamming_distance: int = Field(ge=0)
    bit_count: int = Field(default=64, ge=1)
    exact_text_match: bool = False


class DocumentFingerprints(BaseModel):
    """Stable document identity signals used by enterprise features."""

    model_config = ConfigDict(extra="forbid")

    document_sha256: str | None = None
    content_sha256: str
    content_simhash: str
    normalized_character_count: int = Field(default=0, ge=0)
    normalized_token_count: int = Field(default=0, ge=0)
    person_fingerprint: str | None = None
    normalized_text_preview: str | None = None


class VersionMatchResult(BaseModel):
    """Final duplicate/versioning decision for two CV documents."""

    model_config = ConfigDict(extra="forbid")

    relation: DocumentRelationKind
    similarity: SimilarityResult
    confidence: float = Field(ge=0.0, le=1.0)
    same_person: bool = False
    reason_codes: list[str] = Field(default_factory=list)
