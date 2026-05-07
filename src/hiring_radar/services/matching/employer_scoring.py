"""Employer–candidate matching engine.

Given an employer job posting and a candidate profile (extracted from CV),
produces a directional match score, strengths/weaknesses summary, and risk
indicators. This is the inverse of the subscriber-facing job matching: instead
of scoring jobs for a candidate, we score candidates for a job.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hiring_radar.services.jobs.normalization import _SENIORITY_RANK
from hiring_radar.services.matching.scoring import (
    _clamp,
    _jaccard_similarity,
    _ordered_difference,
    _ordered_intersection,
)


@dataclass(slots=True, frozen=True)
class EmployerCandidateMatchResult:
    """Directional match result from the employer's perspective."""

    match_score: float  # 0.0 – 1.0
    overall_fit_band: str  # excellent | strong | moderate | weak | poor

    # Why this candidate fits (or doesn't)
    strengths: tuple[str, ...] = field(default_factory=tuple)
    gaps: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)

    # Component-level breakdown
    skill_overlap_ratio: float = 0.0
    skill_gap_ratio: float = 0.0
    required_skills_present: tuple[str, ...] = field(default_factory=tuple)
    required_skills_missing: tuple[str, ...] = field(default_factory=tuple)

    seniority_delta: int = 0  # negative = candidate underqualified
    experience_years_delta: float = 0.0  # negative = candidate underexperienced

    location_match: bool = False
    remote_match: bool = False

    # Enrichment signal
    review_required: bool = False
    review_reasons: tuple[str, ...] = field(default_factory=tuple)


# Weights for employer-candidate directional scoring.
# Slightly different from subscriber-facing weights because the employer
# cares more about skill coverage and seniority/experience alignment.
_EMPLOYER_COMPONENT_WEIGHTS: dict[str, float] = {
    "skill_coverage": 0.35,
    "seniority_fit": 0.15,
    "experience_years": 0.12,
    "role_relevance": 0.12,
    "location_fit": 0.10,
    "workplace_fit": 0.08,
    "language_fit": 0.05,
    "education_fit": 0.03,
}

assert abs(sum(_EMPLOYER_COMPONENT_WEIGHTS.values()) - 1.0) < 1e-9


def _safe_lower(value: str | None) -> str:
    return (value or "").lower()


