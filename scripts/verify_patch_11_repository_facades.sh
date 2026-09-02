#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${1:-.}"
cd "$ROOT"

python3 -m compileall src tests
pytest -q tests/test_repository_domain_facades.py tests/test_repository_user_auth.py tests/test_repository_subscriber_profile.py tests/test_repository_job_catalog.py tests/test_repository_job_interactions.py tests/test_api_user_saved_jobs.py

python3 - <<'PY'
from pathlib import Path
required = [
    'src/hiring_radar/db/repositories/__init__.py',
    'src/hiring_radar/db/repositories/base.py',
    'src/hiring_radar/db/repositories/auth.py',
    'src/hiring_radar/db/repositories/profile.py',
    'src/hiring_radar/db/repositories/jobs.py',
]
missing = [p for p in required if not Path(p).exists()]
if missing:
    raise SystemExit(f'Missing repository facade files: {missing}')
text = Path('src/hiring_radar/db/repository.py').read_text()
for needle in ['self.auth = AuthRepository(self)', 'self.profile = ProfileRepository(self)', 'self.jobs = JobsRepository(self)']:
    if needle not in text:
        raise SystemExit(f'Missing repository facade wiring: {needle}')
print('Patch 11 repository facade smoke checks passed.')
PY
