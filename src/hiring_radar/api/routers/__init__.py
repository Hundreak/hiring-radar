from hiring_radar.api.routers.admin_auth import router as admin_auth_router
from hiring_radar.api.routers.admin_dashboard import router as admin_dashboard_router
from hiring_radar.api.routers.admin_shell import router as admin_shell_router
from hiring_radar.api.routers.health import router as health_router

__all__ = [
    "admin_auth_router",
    "admin_dashboard_router",
    "admin_shell_router",
    "health_router",
]