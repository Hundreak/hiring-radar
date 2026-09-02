from hiring_radar.api.routers.admin_auth import router as admin_auth_router
from hiring_radar.api.routers.admin_cv_engine import router as admin_cv_engine_router
from hiring_radar.api.routers.admin_dashboard import router as admin_dashboard_router
from hiring_radar.api.routers.admin_jobs import router as admin_jobs_router
from hiring_radar.api.routers.admin_runs import router as admin_runs_router
from hiring_radar.api.routers.admin_settings import router as admin_settings_router
from hiring_radar.api.routers.admin_shell import router as admin_shell_router
from hiring_radar.api.routers.admin_subscribers import router as admin_subscribers_router
from hiring_radar.api.routers.employer_auth import router as employer_auth_router
from hiring_radar.api.routers.employer_compliance import router as employer_compliance_router
from hiring_radar.api.routers.employer_dashboard import router as employer_dashboard_router
from hiring_radar.api.routers.employer_outreach import router as employer_outreach_router
from hiring_radar.api.routers.employer_settings import router as employer_settings_router
from hiring_radar.api.routers.employer_team import router as employer_team_router
from hiring_radar.api.routers.health import router as health_router
from hiring_radar.api.routers.oauth_auth import router as google_oauth_router
from hiring_radar.api.routers.public_auth import router as public_auth_router
from hiring_radar.api.routers.user_ai import router as user_ai_router
from hiring_radar.api.routers.user_auth import router as user_auth_router
from hiring_radar.api.routers.user_jobs import router as user_jobs_router
from hiring_radar.api.routers.user_match_insights import router as user_match_insights_router
from hiring_radar.api.routers.user_me import router as user_me_router
from hiring_radar.api.routers.user_profile import router as user_profile_router
from hiring_radar.api.routers.user_retrieval import router as user_retrieval_router
from hiring_radar.api.routers.user_saved_jobs import router as user_saved_jobs_router
from hiring_radar.api.routers.user_security import router as user_security_router
from hiring_radar.api.routers.user_shell import router as user_shell_router

__all__ = [
    "admin_cv_engine_router",
    "admin_auth_router",
    "admin_dashboard_router",
    "admin_jobs_router",
    "admin_runs_router",
    "admin_settings_router",
    "admin_shell_router",
    "admin_subscribers_router",
    "employer_auth_router",
    "employer_compliance_router",
    "employer_dashboard_router",
    "employer_team_router",
    "employer_outreach_router",
    "employer_settings_router",
    "health_router",
    "user_auth_router",
    "user_me_router",
    "user_shell_router",
    "user_jobs_router",
    "public_auth_router",
    "user_profile_router",
    "user_retrieval_router",
    "user_ai_router",
    "user_match_insights_router",
    "user_saved_jobs_router",
    "user_security_router",
    "google_oauth_router",
]
