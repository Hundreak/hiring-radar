from __future__ import annotations

from hiring_radar.api.schemas.profile_contract import (
    CandidateProfileAggregate,
    ProfileCompletenessSummary,
    ProfilePreferencesRecord,
    ProfileTextField,
)
from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiStructuredGenerationResponse
from hiring_radar.services.ai.runtime import LocalAiRuntimeService
from hiring_radar.services.ai.tasks.headline_summary_task import HeadlineSummarySuggestionTask


class StubAdapter:
    def health(self):
        raise AssertionError("health should not be called in this test")

    def generate_structured(self, request):
        return AiStructuredGenerationResponse(
            model=request.model,
            content={
                "headline_options": [
                    {"title": "Embedded Systems Engineer", "rationale": "Clear and focused."},
                    {"title": "Embedded Systems Engineer", "rationale": "Duplicate should be removed."},
                ],
                "summary_options": [
                    {"text": "Experienced in embedded systems and firmware development.", "rationale": "Concise."},
                    {"text": "Experienced in embedded systems and firmware development.", "rationale": "Duplicate."},
                ],
                "warnings": [],
                "confidence_band": "medium",
            },
            response_time_ms=12,
        )


def _build_profile() -> CandidateProfileAggregate:
    return CandidateProfileAggregate(
        id="7",
        user_id="7",
        full_name=ProfileTextField(value="Alice Example"),
        headline=ProfileTextField(value=""),
        summary=ProfileTextField(value=""),
        primary_email=ProfileTextField(value="alice@example.com"),
        phone=ProfileTextField(value=None),
        preferences=ProfilePreferencesRecord(target_roles=["Embedded Systems Engineer"]),
        completeness=ProfileCompletenessSummary(score=55, sections=[]),
        experiences=[],
        education=[],
        languages=[],
        skills=[],
        last_cv_parse=None,
        created_at="2026-04-05T10:00:00Z",
        updated_at="2026-04-05T10:00:00Z",
    )


def test_headline_summary_task_deduplicates_and_limits_results() -> None:
    runtime = LocalAiRuntimeService(
        config=LocalAiRuntimeConfig(enabled=True, default_model="llama3.1:8b"),
        _adapter=StubAdapter(),
    )
    task = HeadlineSummarySuggestionTask(runtime)

    result = task.run(profile=_build_profile(), locale="tr", headline_option_count=3, summary_option_count=3)

    assert len(result.headline_options) == 1
    assert result.headline_options[0].title == "Embedded Systems Engineer"
    assert len(result.summary_options) == 1
