#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/tmp/hiring_radar_patch17_compile.log
python3 scripts/check_source_hygiene.py .

required_files=(
  ".github/workflows/ci.yml"
  "scripts/check_source_hygiene.py"
  "scripts/ci_backend_verify.sh"
  "scripts/ci_frontend_verify.sh"
  "scripts/ci_full_verify.sh"
)
for file in "${required_files[@]}"; do
  test -f "$file" || { echo "Missing expected file: $file" >&2; exit 1; }
done

grep -q "ci_backend_verify.sh" .github/workflows/ci.yml
grep -q "ci_frontend_verify.sh" .github/workflows/ci.yml
grep -q "backend-ci" Makefile
grep -q "frontend-ci" Makefile
grep -q "ci:" Makefile
grep -q "check_source_hygiene.py" README.md
grep -q "Patch 17" docs/patch-plan.md

# Syntax-only validation for the shell entrypoints. This keeps the patch verifier
# lightweight in sandboxes where npm/ruff may not be installed.
bash -n scripts/ci_backend_verify.sh
bash -n scripts/ci_frontend_verify.sh
bash -n scripts/ci_full_verify.sh
bash -n scripts/verify_patch_17_ci_suite.sh

if [ -d frontend ]; then
  node frontend/scripts/check-duplicate-sources.mjs
  node frontend/scripts/check-component-size.mjs
fi

echo "Patch 17 CI suite verification passed."
