#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

echo "===== Patch 03 verify: compile ====="
python3 -m compileall -q src tests

echo "===== Patch 03 verify: targeted tests ====="
pytest -q \
  tests/test_api_rate_limit.py \
  tests/test_api_user_auth.py \
  tests/test_api_public_signup.py \
  tests/test_api_admin_auth.py \
  tests/test_employer_auth_rbac.py \
  tests/test_api_user_profile_uploads.py
