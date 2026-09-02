"""Regression tests for employer-candidate matching engine.

These tests verify directional match scoring, strengths/gaps/risk detection,
and the generic JSON job source adapter.
"""
from __future__ import annotations

from hiring_radar.services.jobs.adapters.generic_json import GenericJsonJobSourceAdapter
from hiring_radar.services.jobs.contracts import JobSourceDefinition, JobSourcePayload
from hiring_radar.services.matching.employer_scoring import (
    EmployerCandidateMatchResult,
    build_employer_candidate_match,
)


def _make_definition(metadata: dict | None = None) -> JobSourceDefinition:
    return JobSourceDefinition(
        source_type="generic_json",
        source_name="test_board",
        account_slug="test",
        company_name="Example Inc",
        base_url="https://example.com/jobs",
        trust_score=0.95,
        metadata=metadata or {},
    )


class TestGenericJsonAdapter:
    """Test generic JSON job source adapter."""

    def test_parse_top_level_list(self):
        adapter = GenericJsonJobSourceAdapter()
        definition = _make_definition()
        payload = JobSourcePayload(
            fetched_url="https://example.com/jobs",
            fetched_at="2026-04-15T00:00:00Z",
            body='[{"id":"123","title":"Backend Engineer","location":"Berlin"}]',
        )
        jobs = adapter.parse_jobs(definition, payload)
        assert len(jobs) == 1
        assert jobs[0].external_job_id == "123"
        assert jobs[0].title == "Backend Engineer"
        assert jobs[0].company_name == "Example Inc"

    def test_parse_nested_jobs_key(self):
        adapter = GenericJsonJobSourceAdapter()
        definition = _make_definition()
        payload = JobSourcePayload(
            fetched_url="https://example.com/jobs",
            fetched_at="2026-04-15T00:00:00Z",
            body='{"jobs":[{"id":"456","title":"Frontend Engineer","location":"Remote"}]}',
        )
        jobs = adapter.parse_jobs(definition, payload)
        assert len(jobs) == 1
        assert jobs[0].external_job_id == "456"

    def test_parse_alternative_list_keys(self):
        adapter = GenericJsonJobSourceAdapter()
        definition = _make_definition()
        for key in ("data", "results", "items", "postings"):
            payload = JobSourcePayload(
                fetched_url="https://example.com/jobs",
                fetched_at="2026-04-15T00:00:00Z",
                body=f'{{"{key}":[{{"id":"1","title":"Role A","location":"A"}}]}}',
            )
            jobs = adapter.parse_jobs(definition, payload)
            assert len(jobs) == 1, f"failed for key {key}"

    def test_skip_invalid_json(self):
        adapter = GenericJsonJobSourceAdapter()
        definition = _make_definition()
        payload = JobSourcePayload(
            fetched_url="https://example.com/jobs",
            fetched_at="2026-04-15T00:00:00Z",
            body="not json",
        )
        jobs = adapter.parse_jobs(definition, payload)
        assert jobs == []

    def test_field_map_override_via_metadata(self):
        adapter = GenericJsonJobSourceAdapter()
        definition = _make_definition(
            metadata={"field_map": {"title": "job_title", "location": "city"}}
        )
        payload = JobSourcePayload(
            fetched_url="https://example.com/jobs",
            fetched_at="2026-04-15T00:00:00Z",
            body='[{"id":"1","job_title":"Data Scientist","city":"London"}]',
        )
        jobs = adapter.parse_jobs(definition, payload)
        assert len(jobs) == 1
        assert jobs[0].title == "Data Scientist"
        assert jobs[0].location_text == "London"

    def test_url_validation(self):
        adapter = GenericJsonJobSourceAdapter()
        definition = _make_definition()
        payload = JobSourcePayload(
            fetched_url="https://example.com/jobs",
            fetched_at="2026-04-15T00:00:00Z",
            body='[{"id":"1","title":"Role","apply_url":"/internal/1","canonical_url":"https://jobs.example.com/1"}]',
        )
        jobs = adapter.parse_jobs(definition, payload)
        assert len(jobs) == 1
        # Relative apply_url rejected, falls back to canonical_url
        assert jobs[0].apply_url == "https://jobs.example.com/1"
        assert jobs[0].canonical_url == "https://jobs.example.com/1"


