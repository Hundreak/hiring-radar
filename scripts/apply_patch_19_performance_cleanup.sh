#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

paths=(
  "frontend/public/brand/coresift-logo.png"
  "frontend/public/brand/coresift-copliot-logo.png"
)

for asset in "${paths[@]}"; do
  name="$(basename "$asset")"
  if [ -e "$asset" ]; then
    if grep -R --fixed-strings --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git --exclude="$name" "$name" frontend/src frontend/messages frontend/package.json >/dev/null 2>&1; then
      echo "Refusing to delete $asset because a source reference to $name was found." >&2
      exit 1
    fi
    size="$(wc -c < "$asset" | tr -d ' ')"
    rm -f "$asset"
    echo "Deleted unused public asset: $asset (${size} bytes)"
  else
    echo "Already absent: $asset"
  fi
done

rmdir frontend/public/brand 2>/dev/null || true

echo "Patch 19 performance cleanup complete."
