from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from hiring_radar.services.matching.analysis_quality import build_job_analysis_coverage
from hiring_radar.services.matching.contracts import (
    ExternalSourceInsights,
    JobAnalysisCoverage,
    MatchExplanationBreakdownItem,
    MatchExplanationEvidencePoint,
    MatchExplanationGapItem,
    MatchExplanationPayload,
    MatchScoreComponent,
    RankedJobMatch,
)

_COMPONENT_LABELS: Final[dict[str, str]] = {
    "skill_alignment": "Skill overlap",
    "role_alignment": "Role alignment",
    "seniority_alignment": "Seniority fit",
    "discipline_alignment": "Discipline fit",
    "domain_alignment": "Domain experience fit",
    "location_alignment": "Location fit",
    "experience_alignment": "Experience fit",
    "title_alignment": "Title similarity",
    "responsibility_scope_alignment": "Responsibility scope fit",
    "workplace_alignment": "Workplace preference fit",
    "language_alignment": "Language fit",
    "education_alignment": "Education fit",
}

_EVIDENCE_PRIORITY: Final[tuple[str, ...]] = (
    "skill_alignment",
    "role_alignment",
    "seniority_alignment",
    "domain_alignment",
    "discipline_alignment",
    "location_alignment",
    "experience_alignment",
    "responsibility_scope_alignment",
    "workplace_alignment",
    "title_alignment",
    "language_alignment",
    "education_alignment",
)

_GAP_PRIORITY: Final[tuple[str, ...]] = (
    "skill_alignment",
    "seniority_alignment",
    "responsibility_scope_alignment",
    "experience_alignment",
    "domain_alignment",
    "language_alignment",
    "location_alignment",
    "workplace_alignment",
    "education_alignment",
    "role_alignment",
    "discipline_alignment",
    "title_alignment",
)


