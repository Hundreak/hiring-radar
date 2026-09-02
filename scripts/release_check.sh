#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
ENV_FILE="${HIRING_RADAR_RELEASE_ENV_FILE:-.env.production}"

echo "===== Hiring Radar release gate started ====="

"$PYTHON_BIN" scripts/check_source_hygiene.py .

if [ "${HIRING_RADAR_RELEASE_SKIP_ENV_CHECK:-0}" = "1" ]; then
  echo "Skipping production env check because HIRING_RADAR_RELEASE_SKIP_ENV_CHECK=1"
else
  "$PYTHON_BIN" scripts/check_release_environment.py \
    --env-file "$ENV_FILE" \
    --strict-production
fi

if [ "${HIRING_RADAR_RELEASE_SKIP_MIGRATION_DRY_RUN:-0}" = "1" ]; then
  echo "Skipping migration dry-run because HIRING_RADAR_RELEASE_SKIP_MIGRATION_DRY_RUN=1"
else
  "$PYTHON_BIN" scripts/release_migration_dry_run.py
fi

if [ "${HIRING_RADAR_RELEASE_SKIP_BACKEND_CI:-0}" = "1" ]; then
  echo "Skipping backend CI because HIRING_RADAR_RELEASE_SKIP_BACKEND_CI=1"
else
  bash scripts/ci_backend_verify.sh .
fi

if [ "${HIRING_RADAR_RELEASE_SKIP_FRONTEND_CI:-0}" = "1" ]; then
  echo "Skipping frontend CI because HIRING_RADAR_RELEASE_SKIP_FRONTEND_CI=1"
elif [ "${HIRING_RADAR_SKIP_FRONTEND_CI:-0}" = "1" ]; then
  echo "Skipping frontend CI because HIRING_RADAR_SKIP_FRONTEND_CI=1"
else
  bash scripts/ci_frontend_verify.sh .
fi

echo "Hiring Radar production release gate passed."
