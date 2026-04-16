from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParseReuseMode(str, Enum):
    """The degree of reuse that can be applied to a new parse request."""

    EXACT_HIT = "exact_hit"
    PARTIAL_REUSE = "partial_reuse"
    MISS = "miss"


class ParseCacheKey(BaseModel):
    """Stable cache identity for one parser/runtime/config combination."""

    model_config = ConfigDict(extra="forbid")

    namespace: str = "cv_engine"
    parser_version: str
    config_fingerprint: str
    content_sha256: str
    document_sha256: str | None = None

    def as_storage_key(self) -> str:
        """Return a compact string representation for storage backends."""
        document_part = self.document_sha256 or "no-document-hash"
        return ":".join(
            [
                self.namespace,
                self.parser_version,
                self.config_fingerprint,
                self.content_sha256,
                document_part,
            ]
        )


class SectionHash(BaseModel):
    """Stable digest for one logical section of a CV."""

    model_config = ConfigDict(extra="forbid")

    section_name: str
    sha256: str
    text_length: int = Field(default=0, ge=0)


class ParseCacheEntry(BaseModel):
    """Cached parser output with section-level reuse metadata."""

    model_config = ConfigDict(extra="forbid")

    key: ParseCacheKey
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat()
    )
    status: str = "succeeded"
    content_simhash: str | None = None
    person_fingerprint: str | None = None
    section_hashes: list[SectionHash] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def section_hash_map(self) -> dict[str, SectionHash]:
        """Return section hashes keyed by their logical section names."""
        return {item.section_name: item for item in self.section_hashes}


class IncrementalParsePlan(BaseModel):
    """Decision object describing how much cached state can be reused."""

    model_config = ConfigDict(extra="forbid")

    mode: ParseReuseMode
    reusable_section_names: list[str] = Field(default_factory=list)
    changed_section_names: list[str] = Field(default_factory=list)
    matched_entry_key: ParseCacheKey | None = None
    matched_similarity: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)
