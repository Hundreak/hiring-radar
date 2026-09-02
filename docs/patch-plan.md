# Patch Plan

This plan is intentionally incremental. The product already has many moving parts; the safest path is controlled patches with verification after each step.

## Phase 0 — Baseline and hygiene

### Patch 01 — Project hygiene and source of truth

Status: prepared.

Goals:

- remove local backups, database backups, build caches and duplicate source trees from the tracked project
- update `.gitignore`
- add `.env.example`
- rewrite README and architecture docs to match the current platform
- provide `_DELETE_FILES.txt` and a safe cleanup script

Runtime behavior: no intentional behavior change.

## Phase 1 — Security hardening

### Patch 02 — Production auth safety

Status: prepared.

- fail fast in production when user/admin/employer session secrets are missing, weak or default
- centralize runtime environment, boolean and cookie option parsing
- make auth cookies default to `Secure` in production while keeping local development compatible
- reject mock employer tokens by default in production unless demo mode is explicitly enabled
- stop exposing low-level email/auth delivery errors to users
- document required production variables

### Patch 03 — Rate limiting and abuse protection

- add IP + identity-aware rate limits for login, magic link, password reset, signup verification, TOTP and uploads
- start with an in-memory adapter
- design the interface so Redis can replace the in-memory store later

### Patch 04 — CSRF protection

- add CSRF protection for cookie-authenticated mutating endpoints
- issue a CSRF token after session creation
- update the frontend API client to send the CSRF header

## Phase 2 — Frontend architecture and performance

### Patch 05 — Frontend duplicate cleanup verification

- delete legacy `frontend/src/{ai,auth,brand,jobs,landing,layout,marketing,matches,profile,providers,saved,settings,theme,ui}` folders
- remove TypeScript exclude hacks
- verify imports use `@/components/**`
- run lint/build after dependencies are installed

### Patch 06 — API state layer

- add a single React Query provider
- introduce query/mutation hooks for session, profile, jobs, matches and saved jobs
- reduce manual loading/error/refetch code

### Patch 07 — Heavy component split

- split `profile-aggregate-workspace.tsx`
- split `cv-upload-module.tsx`
- split `cv-review-card.tsx`
- split `talent-command-center.tsx`
- add dynamic imports for heavy panels and drawers

## Phase 3 — Employer product readiness

### Patch 08 — Employer auth guard and demo mode separation

- make demo/mock mode explicit through env/config
- reject mock employer tokens outside demo mode
- add route guard consistency on employer pages

### Patch 09 — Employer dashboard real data bridge

- replace dashboard mock stats with repository-backed values
- keep demo data only behind demo mode

### Patch 10 — Employer workflow persistence

- move remaining JSON/file-backed outreach/campaign state into DB-backed repositories
- strengthen audit events and role checks

## Phase 4 — Backend modularization

### Patch 11 — Repository split

- split `repository.py` into domain repositories while preserving a compatibility facade
- start with auth/profile/jobs boundaries

### Patch 12 — User profile router split

- split the large user profile router into profile, CV, assets, AI audit and preference routers

### Patch 13 — Migration registry

- add `schema_migrations`
- version DB changes
- make schema initialization predictable and auditable

## Phase 5 — UX/product improvements

### Patch 14 — Candidate onboarding flow

- add first-login checklist
- make CV upload, profile completion and first match review feel like a guided product flow

### Patch 15 — Match explainability upgrade

- show why a job matched
- expose strong signals, gaps and next actions

### Patch 16 — Saved jobs pipeline

- add application states and notes to saved jobs
- prepare for reminders/follow-up workflows

## Phase 6 — Production quality

### Patch 17 — CI verify suite

- backend lint/compile/tests
- frontend lint/build/type verification
- smoke checks

### Patch 18 — Observability

- request ID middleware
- structured logs
- slow endpoint logging
- consistent error envelope

### Patch 19 — Performance budget

Status: implemented.

- executable frontend performance budget
- public asset total/per-file guardrails
- source and route file byte budgets
- optional Next build JS/CSS gzip chunk budgets
- CI integration through `npm run ci:verify`