class TestEmployerCandidateMatch:
    """Test employer-candidate directional match scoring."""

    def test_perfect_match(self):
        result = build_employer_candidate_match(
            job_required_skills=("python", "django"),
            job_seniority="senior",
            job_min_experience_years=5.0,
            job_title="Senior Backend Engineer",
            job_location_text="Berlin",
            job_remote_policy="remote",
            job_role_family="backend",
            candidate_skills=("python", "django", "postgresql"),
            candidate_seniority="senior",
            candidate_experience_years=6.0,
            candidate_preferred_locations=("Berlin",),
            candidate_remote_preference="remote",
            candidate_role_family="backend",
            candidate_headline="Senior Backend Engineer",
        )
        assert isinstance(result, EmployerCandidateMatchResult)
        assert result.match_score >= 0.75
        assert result.overall_fit_band in ("excellent", "strong")
        assert len(result.strengths) > 0
        assert result.location_match is True
        assert result.remote_match is True
        assert result.review_required is False

    def test_underqualified_candidate(self):
        result = build_employer_candidate_match(
            job_required_skills=("python", "django", "kubernetes"),
            job_seniority="senior",
            job_min_experience_years=5.0,
            candidate_skills=("python",),
            candidate_seniority="junior",
            candidate_experience_years=1.0,
            candidate_headline="Junior Developer",
        )
        assert result.match_score < 0.50
        assert result.overall_fit_band in ("weak", "poor")
        assert len(result.gaps) > 0
        assert len(result.risks) > 0
        assert result.review_required is True
        assert "missing_required_skills" in result.review_reasons
        assert result.seniority_delta < 0
        assert result.experience_years_delta < 0

    def test_skill_gap_detection(self):
        result = build_employer_candidate_match(
            job_required_skills=("react", "typescript", "next.js"),
            job_preferred_skills=("tailwind", "storybook"),
            candidate_skills=("react", "typescript"),
        )
        assert result.skill_gap_ratio > 0.0
        assert "next.js" in result.required_skills_missing
        assert "react" in result.required_skills_present

    def test_location_match(self):
        result = build_employer_candidate_match(
            job_location_text="Istanbul, Turkey",
            job_remote_policy="onsite",
            candidate_preferred_locations=("Istanbul",),
        )
        assert result.location_match is True

    def test_location_mismatch_with_remote_friendly(self):
        result = build_employer_candidate_match(
            job_location_text="San Francisco, CA",
            job_remote_policy="remote",
            candidate_preferred_locations=("Berlin",),
            candidate_remote_preference="remote",
        )
        assert result.location_match is True  # remote-friendly
        assert result.remote_match is True

    def test_education_fit(self):
        result = build_employer_candidate_match(
            job_education_level="bachelor",
            candidate_education_level="master",
        )
        assert result.match_score >= 0.0

    def test_language_fit(self):
        result = build_employer_candidate_match(
            job_language_requirements=("english", "turkish"),
            candidate_languages=("english", "turkish", "german"),
        )
        assert result.match_score > 0.0

    def test_empty_profile_review_required(self):
        result = build_employer_candidate_match(
            job_required_skills=("java", "spring"),
            candidate_skills=(),
            candidate_headline=None,
        )
        assert result.review_required is True
        assert "sparse_profile" in result.review_reasons

    def test_fit_band_boundaries(self):
        # Strong (all signals aligned)
        strong = build_employer_candidate_match(
            job_required_skills=("python", "django"),
            job_preferred_skills=("postgresql", "docker"),
            candidate_skills=("python", "django", "postgresql", "docker"),
            candidate_seniority="senior",
            job_seniority="senior",
            candidate_experience_years=8.0,
            job_min_experience_years=5.0,
            job_location_text="Berlin",
            candidate_preferred_locations=("Berlin",),
            job_remote_policy="remote",
            candidate_remote_preference="remote",
            candidate_headline="Senior Python Engineer",
        )
        assert strong.overall_fit_band in ("excellent", "strong")

        # Poor
        poor = build_employer_candidate_match(
            job_required_skills=("rust", "wasm"),
            candidate_skills=("html",),
            candidate_seniority="junior",
            job_seniority="principal",
            candidate_experience_years=0.5,
            job_min_experience_years=10.0,
        )
        assert poor.overall_fit_band == "poor"

    def test_overqualified_not_heavily_penalized(self):
        result = build_employer_candidate_match(
            job_seniority="mid",
            candidate_seniority="principal",
            job_required_skills=("python",),
            candidate_skills=("python",),
            candidate_headline="Principal Engineer",
        )
        assert result.seniority_delta > 0
        assert result.match_score >= 0.30  # Overqualified should not tank score

    def test_required_vs_preferred_skill_weighting(self):
        result = build_employer_candidate_match(
            job_required_skills=("python",),
            job_preferred_skills=("django", "fastapi"),
            candidate_skills=("python", "django"),
        )
        assert result.required_skills_present == ("python",)
        assert result.skill_overlap_ratio > 0.5

    def test_remote_policy_mapping(self):
        mappings = [
            (("remote", "remote"), True),
            (("onsite", "remote"), False),
            (("hybrid", "hybrid"), True),
            (("flexible", "remote"), True),
        ]
        for (job_policy, cand_pref), expected_match in mappings:
            result = build_employer_candidate_match(
                job_remote_policy=job_policy,
                candidate_remote_preference=cand_pref,
            )
            assert result.remote_match is expected_match, f"failed for {job_policy}+{cand_pref}"
