#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/tmp/hiring_radar_patch14_compile.log

if [ -d frontend ]; then
  cd frontend
  node scripts/check-duplicate-sources.mjs
  node scripts/check-component-size.mjs src

  test -f src/components/onboarding/candidate-onboarding-panel.tsx
  test -f src/lib/candidate-onboarding.ts

  grep -q "CandidateOnboardingPanel" src/components/layout/app-shell.tsx
  grep -q "buildCandidateOnboardingModel" src/lib/candidate-onboarding.ts
  grep -q "noytera:candidate-onboarding:dismissed-until" src/components/onboarding/candidate-onboarding-panel.tsx
  grep -q "useUserProfileAggregateQuery" src/components/onboarding/candidate-onboarding-panel.tsx
fi

echo "Patch 14 candidate onboarding verification passed."
