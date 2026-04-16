from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.services.ai.contracts import HeadlineSummarySuggestionResponse
from hiring_radar.services.ai.exceptions import LocalAiGenerationError, LocalAiStructuredOutputError
from hiring_radar.services.ai.prompts.headline_summary import build_headline_summary_request
from hiring_radar.services.ai.runtime import LocalAiRuntimeService


@dataclass(slots=True)
class HeadlineSummarySuggestionTask:
    runtime: LocalAiRuntimeService

    def run(
        self,
        *,
        profile: CandidateProfileAggregate,
        locale: str = "tr",
        headline_option_count: int = 3,
        summary_option_count: int = 3,
        grounding_context: str | None = None,
    ) -> HeadlineSummarySuggestionResponse:
        request = build_headline_summary_request(
            profile=profile,
            config=self.runtime.config,
            locale=locale,
            headline_option_count=headline_option_count,
            summary_option_count=summary_option_count,
            grounding_context=grounding_context,
        )
        try:
            response = self.runtime.generate_structured(request)
            parsed = HeadlineSummarySuggestionResponse.model_validate(response.content)
        except (LocalAiGenerationError, LocalAiStructuredOutputError, ValueError) as exc:
            raise LocalAiGenerationError(
                f"Failed to generate headline/summary suggestions: {exc}"
            ) from exc

        parsed.headline_options = self._unique_headlines(parsed.headline_options)[:headline_option_count]
        parsed.summary_options = self._unique_summaries(parsed.summary_options)[:summary_option_count]
        if not parsed.headline_options and not parsed.summary_options:
            parsed.warnings.append("Model returned no usable suggestion content.")
            parsed.confidence_band = "low"
        return parsed

    @staticmethod
    def _unique_headlines(items):
        seen: set[str] = set()
        result = []
        for item in items:
            normalized = item.title.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            item.title = item.title.strip()
            result.append(item)
        return result

    @staticmethod
    def _unique_summaries(items):
        seen: set[str] = set()
        result = []
        for item in items:
            normalized = item.text.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            item.text = item.text.strip()
            result.append(item)
        return result
