from __future__ import annotations

from collections.abc import Iterable

from hiring_radar.services.cv_engine.cache.models import ParseCacheEntry, ParseCacheKey


class InMemoryParseCacheStore:
    """Simple in-memory cache store for deterministic parser reuse tests."""

    def __init__(self) -> None:
        self._entries: dict[str, ParseCacheEntry] = {}

    def get(self, key: ParseCacheKey) -> ParseCacheEntry | None:
        """Return a cache entry by its exact storage key."""
        return self._entries.get(key.as_storage_key())

    def put(self, entry: ParseCacheEntry) -> None:
        """Persist or overwrite a cache entry."""
        self._entries[entry.key.as_storage_key()] = entry

    def delete(self, key: ParseCacheKey) -> None:
        """Delete a cache entry if it exists."""
        self._entries.pop(key.as_storage_key(), None)

    def clear(self) -> None:
        """Remove all cached entries."""
        self._entries.clear()

    def iter_entries(self) -> Iterable[ParseCacheEntry]:
        """Return an iterable view over all cached entries."""
        return self._entries.values()

    def find_candidates(
        self,
        *,
        parser_version: str,
        config_fingerprint: str,
    ) -> list[ParseCacheEntry]:
        """Return entries that match the same parser/runtime identity."""
        return [
            entry
            for entry in self._entries.values()
            if entry.key.parser_version == parser_version
            and entry.key.config_fingerprint == config_fingerprint
        ]
