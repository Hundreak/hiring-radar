# Hiring Radar Frontend

This package contains the Next.js App Router frontend for the current Hiring Radar product.

## Current surfaces

- public marketing pages
- candidate auth pages
- candidate dashboard: jobs, matches, saved jobs and profile/settings flows
- employer workspace: dashboard, talent, jobs, campaigns, interviews, analytics, company, team/settings-like pages and support surfaces
- localized routing through `next-intl`

## Source-of-truth rule

Use `frontend/src/components/**` as the canonical component tree.

Do not edit or import the legacy duplicate folders under:

```text
frontend/src/ai
frontend/src/auth
frontend/src/brand
frontend/src/jobs
frontend/src/landing
frontend/src/layout
frontend/src/marketing
frontend/src/matches
frontend/src/profile
frontend/src/providers
frontend/src/saved
frontend/src/settings
frontend/src/theme
frontend/src/ui
```

Patch 01 removed those legacy duplicate folders. Patch 05 adds an automated duplicate-source guard so the problem does not silently return.

## Install

```bash
cd frontend
npm install
npm run dev
```

## Verify

Fast duplicate-source check:

```bash
npm run check:duplicates
```

Performance budget check:

```bash
npm run check:performance
```

Full frontend verification after dependencies are installed:

```bash
npm run ci:verify
```

`ci:verify` runs duplicate detection, component/source size checks, lint, TypeScript typecheck, production build and performance budget checks.

## Important routes

Candidate/public examples:

- `/tr`
- `/tr/login`
- `/tr/signup`
- `/tr/jobs`
- `/tr/matches`
- `/tr/saved`

Employer examples:

- `/tr/employer`
- `/tr/employer/dashboard`
- `/tr/employer/talent`
- `/tr/employer/campaigns`
- `/tr/employer/analytics`


## CSRF-aware API calls

`src/lib/api.ts` automatically reads the browser-readable `hiring_radar_csrf` cookie and sends it as `X-CSRF-Token` for unsafe methods. Keep `NEXT_PUBLIC_CSRF_COOKIE_NAME` and `NEXT_PUBLIC_CSRF_HEADER_NAME` aligned with backend env values if you customize names.

## Route alias rule

If two routes intentionally render the same experience, keep the real implementation in a shared module under `frontend/src/components/**` or `frontend/src/lib/**`. Route files should stay thin and should not copy parsing/rendering logic from another route.

## CI verification

Patch 17 standardizes frontend verification through the repository-level CI scripts.

From the project root:

```bash
make frontend-ci
# or
bash scripts/ci_frontend_verify.sh .
```

The frontend gate runs `npm run ci:verify`, which checks duplicate sources, component/source size, ESLint, TypeScript, production build and performance budgets.

Use this when dependencies are already installed and you do not want the wrapper to run `npm ci`:

```bash
HIRING_RADAR_FRONTEND_INSTALL=never bash scripts/ci_frontend_verify.sh .
```


## Performance budget

Patch 19 adds an executable frontend performance budget in `performance-budget.json`. The budget currently guards:

- total and per-file public asset size,
- large source and route files,
- localization message size,
- gzip JS/CSS chunk size when `.next/static` exists after a production build.

Run this after changing public assets, route files, heavy components or build configuration:

```bash
npm run check:performance
```

If the check fails, prefer compressing/converting assets, dynamic-loading heavy UI or splitting route/component files before raising the budget.
