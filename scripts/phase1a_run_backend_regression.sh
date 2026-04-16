#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Phase 1A backend regression ==="
pytest \
  tests/test_api_user_profile.py \
  tests/test_api_user_profile_uploads.py \
  tests/test_api_user_profile_cv_workspace_context.py \
  -q
