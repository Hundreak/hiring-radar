#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 -m compileall src tests >/dev/null
pytest -q tests/test_employer_communication_preferences.py tests/test_employer_auth_rbac.py tests/test_api_csrf.py
python3 scripts/check_source_hygiene.py .
(cd frontend && npm run check:duplicates && npm run check:component-size && npm run check:runtime-ux && npm run check:pagination-ux && npm run check:auth-session-ux && npm run check:notification-center && npm run check:employer-communication-center && npm run check:performance)
echo "Patch 28 employer communication controls verification passed."
