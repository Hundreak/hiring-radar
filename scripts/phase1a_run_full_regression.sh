#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Phase 1A full regression harness ==="
./scripts/phase1a_run_backend_regression.sh

echo
./scripts/phase1a_run_frontend_regression.sh

echo
cat <<'MSG'
Phase 1A automated regression checks passed.
Now run the manual closure checklist in docs/phase1a_closure_checklist.md before marking the phase as closed.
MSG
