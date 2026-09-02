#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests
pytest -q \
  tests/test_sqlite_query_performance.py \
  tests/test_sqlite_migration_registry.py \
  tests/test_employer_database_schema.py \
  tests/test_api_observability.py

python3 scripts/check_source_hygiene.py .

if [ -d frontend ] && command -v node >/dev/null 2>&1; then
  cd frontend
  node scripts/check-duplicate-sources.mjs
  node scripts/check-component-size.mjs src
  node scripts/check-runtime-ux.mjs .
  node scripts/check-performance-budget.mjs .
  cd ..
else
  echo "Skipping frontend smoke checks because frontend directory or node is unavailable."
fi

echo "Patch 21 backend performance verification passed."
