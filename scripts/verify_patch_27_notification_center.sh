#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/dev/null
pytest -q \
  tests/test_api_user_notification_preferences.py \
  tests/test_repository_notification_preferences.py \
  tests/test_api_user_me.py

python3 scripts/check_source_hygiene.py .
(cd frontend && npm run check:duplicates && npm run check:component-size && npm run check:runtime-ux && npm run check:pagination-ux && npm run check:auth-session-ux && npm run check:notification-center && npm run check:performance)

echo "Patch 27 notification center verification passed."