## Patch 03 — Rate Limit + Abuse Protection

Status: completed in this package.

Outcome:

- Added configurable IP and identity rate limits to public/auth/security/upload endpoints.
- Returned standard `429 Too Many Requests` responses with `Retry-After`.
- Kept raw emails/user identifiers out of limiter state by hashing identity keys.
- Added targeted tests and `scripts/verify_patch_03_rate_limit.sh`.

Patch 04 is now implemented below. Next recommended patch: **Patch 05 — Frontend Duplicate Cleanup**.


## Patch 04 — CSRF Protection

Status: implemented.

What changed:

- Added `CsrfProtectionMiddleware` for cookie-authenticated mutating API requests.
- Added server helpers to attach and clear a browser-readable CSRF cookie.
- Issued CSRF cookies on user, admin, employer, public signup and Google OAuth session creation.
- Cleared CSRF cookies on logout/account deletion flows.
- Updated the frontend API client to send `X-CSRF-Token` for unsafe requests.
- Added regression tests for missing-token rejection, valid-token acceptance, logout cleanup and safe-request backfill.

Next recommended patch: **Patch 05 — Frontend Duplicate Cleanup**.

## Patch 05 — Frontend Duplicate Cleanup

Status: implemented.

What changed:

- Moved the duplicated employer talent route implementation into one shared route module.
- Added a frontend duplicate-source guard and `npm run check:duplicates`.
- Added `npm run typecheck` and `npm run ci:verify` to standardize frontend verification.

## Patch 06 — API State Layer with React Query

Status: implemented.

What changed:

- Added a client-side React Query provider under the localized app layout.
- Added centralized query keys for auth, user profile, jobs, matches, saved jobs, security and AI health surfaces.
- Added reusable API query/mutation hooks for jobs, matches, saved jobs, profile aggregate and saved-job workflow actions.
- Migrated `/jobs`, `/matches` and `/saved` dashboard pages away from manual `useEffect` request orchestration.
- Added cache updates/invalidation for save/unsave/status/note mutations so the job, match and saved-job surfaces remain synchronized.

Next recommended patch: **Patch 07 — Heavy Component Split**.

## Patch 07 — Heavy Component Split

Status: implemented.

What changed:

- Moved the large profile workspace localization table into `profile-workspace-copy.ts`.
- Moved reusable profile workspace primitives into `profile-workspace-primitives.tsx`.
- Moved the CV upload localization table into `cv-upload-copy.ts`.
- Moved the CV review localization table into `cv-review-copy.ts`.
- Added a frontend source-size guard with `npm run check:component-size`.
- Added the component-size guard to `npm run ci:verify` so future large source files are caught early.

Outcome:

- `profile-aggregate-workspace.tsx` dropped from 2503 lines to 1920 lines.
- `cv-upload-module.tsx` dropped from 2019 lines to 1543 lines.
- `cv-review-card.tsx` dropped from 2018 lines to 1489 lines.

Next recommended patch: **Patch 08 — Employer Auth Guard + Mock Mode Separation**.


## Patch 08 — Employer Auth Guard + Mock Mode Separation

Status: implemented.

What changed:

- Added a frontend auth gate for the employer workspace.
- Moved employer topbar identity and logout to the real employer session API.
- Made mock-token acceptance fail closed in production.
- Added `/api/employer/runtime` so frontend surfaces can distinguish demo/runtime behavior.

## Patch 09 — Employer Dashboard Real Data Bridge

Status: implemented.

What changed:

- Replaced production employer dashboard demo responses with repository-backed metrics.
- Kept demo fixtures only behind explicit demo mode/mock-token flows.
- Connected jobs, candidates, matches, analytics and activity surfaces to DB-backed records.

## Patch 10 — Employer Workflow Persistence / Outreach DB Bridge

Status: implemented.

What changed:

