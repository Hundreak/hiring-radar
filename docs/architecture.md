# Hiring Radar Architecture

## 1. Purpose

Hiring Radar is currently an AI-assisted job matching platform with three major product surfaces:

- **Candidate experience:** account, CV upload/parsing, structured profile, job matches, saved jobs, AI copilot and security settings.
- **Employer experience:** employer authentication, dashboard, talent review, campaigns/outreach, team, quality/compliance/localization and analytics screens.
- **Operations/admin/ingestion:** crawler CLI, admin API, job source ingestion, filtering, exports, subscriber/admin workflows and runtime diagnostics.

The first MVP was a CLI crawler. That layer still exists, but the architecture has grown into a FastAPI + Next.js product.

---

## 2. Runtime layers

```text
Browser / Next.js App Router
        │
        ▼
Next.js route handlers and API proxy layer
        │
        ▼
FastAPI routers and dependencies
        │
        ▼
Service layer: auth, CV, matching, AI, retrieval, email, crawl, exports
        │
        ▼
Repository layer
        │
        ▼
SQLite database and local runtime storage
```

### Frontend

- Framework: Next.js App Router
- Language: TypeScript + React
- Styling: Tailwind CSS 4
- i18n: `next-intl`
- Canonical component tree: `frontend/src/components/**`
- Route tree: `frontend/src/app/**`
- API client and helpers: `frontend/src/lib/**`

Known cleanup rule:

- Legacy component folders under `frontend/src/{ai,auth,brand,jobs,landing,layout,marketing,matches,profile,providers,saved,settings,theme,ui}` are not canonical. They duplicate `frontend/src/components/**` and should be removed after applying Patch 01 cleanup.

### Backend

- Framework: FastAPI
- Package root: `src/hiring_radar`
- API app: `src/hiring_radar/api/app.py`
- API routers: `src/hiring_radar/api/routers/**`
- API schemas: `src/hiring_radar/api/schemas/**`
- Services: `src/hiring_radar/services/**`
- Database/repository: `src/hiring_radar/db/**`
- CLI entrypoint: `src/hiring_radar/cli.py`

---

## 3. Backend domains

### Auth and account security

#### CSRF protection

Patch 04 adds a double-submit CSRF layer for HttpOnly-cookie sessions. The API issues a non-HttpOnly CSRF cookie alongside user, admin and employer session cookies. The frontend API client sends that cookie value in `X-CSRF-Token` for unsafe methods. The middleware rejects mutating `/api/*` requests that carry a session cookie without a matching header, while login/signup/OAuth bootstrap endpoints stay exempt.


Implemented domains include:

- admin auth
- user auth
- public signup/verification flows
- password reset and magic-link style flows
- Google OAuth
- employer auth
- user security settings and TOTP-related flows

Important security debt to address next:

- production must never accept default development secrets
- cookie-authenticated mutating endpoints are protected by Patch 04 double-submit CSRF middleware
- login, reset, magic link, signup verification, TOTP and upload endpoints need rate limiting
- employer mock/demo tokens must be disabled outside explicit demo mode
- TOTP secrets should be encrypted, not merely stored under a field named `secret_encrypted`

### Candidate profile and CV

The candidate profile domain includes:

- CV upload and asset handling
- CV text extraction and OCR support
- CV parsing and profile draft creation
- profile completeness calculation
- education, experience, skills, languages and preference structures
- profile AI audit and insight features

Large files in this domain should be split during backend/frontend modularization patches.

### Jobs and matching

The job domain includes:

- source adapters and ingestion
- job canonicalization
- feature extraction
- candidate match scoring
- match explanations
- saved jobs and job interactions
- retrieval/context around jobs

### Employer workspace

The employer domain includes:

- employer auth/session services
- employer repository/schema
- dashboard and talent/candidate surfaces
- outreach/campaign persistence
- team/RBAC flows

Production readiness requires a clean separation between demo/mock data and real persisted workspace data.

---

## 4. Persistence

Current persistence is SQLite-first. This is acceptable for local development and controlled demos, but the project now has enough product complexity to need stricter migration discipline.

Current DB-related files:

- `src/hiring_radar/db/sqlite.py`
- `src/hiring_radar/db/schema.py`
- `src/hiring_radar/db/employer_schema.py`
- `src/hiring_radar/db/repository.py`
- `src/hiring_radar/db/employer_repository.py`

