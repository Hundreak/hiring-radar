from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.services.ai.contracts import RoleFocusSuggestionResponse
from hiring_radar.services.ai.exceptions import LocalAiGenerationError, LocalAiStructuredOutputError
from hiring_radar.services.ai.prompts.role_focus import build_role_focus_request
from hiring_radar.services.ai.runtime import LocalAiRuntimeService


@dataclass(slots=True)
class RoleFocusSuggestionTask:
    runtime: LocalAiRuntimeService

    def run(
        self,
        *,
        profile: CandidateProfileAggregate,
        locale: str = "tr",
        suggestion_count: int = 4,
        grounding_context: str | None = None,
    ) -> RoleFocusSuggestionResponse:
        request = build_role_focus_request(
            profile=profile,
            config=self.runtime.config,
            locale=locale,
            suggestion_count=suggestion_count,
            grounding_context=grounding_context,
        )
        try:
            response = self.runtime.generate_structured(request)
            parsed = RoleFocusSuggestionResponse.model_validate(response.content)
        except (LocalAiGenerationError, LocalAiStructuredOutputError, ValueError) as exc:
            raise LocalAiGenerationError(
                f"Failed to generate role focus suggestions: {exc}"
            ) from exc

        parsed.role_suggestions = self._normalize_role_suggestions(parsed.role_suggestions)[:suggestion_count]
        if not parsed.role_suggestions:
            parsed.warnings.append("Model returned no usable role focus suggestions.")
        return parsed

    @staticmethod
    def _normalize_role_suggestions(items):
        seen: set[str] = set()
        result = []
        ordered = sorted(items, key=lambda item: (item.priority, item.role_name.strip().lower()))
        for item in ordered:
            normalized_name = item.role_name.strip()
            key = normalized_name.lower()
            if not normalized_name or key in seen:
                continue
            seen.add(key)
            item.role_name = normalized_name
            item.fit_reason = item.fit_reason.strip()
            item.missing_signals = [
                signal.strip()
                for signal in item.missing_signals
                if isinstance(signal, str) and signal.strip()
            ][:3]
            result.append(item)
        return result
