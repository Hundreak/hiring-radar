#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-$(pwd)}"
FRONTEND_DIR="$ROOT/frontend"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "frontend directory not found: $FRONTEND_DIR" >&2
  exit 1
fi

cd "$FRONTEND_DIR"
node scripts/check-duplicate-sources.mjs

if [[ -d node_modules ]]; then
  npm run lint
  npm run typecheck
else
  echo "node_modules not found; skipped npm run lint and npm run typecheck."
  echo "Run 'npm install' inside frontend, then run: npm run ci:verify"
fi