- Moved outreach campaign list/create endpoints from the legacy JSON store to `employer_outreach_campaigns`.
- Moved send-queue prepare/read/update from the legacy JSON store to `employer_send_queue_items`.
- Preserved the frontend API response shape so campaign and drawer screens continue working.
- Added audit events for campaign creation, queue preparation and queue item updates.
- Kept candidate workflow side effects in DB-backed tags/notes/stage data.

Next recommended patch: **Patch 11 — Repository Split: Profile/Auth/Jobs**.

## Patch 11 — Repository Split: Profile/Auth/Jobs

Status: implemented.

What changed:

- Added backward-compatible domain repository facades under `src/hiring_radar/db/repositories/`.
- Exposed `repo.auth`, `repo.profile` and `repo.jobs` without removing legacy repository methods.
- Added regression coverage for facade parity.

## Patch 12 — User Profile Router Split

Status: implemented.

What changed:

- Extracted user profile suggestions into `user_profile_insights.py`.
- Extracted AI audit lifecycle endpoints into `user_profile_ai_audit.py`.
- Added shared profile-router helper/dependency utilities.
- Left CV upload/parse endpoints in place to avoid disrupting existing monkeypatch-heavy tests.

## Patch 13 — Migration Registry

Status: implemented.

What changed:

- Added `schema_migrations` and an idempotent SQLite migration registry.
- Attached existing schema ensure functions to ordered migration IDs.
- Added busy timeout setup and migration registry regression tests.

## Patch 14 — Candidate Onboarding Flow

Status: implemented.

What changed:

- Added a dashboard-level candidate onboarding panel.
- Derived next-best-action guidance from profile aggregate data and saved-job state.
- Added a visible readiness checklist for CV, profile basics, target roles, skills, experience, first saved job and match review.
- Added a 24-hour local dismiss control so guidance is useful without becoming noisy.
- Kept the profile edit page uncluttered by hiding the panel on `/settings/profile`.

Next recommended patch: **Patch 15 — Match Explainability Upgrade**.

## Patch 15 — Match Explainability Upgrade

Status: implemented.

What changed:

- Added a match explainability model that turns existing deterministic match data into readable product concepts.
- Added application readiness, analysis confidence, score drivers, strong signals, risk/missing signals and suggested next actions to match cards.
- Added an AI application-plan prompt that carries the same explainability context into the copilot.
- Localized new match explainability copy in Turkish, English and German.

Next recommended patch: **Patch 16 — Saved Jobs Pipeline**.

## Patch 16 — Saved Jobs Pipeline

Status: implemented.

What changed:

- Expanded saved-job statuses with `offer` and `rejected`.
- Added a saved-job pipeline summary, search, sort and status filtering.
- Updated candidate saved-job flows so saved jobs behave like a lightweight application tracker instead of a simple bookmark list.
- Added backend validation coverage for the expanded status set.

Next recommended patch: **Patch 17 — CI Verify Suite**.

## Patch 17 — CI Verify Suite

Status: implemented.

What changed:

- Added repository-level CI scripts for backend, frontend and full verification.
- Added a source hygiene guard to block local/generated artifacts such as DB backups, zips, `.env` files and frontend TypeScript build info from entering release/source packages.
- Added `.github/workflows/ci.yml` with separate backend and frontend jobs.
- Updated `Makefile` so `make backend-ci`, `make frontend-ci`, `make ci` and `make verify` use the new quality gates.
- Documented local and GitHub Actions verification commands in README files.

Next recommended patch: **Patch 18 — API Observability**.

## Patch 18 — API Observability

Status: implemented.

Scope:

- Add request id middleware.
- Add response timing header.
- Add structured request/error logging.
- Add non-leaky generic 500 envelope with request id.
- Keep existing 4xx response shapes backward-compatible.
- Add targeted observability tests and verification script.

Verification:

```bash
bash scripts/verify_patch_18_observability.sh .
```


## Patch 22 — API Pagination / Response Contract Hardening

- Added shared API pagination contract helpers.
- Hardened user jobs/matches page-size and query bounds.
- Added pagination metadata and headers to saved jobs and employer list endpoints.
- Added bounded query/filter parameters to admin list surfaces.
- Added regression tests and verification script.
