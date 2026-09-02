from __future__ import annotations

from hiring_radar.services.cv_engine.cache.incremental import plan_incremental_parse
from hiring_radar.services.cv_engine.cache.keys import (
    build_config_fingerprint,
    build_parse_cache_key,
    build_section_hashes,
)
from hiring_radar.services.cv_engine.cache.models import ParseCacheEntry, ParseReuseMode
from hiring_radar.services.cv_engine.cache.store import InMemoryParseCacheStore
from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.enterprise.fingerprints import (
    build_document_fingerprints,
)

PARSER_VERSION = "cv-engine-v2"


def _build_entry(
    *,
    text: str,
    sections: dict[str, str],
    full_name: str,
    email: str,
) -> ParseCacheEntry:
    runtime_config = ParserRuntimeConfig()
    fingerprints = build_document_fingerprints(
        text=text,
        full_name=full_name,
        email=email,
        phone=None,
    )
    key = build_parse_cache_key(
        parser_version=PARSER_VERSION,
        content_sha256=fingerprints.content_sha256,
        document_sha256=fingerprints.document_sha256,
        config_fingerprint=build_config_fingerprint(runtime_config),
        cache_config=runtime_config.parse_cache,
    )
    return ParseCacheEntry(
        key=key,
        content_simhash=fingerprints.content_simhash,
        person_fingerprint=fingerprints.person_fingerprint,
        section_hashes=build_section_hashes(sections),
        payload={"summary": "cached-result"},
    )


def test_in_memory_parse_cache_store_exact_hit() -> None:
    store = InMemoryParseCacheStore()
    entry = _build_entry(
        text="Alice Example\nBackend Engineer\nPython FastAPI",
        sections={"summary": "Backend engineer", "skills": "Python FastAPI"},
        full_name="Alice Example",
        email="alice@example.com",
    )
    store.put(entry)

    assert store.get(entry.key) == entry


def test_plan_incremental_parse_returns_exact_hit_for_same_key() -> None:
    runtime_config = ParserRuntimeConfig()
    store = InMemoryParseCacheStore()
    entry = _build_entry(
        text="Alice Example\nBackend Engineer\nPython FastAPI",
        sections={"summary": "Backend engineer", "skills": "Python FastAPI"},
        full_name="Alice Example",
        email="alice@example.com",
    )
    store.put(entry)
    fingerprints = build_document_fingerprints(
        text="Alice Example\nBackend Engineer\nPython FastAPI",
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )

    plan = plan_incremental_parse(
        key=entry.key,
        incoming_fingerprints=fingerprints,
        incoming_section_hashes=entry.section_hashes,
        candidates=list(store.iter_entries()),
        cache_config=runtime_config.parse_cache,
        versioning_config=runtime_config.document_versioning,
    )

    assert plan.mode == ParseReuseMode.EXACT_HIT
    assert plan.reusable_section_names == ["summary", "skills"]


def test_plan_incremental_parse_returns_partial_reuse_when_only_one_section_changes() -> None:
    runtime_config = ParserRuntimeConfig()
    store = InMemoryParseCacheStore()
    cached_entry = _build_entry(
        text=(
            "Alice Example\nBackend Engineer\nSummary: Reliable backend engineer\n"
            "Skills: Python FastAPI PostgreSQL"
        ),
        sections={
            "summary": "Reliable backend engineer",
            "skills": "Python FastAPI PostgreSQL",
        },
        full_name="Alice Example",
        email="alice@example.com",
    )
    store.put(cached_entry)

    incoming_text = (
        "Alice Example\nSenior Backend Engineer\nSummary: Reliable backend engineer\n"
        "Skills: Python FastAPI PostgreSQL Docker"
    )
    incoming_fingerprints = build_document_fingerprints(
        text=incoming_text,
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )
    incoming_sections = build_section_hashes(
        {
            "summary": "Reliable backend engineer",
            "skills": "Python FastAPI PostgreSQL Docker",
        }
    )
    incoming_key = build_parse_cache_key(
        parser_version=PARSER_VERSION,
        content_sha256=incoming_fingerprints.content_sha256,
        document_sha256=incoming_fingerprints.document_sha256,
        config_fingerprint=build_config_fingerprint(runtime_config),
        cache_config=runtime_config.parse_cache,
    )

    plan = plan_incremental_parse(
        key=incoming_key,
        incoming_fingerprints=incoming_fingerprints,
        incoming_section_hashes=incoming_sections,
        candidates=list(store.iter_entries()),
        cache_config=runtime_config.parse_cache,
        versioning_config=runtime_config.document_versioning,
    )

    assert plan.mode == ParseReuseMode.PARTIAL_REUSE
    assert plan.reusable_section_names == ["summary"]
    assert plan.changed_section_names == ["skills"]


def test_plan_incremental_parse_returns_miss_for_unrelated_candidate() -> None:
    runtime_config = ParserRuntimeConfig()
    store = InMemoryParseCacheStore()
    store.put(
        _build_entry(
            text="Bob Example\nGraphic Designer\nFigma Illustrator Photoshop",
            sections={"summary": "Designer", "skills": "Figma Illustrator"},
            full_name="Bob Example",
            email="bob@example.com",
        )
    )
    incoming_text = "Alice Example\nBackend Engineer\nPython FastAPI"
    incoming_fingerprints = build_document_fingerprints(
        text=incoming_text,
        full_name="Alice Example",
        email="alice@example.com",
        phone=None,
    )
    incoming_key = build_parse_cache_key(
        parser_version=PARSER_VERSION,
        content_sha256=incoming_fingerprints.content_sha256,
        document_sha256=incoming_fingerprints.document_sha256,
        config_fingerprint=build_config_fingerprint(runtime_config),
        cache_config=runtime_config.parse_cache,
    )
    incoming_sections = build_section_hashes(
        {"summary": "Backend Engineer", "skills": "Python FastAPI"}
    )

    plan = plan_incremental_parse(
        key=incoming_key,
        incoming_fingerprints=incoming_fingerprints,
        incoming_section_hashes=incoming_sections,
        candidates=list(store.iter_entries()),
        cache_config=runtime_config.parse_cache,
        versioning_config=runtime_config.document_versioning,
    )

    assert plan.mode == ParseReuseMode.MISS
