from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from hiring_radar.api.dependencies import get_repository
from hiring_radar.api.schemas.user_profile import UserAiSystemHealthResponse
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.ai.runtime import build_local_ai_runtime_service

router = APIRouter()

RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/health/system", response_model=UserAiSystemHealthResponse)
def system_health(repository: RepositoryDep) -> UserAiSystemHealthResponse:
    request_ref = "health_static"
    database_status = "ok"
    database_message = "Database connection is healthy."
    try:
        repository.connection.execute("SELECT 1").fetchone()
    except Exception as exc:
        database_status = "degraded"
        database_message = str(exc)

    ai_result = build_local_ai_runtime_service().health()
    overall = "ok" if database_status == "ok" and ai_result.runtime_status in {"ready", "disabled"} else "degraded"
    return UserAiSystemHealthResponse(
        status=overall,
        request_ref=request_ref,
        database={"status": database_status, "message": database_message},
        ai_runtime=ai_result.model_dump(),
    )
