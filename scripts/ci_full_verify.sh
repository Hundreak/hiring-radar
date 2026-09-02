#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

bash scripts/ci_backend_verify.sh .

if [ "${HIRING_RADAR_SKIP_FRONTEND_CI:-0}" = "1" ]; then
  echo "Skipping frontend CI because HIRING_RADAR_SKIP_FRONTEND_CI=1"
else
  bash scripts/ci_frontend_verify.sh .
fi

echo "Full CI verification passed."
