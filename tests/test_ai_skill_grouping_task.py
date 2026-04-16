from __future__ import annotations

from hiring_radar.api.schemas.profile_contract import (
    CandidateProfileAggregate,
    ProfileCompletenessSummary,
    ProfilePreferencesRecord,
    ProfileSkillRecord,
    ProfileTextField,
)
from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiStructuredGenerationResponse
from hiring_radar.services.ai.runtime import LocalAiRuntimeService
from hiring_radar.services.ai.tasks.skill_grouping_task import SkillGroupingSuggestionTask


class StubAdapter:
    def health(self):
        raise AssertionError("health should not be called in this test")

    def generate_structured(self, request):
        return AiStructuredGenerationResponse(
            model=request.model,
            content={
                "groups": [
                    {
                        "group_name": "Embedded & Firmware",
                        "skills": ["C", "STM32", "C", "RTOS"],
                        "notes": "Low-level systems and embedded device work.",
                    },
                    {
                        "group_name": "Software & Backend",
                        "skills": ["Python", "FastAPI", "PostgreSQL"],
                        "notes": "Application and service-layer development.",
                    },
                    {
                        "group_name": "Embedded & Firmware",
                        "skills": ["UART"],
                        "notes": "Duplicate group should be removed.",
                    },
                ],
                "duplicates": ["C / C Language", "STM32 / STM32CubeIDE", "C / C Language"],
                "normalization_suggestions": ["Use a single naming style for STM32-related tools.", "Prefer one canonical label for C."],
                "warnings": [],
            },
            response_time_ms=9,
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
        experiences=[],
        education=[],
        languages=[],
        skills=[
            ProfileSkillRecord(skill_name="C", category="Embedded"),
            ProfileSkillRecord(skill_name="STM32", category="Embedded"),
            ProfileSkillRecord(skill_name="Python", category="Software"),
        ],
        last_cv_parse=None,
        created_at="2026-04-05T10:00:00Z",
        updated_at="2026-04-05T10:00:00Z",
    )


def test_skill_grouping_task_normalizes_groups_and_duplicates() -> None:
    runtime = LocalAiRuntimeService(
        config=LocalAiRuntimeConfig(enabled=True, default_model="llama3.1:8b"),
        _adapter=StubAdapter(),
    )
    task = SkillGroupingSuggestionTask(runtime)

    result = task.run(profile=_build_profile(), locale="tr", group_limit=5, skill_limit_per_group=8)

    assert len(result.groups) == 2
    assert result.groups[0].group_name == "Embedded & Firmware"
    assert result.groups[0].skills == ["C", "STM32", "RTOS"]
    assert result.duplicates == ["C / C Language", "STM32 / STM32CubeIDE"]
