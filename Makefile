.PHONY: install lint format test compile verify backend-verify backend-performance frontend-install frontend-lint frontend-build frontend-performance  frontend-security-center-ux frontend-verify backend-ci frontend-ci ci help

install:
	python3 -m pip install --upgrade pip
	python3 -m pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

compile:
	python3 -m compileall src tests

test:
	pytest

backend-verify: lint compile test

frontend-install:
	cd frontend && npm install

frontend-lint:
	cd frontend && npm run lint

frontend-build:
	cd frontend && npm run build

frontend-performance:
	cd frontend && npm run check:performance

frontend-verify:
	cd frontend && npm run ci:verify

backend-performance:
	pytest -q tests/test_sqlite_query_performance.py

backend-ci:
	bash scripts/ci_backend_verify.sh .

frontend-ci:
	bash scripts/ci_frontend_verify.sh .

ci:
	bash scripts/ci_full_verify.sh .

verify: ci

help:
	hiring-radar --help

frontend-runtime-ux:
	cd frontend && npm run check:runtime-ux

verify-patch-22:
	bash scripts/verify_patch_22_api_contracts.sh .

frontend-auth-session-ux:
	cd frontend && npm run check:auth-session-ux

frontend-security-center-ux:
	cd frontend && npm run check:security-center-ux

.PHONY: frontend-notification-center frontend-employer-communication-center
frontend-notification-center:
	cd frontend && npm run check:notification-center

.PHONY: frontend-employer-communication-center
frontend-employer-communication-center:
	cd frontend && npm run check:employer-communication-center

.PHONY: frontend-employer-audit-evidence verify-patch-29
frontend-employer-audit-evidence:
	cd frontend && npm run check:employer-audit-evidence

verify-patch-29:
	bash scripts/verify_patch_29_employer_audit.sh .

.PHONY: release-env-check release-migration-dry-run release-check verify-patch-30
release-env-check:
	python3 scripts/check_release_environment.py --env-file $${HIRING_RADAR_RELEASE_ENV_FILE:-.env.production} --strict-production

release-migration-dry-run:
	python3 scripts/release_migration_dry_run.py

release-check:
	bash scripts/release_check.sh .

verify-patch-30:
	bash scripts/verify_patch_30_release_gate.sh .
