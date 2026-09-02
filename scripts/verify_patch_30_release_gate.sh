#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall scripts tests src >/dev/null
python3 -m pytest -q tests/test_release_environment_check.py
python3 scripts/release_migration_dry_run.py
python3 scripts/check_release_environment.py \
  --env-file config/production.env.example \
  --strict-production || true
python3 scripts/check_source_hygiene.py .

required_files=(
  "RELEASE_CHECKLIST.md"
  "CHANGELOG.md"
  "docs/production-release-gate.md"
  "config/production.env.example"
  "scripts/check_release_environment.py"
  "scripts/release_migration_dry_run.py"
  "scripts/release_check.sh"
)

for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "Missing Patch 30 release gate file: $file" >&2
    exit 1
  fi
done

if ! grep -q "release-check" Makefile; then
  echo "Makefile is missing release-check target." >&2
  exit 1
fi

if ! grep -q "production release gate" RELEASE_CHECKLIST.md; then
  echo "RELEASE_CHECKLIST.md does not describe the production release gate." >&2
  exit 1
fi

echo "Patch 30 production release gate verification passed."
