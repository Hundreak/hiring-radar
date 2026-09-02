#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

echo "== Patch 12: Python syntax check =="
python3 -m compileall src tests >/tmp/hiring_radar_patch12_compile.log
cat /tmp/hiring_radar_patch12_compile.log | tail -20

echo "== Patch 12: targeted regression tests =="
pytest -q \
  tests/test_user_profile_router_split.py \
  tests/test_api_user_profile_ai_audit.py \
  tests/test_api_user_profile.py \
  tests/test_api_user_profile_uploads.py \
  tests/test_api_user_profile_cv_workspace_context.py \
  tests/test_retrieval_orchestration.py

echo "== Patch 12: source split smoke checks =="
test -f src/hiring_radar/api/routers/user_profile_ai_audit.py
test -f src/hiring_radar/api/routers/user_profile_insights.py
test -f src/hiring_radar/api/routers/user_profile_modules/shared.py

grep -q "router.include_router(_ai_audit_router)" src/hiring_radar/api/routers/user_profile.py
grep -q "router.include_router(_insights_router)" src/hiring_radar/api/routers/user_profile.py

echo "Patch 12 verification passed."
