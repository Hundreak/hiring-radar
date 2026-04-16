from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from hiring_radar.services.cv_engine.cache.models import ParseCacheKey, SectionHash
from hiring_radar.services.cv_engine.config import ParseCacheConfig
from hiring_radar.services.cv_engine.enterprise.fingerprints import (
    compute_content_sha256,
    normalize_text_for_content_fingerprint,
)


JSONDict = Mapping[str, Any]


def build_config_fingerprint(config: BaseModel | JSONDict[str, Any]) -> str:
    """Return a stable digest for a parser runtime configuration."""
    if isinstance(config, BaseModel):
        payload = config.model_dump(mode="json")
    else:
        payload = dict(config)
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_parse_cache_key(
    *,
    parser_version: str,
    content_sha256: str,
    config_fingerprint: str,
    document_sha256: str | None = None,
    cache_config: ParseCacheConfig | None = None,
) -> ParseCacheKey:
    """Build a stable parse cache key for one parser invocation."""
    resolved_cache_config = cache_config or ParseCacheConfig()
    return ParseCacheKey(
        namespace=resolved_cache_config.namespace,
        parser_version=parser_version,
        config_fingerprint=config_fingerprint,
        content_sha256=content_sha256,
        document_sha256=document_sha256,
    )


def build_section_hashes(
    sections: Mapping[str, str] | Sequence[tuple[str, str]],
) -> list[SectionHash]:
    """Return deterministic section hashes for incremental parsing."""
    if isinstance(sections, Mapping):
        items = list(sections.items())
    else:
        items = list(sections)
    hashes: list[SectionHash] = []
    for section_name, section_text in items:
        normalized_text = normalize_text_for_content_fingerprint(section_text)
        hashes.append(
            SectionHash(
                section_name=section_name,
                sha256=compute_content_sha256(normalized_text),
                text_length=len(normalized_text),
            )
        )
    return hashes
