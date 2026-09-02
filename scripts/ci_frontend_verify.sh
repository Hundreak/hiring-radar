#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

FRONTEND_DIR="${FRONTEND_DIR:-frontend}"
if [ ! -d "$FRONTEND_DIR" ]; then
  echo "Frontend directory not found: $FRONTEND_DIR" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is not installed or not on PATH." >&2
  exit 1
fi

if [ "${HIRING_RADAR_FRONTEND_INSTALL:-auto}" = "auto" ] && [ ! -d node_modules ]; then
  npm ci
elif [ "${HIRING_RADAR_FRONTEND_INSTALL:-auto}" = "always" ]; then
  npm ci
fi

npm run ci:verify

echo "Frontend CI verification passed."
