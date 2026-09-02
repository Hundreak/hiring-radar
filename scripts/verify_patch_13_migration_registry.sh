#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests
pytest -q \
  tests/test_sqlite_migration_registry.py \
  tests/test_sqlite_saved_jobs_api_migration.py \
  tests/test_notification_runs.py \
  tests/test_notification_checkpoints.py \
  tests/test_employer_database_schema.py

echo "Patch 13 migration registry verification passed."
