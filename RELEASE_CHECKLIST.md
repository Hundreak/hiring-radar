# Hiring Radar production release gate

Use this checklist before every production cut. Patch 30 turns the checklist into
an executable gate with `make release-check`; do not treat the document as a
replacement for the command.

## 1. Prepare production environment

Create a private `.env.production` file outside version control. Start from
`config/production.env.example`, then replace every placeholder.

Required release posture:

- `HIRING_RADAR_ENV=production`
- all user/admin/employer session secrets are unique, rotated and at least 32 characters
- all session and CSRF cookies use `Secure=true`
- CSRF, rate limiting and observability stay enabled
- employer demo/mock auth is disabled
- public app/API/OAuth URLs use HTTPS
- SMTP settings are real, because auth flows depend on email delivery
- database and upload paths point to persistent storage

## 2. Run the final gate locally or in CI

```bash
HIRING_RADAR_RELEASE_ENV_FILE=.env.production make release-check
```

The release gate runs:

1. source hygiene checks,
2. production env validation,
3. migration dry-run on a disposable SQLite database,
4. backend lint/compile/test CI,
5. frontend lint/typecheck/build/performance CI.

For a backend-only emergency check, skip frontend explicitly and document why:

```bash
HIRING_RADAR_RELEASE_ENV_FILE=.env.production \
HIRING_RADAR_RELEASE_SKIP_FRONTEND_CI=1 \
make release-check
```

## 3. Pre-deploy smoke checks

- Confirm `GET /api/health` or equivalent API health probe from the target network.
- Confirm login, logout, CSRF-protected mutation and rate-limit behavior on staging.
- Confirm employer production account does not accept `mock_token_*`.
- Confirm email delivery for magic link, signup verification and password reset.
- Confirm `X-Request-ID` appears on API responses and request logs.
- Confirm database backups and upload storage backups are enabled.

## 4. Deploy

Recommended order:

1. deploy backend image/package,
2. run migration/bootstrap command or app startup migration,
3. deploy frontend build,
4. restart workers/API,
5. run post-deploy smoke checks.

## 5. Rollback notes

Before release, record:

- previous backend artifact/version,
- previous frontend artifact/version,
- database backup timestamp,
- migration identifiers applied in this release,
- owner responsible for the release.

Rollback should restore the previous app artifact first. If a migration changed
stored data semantics, restore from backup instead of hand-editing production rows.

## 6. Release evidence

Attach these outputs to the release record:

- `make release-check` terminal output,
- production env check output with secret values redacted,
- migration dry-run output,
- frontend build result,
- backend test summary,
- employer audit/compliance export smoke result.
