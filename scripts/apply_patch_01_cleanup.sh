#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

DELETE_LIST="_DELETE_FILES.txt"
if [[ ! -f "$DELETE_LIST" ]]; then
  echo "ERROR: _DELETE_FILES.txt not found in $ROOT" >&2
  echo "Run this script from the project root after extracting Patch 01." >&2
  exit 1
fi

echo "== Patch 01 cleanup =="
echo "Project root: $ROOT"

while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
  line="${raw_line%%#*}"
  line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  [[ -z "$line" ]] && continue

  # Safety: prevent absolute paths and parent traversal.
  if [[ "$line" == /* || "$line" == *".."* ]]; then
    echo "SKIP unsafe path: $line"
    continue
  fi

  path="${line%/}"
  if [[ -e "$path" ]]; then
    rm -rf -- "$path"
    echo "deleted: $line"
  else
    echo "missing:  $line"
  fi
done < "$DELETE_LIST"

echo "== Cleanup complete =="
echo "Recommended next checks:"
echo "  python3 -m compileall src tests"
echo "  pytest"
echo "  cd frontend && npm install && npm run lint && npm run build"
