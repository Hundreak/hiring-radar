# Production release gate

Patch 30 adds the final gate that decides whether the project is ready to leave a
developer machine and move toward staging or production.

## Command

```bash
HIRING_RADAR_RELEASE_ENV_FILE=.env.production make release-check
```

The command is intentionally strict. If the env file is missing or contains local
values, the gate fails.

## What it checks

### Source hygiene

`python3 scripts/check_source_hygiene.py .` prevents local artifacts from leaking
into release packages: `.env`, database files, backups, zip/tar archives and local
settings.

### Production env safety

`python3 scripts/check_release_environment.py --strict-production` validates:

- runtime environment,
- auth/session secrets,
- admin bootstrap values,
- secure cookies,
- CSRF/rate limit/observability flags,
- employer demo/mock flags,
- HTTPS URLs,
- persistent storage paths,
- SMTP sender settings,
- AI audit posture.

### Migration dry-run

`python3 scripts/release_migration_dry_run.py` initializes a disposable SQLite DB,
runs schema bootstrap + the migration registry, and checks release-critical tables,
indexes and pragmas.

### Backend CI

`bash scripts/ci_backend_verify.sh .` runs source hygiene, ruff, compileall and pytest.

### Frontend CI

`bash scripts/ci_frontend_verify.sh .` runs duplicate checks, component-size checks,
runtime UX checks, pagination UX checks, data recovery checks, auth/session checks,
security/notification/employer compliance checks, lint, typecheck, build and
performance budgets.

## Controlled skips

Use skip flags only for a documented emergency or a dedicated partial verification:

```bash
HIRING_RADAR_RELEASE_SKIP_ENV_CHECK=1
HIRING_RADAR_RELEASE_SKIP_MIGRATION_DRY_RUN=1
HIRING_RADAR_RELEASE_SKIP_BACKEND_CI=1
HIRING_RADAR_RELEASE_SKIP_FRONTEND_CI=1
```

A release with any skip flag should not be considered fully certified.

## Recommended CI setup

Use `.github/workflows/release-gate.yml` as a manual workflow. Configure repository
secrets for production-like values, then run the workflow before tagging a release.

## Exit code meaning

- `0`: gate passed.
- `1`: validation failed.
- `2`: production env file is missing.