@dataclass(slots=True, frozen=True)
class ExplanationGenerator:
    """Builds deterministic, contract-safe match explanations.

    This service converts scoring-engine outputs into a stable payload that can be
    consumed directly by Jobs/Matches APIs and UI surfaces. It intentionally does
    not use any LLM or external inference layer.
    """

    max_breakdown_items: int = 6
    max_evidence_points: int = 4
    max_gap_items: int = 4
    max_top_reasons: int = 3

    def generate_for_ranked_match(self, match: RankedJobMatch) -> MatchExplanationPayload:
        analysis_coverage = build_job_analysis_coverage(match.job, match.job_feature)
        breakdown = self._build_breakdown(match)
        evidence_points = self._build_evidence_points(match, analysis_coverage=analysis_coverage)
        gap_analysis = self._build_gap_analysis(match, analysis_coverage=analysis_coverage)
        top_reasons = self._build_top_reasons(match, evidence_points, gap_analysis, analysis_coverage=analysis_coverage)
        summary = top_reasons[0] if top_reasons else self._build_safe_summary(match)

        return MatchExplanationPayload(
            summary=summary,
            fit_score=match.result.fit_score,
            catalog_score=match.result.catalog_score,
            final_score=match.result.final_score,
            behavioral_affinity_score=match.result.behavioral_affinity_score,
            matched_skill_terms=match.result.matched_skill_terms,
            missing_skill_terms=match.result.missing_skill_terms,
            matched_location_terms=match.result.matched_location_terms,
            matching_score_breakdown=breakdown,
            key_evidence_points=evidence_points,
            gap_analysis=gap_analysis,
            top_reasons=top_reasons,
            analysis_coverage=analysis_coverage,
        )

    def generate_for_legacy_job(
        self,
        *,
        title: str,
        company_name: str,
        matched: bool,
        match_score: int | None,
        matched_keywords: tuple[str, ...],
    ) -> MatchExplanationPayload:
        bounded_score = max(0.0, min(0.78, (match_score or 0) / 100))
        breakdown = (
            MatchExplanationBreakdownItem(
                component_key="legacy_keyword_alignment",
                label="Saved interest overlap",
                weight=1.0,
                raw_score=bounded_score,
                weighted_score=bounded_score,
                impact=self._impact_for_score(bounded_score),
                summary="Fallback scoring uses saved interest overlap until full deterministic job features are available.",
                evidence_terms=matched_keywords[:6],
                missing_terms=(),
            ),
        )
        evidence_points: tuple[MatchExplanationEvidencePoint, ...]
        if matched_keywords:
            evidence_points = (
                MatchExplanationEvidencePoint(
                    code="legacy_keywords_matched",
                    title="Saved interest overlap",
                    detail=(
                        f"The listing '{title}' at {company_name} overlaps with your saved interest areas, including "
                        f"{self._human_join(matched_keywords[:4])}."
                    ),
                    supporting_terms=matched_keywords[:6],
                ),
            )
        else:
            evidence_points = (
                MatchExplanationEvidencePoint(
                    code="legacy_fallback_context",
                    title="Fallback ranking mode",
                    detail="This listing is currently using fallback ranking because full deterministic job-match features are not available yet.",
                    supporting_terms=(),
                ),
            )

        gap_analysis = () if matched else (
            MatchExplanationGapItem(
                code="legacy_keyword_gap",
                title="Limited overlap",
                detail="Saved interest signals show only limited overlap with this listing so the recommendation should be reviewed carefully.",
                severity="medium",
                missing_terms=(),
            ),
        )
        top_reasons = (
            evidence_points[0].detail,
        )
        return MatchExplanationPayload(
            summary=top_reasons[0],
            fit_score=bounded_score,
            catalog_score=0.0,
            final_score=bounded_score,
            behavioral_affinity_score=None,
            matched_skill_terms=matched_keywords,
            missing_skill_terms=(),
            matched_location_terms=(),
            matching_score_breakdown=breakdown,
            key_evidence_points=evidence_points,
            gap_analysis=gap_analysis,
            top_reasons=top_reasons,
            analysis_coverage=JobAnalysisCoverage(
                score=0.18,
                level="limited",
                summary="Legacy fallback mode does not yet have a structured job-content packet.",
                content_sources=("legacy_keyword_overlap",),
                detected_signal_types=("saved_interest_overlap",),
                warning="This fallback explanation is not using the full deterministic job-content analysis path.",
            ),
        )

    def with_external_source_insights(
        self,
        payload: MatchExplanationPayload,
        insights: ExternalSourceInsights,
    ) -> MatchExplanationPayload:
        return MatchExplanationPayload(
            summary=payload.summary,
            fit_score=payload.fit_score,
            catalog_score=payload.catalog_score,
            final_score=payload.final_score,
            behavioral_affinity_score=payload.behavioral_affinity_score,
            matched_skill_terms=payload.matched_skill_terms,
            missing_skill_terms=payload.missing_skill_terms,
            matched_location_terms=payload.matched_location_terms,
            matching_score_breakdown=payload.matching_score_breakdown,
            key_evidence_points=payload.key_evidence_points,
            gap_analysis=payload.gap_analysis,
            top_reasons=payload.top_reasons,
            analysis_coverage=payload.analysis_coverage,
            external_source_insights=insights,
        )

    def _build_breakdown(self, match: RankedJobMatch) -> tuple[MatchExplanationBreakdownItem, ...]:
        ordered = sorted(
            match.result.components,
            key=lambda component: component.weighted_score,
            reverse=True,
        )
        selected = ordered[: self.max_breakdown_items]
        return tuple(
            MatchExplanationBreakdownItem(
                component_key=component.name,
                label=_COMPONENT_LABELS.get(component.name, component.name.replace("_", " ").title()),
                weight=component.weight,
                raw_score=component.raw_score,
                weighted_score=component.weighted_score,
                impact=self._impact_for_score(component.raw_score),
                summary=component.summary,
                evidence_terms=component.matched_terms[:6],
                missing_terms=component.missing_terms[:6],
            )
            for component in selected
        )

    def _build_evidence_points(
        self,
        match: RankedJobMatch,
        *,
        analysis_coverage: JobAnalysisCoverage,
    ) -> tuple[MatchExplanationEvidencePoint, ...]:
        component_map = {component.name: component for component in match.result.components}
        evidence_points: list[MatchExplanationEvidencePoint] = []

        for component_name in _EVIDENCE_PRIORITY:
            component = component_map.get(component_name)
            if component is None or not self._qualifies_for_evidence(component):
                continue
            evidence_point = self._build_evidence_point(component=component, match=match)
            if evidence_point is not None:
                evidence_points.append(evidence_point)
            if len(evidence_points) >= self.max_evidence_points:
                break

        if analysis_coverage.level == "strong":
            verification_point = MatchExplanationEvidencePoint(
                code="job_content_verified",
                title="Job content analyzed clearly",
                detail=(
                    "The score is supported by a strong job-content packet with structured requirements, "
                    "responsibility signals, and enough source material for deterministic analysis."
                ),
                supporting_terms=analysis_coverage.detected_signal_types[:4],
            )
            if len(evidence_points) < self.max_evidence_points:
                evidence_points.append(verification_point)
            elif not any(point.code == "job_content_verified" for point in evidence_points):
                evidence_points[-1] = verification_point

        if evidence_points:
            return tuple(evidence_points)

        fallback_component = max(match.result.components, key=lambda component: component.weighted_score)
        return (
            MatchExplanationEvidencePoint(
                code=f"fallback_{fallback_component.name}",
                title=_COMPONENT_LABELS.get(fallback_component.name, "Deterministic match signal"),
                detail=fallback_component.summary,
                supporting_terms=fallback_component.matched_terms[:4],
            ),
        )

    def _qualifies_for_evidence(self, component: MatchScoreComponent) -> bool:
        if component.raw_score >= 0.55:
            return True

        if (
            component.name == "skill_alignment"
            and len(component.matched_terms) >= 3
            and component.weighted_score >= 0.12
        ):
            return True

        return False


    def _build_gap_analysis(
        self,
        match: RankedJobMatch,
        *,
        analysis_coverage: JobAnalysisCoverage,
    ) -> tuple[MatchExplanationGapItem, ...]:
        component_map = {component.name: component for component in match.result.components}
        gaps: list[MatchExplanationGapItem] = []

        for component_name in _GAP_PRIORITY:
            component = component_map.get(component_name)
            if component is None:
                continue
            gap = self._build_gap_item(component=component, match=match)
            if gap is None:
                continue
            gaps.append(gap)
            if len(gaps) >= self.max_gap_items:
                break

        if analysis_coverage.level == "limited" and len(gaps) < self.max_gap_items:
            gaps.append(
                MatchExplanationGapItem(
                    code="job_content_partial",
                    title="Job content is still partial",
                    detail=analysis_coverage.summary,
                    severity="medium",
                    missing_terms=(),
                )
            )

        return tuple(gaps)

    def _build_top_reasons(
        self,
        match: RankedJobMatch,
        evidence_points: tuple[MatchExplanationEvidencePoint, ...],
        gap_analysis: tuple[MatchExplanationGapItem, ...],
        *,
        analysis_coverage: JobAnalysisCoverage,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        title = match.job.display_title
        company = match.job.display_company_name

        if evidence_points:
            reasons.append(f"{title} at {company} ranks well because {self._lower_first(evidence_points[0].detail)}")
        if len(evidence_points) > 1:
            reasons.append(self._sentence_with_period(evidence_points[1].detail))
        if match.result.behavioral_affinity_score is not None and match.result.behavioral_affinity_score >= 0.6:
            reasons.append(
                "Recent engagement with similar jobs gives this role a measured personalization boost without overriding core fit."
            )
        elif gap_analysis:
            reasons.append(self._sentence_with_period(gap_analysis[0].detail))

        if analysis_coverage.level == "strong":
            reasons.append("The recommendation is grounded in a strong job-content packet rather than title-only overlap.")
        elif analysis_coverage.level == "limited":
            reasons.append("This listing is being ranked from partial job content, so the score should be read a bit more cautiously.")

        cleaned = tuple(dict.fromkeys(self._sentence_with_period(reason) for reason in reasons if reason.strip()))
        if cleaned:
            return cleaned[: self.max_top_reasons]
        return (self._build_safe_summary(match),)

    def _build_safe_summary(self, match: RankedJobMatch) -> str:
        return (
            f"{match.job.display_title} is ranked with deterministic profile-to-job signals across skills, title fit, location, and job quality metadata."
        )

    def _build_evidence_point(
        self,
        *,
        component: MatchScoreComponent,
        match: RankedJobMatch,
    ) -> MatchExplanationEvidencePoint | None:
        matched_terms = component.matched_terms[:6]
        if component.name == "skill_alignment" and matched_terms:
            source_suffix = " from the source-enriched job page" if (
                match.job_feature.external_requirement_terms
                or match.job_feature.external_technology_terms
                or match.job_feature.external_responsibility_terms
            ) else ""
            return MatchExplanationEvidencePoint(
                code="skill_overlap_high",
                title="Strong skill overlap",
                detail=(
                    "Your normalized profile evidence overlaps with core job requirements"
                    f"{source_suffix}, such as {self._human_join(matched_terms[:4])}."
                ),
                supporting_terms=matched_terms,
            )
        if component.name == "role_alignment" and matched_terms:
            return MatchExplanationEvidencePoint(
                code="role_family_match",
                title="Role family match",
                detail=f"The role family aligns with your current target direction, including {self._human_join(matched_terms[:3])}.",
                supporting_terms=matched_terms,
            )
        if component.name == "title_alignment" and matched_terms:
            return MatchExplanationEvidencePoint(
                code="title_similarity_strong",
                title="Title similarity",
                detail=f"The job title meaningfully overlaps with your profile language around {self._human_join(matched_terms[:4])}.",
                supporting_terms=matched_terms,
            )
        if component.name == "discipline_alignment" and matched_terms:
            return MatchExplanationEvidencePoint(
                code="discipline_preference_match",
                title="Discipline fit",
                detail=f"This job sits inside a discipline already reflected in your profile, including {self._human_join(matched_terms[:3])}.",
                supporting_terms=matched_terms,
            )
        if component.name == "location_alignment":
            if matched_terms:
                return MatchExplanationEvidencePoint(
                    code="location_preference_match",
                    title="Location preference fit",
                    detail=f"The listing aligns with your location preferences through {self._human_join(matched_terms[:3])}.",
                    supporting_terms=matched_terms,
                )
            if match.job.workplace_type == "remote" and component.raw_score >= 0.85:
                return MatchExplanationEvidencePoint(
                    code="remote_preference_match",
                    title="Remote preference fit",
                    detail="The remote setup fits the work mode you appear to prefer.",
                    supporting_terms=("remote",),
                )
        if component.name == "workplace_alignment" and matched_terms:
            return MatchExplanationEvidencePoint(
                code="workplace_mode_match",
                title="Workplace mode fit",
                detail=f"The workplace setup is compatible with your profile preferences, especially {self._human_join(matched_terms[:2])}.",
                supporting_terms=matched_terms,
            )
        if component.name == "experience_alignment" and component.raw_score >= 0.8:
            profile_years = component.matched_terms[0] if component.matched_terms else "your experience"
            required_years = component.missing_terms[0] if component.missing_terms else "the stated minimum"
            return MatchExplanationEvidencePoint(
                code="experience_requirement_covered",
                title="Experience coverage",
                detail=f"Your profile shows around {profile_years} years of experience against a job baseline near {required_years} years.",
                supporting_terms=(profile_years, required_years),
            )
        if component.name == "language_alignment" and matched_terms:
            return MatchExplanationEvidencePoint(
                code="language_requirement_covered",
                title="Language coverage",
                detail=f"You already show language capability overlap for {self._human_join(matched_terms[:3])}.",
                supporting_terms=matched_terms,
            )
        if component.name == "education_alignment" and matched_terms:
            return MatchExplanationEvidencePoint(
                code="education_requirement_covered",
                title="Education signal present",
                detail=f"Your education profile supports the role requirement with signals such as {self._human_join(matched_terms[:2])}.",
                supporting_terms=matched_terms,
            )
        if component.name == "seniority_alignment" and component.raw_score >= 0.80:
            profile_seniority = component.matched_terms[0] if component.matched_terms else "your seniority level"
            return MatchExplanationEvidencePoint(
                code="seniority_match",
                title="Seniority level fit",
                detail=f"Your seniority profile ({profile_seniority}) aligns well with the level expected for this role.",
                supporting_terms=component.matched_terms[:2],
            )
        if component.name == "domain_alignment" and matched_terms and component.raw_score >= 0.76:
            return MatchExplanationEvidencePoint(
                code="domain_experience_match",
                title="Domain experience match",
                detail=f"Your experience background overlaps with the job's domain context, including {self._human_join(matched_terms[:3])}.",
                supporting_terms=matched_terms[:4],
            )
        if component.name == "responsibility_scope_alignment" and component.raw_score >= 0.80:
            scope = component.matched_terms[0] if component.matched_terms else "your responsibility scope"
            return MatchExplanationEvidencePoint(
                code="scope_alignment",
                title="Responsibility scope fit",
                detail=f"The ownership and responsibility expectations ({scope}) align with your profile signals.",
                supporting_terms=component.matched_terms[:2],
            )
        return None

    def _build_gap_item(
        self,
        *,
        component: MatchScoreComponent,
        match: RankedJobMatch,
    ) -> MatchExplanationGapItem | None:
        missing_terms = component.missing_terms[:6]
        severity = self._severity_for_score(component.raw_score)
        if component.name == "skill_alignment" and component.raw_score < 0.75:
            # Prefer blocker_terms from the match result if this is a hard blocker
            blocker = match.result.blocker_terms
            if blocker and severity == "high":
                return MatchExplanationGapItem(
                    code="skill_hard_blocker",
                    title="Hard skill blockers",
                    detail=(
                        f"This role has required skills that are not evidenced anywhere in your profile: "
                        f"{self._human_join(blocker[:4])}. These are likely hard screening barriers."
                    ),
                    severity="high",
                    missing_terms=blocker[:6],
                )
            if missing_terms:
                if severity == "medium":
                    detail = (
                        f"The job emphasizes skills not yet clearly visible in your profile, such as "
                        f"{self._human_join(missing_terms[:4])}. Closing this gap would significantly improve fit."
                    )
                else:
                    detail = (
                        f"Some skill areas in the job description are not yet in your profile, "
                        f"including {self._human_join(missing_terms[:4])}."
                    )
                return MatchExplanationGapItem(
                    code="skill_gap_detected",
                    title="Skills to strengthen",
                    detail=detail,
                    severity=severity,
                    missing_terms=missing_terms,
                )
            return None
        if component.name == "seniority_alignment" and component.raw_score < 0.55:
            profile_seniority = component.matched_terms[0] if component.matched_terms else None
            job_seniority = component.missing_terms[0] if component.missing_terms else None
            if job_seniority is not None:
                detail = (
                    f"The job targets a '{job_seniority}' level while your profile shows "
                    f"'{profile_seniority or 'a lower level'}'. "
                    "This gap may raise a hard screening barrier at the resume review stage."
                )
            elif profile_seniority is not None:
                detail = (
                    f"Your seniority profile ('{profile_seniority}') is considerably above the "
                    "level this role is targeting. The role may not offer sufficient scope or "
                    "compensation ceiling."
                )
            else:
                detail = "Seniority expectations appear significantly misaligned between your profile and the role."
            return MatchExplanationGapItem(
                code="seniority_gap_detected",
                title="Seniority mismatch",
                detail=detail,
                severity=severity,
                missing_terms=component.missing_terms[:2],
            )
        if component.name == "experience_alignment" and component.raw_score < 0.7:
            required_years = component.missing_terms[0] if component.missing_terms else "the stated minimum"
            return MatchExplanationGapItem(
                code="experience_gap_detected",
                title="Experience gap to review",
                detail=f"The role appears to ask for around {required_years} years of experience, so this requirement should be reviewed carefully before applying.",
                severity=severity,
                missing_terms=component.missing_terms[:2],
            )
        if component.name == "language_alignment" and missing_terms:
            return MatchExplanationGapItem(
                code="language_requirement_gap",
                title="Language requirement gap",
                detail=f"The description calls out language requirements such as {self._human_join(missing_terms[:3])} that are not clearly backed by your profile yet.",
                severity=severity,
                missing_terms=missing_terms,
            )
        if component.name == "location_alignment" and component.raw_score < 0.45:
            terms = missing_terms or match.job_feature.location_tokens[:4]
            return MatchExplanationGapItem(
                code="location_preference_gap",
                title="Location mismatch risk",
                detail="The job location does not line up cleanly with your current preferred locations.",
                severity=severity,
                missing_terms=terms,
            )
        if component.name == "workplace_alignment" and component.raw_score < 0.45:
            return MatchExplanationGapItem(
                code="workplace_preference_gap",
                title="Workplace mode mismatch",
                detail="The role's workplace setup appears weaker than your stated work mode preference.",
                severity=severity,
                missing_terms=missing_terms,
            )
        if component.name == "education_alignment" and component.raw_score < 0.65 and missing_terms:
            return MatchExplanationGapItem(
                code="education_signal_gap",
                title="Education requirement to verify",
                detail=f"The posting suggests an education level such as {self._human_join(missing_terms[:2])}; confirm whether your background will be interpreted as equivalent.",
                severity=severity,
                missing_terms=missing_terms,
            )
        if component.name == "domain_alignment" and component.raw_score < 0.45 and missing_terms:
            return MatchExplanationGapItem(
                code="domain_experience_gap",
                title="Domain experience gap",
                detail=(
                    f"The job is in a domain context ({self._human_join(missing_terms[:2])}) "
                    "not clearly represented in your current experience background."
                ),
                severity=severity,
                missing_terms=missing_terms,
            )
        if component.name == "responsibility_scope_alignment" and component.raw_score < 0.50:
            profile_scope = component.matched_terms[0] if component.matched_terms else None
            job_scope = component.missing_terms[0] if component.missing_terms else None
            if job_scope is not None and profile_scope is not None:
                detail = (
                    f"The role expects '{job_scope}' level ownership while your profile signals '{profile_scope}'. "
                    "This scope gap may surface as a seniority or leadership concern during screening."
                )
            elif job_scope is not None:
                detail = f"The role expects '{job_scope}' level responsibility scope, which may exceed your current signals."
            else:
                detail = "There is a mismatch between your profile's expected responsibility level and what the job requires."
            return MatchExplanationGapItem(
                code="responsibility_scope_gap",
                title="Responsibility scope mismatch",
                detail=detail,
                severity=severity,
                missing_terms=component.missing_terms[:2],
            )
        if component.name == "role_alignment" and component.raw_score < 0.4 and missing_terms:
            return MatchExplanationGapItem(
                code="role_alignment_gap",
                title="Role direction mismatch",
                detail=f"The role family leans toward {self._human_join(missing_terms[:2])}, which is outside your current profile direction.",
                severity=severity,
                missing_terms=missing_terms,
            )
        return None

    @staticmethod
    def _human_join(terms: tuple[str, ...] | list[str]) -> str:
        cleaned = [term.replace("_", " ") for term in terms if term]
        if not cleaned:
            return "relevant profile evidence"
        if len(cleaned) == 1:
            return cleaned[0]
        if len(cleaned) == 2:
            return f"{cleaned[0]} and {cleaned[1]}"
        return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"

    @staticmethod
    def _impact_for_score(score: float) -> str:
        if score >= 0.75:
            return "strong"
        if score >= 0.45:
            return "moderate"
        return "weak"

    @staticmethod
    def _severity_for_score(score: float) -> str:
        if score < 0.35:
            return "high"
        if score < 0.60:
            return "medium"
        return "low"

    @staticmethod
    def _lower_first(text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return stripped
        return stripped[:1].lower() + stripped[1:]

    @staticmethod
    def _sentence_with_period(text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return stripped
        return stripped if stripped.endswith(".") else f"{stripped}."
