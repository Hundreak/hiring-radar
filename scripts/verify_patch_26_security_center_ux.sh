#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/tmp/hiring_radar_patch26_compile.log

if [ -f frontend/scripts/check-duplicate-sources.mjs ]; then
  (cd frontend && node scripts/check-duplicate-sources.mjs .)
fi
if [ -f frontend/scripts/check-component-size.mjs ]; then
  (cd frontend && node scripts/check-component-size.mjs src)
fi
if [ -f frontend/scripts/check-runtime-ux.mjs ]; then
  (cd frontend && node scripts/check-runtime-ux.mjs .)
fi
if [ -f frontend/scripts/check-pagination-ux.mjs ]; then
  (cd frontend && node scripts/check-pagination-ux.mjs .)
fi
if [ -f frontend/scripts/check-data-fetch-recovery.mjs ]; then
  (cd frontend && node scripts/check-data-fetch-recovery.mjs .)
fi
if [ -f frontend/scripts/check-auth-session-ux.mjs ]; then
  (cd frontend && node scripts/check-auth-session-ux.mjs .)
fi
(cd frontend && node scripts/check-security-center-ux.mjs .)
if [ -f frontend/scripts/check-performance-budget.mjs ]; then
  (cd frontend && node scripts/check-performance-budget.mjs .)
fi

printf 'Patch 26 security center UX verification passed.\n'
