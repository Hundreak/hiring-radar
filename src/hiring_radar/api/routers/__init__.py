from hiring_radar.api.routers.admin_auth import router as admin_auth_router
from hiring_radar.api.routers.admin_dashboard import router as admin_dashboard_router
from hiring_radar.api.routers.admin_jobs import router as admin_jobs_router
from hiring_radar.api.routers.admin_runs import router as admin_runs_router
from hiring_radar.api.routers.admin_settings import router as admin_settings_router
from hiring_radar.api.routers.admin_shell import router as admin_shell_router
from hiring_radar.api.routers.admin_subscribers import router as admin_subscribers_router
from hiring_radar.api.routers.health import router as health_router
from hiring_radar.api.routers.user_auth import router as user_auth_router
from hiring_radar.api.routers.user_me import router as user_me_router
from hiring_radar.api.routers.user_shell import router as user_shell_router

__all__ = [
    "admin_auth_router",
    "admin_dashboard_router",
    "admin_jobs_router",
    "admin_runs_router",
    "admin_settings_router",
    "admin_shell_router",
    "admin_subscribers_router",
    "health_router",
    "user_auth_router",
    "user_me_router",
    "user_shell_router",
]