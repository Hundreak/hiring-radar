from __future__ import annotations

from fastapi import FastAPI

from hiring_radar.api.routers import (
    admin_auth_router,
    admin_cv_engine_router,
    admin_dashboard_router,
    admin_jobs_router,
    admin_runs_router,
    admin_settings_router,
    admin_shell_router,
    admin_subscribers_router,
    employer_auth_router,
    employer_dashboard_router,
    health_router,
    public_auth_router,
    user_auth_router,
    user_jobs_router,
    user_me_router,
    user_profile_router,
    user_retrieval_router,
    user_ai_router,
    user_match_insights_router,
    user_saved_jobs_router,
    user_security_router,
    user_shell_router,
    google_oauth_router,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="NoyTera API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.include_router(health_router)
    app.include_router(admin_auth_router)
    app.include_router(admin_cv_engine_router)
    app.include_router(admin_dashboard_router)
    app.include_router(admin_jobs_router)
    app.include_router(admin_runs_router)
    app.include_router(admin_subscribers_router)
    app.include_router(admin_settings_router)
    app.include_router(user_auth_router)
    app.include_router(user_me_router)
    app.include_router(user_profile_router)
    app.include_router(user_retrieval_router)
    app.include_router(user_ai_router)
    app.include_router(user_jobs_router)
    app.include_router(user_match_insights_router)
    app.include_router(user_saved_jobs_router)
    app.include_router(user_security_router)
    app.include_router(admin_shell_router)
    app.include_router(user_shell_router)
    app.include_router(public_auth_router)
    app.include_router(google_oauth_router)
    app.include_router(employer_auth_router)
    app.include_router(employer_dashboard_router)

    return app


app = create_app()
