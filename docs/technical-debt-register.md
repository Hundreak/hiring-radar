# Technical Debt Register

This register captures the main debt discovered during Patch 01 review. It is not a blame list; it is the order-of-attack for turning the current platform into a production-grade product.

## Critical

### 1. Default development secrets can still exist in auth paths

Risk: production sessions/signatures become weak if the application falls back to development secrets.

Next patch: Patch 02.

### 2. Cookie-based auth CSRF layer

Risk: mutating API endpoints can be vulnerable when authenticated by browser cookies.

Next patch: Patch 04.

### 3. Abuse-sensitive endpoints lack rate limiting

Risk: login, magic link, reset, signup, TOTP and upload endpoints are vulnerable to brute force or resource abuse.

Next patch: Patch 03.

### 4. Employer mock token behavior is mixed with production code paths

Risk: demo behavior can leak into production behavior.

Next patch: Patch 08.

## High

### 5. Frontend source-of-truth drift

Patch 01 removed the legacy duplicate component trees and Patch 05 removes the remaining identical employer route implementation.

Canonical component tree: `frontend/src/components/**`.

Risk remaining: future route/page aliases can accidentally copy-paste implementation logic instead of importing a shared module.

Guardrail: `frontend/scripts/check-duplicate-sources.mjs` now fails when identical source files return.

### 6. Oversized frontend components

Examples:

- `frontend/src/components/profile/profile-aggregate-workspace.tsx`
- `frontend/src/components/profile/cv-upload-module.tsx`
- `frontend/src/components/profile/cv-review-card.tsx`
- `frontend/src/components/employer/talent/talent-command-center.tsx`

Risk: difficult review, poor component isolation and harder performance optimization.

Next patch: Patch 07.

### 7. Oversized backend repository/router files

Examples:

- `src/hiring_radar/db/repository.py`
- `src/hiring_radar/api/routers/user_profile.py`
- `src/hiring_radar/services/cv_profile_parser.py`

Risk: high regression risk and slow development as domains continue to grow.

Next patches: Patch 11 and Patch 12.

## Medium

### 8. Product naming is inconsistent

Observed naming includes Hiring Radar, NoyTera and CoreSift.

Risk: user trust, SEO, documentation and investor/demo presentation become inconsistent.

Action: choose the canonical product name before broad UI/email copy cleanup. Patch 01 keeps package naming as Hiring Radar and documents the ambiguity instead of rewriting runtime copy blindly.

### 9. SQLite schema changes need migration discipline

Risk: schema drift, hard-to-debug local DB failures and difficult deployment upgrades.

Next patch: Patch 13.

### 10. Runtime-generated files were present in the source package

Examples:

- local DB backups
- CV inspect output
- TypeScript build info
- local Claude settings
- backup snapshot folders

Risk: noisy patches, accidental secret/data leakage and unnecessary zip size.

Action: Patch 01 adds `.gitignore`, `_DELETE_FILES.txt` and cleanup script.


## Patch 02 resolved items

- Production now fails fast when user/admin/employer session secrets are missing, short or known development placeholders.
- Session cookie security defaults now follow runtime environment: development remains local-friendly, production defaults to `Secure`.
- Employer mock tokens are no longer accepted by default in production.
- SMTP/auth delivery exceptions no longer leak low-level configuration or transport details through public API responses.

Patch 03 added rate limiting and Patch 04 added CSRF protection for cookie-authenticated mutations. Remaining follow-up: encrypt TOTP secrets and move rate limits to Redis for multi-node production.

## Patch 03 note — Abuse protection baseline

Patch 03 introduces a first-pass, dependency-free in-memory rate limiter for high-risk endpoints. It reduces brute-force and spam pressure on login, magic-link, password reset, signup verification, TOTP, account security and upload flows.

Remaining technical debt:

- The limiter is process-local. Multi-worker or multi-node deployments need a shared Redis-backed adapter.
- CSRF protection is implemented for cookie-authenticated mutating endpoints in Patch 04.
- TOTP secrets are still stored in the existing persistence format and should be encrypted in a later security patch.


### Patch 04 note

Patch 04 closes the dedicated CSRF gap for browser-based session cookies. Remaining follow-up: if future non-browser clients rely on cookie auth, they must request or receive a CSRF token before mutating calls, or move to explicit bearer/service authentication.

## Patch 05 resolved items

- The duplicate `/employer/talent` and `/employer/candidates` page implementation now lives in a single shared module: `frontend/src/components/employer/talent/talent-route-page.tsx`.
- Both route files are thin aliases and no longer contain duplicated parsing/rendering logic.
- `npm run check:duplicates` now detects identical frontend source files before they become long-lived technical debt.
- `npm run ci:verify` gives the frontend a single verification entrypoint for duplicate scan, lint, typecheck and build.

## Patch 06 resolved items

- Jobs, matches and saved jobs now use React Query instead of isolated manual `useEffect` loading/error state.
- API cache keys now have one source of truth in `frontend/src/lib/query-keys.ts`.
- Save/unsave mutations now update the saved-jobs cache and invalidate related job surfaces, reducing cross-page stale UI risk.
- Saved-job status and note mutations now invalidate/update cached saved-job data instead of relying on local-only state patches.

Remaining technical debt:

- The large profile/CV/employer components still use local request orchestration and should be migrated as they are split in Patch 07.
- React Query persistence/offline strategy is not added yet; current cache is in-memory per browser tab.
- Error UX is still page-level and should eventually be standardized through shared empty/error/loading components.

## Patch 12 update — User profile router split started

The large user profile router has begun moving toward domain route modules. Suggestions
and AI audit endpoints are now extracted into smaller routers while CV/upload-heavy
routes remain in the legacy module until their test seams are split safely.

## Patch 17 resolved items

- Local quality verification now has stable project-level entrypoints: `make backend-ci`, `make frontend-ci` and `make ci`.
- GitHub Actions now runs backend and frontend gates separately, which makes failures easier to diagnose.
- Source hygiene checks now guard against high-risk local/generated artifacts entering handoff packages or repository history.
- Frontend CI now uses the existing duplicate-source and component-size guards before lint/typecheck/build.

Remaining technical debt:

- CI currently runs the full backend pytest suite as one job. If runtime grows, split it into fast unit, API integration and slow/CV/AI suites.
- Frontend performance budget now exists, but real-device Core Web Vitals/Lighthouse checks are still not automated.
- No coverage threshold is enforced yet; add one only after flaky/slow integration tests are categorized.

## Patch 19 resolved items

- Added frontend public asset budgets, including total and per-file limits.
- Added source and app-route file byte budgets to complement line-count checks.
- Added optional Next build artifact JS/CSS gzip budgets that run when `.next/static` exists.
- Removed two unused oversized legacy PNG assets from the public tree through a safe cleanup script.

Remaining technical debt:

- No browser-based Lighthouse/Core Web Vitals CI yet. Add this only after stable staging URLs exist.
- Bundle budgets are intentionally conservative but not route-specific per user journey yet. Add route-level bundle attribution once build analyzer output is introduced.
