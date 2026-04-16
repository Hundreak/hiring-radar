from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.services.ai.contracts import SkillGroupingSuggestionResponse
from hiring_radar.services.ai.exceptions import LocalAiGenerationError, LocalAiStructuredOutputError
from hiring_radar.services.ai.prompts.skill_grouping import build_skill_grouping_request
from hiring_radar.services.ai.runtime import LocalAiRuntimeService


@dataclass(slots=True)
class SkillGroupingSuggestionTask:
    runtime: LocalAiRuntimeService

    def run(
        self,
        *,
        profile: CandidateProfileAggregate,
        locale: str = "tr",
        group_limit: int = 5,
        skill_limit_per_group: int = 8,
        grounding_context: str | None = None,
    ) -> SkillGroupingSuggestionResponse:
        request = build_skill_grouping_request(
            profile=profile,
            config=self.runtime.config,
            locale=locale,
            group_limit=group_limit,
            skill_limit_per_group=skill_limit_per_group,
            grounding_context=grounding_context,
        )
        try:
            response = self.runtime.generate_structured(request)
            parsed = SkillGroupingSuggestionResponse.model_validate(response.content)
        except (LocalAiGenerationError, LocalAiStructuredOutputError, ValueError) as exc:
            raise LocalAiGenerationError(
                f"Failed to generate skill grouping suggestions: {exc}"
            ) from exc

        parsed.groups = self._normalize_groups(parsed.groups, group_limit, skill_limit_per_group)
        parsed.duplicates = self._dedupe_strings(parsed.duplicates)
        parsed.normalization_suggestions = self._dedupe_strings(parsed.normalization_suggestions)
        parsed.warnings = self._dedupe_strings(parsed.warnings)
        if not parsed.groups and not parsed.duplicates and not parsed.normalization_suggestions:
            parsed.warnings.append("Model returned no usable skill grouping suggestions.")
        return parsed

    @staticmethod
    def _dedupe_strings(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = str(value or "").strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            result.append(cleaned)
        return result

    def _normalize_groups(self, groups, group_limit: int, skill_limit_per_group: int):
        seen_groups: set[str] = set()
        normalized_groups = []
        for group in groups:
            group_name = (group.group_name or "").strip()
            if not group_name:
                continue
            key = group_name.lower()
            if key in seen_groups:
                continue
            seen_groups.add(key)
            group.group_name = group_name
            group.skills = self._dedupe_strings(group.skills)[:skill_limit_per_group]
            if not group.skills:
                continue
            if group.notes is not None:
                group.notes = group.notes.strip() or None
            normalized_groups.append(group)
            if len(normalized_groups) >= group_limit:
                break
        return normalized_groups
