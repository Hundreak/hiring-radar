"""Employer dashboard router — mock data endpoints for the employer UI."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from hiring_radar.api.dependencies import get_db

router = APIRouter(prefix="/employer", tags=["employer"])


def _require_employer(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "employer":
        raise HTTPException(status_code=401, detail="unauthorized")
    return user


# ─────────────────────────── Dashboard ───────────────────────────

@router.get("/dashboard/stats")
def dashboard_stats(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get employer dashboard statistics."""
    _require_employer(request)
    return {
        "ok": True,
        "stats": {
            "active_jobs": 5,
            "total_applications": 127,
            "pending_reviews": 23,
            "avg_match_score": 78.4,
            "active_jobs_delta": +2,
            "applications_delta": +15,
            "pending_delta": -5,
            "match_score_delta": +3.2,
        },
    }


@router.get("/dashboard/recent-jobs")
def dashboard_recent_jobs(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get recent job postings for dashboard."""
    _require_employer(request)
    return {
        "ok": True,
        "items": [
            {
                "id": "job_1",
                "title": "Senior Frontend Engineer",
                "department": "Engineering",
                "location": "İstanbul (Hybrid)",
                "status": "active",
                "applicants": 34,
                "match_avg": 82.5,
                "posted_at": "2026-05-01",
            },
            {
                "id": "job_2",
                "title": "Backend Developer",
                "department": "Engineering",
                "location": "Remote",
                "status": "active",
                "applicants": 28,
                "match_avg": 75.3,
                "posted_at": "2026-04-28",
            },
            {
                "id": "job_3",
                "title": "Product Manager",
                "department": "Product",
                "location": "Ankara",
                "status": "paused",
                "applicants": 15,
                "match_avg": 68.9,
                "posted_at": "2026-04-20",
            },
            {
                "id": "job_4",
                "title": "DevOps Engineer",
                "department": "Infrastructure",
                "location": "İstanbul",
                "status": "active",
                "applicants": 19,
                "match_avg": 71.2,
                "posted_at": "2026-04-15",
            },
            {
                "id": "job_5",
                "title": "Data Scientist",
                "department": "Data",
                "location": "Remote",
                "status": "closed",
                "applicants": 42,
                "match_avg": 79.8,
                "posted_at": "2026-04-01",
            },
        ],
    }


@router.get("/dashboard/top-candidates")
def dashboard_top_candidates(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get top matched candidates for dashboard."""
    _require_employer(request)
    return {
        "ok": True,
        "items": [
            {
                "id": "cand_1",
                "name": "Ahmet Yılmaz",
                "headline": "Senior Frontend Developer",
                "match_score": 94,
                "skills": ["React", "TypeScript", "Next.js"],
                "experience_years": 7,
                "location": "İstanbul",
            },
            {
                "id": "cand_2",
                "name": "Merve Kaya",
                "headline": "Full Stack Engineer",
                "match_score": 89,
                "skills": ["Node.js", "Python", "AWS"],
                "experience_years": 5,
                "location": "Ankara",
            },
            {
                "id": "cand_3",
                "name": "Can Demir",
                "headline": "DevOps Engineer",
                "match_score": 86,
                "skills": ["Kubernetes", "Docker", "CI/CD"],
                "experience_years": 6,
                "location": "İzmir",
            },
            {
                "id": "cand_4",
                "name": "Elif Şahin",
                "headline": "Product Manager",
                "match_score": 81,
                "skills": ["Agile", "Scrum", "Analytics"],
                "experience_years": 4,
                "location": "İstanbul",
            },
        ],
    }


@router.get("/dashboard/activity")
def dashboard_activity(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get recent activity feed."""
    _require_employer(request)
    return {
        "ok": True,
        "items": [
            {"type": "application", "text": "Yeni başvuru: Senior Frontend Engineer pozisyonuna", "time": "5 dakika önce"},
            {"type": "match", "text": "Yüksek eşleşme: Merve Kaya (%89)", "time": "15 dakika önce"},
            {"type": "upload", "text": "CV yüklendi: Can Demir", "time": "1 saat önce"},
            {"type": "job", "text": "İlan yayınlandı: Backend Developer", "time": "2 saat önce"},
            {"type": "review", "text": "Değerlendirme tamamlandı: 5 aday", "time": "3 saat önce"},
        ],
    }


# ─────────────────────────── Jobs ───────────────────────────

@router.get("/jobs")
def employer_jobs(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
    status: str | None = None,
) -> dict:
    """Get employer's job postings."""
    _require_employer(request)
    jobs = [
        {"id": "job_1", "title": "Senior Frontend Engineer", "department": "Engineering", "location": "İstanbul (Hybrid)", "status": "active", "applicants": 34, "match_avg": 82.5, "posted_at": "2026-05-01"},
        {"id": "job_2", "title": "Backend Developer", "department": "Engineering", "location": "Remote", "status": "active", "applicants": 28, "match_avg": 75.3, "posted_at": "2026-04-28"},
        {"id": "job_3", "title": "Product Manager", "department": "Product", "location": "Ankara", "status": "paused", "applicants": 15, "match_avg": 68.9, "posted_at": "2026-04-20"},
        {"id": "job_4", "title": "DevOps Engineer", "department": "Infrastructure", "location": "İstanbul", "status": "active", "applicants": 19, "match_avg": 71.2, "posted_at": "2026-04-15"},
        {"id": "job_5", "title": "Data Scientist", "department": "Data", "location": "Remote", "status": "closed", "applicants": 42, "match_avg": 79.8, "posted_at": "2026-04-01"},
        {"id": "job_6", "title": "UI/UX Designer", "department": "Design", "location": "İstanbul", "status": "active", "applicants": 12, "match_avg": 65.4, "posted_at": "2026-05-03"},
    ]
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    return {"ok": True, "items": jobs}


@router.post("/jobs")
def employer_create_job(
    payload: dict,
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Create a new job posting."""
    _require_employer(request)
    return {
        "ok": True,
        "job": {
            "id": f"job_{datetime.now(timezone.utc).timestamp()}",
            "title": payload.get("title", ""),
            "department": payload.get("department", ""),
            "location": payload.get("location", ""),
            "status": "active",
            "applicants": 0,
            "match_avg": 0,
            "posted_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
    }


# ─────────────────────────── Candidates ───────────────────────────

@router.get("/candidates")
def employer_candidates(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get candidates for employer."""
    _require_employer(request)
    return {
        "ok": True,
        "items": [
            {"id": "cand_1", "name": "Ahmet Yılmaz", "headline": "Senior Frontend Developer", "match_score": 94, "skills": ["React", "TypeScript", "Next.js", "GraphQL"], "experience_years": 7, "location": "İstanbul", "education": "İTÜ Bilgisayar Mühendisliği", "status": "new"},
            {"id": "cand_2", "name": "Merve Kaya", "headline": "Full Stack Engineer", "match_score": 89, "skills": ["Node.js", "Python", "AWS", "PostgreSQL"], "experience_years": 5, "location": "Ankara", "education": "ODTÜ Bilgisayar Mühendisliği", "status": "reviewed"},
            {"id": "cand_3", "name": "Can Demir", "headline": "DevOps Engineer", "match_score": 86, "skills": ["Kubernetes", "Docker", "CI/CD", "Terraform"], "experience_years": 6, "location": "İzmir", "education": "Ege Üniversitesi", "status": "shortlisted"},
            {"id": "cand_4", "name": "Elif Şahin", "headline": "Product Manager", "match_score": 81, "skills": ["Agile", "Scrum", "Analytics", "Figma"], "experience_years": 4, "location": "İstanbul", "education": "Boğaziçi Üniversitesi", "status": "new"},
            {"id": "cand_5", "name": "Burak Özdemir", "headline": "Backend Developer", "match_score": 76, "skills": ["Java", "Spring Boot", "Microservices"], "experience_years": 4, "location": "İstanbul", "education": "İTÜ", "status": "reviewed"},
            {"id": "cand_6", "name": "Zeynep Aydın", "headline": "Data Scientist", "match_score": 73, "skills": ["Python", "ML", "TensorFlow", "SQL"], "experience_years": 3, "location": "Ankara", "education": "Hacettepe", "status": "new"},
            {"id": "cand_7", "name": "Emre Kılıç", "headline": "Mobile Developer", "match_score": 68, "skills": ["React Native", "iOS", "Android"], "experience_years": 5, "location": "İzmir", "education": "Ege Üniversitesi", "status": "reviewed"},
            {"id": "cand_8", "name": "Selin Yıldız", "headline": "UI/UX Designer", "match_score": 65, "skills": ["Figma", "Adobe XD", "Prototyping"], "experience_years": 3, "location": "İstanbul", "education": "Mimar Sinan", "status": "new"},
        ],
    }


@router.get("/candidates/{candidate_id}")
def employer_candidate_detail(
    candidate_id: str,
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get candidate detail."""
    _require_employer(request)
    # Mock detail — in production, fetch from DB
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
    candidate = candidates.get(candidate_id, candidates["cand_1"])
    return {"ok": True, "candidate": candidate}


# ─────────────────────────── Matches ───────────────────────────

@router.get("/matches")
def employer_matches(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
) -> dict:
    """Get job-candidate matches."""
    _require_employer(request)
    return {
        "ok": True,
        "items": [
            {"id": "match_1", "candidate_id": "cand_1", "candidate_name": "Ahmet Yılmaz", "job_id": "job_1", "job_title": "Senior Frontend Engineer", "match_score": 94, "breakdown": {"skills": 95, "experience": 90, "education": 92, "location": 98, "language": 88}},
            {"id": "match_2", "candidate_id": "cand_2", "candidate_name": "Merve Kaya", "job_id": "job_2", "job_title": "Backend Developer", "match_score": 89, "breakdown": {"skills": 88, "experience": 85, "education": 90, "location": 80, "language": 92}},
            {"id": "match_3", "candidate_id": "cand_3", "candidate_name": "Can Demir", "job_id": "job_4", "job_title": "DevOps Engineer", "match_score": 86, "breakdown": {"skills": 90, "experience": 82, "education": 78, "location": 85, "language": 80}},
            {"id": "match_4", "candidate_id": "cand_4", "candidate_name": "Elif Şahin", "job_id": "job_3", "job_title": "Product Manager", "match_score": 81, "breakdown": {"skills": 78, "experience": 75, "education": 88, "location": 85, "language": 90}},
        ],
    }


# ─────────────────────────── Analytics ───────────────────────────

@router.get("/analytics")
def employer_analytics(
    request: Request,
    db: Annotated[dict, Depends(get_db)],
    period: str = "30d",
) -> dict:
    """Get analytics data."""
    _require_employer(request)
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
