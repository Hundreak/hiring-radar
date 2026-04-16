#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
cd "$FRONTEND_DIR"

echo "=== Phase 1A frontend contract audit ==="
node ./scripts/phase1a-profile-audit.mjs

echo
echo "=== Phase 1A targeted eslint ==="
./node_modules/.bin/eslint \
  src/components/ui/feedback-banner.tsx \
  src/components/profile/profile-aggregate-workspace.tsx \
  src/components/profile/cv-upload-module.tsx \
  src/components/profile/profile-health-drawer.tsx \
  src/components/profile/avatar-crop-dialog.tsx \
  src/components/layout/user-menu.tsx \
  src/app/[locale]/\(dashboard\)/settings/notifications/page.tsx \
  src/lib/api.ts \
  src/types/profile.ts \
  src/types/user.ts
