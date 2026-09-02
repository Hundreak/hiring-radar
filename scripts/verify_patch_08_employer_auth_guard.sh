#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests
pytest -q   tests/test_auth_production_safety.py   tests/test_employer_auth_rbac.py   tests/test_employer_runtime_modes.py

python3 - <<'PY'
from pathlib import Path

required = [
    'src/hiring_radar/api/employer_runtime.py',
    'frontend/src/components/employer/employer-auth-gate.tsx',
    'frontend/src/components/employer/employer-shell.tsx',
    'frontend/src/components/employer/employer-topbar.tsx',
    'frontend/src/components/employer/employer-user-menu.tsx',
]
missing = [path for path in required if not Path(path).exists()]
if missing:
    raise SystemExit(f'Missing Patch 08 files: {missing}')

runtime = Path('src/hiring_radar/api/employer_runtime.py').read_text()
if 'production = is_production()' not in runtime or 'mock_auth_enabled = False' not in runtime:
    raise SystemExit('Employer runtime production hard-lock guard is missing.')

shell = Path('frontend/src/components/employer/employer-shell.tsx').read_text()
if 'EmployerAuthGate' not in shell or 'session={session}' not in shell:
    raise SystemExit('Employer shell is not protected by EmployerAuthGate.')

api = Path('frontend/src/lib/api.ts').read_text()
for needle in ('getEmployerSession', 'logoutEmployer', 'getEmployerRuntime'):
    if needle not in api:
        raise SystemExit(f'Frontend API is missing {needle}.')

print('Patch 08 smoke checks passed.')
PY
