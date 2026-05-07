from __future__ import annotations

from collections.abc import Iterable

from hiring_radar.models import CanonicalJob, CanonicalJobFeature, SubscriberProfileFeature
from hiring_radar.services.jobs.normalization import _SENIORITY_RANK
from hiring_radar.services.matching.analysis_quality import compute_job_analysis_score
from hiring_radar.services.matching.contracts import DeterministicMatchResult, MatchScoreComponent

# ---------------------------------------------------------------------------
# Weight distribution — must sum to exactly 1.0
#
# skill_alignment (0.26): dominant signal; now differentiated via required/preferred
# role_alignment  (0.14): critical — but binary, so other signals must carry load
# seniority       (0.08): hard differentiator; levels-based, steep curve
# discipline      (0.09): second structural dimension
# domain          (0.06): NEW — fintech vs saas vs healthcare vs startup context
# location        (0.09): practical gate signal
# experience      (0.08): years delta against job minimum
# title           (0.05): reduced (role/discipline already carry family signal)
# responsibility  (0.04): NEW — ic vs senior-ic vs tech-lead vs architect vs manager
# workplace       (0.05): remote/hybrid/onsite preference
# language        (0.03): minor, most jobs don't specify
# education       (0.03): minor, rarely determinative
# ---------------------------------------------------------------------------
_COMPONENT_WEIGHTS: dict[str, float] = {
    "skill_alignment":              0.26,
    "role_alignment":               0.14,
    "seniority_alignment":          0.08,
    "discipline_alignment":         0.09,
    "domain_alignment":             0.06,
    "location_alignment":           0.09,
    "experience_alignment":         0.08,
    "title_alignment":              0.05,
    "responsibility_scope_alignment": 0.04,
    "workplace_alignment":          0.05,
    "language_alignment":           0.03,
    "education_alignment":          0.03,
}

