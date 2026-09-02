#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/dev/null

required_files=(
  "frontend/src/components/profile/profile-workspace-copy.ts"
  "frontend/src/components/profile/profile-workspace-primitives.tsx"
  "frontend/src/components/profile/cv-upload-copy.ts"
  "frontend/src/components/profile/cv-review-copy.ts"
  "frontend/scripts/check-component-size.mjs"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing expected Patch 07 file: $file" >&2
    exit 1
  fi
done

if command -v node >/dev/null 2>&1; then
  (cd frontend && node scripts/check-component-size.mjs src)
else
  echo "node is not available; skipped frontend component-size check" >&2
fi

python3 - <<'PY'
from pathlib import Path
checks = {
    'frontend/src/components/profile/profile-aggregate-workspace.tsx': [
        'profileWorkspaceCopy as copy',
        'profile-workspace-primitives',
    ],
    'frontend/src/components/profile/cv-upload-module.tsx': [
        'cvUploadCopy as copy',
    ],
    'frontend/src/components/profile/cv-review-card.tsx': [
        'CV_REVIEW_COPY as COPY',
    ],
}
for filename, needles in checks.items():
    text = Path(filename).read_text()
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'{filename} does not contain expected marker: {needle}')
print('Patch 07 smoke checks passed.')
PY
