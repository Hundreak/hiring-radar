"""Employer runtime mode helpers.

The employer product currently has two distinct concerns that must not blur:

- signed employer sessions for real workspaces;
- demo/mock data used by the work-in-progress employer cockpit.

Patch 08 makes that separation explicit. Mock bearer tokens and demo data are
available only in non-production runtimes unless deliberately enabled there.
Production always rejects mock tokens and must be wired to real data surfaces
before these endpoints are exposed.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from hiring_radar.security_runtime import bool_env, is_production, runtime_env

MOCK_EMPLOYER_TOKEN_PREFIX = "mock_token_"


@dataclass(frozen=True, slots=True)
class EmployerRuntimeSettings:
    environment: str
    production: bool
    demo_mode_enabled: bool
    mock_auth_enabled: bool
    data_mode: str


def load_employer_runtime_settings() -> EmployerRuntimeSettings:
    """Resolve employer demo/mock safety settings from environment variables.

    ``HIRING_RADAR_EMPLOYER_DEMO_MODE`` controls whether mock-backed employer
    data endpoints are allowed. ``HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH`` controls
    whether ``mock_token_*`` bearer tokens are accepted for local/demo UI work.

    Production is intentionally hard-locked: both flags become false even if a
    misconfigured environment tries to enable them.
    """

    production = is_production()
    demo_mode_enabled = bool_env(
        "HIRING_RADAR_EMPLOYER_DEMO_MODE",
        default=not production,
    )
    mock_auth_enabled = bool_env(
        "HIRING_RADAR_EMPLOYER_ALLOW_MOCK_AUTH",
        default=not production,
    )

    if production:
        demo_mode_enabled = False
        mock_auth_enabled = False

    # Mock auth is never meaningful without demo mode. This prevents a partial
    # misconfiguration where tokens are accepted while mock/demo surfaces are off.
    mock_auth_enabled = mock_auth_enabled and demo_mode_enabled

    return EmployerRuntimeSettings(
        environment=runtime_env(),
        production=production,
        demo_mode_enabled=demo_mode_enabled,
        mock_auth_enabled=mock_auth_enabled,
        data_mode="demo" if demo_mode_enabled else "production",
    )


def require_employer_demo_data_enabled() -> EmployerRuntimeSettings:
    """Guard employer endpoints that still return demo/mock data.

    Patch 09 will replace the current mock data payloads with real repository
    queries. Until then, production should fail closed instead of showing fake
    dashboard, job, candidate or analytics data to authenticated workspaces.
    """

    settings = load_employer_runtime_settings()
    if not settings.demo_mode_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="employer_demo_data_disabled",
        )
    return settings


def employer_runtime_payload() -> dict[str, object]:
    settings = load_employer_runtime_settings()
    return {
        "ok": True,
        "environment": settings.environment,
        "production": settings.production,
        "demo_mode_enabled": settings.demo_mode_enabled,
        "mock_auth_enabled": settings.mock_auth_enabled,
        "data_mode": settings.data_mode,
    }
