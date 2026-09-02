#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

bash scripts/apply_patch_19_performance_cleanup.sh .

python3 -m compileall src tests
python3 scripts/check_source_hygiene.py .

cd frontend
node scripts/check-duplicate-sources.mjs
node scripts/check-component-size.mjs src
node scripts/check-performance-budget.mjs .

if command -v npm >/dev/null 2>&1 && [ -d node_modules ]; then
  npm run check:performance
else
  echo "Skipping npm wrapper smoke check because npm or node_modules is unavailable. Direct Node budget check already passed."
fi

cd ..

echo "Patch 19 performance budget verification passed."
