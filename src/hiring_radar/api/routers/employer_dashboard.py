"""Employer dashboard router — production DB-backed employer UI endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from hiring_radar.api.employer_dependencies import get_employer_repository
from hiring_radar.api.employer_runtime import (
    MOCK_EMPLOYER_TOKEN_PREFIX,
    employer_runtime_payload,
    load_employer_runtime_settings,
    require_employer_demo_data_enabled,
)
from hiring_radar.api.pagination import (
    EMPLOYER_LIST_BOUNDS,
    EMPLOYER_WIDGET_BOUNDS,
    list_envelope,
    normalize_page_contract,
    paginate_sequence,
    set_pagination_headers,
)
from hiring_radar.db.employer_repository import EmployerRepository
from hiring_radar.services.employer_auth import (
    EmployerAuthError,
    decode_employer_session_token,
    load_employer_auth_settings,
)

router = APIRouter(prefix="/api/employer", tags=["employer"])

EMPLOYER_SESSION_COOKIE_NAME = "hiring_radar_employer_session"


DEMO_STATS: dict[str, Any] = {
    "active_jobs": 5,
    "total_applications": 127,
    "pending_reviews": 23,
    "avg_match_score": 78.4,
    "active_jobs_delta": +2,
    "applications_delta": +15,
    "pending_delta": -5,
    "match_score_delta": +3.2,
}

DEMO_JOBS: list[dict[str, Any]] = [
    {"id": "job_1", "title": "Senior Frontend Engineer", "department": "Engineering", "location": "İstanbul (Hybrid)", "status": "active", "applicants": 34, "match_avg": 82.5, "posted_at": "2026-05-01"},
    {"id": "job_2", "title": "Backend Developer", "department": "Engineering", "location": "Remote", "status": "active", "applicants": 28, "match_avg": 75.3, "posted_at": "2026-04-28"},
    {"id": "job_3", "title": "Product Manager", "department": "Product", "location": "Ankara", "status": "paused", "applicants": 15, "match_avg": 68.9, "posted_at": "2026-04-20"},
    {"id": "job_4", "title": "DevOps Engineer", "department": "Infrastructure", "location": "İstanbul", "status": "active", "applicants": 19, "match_avg": 71.2, "posted_at": "2026-04-15"},
    {"id": "job_5", "title": "Data Scientist", "department": "Data", "location": "Remote", "status": "closed", "applicants": 42, "match_avg": 79.8, "posted_at": "2026-04-01"},
    {"id": "job_6", "title": "UI/UX Designer", "department": "Design", "location": "İstanbul", "status": "active", "applicants": 12, "match_avg": 65.4, "posted_at": "2026-05-03"},
]

DEMO_CANDIDATES: list[dict[str, Any]] = [
    {"id": "cand_1", "name": "Ahmet Yılmaz", "headline": "Senior Frontend Developer", "match_score": 94, "skills": ["React", "TypeScript", "Next.js", "GraphQL"], "experience_years": 7, "location": "İstanbul", "education": "İTÜ Bilgisayar Mühendisliği", "status": "new"},
    {"id": "cand_2", "name": "Merve Kaya", "headline": "Full Stack Engineer", "match_score": 89, "skills": ["Node.js", "Python", "AWS", "PostgreSQL"], "experience_years": 5, "location": "Ankara", "education": "ODTÜ Bilgisayar Mühendisliği", "status": "reviewed"},
    {"id": "cand_3", "name": "Can Demir", "headline": "DevOps Engineer", "match_score": 86, "skills": ["Kubernetes", "Docker", "CI/CD", "Terraform"], "experience_years": 6, "location": "İzmir", "education": "Ege Üniversitesi", "status": "shortlisted"},
    {"id": "cand_4", "name": "Elif Şahin", "headline": "Product Manager", "match_score": 81, "skills": ["Agile", "Scrum", "Analytics", "Figma"], "experience_years": 4, "location": "İstanbul", "education": "Boğaziçi Üniversitesi", "status": "new"},
    {"id": "cand_5", "name": "Burak Özdemir", "headline": "Backend Developer", "match_score": 76, "skills": ["Java", "Spring Boot", "Microservices"], "experience_years": 4, "location": "İstanbul", "education": "İTÜ", "status": "reviewed"},
    {"id": "cand_6", "name": "Zeynep Aydın", "headline": "Data Scientist", "match_score": 73, "skills": ["Python", "ML", "TensorFlow", "SQL"], "experience_years": 3, "location": "Ankara", "education": "Hacettepe", "status": "new"},
    {"id": "cand_7", "name": "Emre Kılıç", "headline": "Mobile Developer", "match_score": 68, "skills": ["React Native", "iOS", "Android"], "experience_years": 5, "location": "İzmir", "education": "Ege Üniversitesi", "status": "reviewed"},
    {"id": "cand_8", "name": "Selin Yıldız", "headline": "UI/UX Designer", "match_score": 65, "skills": ["Figma", "Adobe XD", "Prototyping"], "experience_years": 3, "location": "İstanbul", "education": "Mimar Sinan", "status": "new"},
]

DEMO_MATCHES: list[dict[str, Any]] = [
    {"id": "match_1", "candidate_id": "cand_1", "candidate_name": "Ahmet Yılmaz", "job_id": "job_1", "job_title": "Senior Frontend Engineer", "match_score": 94, "breakdown": {"skills": 95, "experience": 90, "education": 92, "location": 98, "language": 88}},
    {"id": "match_2", "candidate_id": "cand_2", "candidate_name": "Merve Kaya", "job_id": "job_2", "job_title": "Backend Developer", "match_score": 89, "breakdown": {"skills": 88, "experience": 85, "education": 90, "location": 80, "language": 92}},
    {"id": "match_3", "candidate_id": "cand_3", "candidate_name": "Can Demir", "job_id": "job_4", "job_title": "DevOps Engineer", "match_score": 86, "breakdown": {"skills": 90, "experience": 82, "education": 78, "location": 85, "language": 80}},
    {"id": "match_4", "candidate_id": "cand_4", "candidate_name": "Elif Şahin", "job_id": "job_3", "job_title": "Product Manager", "match_score": 81, "breakdown": {"skills": 78, "experience": 75, "education": 88, "location": 85, "language": 90}},
]


class EmployerRequestContext(dict):
    """Small dict subtype used to keep endpoint payloads readable."""

    @property
    def is_mock(self) -> bool:
        return self.get("auth_mode") == "mock"

    @property
    def company_id(self) -> int:
        value = self.get("company_id")
        if value is None:
            raise HTTPException(status_code=401, detail="employer_company_missing")
        return int(value)

    @property
    def user_id(self) -> int | None:
        value = self.get("user_id")
        return int(value) if value is not None and str(value).isdigit() else None


def _mock_employer_auth_enabled() -> bool:
    return load_employer_runtime_settings().mock_auth_enabled


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token.strip():
        return None
    return token.strip()


def _mock_employer_from_token(token: str | None) -> dict | None:
    if not token:
        return None

    if token.startswith(MOCK_EMPLOYER_TOKEN_PREFIX):
        if not _mock_employer_auth_enabled():
            return None
        return {
            "user_id": token.removeprefix(MOCK_EMPLOYER_TOKEN_PREFIX) or "emp_demo",
            "role": "employer",
            "auth_mode": "mock",
        }

    try:
        session = decode_employer_session_token(token, settings=load_employer_auth_settings())
    except EmployerAuthError:
        return None

    return {
        "user_id": session.user_id,
        "company_id": session.company_id,
        "member_id": session.member_id,
        "email": session.email,
        "role": "employer",
        "role_key": session.role_key,
        "auth_mode": "db",
    }


def _require_employer(request: Request) -> dict:
    """Resolve the current employer from state, secure cookie or bearer token.

    Local/demo mock auth is still accepted only when explicitly enabled by the
    runtime settings. Production DB sessions are resolved to a company-scoped
    context so dashboard endpoints can serve real data instead of demo fixtures.
    """
    state_user = getattr(request.state, "user", None)
    if isinstance(state_user, dict):
        if state_user.get("role") == "employer":
            return state_user
        raise HTTPException(status_code=403, detail="forbidden")

    cookie_user = _mock_employer_from_token(request.cookies.get(EMPLOYER_SESSION_COOKIE_NAME))
    if cookie_user is not None:
        return cookie_user

    bearer_user = _mock_employer_from_token(
        _extract_bearer_token(request.headers.get("authorization"))
    )
    if bearer_user is not None:
        return bearer_user

    raise HTTPException(status_code=401, detail="unauthorized")


def _require_employer_context(request: Request) -> EmployerRequestContext:
    employer = EmployerRequestContext(_require_employer(request))
    if employer.is_mock:
        require_employer_demo_data_enabled()
    return employer


def _db_status_from_api(status: str | None) -> str | None:
    mapping = {
        "active": "published",
        "published": "published",
        "paused": "paused",
        "closed": "closed",
        "archived": "archived",
        "draft": "draft",
    }
    if status is None:
        return None
    return mapping.get(status)


def _parse_numeric_id(value: str, *, prefix: str) -> int | None:
    cleaned = value.strip()
    if cleaned.isdigit():
        return int(cleaned)
    if cleaned.startswith(prefix):
        suffix = cleaned.removeprefix(prefix)
        return int(suffix) if suffix.isdigit() else None
    return None


def _paginated_employer_items(
    items: list[dict[str, Any]],
    *,
    response: Response,
    page: int,
    page_size: int,
    widget: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    meta = normalize_page_contract(
        page=page,
        page_size=page_size,
        total_items=len(items),
        bounds=EMPLOYER_WIDGET_BOUNDS if widget else EMPLOYER_LIST_BOUNDS,
    )
    set_pagination_headers(response, meta=meta)
    return list_envelope(items=paginate_sequence(items, meta=meta), meta=meta, **extra)


@router.get("/runtime")
def employer_runtime() -> dict[str, object]:
    """Expose safe employer runtime mode flags to the frontend."""

    return employer_runtime_payload()


# ─────────────────────────── Dashboard ───────────────────────────

@router.get("/dashboard/stats")
def dashboard_stats(
    request: Request,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get employer dashboard statistics from DB sessions or local demo data."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return {"ok": True, "stats": DEMO_STATS}
    return {"ok": True, "stats": repository.get_dashboard_stats(employer.company_id)}


@router.get("/dashboard/recent-jobs")
def dashboard_recent_jobs(
    request: Request,
    response: Response,
    page_size: Annotated[int, Query(ge=1, le=25)] = 5,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get recent job postings for dashboard."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return _paginated_employer_items(
            DEMO_JOBS,
            response=response,
            page=1,
            page_size=page_size,
            widget=True,
        )
    return _paginated_employer_items(
        repository.list_dashboard_jobs(employer.company_id, limit=page_size),
        response=response,
        page=1,
        page_size=page_size,
        widget=True,
    )


@router.get("/dashboard/top-candidates")
def dashboard_top_candidates(
    request: Request,
    response: Response,
    page_size: Annotated[int, Query(ge=1, le=25)] = 4,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get top matched candidates for dashboard."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return _paginated_employer_items(
            DEMO_CANDIDATES,
            response=response,
            page=1,
            page_size=page_size,
            widget=True,
        )
    return _paginated_employer_items(
        repository.list_dashboard_candidates(employer.company_id, limit=page_size),
        response=response,
        page=1,
        page_size=page_size,
        widget=True,
    )


@router.get("/dashboard/activity")
def dashboard_activity(
    request: Request,
    response: Response,
    page_size: Annotated[int, Query(ge=1, le=25)] = 10,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get recent activity feed."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return _paginated_employer_items(
            [
                {"type": "application", "text": "Yeni başvuru: Senior Frontend Engineer pozisyonuna", "time": "5 dakika önce"},
                {"type": "match", "text": "Yüksek eşleşme: Merve Kaya (%89)", "time": "15 dakika önce"},
                {"type": "upload", "text": "CV yüklendi: Can Demir", "time": "1 saat önce"},
                {"type": "job", "text": "İlan yayınlandı: Backend Developer", "time": "2 saat önce"},
                {"type": "review", "text": "Değerlendirme tamamlandı: 5 aday", "time": "3 saat önce"},
            ],
            response=response,
            page=1,
            page_size=page_size,
            widget=True,
        )
    return _paginated_employer_items(
        repository.list_dashboard_activity(employer.company_id, limit=page_size),
        response=response,
        page=1,
        page_size=page_size,
        widget=True,
    )


# ─────────────────────────── Jobs ───────────────────────────

@router.get("/jobs")
def employer_jobs(
    request: Request,
    response: Response,
    status: Annotated[str | None, Query(max_length=32)] = None,
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get employer's job postings."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        jobs = DEMO_JOBS
        if status:
            jobs = [job for job in jobs if job["status"] == status]
        return _paginated_employer_items(
            jobs,
            response=response,
            page=page,
            page_size=page_size,
            status=status,
        )

    db_status = _db_status_from_api(status)
    if status is not None and db_status is None:
        raise HTTPException(status_code=400, detail="invalid_job_status")
    return _paginated_employer_items(
        repository.list_dashboard_jobs(employer.company_id, status=db_status),
        response=response,
        page=page,
        page_size=page_size,
        status=status,
    )


@router.post("/jobs")
def employer_create_job(
    payload: dict,
    request: Request,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Create a new job posting."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return {
            "ok": True,
            "job": {
                "id": f"job_{datetime.now(UTC).timestamp()}",
                "title": payload.get("title", ""),
                "department": payload.get("department", ""),
                "location": payload.get("location", ""),
                "status": "active",
                "applicants": 0,
                "match_avg": 0,
                "posted_at": datetime.now(UTC).strftime("%Y-%m-%d"),
            },
        }

    status = _db_status_from_api(str(payload.get("status") or "active"))
    if status is None:
        raise HTTPException(status_code=400, detail="invalid_job_status")
    title = str(payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="job_title_required")
    job = repository.create_job(
        company_id=employer.company_id,
        title=title,
        status=status,
        location=payload.get("location"),
        work_model=payload.get("work_model") or payload.get("workModel"),
        employment_type=payload.get("employment_type") or payload.get("employmentType"),
        seniority=payload.get("seniority"),
        department=payload.get("department"),
        salary_min=payload.get("salary_min") or payload.get("salaryMin"),
        salary_max=payload.get("salary_max") or payload.get("salaryMax"),
        salary_currency=payload.get("salary_currency") or payload.get("salaryCurrency") or "TRY",
        description=payload.get("description"),
        required_skills=payload.get("required_skills") or payload.get("requiredSkills") or [],
        preferred_skills=payload.get("preferred_skills") or payload.get("preferredSkills") or [],
        quality_score=int(payload.get("quality_score") or payload.get("qualityScore") or 0),
        created_by_user_id=employer.user_id,
        published_at=datetime.now(UTC).isoformat() if status == "published" else None,
    )
    repository.create_audit_event(
        company_id=employer.company_id,
        actor_user_id=employer.user_id,
        event_type="employer.job.created",
        resource_type="job",
        resource_id=str(job.id),
        after={"title": job.title, "status": job.status},
    )
    return {"ok": True, "job": repository.list_dashboard_jobs(employer.company_id, limit=1)[0]}


# ─────────────────────────── Candidates ───────────────────────────

@router.get("/candidates")
def employer_candidates(
    request: Request,
    response: Response,
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get candidates for employer."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return _paginated_employer_items(
            DEMO_CANDIDATES,
            response=response,
            page=page,
            page_size=page_size,
        )
    return _paginated_employer_items(
        repository.list_dashboard_candidates(employer.company_id),
        response=response,
        page=page,
        page_size=page_size,
    )


@router.get("/candidates/{candidate_id}")
def employer_candidate_detail(
    candidate_id: str,
    request: Request,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get candidate detail."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        candidates = {
            "cand_1": {
                "id": "cand_1", "name": "Ahmet Yılmaz", "headline": "Senior Frontend Developer",
                "email": "ahmet.yilmaz@email.com", "phone": "+90 532 123 45 67",
                "location": "İstanbul", "experience_years": 7,
                "education": "İTÜ Bilgisayar Mühendisliği — 3.72 GPA",
                "skills": ["React", "TypeScript", "Next.js", "GraphQL", "Node.js"],
                "summary": "Frontend geliştirmede 7 yıllık deneyim. React ekosisteminde uzman. Son 3 yılda Next.js ve TypeScript ile ölçeklenebilir uygulamalar geliştirdi.",
                "match_score": 94,
                "match_breakdown": {"skills": 95, "experience": 90, "education": 92, "location": 98, "language": 88},
                "strengths": ["React/TypeScript konusunda güçlü", "7 yıl deneyim", "İstanbul'da", "İngilizce akıcı"],
                "gaps": ["GraphQL deneyimi sınırlı"],
                "ai_note": "İlanın temel gereksinimlerini %95 oranında karşılıyor. Özellikle React ve TypeScript tarafında güçlü bir profil.",
            },
        }
        return {"ok": True, "candidate": candidates.get(candidate_id, candidates["cand_1"])}

    numeric_id = _parse_numeric_id(candidate_id, prefix="cand_")
    if numeric_id is None:
        raise HTTPException(status_code=404, detail="candidate_not_found")
    candidate = repository.get_dashboard_candidate(company_id=employer.company_id, candidate_id=numeric_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate_not_found")
    return {"ok": True, "candidate": candidate}


# ─────────────────────────── Matches ───────────────────────────

@router.get("/matches")
def employer_matches(
    request: Request,
    response: Response,
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get job-candidate matches."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return _paginated_employer_items(
            DEMO_MATCHES,
            response=response,
            page=page,
            page_size=page_size,
        )
    return _paginated_employer_items(
        repository.list_dashboard_matches(employer.company_id),
        response=response,
        page=page,
        page_size=page_size,
    )


# ─────────────────────────── Analytics ───────────────────────────

@router.get("/analytics")
def employer_analytics(
    request: Request,
    period: str = "30d",
    repository: EmployerRepository = Depends(get_employer_repository),
) -> dict:
    """Get analytics data."""
    employer = _require_employer_context(request)
    if employer.is_mock:
        return {
            "ok": True,
            "period": period,
            "kpi": {
                "total_applicants": 127,
                "avg_match_score": 78.4,
                "time_to_hire_days": 18,
                "conversion_rate": 12.5,
            },
            "weekly_applications": [12, 18, 15, 22, 28, 20, 12],
            "source_breakdown": [
                {"source": "LinkedIn", "count": 45, "percentage": 35.4},
                {"source": "NoyTera Match", "count": 38, "percentage": 29.9},
                {"source": "Başvuru Formu", "count": 25, "percentage": 19.7},
                {"source": "Referans", "count": 12, "percentage": 9.4},
                {"source": "Diğer", "count": 7, "percentage": 5.5},
            ],
            "match_distribution": [
                {"range": "90-100%", "count": 12, "color": "#16a34a"},
                {"range": "80-89%", "count": 28, "color": "#22c55e"},
                {"range": "70-79%", "count": 35, "color": "#eab308"},
                {"range": "60-69%", "count": 30, "color": "#f97316"},
                {"range": "<60%", "count": 22, "color": "#ef4444"},
            ],
        }
    return {"ok": True, **repository.get_dashboard_analytics(employer.company_id, period=period)}
