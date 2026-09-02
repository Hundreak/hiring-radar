#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

echo "== Patch 10: Python compile check =="
python3 -m compileall src tests >/tmp/hiring-radar-patch10-compile.log
cat /tmp/hiring-radar-patch10-compile.log | tail -20

echo

echo "== Patch 10: employer outreach DB persistence tests =="
pytest -q   tests/test_employer_database_schema.py   tests/test_employer_workflow_persistence.py   tests/test_api_csrf.py   tests/test_employer_auth_rbac.py

echo

echo "Patch 10 verification passed."
