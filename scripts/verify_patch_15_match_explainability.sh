#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests >/tmp/hiring_radar_patch15_compile.log

if [ -d frontend ]; then
  cd frontend
  node scripts/check-duplicate-sources.mjs
  node scripts/check-component-size.mjs src

  test -f src/lib/match-explainability.ts
  test -f src/components/matches/match-explainability-panel.tsx

  grep -q "buildMatchExplainabilityModel" src/lib/match-explainability.ts
  grep -q "buildMatchActionPlanPrompt" src/lib/match-explainability.ts
  grep -q "MatchExplainabilityPanel" src/components/matches/match-card.tsx
  grep -q "explainabilityTitle" messages/tr.json
  grep -q "explainabilityTitle" messages/en.json
  grep -q "explainabilityTitle" messages/de.json
fi

echo "Patch 15 match explainability verification passed."
