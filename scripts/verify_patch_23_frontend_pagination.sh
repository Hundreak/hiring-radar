#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/tmp/hiring_radar_patch23_compile.log
python3 scripts/check_source_hygiene.py .

(
  cd frontend
  node scripts/check-duplicate-sources.mjs .
  node scripts/check-component-size.mjs src
  node scripts/check-runtime-ux.mjs .
  node scripts/check-pagination-ux.mjs .
  node scripts/check-performance-budget.mjs .
)

echo "Patch 23 frontend pagination verification passed."
