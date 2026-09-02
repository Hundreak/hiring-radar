#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

echo "== Patch 09: compile check =="
python3 -m compileall src tests >/tmp/hiring_radar_patch09_compile.log
cat /tmp/hiring_radar_patch09_compile.log | tail -20

echo "== Patch 09: employer dashboard DB bridge tests =="
pytest -q \
  tests/test_employer_dashboard_real_data.py \
  tests/test_employer_runtime_modes.py \
  tests/test_employer_auth_rbac.py \
  tests/test_employer_database_schema.py \
  tests/test_employer_workflow_persistence.py \
  tests/test_employer_matching.py \
  tests/test_api_csrf.py

echo "Patch 09 verification passed."
