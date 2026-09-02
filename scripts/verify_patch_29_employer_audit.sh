#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/dev/null
pytest -q \
  tests/test_employer_audit_export.py \
  tests/test_employer_communication_preferences.py \
  tests/test_employer_dashboard_real_data.py

python3 scripts/check_source_hygiene.py .
(
  cd frontend
  node scripts/check-duplicate-sources.mjs
  node scripts/check-component-size.mjs src
  node scripts/check-runtime-ux.mjs .
  node scripts/check-pagination-ux.mjs .
  node scripts/check-auth-session-ux.mjs .
  node scripts/check-security-center-ux.mjs .
  node scripts/check-notification-center.mjs
  node scripts/check-employer-communication-center.mjs .
  node scripts/check-employer-audit-evidence.mjs .
  node scripts/check-performance-budget.mjs .
)

echo "Patch 29 employer audit evidence verification passed."
