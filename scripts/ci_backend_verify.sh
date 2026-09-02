#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTEST_ARGS="${PYTEST_ARGS:-}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 1
fi

"$PYTHON_BIN" scripts/check_source_hygiene.py .

if "$PYTHON_BIN" -m ruff --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m ruff check .
elif command -v ruff >/dev/null 2>&1; then
  ruff check .
else
  echo "ruff is not installed. Run: python3 -m pip install -e '.[dev]'" >&2
  exit 1
fi

"$PYTHON_BIN" -m compileall src tests
"$PYTHON_BIN" -m pytest ${PYTEST_ARGS}

echo "Backend CI verification passed."
