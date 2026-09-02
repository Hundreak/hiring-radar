#!/usr/bin/env bash
set -Eeuo pipefail

python3 -m compileall -q src tests
pytest -q \
  tests/test_api_csrf.py \
  tests/test_api_user_auth.py \
  tests/test_api_public_signup.py \
  tests/test_api_admin_auth.py \
  tests/test_employer_auth_rbac.py \
  tests/test_auth_production_safety.py \
  tests/test_api_rate_limit.py
