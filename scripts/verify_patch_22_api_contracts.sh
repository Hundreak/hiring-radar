#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall -q src tests
pytest -q \
  tests/test_api_pagination_contract.py \
  tests/test_api_saved_jobs_pagination_contract.py \
  tests/test_api_user_jobs.py \
  tests/test_api_user_saved_jobs.py \
  tests/test_api_admin_jobs.py \
  tests/test_api_admin_runs.py \
  tests/test_employer_dashboard_real_data.py

python3 scripts/check_source_hygiene.py .
( cd frontend && node scripts/check-duplicate-sources.mjs && node scripts/check-component-size.mjs && node scripts/check-runtime-ux.mjs && node scripts/check-performance-budget.mjs )

echo "Patch 22 API pagination / response contract verification passed."
