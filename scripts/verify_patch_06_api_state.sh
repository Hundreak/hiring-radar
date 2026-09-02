#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

echo "== Patch 06 verification =="

python3 -m compileall src tests >/tmp/hiring_radar_patch06_compile.log

echo "Python compileall: ok"

required_files=(
  "frontend/src/components/providers/query-provider.tsx"
  "frontend/src/lib/query-keys.ts"
  "frontend/src/hooks/use-api-queries.ts"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing required file: $file" >&2
    exit 1
  fi
done

grep -q "<QueryProvider>" frontend/src/app/\[locale\]/layout.tsx
grep -q "useJobsQuery" frontend/src/app/\[locale\]/\(dashboard\)/jobs/page.tsx
grep -q "useMatchesQuery" frontend/src/app/\[locale\]/\(dashboard\)/matches/page.tsx
grep -q "useSavedJobsQuery" frontend/src/app/\[locale\]/\(dashboard\)/saved/page.tsx

echo "React Query integration smoke checks: ok"

if [[ -d frontend/node_modules ]]; then
  echo "frontend/node_modules found; running frontend duplicate/type verification"
  (cd frontend && npm run check:duplicates && npm run typecheck)
else
  echo "frontend/node_modules not found; skipped npm checks. Run 'cd frontend && npm install && npm run ci:verify' locally."
fi

echo "Patch 06 verification complete."