assert abs(sum(_COMPONENT_WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

_EDUCATION_RANK: dict[str | None, int] = {
    None: 0,
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "doctorate": 5,
}

# Maps profile seniority + management intent → expected responsibility scope
_SCOPE_RANK: dict[str, int] = {
    "ic": 1,
    "senior-ic": 2,
    "tech-lead": 3,
    "architect": 4,
    "manager": 5,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _ordered_intersection(left: Iterable[str], right: Iterable[str]) -> tuple[str, ...]:
    right_set = set(right)
    return tuple(item for item in left if item in right_set)


def _ordered_difference(left: Iterable[str], right: Iterable[str]) -> tuple[str, ...]:
    right_set = set(right)
    return tuple(item for item in left if item not in right_set)


def _jaccard_similarity(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    intersection = len(left_set & right_set)
    union = len(left_set | right_set)
    return intersection / union if union else 0.0


def _profile_evidence_strength(profile: SubscriberProfileFeature) -> float:
    """Estimate how strongly the profile is evidenced beyond top-level skill tags."""
    score = 0.0
    if profile.experience_evidence_terms:
        score += min(0.5, len(profile.experience_evidence_terms) * 0.025)
    if profile.ownership_signals:
        score += min(0.25, len(profile.ownership_signals) * 0.08)
    if profile.impact_signals:
        score += min(0.25, len(profile.impact_signals) * 0.08)
    return _clamp(score)


def _profile_scope_evidence_terms(profile: SubscriberProfileFeature) -> tuple[str, ...]:
    ordered = tuple(dict.fromkeys((*profile.ownership_signals, *profile.impact_signals)))
    return ordered[:6]


def _job_content_signal_strength(job_feature: CanonicalJobFeature) -> float:
    """Estimate how complete and trustworthy the structured job-content packet is.

    This score is intentionally job-side only. It does not represent profile fit by itself;
    it reflects whether the recommendation is backed by richer deterministic job evidence
    beyond a sparse title/location shell.
    """
    score = 0.0

    if job_feature.required_skill_terms:
        score += min(0.28, len(job_feature.required_skill_terms) * 0.035)
    elif job_feature.skill_terms:
        score += min(0.18, len(job_feature.skill_terms) * 0.02)

    if job_feature.preferred_skill_terms:
        score += min(0.10, len(job_feature.preferred_skill_terms) * 0.025)
    if job_feature.domain_signals:
        score += min(0.10, len(job_feature.domain_signals) * 0.04)
    if job_feature.responsibility_scope is not None:
        score += 0.12
    if job_feature.years_experience_min is not None:
        score += 0.08
    if job_feature.language_requirements:
        score += min(0.06, len(job_feature.language_requirements) * 0.03)

    if (job_feature.external_context_status or "").casefold() not in {"", "unavailable", "error"}:
        score += 0.10
        if job_feature.external_requirement_terms:
            score += min(0.08, len(job_feature.external_requirement_terms) * 0.02)
        if job_feature.external_technology_terms:
            score += min(0.10, len(job_feature.external_technology_terms) * 0.025)
        if job_feature.external_responsibility_terms:
            score += min(0.08, len(job_feature.external_responsibility_terms) * 0.02)

    return _clamp(score)


def _build_component(
    *,
    name: str,
    raw_score: float,
    summary: str,
    matched_terms: tuple[str, ...] = (),
    missing_terms: tuple[str, ...] = (),
) -> MatchScoreComponent:
    weight = _COMPONENT_WEIGHTS[name]
    bounded = _clamp(raw_score)
    return MatchScoreComponent(
        name=name,
        weight=weight,
        raw_score=round(bounded, 4),
        weighted_score=round(bounded * weight, 4),
        summary=summary,
        matched_terms=matched_terms,
        missing_terms=missing_terms,
    )


# ---------------------------------------------------------------------------
# Individual scoring functions
# ---------------------------------------------------------------------------

def _score_skill_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    # Use required_skill_terms when the description had explicit sections;
    # otherwise fall back to the generic skill_terms extracted from the full text.
    required = job_feature.required_skill_terms if job_feature.required_skill_terms else job_feature.skill_terms
    preferred = job_feature.preferred_skill_terms

    if not required and not preferred:
        return _build_component(
            name="skill_alignment",
            raw_score=0.50,
            summary="Job skill requirements are not specified; neutral skill alignment applied.",
        )

    if not profile.skill_terms:
        missing = required[:8] + preferred[:4]
        return _build_component(
            name="skill_alignment",
            raw_score=0.08,
            summary="Profile contains no normalised skill evidence against explicit job requirements.",
            missing_terms=missing,
        )

    # ── Required skills ──────────────────────────────────────────────────
    matched_req: tuple[str, ...] = ()
    missing_req: tuple[str, ...] = ()
    base: float

    hard_blocker_ceiling: float | None = None
    if required:
        matched_req = _ordered_intersection(required, profile.skill_terms)
        missing_req = _ordered_difference(required, profile.skill_terms)
        # Cap denominator at 10 so a very long requirements list doesn't make
        # every profile look weak, but still differentiates better than cap=8.
        req_denom = min(10, len(required))
        req_ratio = len(matched_req) / req_denom
        base = 0.10 + (req_ratio * 0.90)

        # Hard blocker thresholds: cap is enforced AFTER preferred bonus so
        # preferred skills cannot escape a hard-required gap.
        missing_count = len(missing_req)
        if missing_count >= 3:
            hard_blocker_ceiling = 0.30   # 3+ required skills missing → hard blocker
        elif missing_count >= 2:
            hard_blocker_ceiling = 0.52   # 2 required missing → medium blocker
    else:
        base = 0.50

    # ── Preferred skills bonus (max +0.08) ───────────────────────────────
    matched_pref: tuple[str, ...] = ()
    missing_pref: tuple[str, ...] = ()
    if preferred and profile.skill_terms:
        matched_pref = _ordered_intersection(preferred, profile.skill_terms)
        missing_pref = _ordered_difference(preferred, profile.skill_terms)
        pref_denom = min(6, len(preferred))
        if pref_denom > 0:
            pref_bonus = (len(matched_pref) / pref_denom) * 0.08
            base = min(1.0, base + pref_bonus)

    # Bonus for very broad required-skill coverage
    if len(matched_req) > 7:
        base = min(1.0, base + 0.04)

    # Strengthen score when matched skills are actually evidenced in experience descriptions,
    # not only listed in top-level profile skills.
    evidence_strength = _profile_evidence_strength(profile)
    if matched_req and profile.experience_evidence_terms:
        matched_req_evidence = _ordered_intersection(matched_req, profile.experience_evidence_terms)
        evidence_ratio = len(matched_req_evidence) / max(1, len(matched_req))
        if evidence_ratio >= 0.75:
            base = min(1.0, base + 0.06)
            if evidence_strength >= 0.55:
                base = min(1.0, base + 0.02)
        elif evidence_ratio >= 0.45:
            base = min(1.0, base + 0.03)
            if evidence_strength >= 0.65:
                base = min(1.0, base + 0.01)
        elif evidence_ratio == 0 and len(matched_req) >= 2:
            penalty = 0.05 if evidence_strength >= 0.3 else 0.08
            base = max(0.0, base - penalty)
    elif matched_req and len(matched_req) >= 2 and evidence_strength < 0.2:
        base = max(0.0, base - 0.04)

    # Apply hard blocker ceiling last — preferred bonus cannot escape it
    if hard_blocker_ceiling is not None:
        base = min(base, hard_blocker_ceiling)

    all_matched = matched_req + matched_pref
    all_missing = missing_req + missing_pref

    return _build_component(
        name="skill_alignment",
        raw_score=base,
        summary=(
            "Skill overlap scored against required and preferred terms extracted from the job description."
        ),
        matched_terms=all_matched[:12],
        missing_terms=all_missing[:12],
    )


def _score_role_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    role = job_feature.role_family
    if role is None:
        return _build_component(
            name="role_alignment",
            raw_score=0.52,
            summary="Job role family is unspecified; neutral role alignment applied.",
        )
    if role in set(profile.role_families):
        return _build_component(
            name="role_alignment",
            raw_score=1.0,
            summary=f"Role family '{role}' aligns with the subscriber's target profile.",
            matched_terms=(role,),
        )
    if not profile.role_families:
        return _build_component(
            name="role_alignment",
            raw_score=0.42,
            summary="Subscriber role intent is sparse; soft-neutral role alignment applied.",
        )
    return _build_component(
        name="role_alignment",
        raw_score=0.16,
        summary=f"Role family '{role}' does not align with current subscriber intent.",
        missing_terms=(role,),
    )


def _score_seniority_alignment(
    profile: SubscriberProfileFeature,
    job: CanonicalJob,
) -> MatchScoreComponent:
    profile_seniority = profile.seniority_level
    job_seniority = job.seniority

    if profile_seniority is None or job_seniority is None:
        return _build_component(
            name="seniority_alignment",
            raw_score=0.58,
            summary="Seniority level is not explicit on one or both sides; neutral seniority fit applied.",
        )

    profile_rank = _SENIORITY_RANK.get(profile_seniority, 3)
    job_rank = _SENIORITY_RANK.get(job_seniority, 3)
    delta = profile_rank - job_rank

    if delta == 0:
        raw, note = 1.00, "Seniority levels match exactly."
    elif delta == 1:
        raw, note = 0.82, "Subscriber is slightly overqualified for the stated seniority level."
    elif delta == 2:
        raw, note = 0.60, "Subscriber's seniority meaningfully exceeds the role's stated level."
    elif delta > 2:
        raw, note = 0.42, "Subscriber is significantly overqualified; role may not offer sufficient scope."
    elif delta == -1:
        raw, note = 0.72, "Subscriber is slightly below the stated seniority; experience overlap may compensate."
    elif delta == -2:
        raw, note = 0.38, "Subscriber's seniority is below the stated job level by two grades."
    else:
        raw, note = 0.18, "Subscriber's seniority is materially below the stated job level."

    return _build_component(
        name="seniority_alignment",
        raw_score=raw,
        summary=note,
        matched_terms=(profile_seniority,),
        missing_terms=() if delta >= 0 else (job_seniority,),
    )


def _score_discipline_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    discipline = job_feature.job_discipline
    if discipline is None:
        return _build_component(
            name="discipline_alignment",
            raw_score=0.50,
            summary="Job discipline is unspecified; neutral discipline fit applied.",
        )
    if discipline in set(profile.discipline_preferences):
        return _build_component(
            name="discipline_alignment",
            raw_score=1.0,
            summary=f"Discipline '{discipline}' is directly represented in the subscriber profile.",
            matched_terms=(discipline,),
        )
    if not profile.discipline_preferences:
        return _build_component(
            name="discipline_alignment",
            raw_score=0.40,
            summary="Subscriber discipline intent is sparse; soft-neutral discipline fit applied.",
        )
    return _build_component(
        name="discipline_alignment",
        raw_score=0.20,
        summary=f"Discipline '{discipline}' is outside the current subscriber focus.",
        missing_terms=(discipline,),
    )


def _score_domain_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    job_domains = job_feature.domain_signals
    profile_domains = profile.domain_signals

    if not job_domains:
        return _build_component(
            name="domain_alignment",
            raw_score=0.55,
            summary="Job domain context not identified; neutral domain fit applied.",
        )
    if not profile_domains:
        return _build_component(
            name="domain_alignment",
            raw_score=0.46,
            summary="Profile domain experience not identified from experience descriptions.",
        )

    matched = _ordered_intersection(job_domains, profile_domains)
    if matched:
        # Stronger match for multiple overlapping domains
        score = min(1.0, 0.76 + len(matched) * 0.08)
        return _build_component(
            name="domain_alignment",
            raw_score=score,
            summary="Profile domain experience overlaps with job domain context.",
            matched_terms=matched[:4],
        )
    return _build_component(
        name="domain_alignment",
        raw_score=0.22,
        summary="Profile domain signals do not align with the job's domain context.",
        missing_terms=job_domains[:4],
    )


def _profile_to_scope(profile: SubscriberProfileFeature) -> str | None:
    """Map a profile's directly extracted responsibility scope first, then fall back to seniority."""
    if profile.responsibility_scope is not None:
        return profile.responsibility_scope
    seniority = profile.seniority_level
    if seniority is None:
        return None
    rank = _SENIORITY_RANK.get(seniority, 3)
    management = profile.management_preference
    if management is True and rank >= 5:
        return "manager"
    if management is True and rank >= 4:
        return "tech-lead"
    if rank >= 6:
        return "architect"
    if rank >= 5:
        return "tech-lead"
    if rank >= 4:
        return "senior-ic"
    return "ic"


def _score_responsibility_scope_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    job_scope = job_feature.responsibility_scope
    if job_scope is None:
        return _build_component(
            name="responsibility_scope_alignment",
            raw_score=0.56,
            summary="Job responsibility scope not identified from description; neutral fit applied.",
            matched_terms=_profile_scope_evidence_terms(profile),
        )

    profile_scope = _profile_to_scope(profile)
    if profile_scope is None:
        return _build_component(
            name="responsibility_scope_alignment",
            raw_score=0.54,
            summary="Profile responsibility scope cannot be inferred from available signals.",
            matched_terms=_profile_scope_evidence_terms(profile),
        )

    j_rank = _SCOPE_RANK.get(job_scope, 2)
    p_rank = _SCOPE_RANK.get(profile_scope, 2)
    delta = p_rank - j_rank
    evidence_terms = _profile_scope_evidence_terms(profile)

    if delta == 0:
        raw = 1.0
    elif delta == 1:
        raw = 0.82
    elif delta == -1:
        raw = 0.70
    elif abs(delta) == 2:
        raw = 0.44
    else:
        raw = 0.20

    if delta <= 0 and evidence_terms:
        if "architecture" in profile.ownership_signals and job_scope in {"architect", "tech-lead"}:
            raw = min(1.0, raw + 0.08)
        elif "technical_leadership" in profile.ownership_signals and job_scope in {"tech-lead", "manager"}:
            raw = min(1.0, raw + 0.06)
        elif "system_ownership" in profile.ownership_signals and job_scope in {"senior-ic", "tech-lead"}:
            raw = min(1.0, raw + 0.04)

    if delta < 0 and not evidence_terms:
        raw = max(0.0, raw - 0.05)

    return _build_component(
        name="responsibility_scope_alignment",
        raw_score=raw,
        summary=f"Profile scope ({profile_scope}) vs job expected scope ({job_scope}).",
        matched_terms=((profile_scope,) + evidence_terms[:2]),
        missing_terms=() if delta >= 0 else (job_scope,),
    )


def _score_title_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    if not profile.title_tokens or not job_feature.title_tokens:
        return _build_component(
            name="title_alignment",
            raw_score=0.40,
            summary="Title-token evidence is partial; soft-neutral title alignment applied.",
        )
    similarity = _jaccard_similarity(profile.title_tokens, job_feature.title_tokens)
    matched = _ordered_intersection(job_feature.title_tokens, profile.title_tokens)
    raw = 0.20 + min(0.80, similarity * 1.4)
    return _build_component(
        name="title_alignment",
        raw_score=raw,
        summary="Job title overlap computed from normalised title tokens.",
        matched_terms=matched[:10],
    )


def _score_location_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
    job: CanonicalJob,
) -> MatchScoreComponent:
    if not profile.preferred_location_tokens:
        remote_pref = (profile.remote_preference or "").casefold()
        if job.workplace_type == "remote" and remote_pref == "onsite":
            return _build_component(
                name="location_alignment",
                raw_score=0.24,
                summary="Subscriber prefers on-site work while the role is remote.",
            )
        return _build_component(
            name="location_alignment",
            raw_score=0.55,
            summary="Subscriber location preference is not specified; neutral location fit applied.",
        )
    matched = _ordered_intersection(job_feature.location_tokens, profile.preferred_location_tokens)
    if matched:
        return _build_component(
            name="location_alignment",
            raw_score=1.0,
            summary="Job location intersects with subscriber preferred locations.",
            matched_terms=matched[:8],
        )
    remote_pref = (profile.remote_preference or "").casefold()
    if job.workplace_type == "remote" and remote_pref in {"remote", "hybrid", "flexible"}:
        return _build_component(
            name="location_alignment",
            raw_score=0.88,
            summary="Remote-friendly role aligns with the subscriber's remote preference.",
            matched_terms=("remote",),
        )
    return _build_component(
        name="location_alignment",
        raw_score=0.18,
        summary="Job location does not intersect with subscriber location preferences.",
        missing_terms=job_feature.location_tokens[:8],
    )


def _score_workplace_alignment(
    profile: SubscriberProfileFeature,
    job: CanonicalJob,
) -> MatchScoreComponent:
    preference = (profile.remote_preference or "").casefold()
    workplace = (job.workplace_type or "").casefold()
    if not preference or not workplace:
        return _build_component(
            name="workplace_alignment",
            raw_score=0.55,
            summary="Remote/workplace preference data is partial; neutral workplace fit applied.",
        )
    if preference == workplace:
        return _build_component(
            name="workplace_alignment",
            raw_score=1.0,
            summary="Job workplace mode matches the subscriber preference exactly.",
            matched_terms=(workplace,),
        )
    compatible_pairs = {("remote", "hybrid"), ("hybrid", "remote"), ("hybrid", "onsite")}
    if (preference, workplace) in compatible_pairs:
        return _build_component(
            name="workplace_alignment",
            raw_score=0.68,
            summary="Job workplace mode is partially compatible with the subscriber preference.",
            matched_terms=(workplace,),
        )
    return _build_component(
        name="workplace_alignment",
        raw_score=0.18,
        summary="Job workplace mode conflicts with the subscriber preference.",
        missing_terms=(workplace,),
    )


def _score_experience_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    evidence_strength = _profile_evidence_strength(profile)
    if job_feature.years_experience_min is None:
        neutral = 0.60 if evidence_strength >= 0.55 else 0.55
        return _build_component(
            name="experience_alignment",
            raw_score=neutral,
            summary="Job experience requirement is not explicit; profile evidence depth is used as a soft proxy.",
            matched_terms=_profile_scope_evidence_terms(profile),
        )
    if profile.years_experience_total is None:
        neutral = 0.62 if evidence_strength >= 0.55 else 0.48
        return _build_component(
            name="experience_alignment",
            raw_score=neutral,
            summary="Subscriber total years are incomplete; scored from experience-description evidence depth.",
            matched_terms=_profile_scope_evidence_terms(profile),
            missing_terms=(str(job_feature.years_experience_min),),
        )

    delta = profile.years_experience_total - job_feature.years_experience_min
    if delta >= 3:
        score = 1.0
    elif delta >= 1:
        score = 0.90
    elif delta == 0:
        score = 0.80
    elif delta == -1:
        score = 0.52
    elif delta == -2:
        score = 0.30
    else:
        score = 0.14

    if evidence_strength >= 0.6:
        if delta >= 0:
            score = min(1.0, score + 0.03)
        elif delta == -1:
            score = min(1.0, score + 0.08)
    elif evidence_strength < 0.2 and delta <= -1:
        score = max(0.0, score - 0.04)

    return _build_component(
        name="experience_alignment",
        raw_score=score,
        summary="Experience alignment compares subscriber cumulative years with the job minimum requirement and profile evidence depth.",
        matched_terms=(str(profile.years_experience_total), *_profile_scope_evidence_terms(profile)[:2]),
        missing_terms=(str(job_feature.years_experience_min),),
    )


def _score_language_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    if not job_feature.language_requirements:
        return _build_component(
            name="language_alignment",
            raw_score=0.65,
            summary="Job language requirements are not explicit; moderate neutral language fit applied.",
        )
    if not profile.language_capabilities:
        return _build_component(
            name="language_alignment",
            raw_score=0.16,
            summary="Subscriber language capability data is missing while the job requires languages.",
            missing_terms=job_feature.language_requirements[:6],
        )
    matched = _ordered_intersection(job_feature.language_requirements, profile.language_capabilities)
    missing = _ordered_difference(job_feature.language_requirements, profile.language_capabilities)
    ratio = len(matched) / max(1, len(job_feature.language_requirements))
    return _build_component(
        name="language_alignment",
        raw_score=0.18 + (ratio * 0.82),
        summary="Language fit computed from explicit job requirements and subscriber language capabilities.",
        matched_terms=matched[:6],
        missing_terms=missing[:6],
    )


def _score_education_alignment(
    profile: SubscriberProfileFeature,
    job_feature: CanonicalJobFeature,
) -> MatchScoreComponent:
    if job_feature.education_level_hint is None:
        return _build_component(
            name="education_alignment",
            raw_score=0.62,
            summary="Job education requirements are not explicit; neutral education fit applied.",
        )
    if profile.education_level is None:
        return _build_component(
            name="education_alignment",
            raw_score=0.32,
            summary="Subscriber education signal is missing while the job has an explicit education hint.",
            missing_terms=(job_feature.education_level_hint,),
        )
    profile_rank = _EDUCATION_RANK.get(profile.education_level, 0)
    job_rank = _EDUCATION_RANK.get(job_feature.education_level_hint, 0)
    if profile_rank >= job_rank:
        return _build_component(
            name="education_alignment",
            raw_score=1.0,
            summary="Subscriber education level satisfies the job requirement.",
            matched_terms=(profile.education_level,),
        )
    if profile_rank + 1 == job_rank:
        return _build_component(
            name="education_alignment",
            raw_score=0.52,
            summary="Subscriber education level is one step below the stated job requirement.",
            matched_terms=(profile.education_level,),
            missing_terms=(job_feature.education_level_hint,),
        )
    return _build_component(
        name="education_alignment",
        raw_score=0.18,
        summary="Subscriber education level is materially below the stated job requirement.",
        missing_terms=(job_feature.education_level_hint,),
    )


# ---------------------------------------------------------------------------
# Top-level result builder
# ---------------------------------------------------------------------------

def build_match_result(
    *,
    subscriber_id: int,
    profile_feature: SubscriberProfileFeature,
    job: CanonicalJob,
    job_feature: CanonicalJobFeature,
    behavioral_affinity_score: float | None = None,
) -> DeterministicMatchResult:
    components = (
        _score_skill_alignment(profile_feature, job_feature),
        _score_role_alignment(profile_feature, job_feature),
        _score_seniority_alignment(profile_feature, job),
        _score_discipline_alignment(profile_feature, job_feature),
        _score_domain_alignment(profile_feature, job_feature),
        _score_location_alignment(profile_feature, job_feature, job),
        _score_experience_alignment(profile_feature, job_feature),
        _score_title_alignment(profile_feature, job_feature),
        _score_responsibility_scope_alignment(profile_feature, job_feature),
        _score_workplace_alignment(profile_feature, job),
        _score_language_alignment(profile_feature, job_feature),
        _score_education_alignment(profile_feature, job_feature),
    )

    fit_score = round(sum(c.weighted_score for c in components), 4)

    job_content_signal_score = _job_content_signal_strength(job_feature)
    job_analysis_score = compute_job_analysis_score(job, job_feature)
    catalog_score = round(
        _clamp(
            (job.trust_score * 0.22)
            + (job.freshness_score * 0.18)
            + (job_feature.match_readiness_score * 0.33)
            + (job_content_signal_score * 0.12)
            + (job_analysis_score * 0.15)
        ),
        4,
    )

    # Final score: fit remains dominant, but sparse job-content packets should not rank
    # as confidently as listings whose requirements and responsibilities were actually parsed.
    if behavioral_affinity_score is None:
        final_score = round((fit_score * 0.91) + (catalog_score * 0.09), 4)
    else:
        bounded_affinity = _clamp(behavioral_affinity_score)
        final_score = round(
            (fit_score * 0.86) + (catalog_score * 0.09) + (bounded_affinity * 0.05),
            4,
        )

    if job_analysis_score < 0.38:
        final_score = round(final_score * 0.92, 4)
    elif job_analysis_score < 0.52:
        final_score = round(final_score * 0.97, 4)
    elif job_analysis_score >= 0.82:
        final_score = round(min(1.0, final_score + 0.01), 4)

    sorted_components = sorted(components, key=lambda c: c.weighted_score, reverse=True)
    explanation_summary = "; ".join(c.summary for c in sorted_components[:3])

    skill_component = next(c for c in components if c.name == "skill_alignment")
    location_component = next(c for c in components if c.name == "location_alignment")

    # Determine hard blockers: required skills that are completely absent from the profile
    # and caused the skill_alignment score to hit the hard-blocker ceiling (≤0.30).
    required = job_feature.required_skill_terms if job_feature.required_skill_terms else job_feature.skill_terms
    if skill_component.raw_score <= 0.30 and required and profile_feature.skill_terms:
        missing_required = _ordered_difference(required, profile_feature.skill_terms)
        blocker_terms = missing_required[:6]
    elif skill_component.raw_score <= 0.30 and required and not profile_feature.skill_terms:
        blocker_terms = required[:6]
    else:
        blocker_terms = ()

    return DeterministicMatchResult(
        subscriber_id=subscriber_id,
        canonical_job_id=job.id or 0,
        fit_score=fit_score,
        catalog_score=catalog_score,
        final_score=final_score,
        behavioral_affinity_score=behavioral_affinity_score,
        matched=final_score >= 0.55,
        explanation_summary=explanation_summary,
        matched_skill_terms=skill_component.matched_terms,
        missing_skill_terms=skill_component.missing_terms,
        matched_location_terms=location_component.matched_terms,
        components=components,
        blocker_terms=blocker_terms,
    )