Near-term target:

- add a migration registry table
- version schema changes
- keep SQLite as local default
- prepare repository/service boundaries so PostgreSQL can be introduced later without a full rewrite

---

## 5. Testing strategy

The backend already has a broad pytest suite. The project should keep the following baseline checks stable:

```bash
ruff check .
python -m compileall src tests
pytest
```

Frontend verification should become a required gate:

```bash
cd frontend
npm run lint
npm run build
```

Patch 17 will formalize these checks in CI.

---

## 6. Architectural direction

The safest improvement sequence is:

1. cleanup repository hygiene and documentation
2. harden auth/session/email behavior for production
3. add rate limiting and CSRF protection
4. delete legacy frontend duplicate trees and remove TypeScript exclude hacks
5. introduce a consistent API state layer on the frontend
6. split oversized frontend components
7. separate employer demo mode from production mode
8. split oversized backend repository/router modules by domain
9. introduce migration registry and observability

## Abuse protection layer

The API now has a lightweight abuse-protection layer in `src/hiring_radar/api/rate_limit.py`.
It applies fixed-window IP buckets and optional identity buckets to high-risk endpoints. Identity keys are normalized and SHA-256 hashed before they are stored in memory.

Current implementation characteristics:

- dependency-free, in-memory store
- per-action environment overrides
- standard `429 Too Many Requests` response with `Retry-After`
- proxy headers ignored by default unless `HIRING_RADAR_RATE_LIMIT_TRUST_PROXY_HEADERS=true`

This layer is suitable as a single-process baseline. A shared Redis adapter should replace the in-memory store for horizontal scaling.

## Patch 11 repository domain seams

Patch 11 adds domain repository facades on the root `HiringRadarRepository`:

- `repo.auth` for authentication, sessions, login history, email-change, TOTP and OAuth persistence.
- `repo.profile` for candidate profile, CV workspace, profile intelligence and AI/copilot persistence.
- `repo.jobs` for job catalog, canonical jobs, matching interactions and saved jobs.

The old root repository methods remain available. New code should prefer the domain facade to reduce coupling and prepare for moving SQL implementations out of the legacy monolithic `repository.py` file.


### Patch 12 user profile router split boundary

`/api/user/profile` is now mounted from the legacy profile router plus smaller included
subrouters. New low-risk user profile surfaces should be added to dedicated modules
instead of extending the legacy monolith. Current split modules:

- `user_profile_insights.py` for suggestions/read-oriented profile insights.
- `user_profile_ai_audit.py` for AI audit lifecycle endpoints.
- `user_profile_modules/shared.py` for shared dependency aliases and aggregate response building.

## API observability layer

Patch 18 adds a dependency-free API observability layer in `src/hiring_radar/api/observability.py`.

Runtime behavior:

- Every API response gets an `X-Request-ID` header.
- Valid incoming `X-Request-ID` values are preserved so reverse proxies and frontend logs can correlate requests end-to-end.
- Invalid or missing request ids are replaced with generated UUID-style ids.
- Successful, rejected and failed requests emit structured request logs through `hiring_radar.api.request`.
- Slow requests are flagged with `slow=true` when they exceed `HIRING_RADAR_SLOW_REQUEST_THRESHOLD_MS`.
- Unexpected server exceptions return a generic envelope with `detail` and `request_id`, without leaking internal exception messages.
- Existing 4xx response bodies remain backward-compatible; this avoids breaking clients and tests that already rely on FastAPI's `detail` shape.

Useful environment settings:

```bash
HIRING_RADAR_OBSERVABILITY_ENABLED=true
HIRING_RADAR_REQUEST_ID_HEADER=X-Request-ID
HIRING_RADAR_RESPONSE_TIME_HEADER=X-Response-Time-Ms
HIRING_RADAR_LOG_REQUESTS=true
HIRING_RADAR_LOG_SLOW_REQUESTS=true
HIRING_RADAR_SLOW_REQUEST_THRESHOLD_MS=750
HIRING_RADAR_JSON_LOGS=true
```

Production note: application logs should be collected by the hosting platform or a log shipper and indexed by `request_id`, `path`, `status_code`, `duration_ms` and `slow`.
