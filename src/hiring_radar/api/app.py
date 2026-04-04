from __future__ import annotations

from fastapi import FastAPI

from hiring_radar.api.routers import (
    admin_auth_router,
    admin_dashboard_router,
    admin_jobs_router,
    admin_runs_router,
    admin_settings_router,
    admin_shell_router,
    admin_subscribers_router,
    health_router,
    user_auth_router,
    user_me_router,
    user_shell_router,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hiring Radar API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.include_router(health_router)
    app.include_router(admin_auth_router)
    app.include_router(admin_dashboard_router)
    app.include_router(admin_jobs_router)
    app.include_router(admin_runs_router)
    app.include_router(admin_subscribers_router)
    app.include_router(admin_settings_router)
    app.include_router(user_auth_router)
    app.include_router(user_me_router)
    app.include_router(admin_shell_router)
    app.include_router(user_shell_router)

    return app


app = create_app()