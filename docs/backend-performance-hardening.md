# Backend Request / Query Performance Hardening

Patch 21 adds a small backend performance foundation without changing product behavior.

## What changed

- SQLite runtime pragmas are centralized in `hiring_radar.db.performance.configure_sqlite_runtime`.
- File-backed SQLite databases use WAL mode when the runtime allows it.
- `busy_timeout`, `temp_store`, and cache-size defaults are applied consistently at connection startup.
- Additive query indexes are managed through the existing migration registry as `2026_05_25_0016_query_performance_indexes`.
- Pagination normalization helpers were added for future API/repository surfaces that accept untrusted page or limit values.

## Indexed read paths

The new indexes target the routes that are most likely to become hot as data grows:

- admin and candidate job lists,
- saved-job pipeline and notes,
- active session and login-history screens,
- retrieval embedding queue reads,
- external job context cache refreshes,
- employer dashboard job/candidate/match summaries,
- employer outreach campaign and send-queue reads.

All indexes are additive and idempotent. They do not remove or rename existing indexes.

## Guardrails

`tests/test_sqlite_query_performance.py` verifies that:

- the performance migration is registered,
- the expected indexes are present after database initialization,
- runtime SQLite pragmas are applied,
- a representative saved-job pipeline query uses the new index,
- pagination normalization clamps untrusted values safely.

## Operational note

SQLite remains suitable for local/demo/small deployments. For heavier production usage, these changes reduce obvious read-path pain, but the long-term target should still be PostgreSQL with explicit migrations and query plans for high-volume candidate/job data.
