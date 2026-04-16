from __future__ import annotations

from hiring_radar.api.schemas.profile_contract import (
    CandidateProfileAggregate,
    ProfileCompletenessSummary,
    ProfileExperienceRecord,
    ProfilePreferencesRecord,
    ProfileSkillRecord,
    ProfileTextField,
)
from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiStructuredGenerationResponse
from hiring_radar.services.ai.runtime import LocalAiRuntimeService
from hiring_radar.services.ai.tasks.role_focus_task import RoleFocusSuggestionTask


class StubAdapter:
    def health(self):
        raise AssertionError("health should not be called in this test")

    def generate_structured(self, request):
        return AiStructuredGenerationResponse(
            model=request.model,
            content={
                "role_suggestions": [
                    {
                        "role_name": "Embedded Systems Engineer",
                        "fit_reason": "Strong embedded and firmware focus.",
                        "missing_signals": ["RTOS depth", "English CV headline"],
                        "priority": 2,
                    },
                    {
                        "role_name": "Firmware Engineer",
                        "fit_reason": "Hands-on low-level systems work is visible.",
                        "missing_signals": ["Public project examples"],
                        "priority": 1,
                    },
                    {
                        "role_name": "Embedded Systems Engineer",
                        "fit_reason": "Duplicate should be removed.",
                        "missing_signals": [],
                        "priority": 3,
                    },
                ],
                "warnings": [],
            },
            response_time_ms=11,
        )


def _build_profile() -> CandidateProfileAggregate:
    return CandidateProfileAggregate(
        id="7",
        user_id="7",
        full_name=ProfileTextField(value="Alice Example"),
        headline=ProfileTextField(value="Embedded Engineer"),
        summary=ProfileTextField(value="Firmware and embedded systems background."),
        primary_email=ProfileTextField(value="alice@example.com"),
        phone=ProfileTextField(value=None),
        preferences=ProfilePreferencesRecord(target_roles=["Embedded Engineer", "Firmware Engineer"]),
        completeness=ProfileCompletenessSummary(score=61, sections=[]),
        experiences=[
            ProfileExperienceRecord(
                title="Embedded Engineer",
                company_name="Acme",
                description="Worked on MCU firmware and device integrations.",
            )
        ],
        education=[],
        languages=[],
        skills=[
            ProfileSkillRecord(skill_name="C"),
            ProfileSkillRecord(skill_name="STM32"),
            ProfileSkillRecord(skill_name="Embedded Linux"),
        ],
        last_cv_parse=None,
        created_at="2026-04-05T10:00:00Z",
        updated_at="2026-04-05T10:00:00Z",
    )


def test_role_focus_task_deduplicates_sorts_and_limits_results() -> None:
    runtime = LocalAiRuntimeService(
        config=LocalAiRuntimeConfig(enabled=True, default_model="llama3.1:8b"),
        _adapter=StubAdapter(),
    )
    task = RoleFocusSuggestionTask(runtime)

    result = task.run(profile=_build_profile(), locale="tr", suggestion_count=4)

    assert len(result.role_suggestions) == 2
    assert result.role_suggestions[0].role_name == "Firmware Engineer"
    assert result.role_suggestions[0].priority == 1
    assert result.role_suggestions[1].role_name == "Embedded Systems Engineer"
