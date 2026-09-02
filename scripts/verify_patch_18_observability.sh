#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests
pytest -q \
  tests/test_api_observability.py \
  tests/test_api_health.py \
  tests/test_api_csrf.py \
  tests/test_api_rate_limit.py \
  tests/test_auth_production_safety.py

python3 scripts/check_source_hygiene.py .

if [ -f frontend/package.json ]; then
  (cd frontend && npm run check:duplicates && npm run check:component-size)
fi

echo "Patch 18 API observability verification passed."