def _parse_year(value: str | int | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _coerce_skill_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(s.strip() for s in value.split(",") if s.strip())
    if isinstance(value, (list, tuple)):
        return tuple(str(s).strip() for s in value if str(s).strip())
    return ()


def _coerce_location_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(s.strip() for s in value.replace(";", ",").split(",") if s.strip())
    if isinstance(value, (list, tuple)):
        return tuple(str(s).strip() for s in value if str(s).strip())
    return ()


def build_employer_candidate_match(
    *,
    job_required_skills: tuple[str, ...] = (),
    job_preferred_skills: tuple[str, ...] = (),
    job_seniority: str | None = None,
    job_min_experience_years: float | None = None,
    job_title: str | None = None,
    job_location_text: str | None = None,
    job_remote_policy: str | None = None,  # remote | hybrid | onsite | flexible
    job_role_family: str | None = None,
    job_domain: str | None = None,
    job_language_requirements: tuple[str, ...] = (),
    job_education_level: str | None = None,
    candidate_skills: tuple[str, ...] = (),
    candidate_seniority: str | None = None,
    candidate_experience_years: float | None = None,
    candidate_preferred_locations: tuple[str, ...] = (),
    candidate_remote_preference: str | None = None,
    candidate_role_family: str | None = None,
    candidate_domain_experience: tuple[str, ...] = (),
    candidate_languages: tuple[str, ...] = (),
    candidate_education_level: str | None = None,
    candidate_headline: str | None = None,
) -> EmployerCandidateMatchResult:
    """Score a candidate against a single employer job posting.

    The function is fully deterministic and requires no external services.
    """
    # Normalize inputs
    job_required_skills = tuple(s.lower() for s in job_required_skills)
    job_preferred_skills = tuple(s.lower() for s in job_preferred_skills)
    candidate_skills = tuple(s.lower() for s in candidate_skills)

    # ---------- Skill coverage ----------
    required_present = _ordered_intersection(job_required_skills, candidate_skills)
    required_missing = _ordered_difference(job_required_skills, candidate_skills)
    preferred_present = _ordered_intersection(job_preferred_skills, candidate_skills)

    total_job_skills = len(job_required_skills) + len(job_preferred_skills)
    if total_job_skills == 0:
        skill_coverage = 0.0
    else:
        required_weight = 0.7
        preferred_weight = 0.3
        required_coverage = len(required_present) / max(len(job_required_skills), 1)
        preferred_coverage = len(preferred_present) / max(len(job_preferred_skills), 1)
        skill_coverage = (
            required_weight * required_coverage + preferred_weight * preferred_coverage
        )

    skill_gap = 1.0 - skill_coverage

    # ---------- Seniority fit ----------
    job_rank = _SENIORITY_RANK.get(job_seniority, 0)
    cand_rank = _SENIORITY_RANK.get(candidate_seniority, 0)
    seniority_delta = cand_rank - job_rank
    if job_rank == 0:
        seniority_fit = 0.0
    else:
        # Overqualified is slightly penalized but not as much as underqualified
        if seniority_delta >= 0:
            seniority_fit = max(0.0, 1.0 - (seniority_delta * 0.08))
        else:
            seniority_fit = max(0.0, 1.0 + (seniority_delta * 0.25))

    # ---------- Experience years ----------
    job_min = job_min_experience_years or 0.0
    cand_years = candidate_experience_years or 0.0
    if job_min <= 0:
        experience_fit = 0.0
    else:
        ratio = cand_years / job_min
        if ratio >= 1.0:
            experience_fit = 1.0
        else:
            experience_fit = _clamp(ratio ** 1.5)
    experience_years_delta = cand_years - job_min

    # ---------- Role relevance ----------
    role_relevance = 0.0
    if job_role_family and candidate_role_family:
        if job_role_family.lower() == candidate_role_family.lower():
            role_relevance = 1.0
        else:
            role_relevance = _jaccard_similarity(
                job_role_family.lower().split(),
                candidate_role_family.lower().split(),
            )

    # ---------- Location fit ----------
    location_match = False
    location_fit = 0.0
    if job_location_text:
        job_locs = _coerce_location_list(job_location_text)
        cand_locs = candidate_preferred_locations
        if cand_locs:
            for jl in job_locs:
                for cl in cand_locs:
                    if jl.lower() in cl.lower() or cl.lower() in jl.lower():
                        location_match = True
                        location_fit = 1.0
                        break
                if location_match:
                    break
        if not location_match and job_remote_policy in ("remote", "flexible"):
            location_fit = 0.6  # Remote-friendly roles are location-agnostic
            location_match = True

    # ---------- Workplace (remote) fit ----------
    remote_match = False
    workplace_fit = 0.0
    if job_remote_policy and candidate_remote_preference:
        mapping = {
            ("remote", "remote"): 1.0,
            ("remote", "hybrid"): 0.7,
            ("hybrid", "hybrid"): 1.0,
            ("hybrid", "remote"): 0.8,
            ("hybrid", "onsite"): 0.5,
            ("onsite", "onsite"): 1.0,
            ("onsite", "hybrid"): 0.6,
            ("onsite", "remote"): 0.0,
            ("flexible", "remote"): 0.9,
            ("flexible", "hybrid"): 0.9,
            ("flexible", "onsite"): 0.7,
        }
        workplace_fit = mapping.get(
            (job_remote_policy.lower(), candidate_remote_preference.lower()), 0.3
        )
        remote_match = workplace_fit >= 0.5

    # ---------- Language fit ----------
    language_fit = 0.0
    if job_language_requirements and candidate_languages:
        cand_lang_set = {l.lower() for l in candidate_languages}
        matches = sum(1 for jl in job_language_requirements if jl.lower() in cand_lang_set)
        language_fit = matches / max(len(job_language_requirements), 1)

    # ---------- Education fit ----------
    education_fit = 0.0
    _EDU_RANK = {"high_school": 1, "associate": 2, "bachelor": 3, "master": 4, "doctorate": 5}
    job_edu_rank = _EDU_RANK.get(job_education_level, 0)
    cand_edu_rank = _EDU_RANK.get(candidate_education_level, 0)
    if job_edu_rank > 0:
        if cand_edu_rank >= job_edu_rank:
            education_fit = 1.0
        else:
            education_fit = max(0.0, cand_edu_rank / job_edu_rank)

    # ---------- Composite score ----------
    weights = _EMPLOYER_COMPONENT_WEIGHTS
    composite = (
        weights["skill_coverage"] * skill_coverage
        + weights["seniority_fit"] * seniority_fit
        + weights["experience_years"] * experience_fit
        + weights["role_relevance"] * role_relevance
        + weights["location_fit"] * location_fit
        + weights["workplace_fit"] * workplace_fit
        + weights["language_fit"] * language_fit
        + weights["education_fit"] * education_fit
    )
    composite = _clamp(composite)

    # ---------- Qualitative bands ----------
    if composite >= 0.85:
        fit_band = "excellent"
    elif composite >= 0.70:
        fit_band = "strong"
    elif composite >= 0.50:
        fit_band = "moderate"
    elif composite >= 0.30:
        fit_band = "weak"
    else:
        fit_band = "poor"

    # ---------- Strengths / Gaps / Risks ----------
    strengths: list[str] = []
    gaps: list[str] = []
    risks: list[str] = []
    review_reasons: list[str] = []

    if len(required_present) >= max(len(job_required_skills) - 1, 1):
        strengths.append("Gerekli becerilerin çoğuna sahip")
    if len(required_missing) == 0 and len(job_required_skills) > 0:
        strengths.append("Tüm gerekli beceriler mevcut")
    if len(required_missing) > 0:
        gaps.append(f"Eksik gerekli beceriler: {', '.join(required_missing[:5])}")
        if len(required_missing) >= max(len(job_required_skills) * 0.5, 2):
            risks.append("Gerekli becerilerin önemli bir kısmı eksik")
            review_reasons.append("missing_required_skills")

    if seniority_delta >= 0:
        if seniority_delta <= 1:
            strengths.append("Kıdem seviyesi uyumlu")
        else:
            strengths.append("Kıdem seviyesi ilanın üzerinde")
    else:
        gaps.append("Kıdem seviyesi ilanın altında")
        if seniority_delta <= -2:
            risks.append("Adayın kıdemi ilan için yeterli olmayabilir")
            review_reasons.append("underqualified_seniority")

    if experience_years_delta >= 0:
        strengths.append("Deneyim yılı gereksinimi karşılanıyor")
    else:
        gaps.append("Deneyim yılı eksik")
        if experience_years_delta < -2:
            risks.append("Adayın deneyimi ilan için önemli ölçüde yetersiz")
            review_reasons.append("underexperienced")

    if location_match:
        strengths.append("Lokasyon uyumu var")
    else:
        gaps.append("Lokasyon uyumu yok")

    if remote_match:
        strengths.append("Uzaktan çalışma tercihi uyumlu")

    if role_relevance >= 0.8:
        strengths.append("Rol ailesi güçlü eşleşme")
    elif role_relevance <= 0.3 and job_role_family:
        gaps.append("Rol ailesi zayıf eşleşme")

    if language_fit >= 0.8:
        strengths.append("Dil gereksinimleri karşılanıyor")
    elif language_fit < 0.5 and job_language_requirements:
        gaps.append("Dil gereksinimleri kısmen eksik")

    # Review flag for OCR / low-confidence extraction
    if not candidate_headline or not candidate_skills:
        review_required = True
        review_reasons.append("sparse_profile")
    else:
        review_required = len(review_reasons) > 0

    return EmployerCandidateMatchResult(
        match_score=round(composite, 4),
        overall_fit_band=fit_band,
        strengths=tuple(strengths),
        gaps=tuple(gaps),
        risks=tuple(risks),
        skill_overlap_ratio=round(skill_coverage, 4),
        skill_gap_ratio=round(skill_gap, 4),
        required_skills_present=tuple(required_present),
        required_skills_missing=tuple(required_missing),
        seniority_delta=seniority_delta,
        experience_years_delta=round(experience_years_delta, 2),
        location_match=location_match,
        remote_match=remote_match,
        review_required=review_required,
        review_reasons=tuple(review_reasons),
    )
