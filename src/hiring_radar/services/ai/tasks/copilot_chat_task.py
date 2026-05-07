from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.ai.contracts import CopilotChatResponse, CopilotGroundingSource
from hiring_radar.services.ai.exceptions import LocalAiGenerationError, LocalAiStructuredOutputError
from hiring_radar.services.ai.grounding import build_copilot_grounding_bundle
from hiring_radar.services.ai.job_analysis_grounding import JobAnalysisGroundingBundle
from hiring_radar.services.ai.job_analysis_response import (
    answer_needs_job_analysis_fallback,
    render_deterministic_job_analysis,
)
from hiring_radar.services.ai.learning_memory import (
    extract_learning_memory_candidates,
    persist_learning_memory_candidates,
)
from hiring_radar.services.ai.prompts.copilot_chat import build_copilot_chat_request
from hiring_radar.services.ai.runtime import LocalAiRuntimeService


@dataclass(slots=True)
class CopilotChatTask:
    runtime: LocalAiRuntimeService

    def run(
        self,
        *,
        repository: HiringRadarRepository,
        subscriber_id: int,
        profile: CandidateProfileAggregate,
        locale: str,
        user_message: str,
        recent_messages: list[tuple[str, str]],
        observed_at: str,
        job_analysis_summary: str = "",
        extra_sources: list[CopilotGroundingSource] | None = None,
        extra_warnings: list[str] | None = None,
        task_mode: str = "general_copilot",
        job_analysis_bundle: JobAnalysisGroundingBundle | None = None,
    ) -> CopilotChatResponse:
        grounding = build_copilot_grounding_bundle(
            repository,
            subscriber_id=subscriber_id,
            profile=profile,
            query=user_message,
            locale=locale,
        )
        request = build_copilot_chat_request(
            config=self.runtime.config,
            locale=locale,
            user_message=user_message,
            recent_messages=recent_messages,
            grounding=grounding,
            task_mode=task_mode,
            job_analysis_summary=job_analysis_summary,
        )

        parsed: CopilotChatResponse | None = None
        runtime_error: Exception | None = None
        try:
            response = self.runtime.generate_structured(request)
            parsed = CopilotChatResponse.model_validate(response.content)
        except (LocalAiGenerationError, LocalAiStructuredOutputError, ValueError) as exc:
            runtime_error = exc

        if parsed is None:
            if task_mode == "job_fit" and job_analysis_bundle is not None:
                rendered = render_deterministic_job_analysis(locale=locale, bundle=job_analysis_bundle)
                parsed = CopilotChatResponse(
                    answer=rendered.answer,
                    follow_up_suggestions=list(rendered.follow_up_suggestions),
                    warnings=["Deterministic job analysis fallback was used because the model response could not be validated."],
                    confidence_band=rendered.confidence_band,
                )
            else:
                raise LocalAiGenerationError(f"Failed to generate grounded copilot response: {runtime_error}") from runtime_error

        parsed.answer = parsed.answer.strip()
        if task_mode == "job_fit" and job_analysis_bundle is not None:
            if answer_needs_job_analysis_fallback(parsed.answer, locale=locale, bundle=job_analysis_bundle):
                rendered = render_deterministic_job_analysis(locale=locale, bundle=job_analysis_bundle)
                parsed.answer = rendered.answer
                parsed.follow_up_suggestions = list(rendered.follow_up_suggestions)
                parsed.confidence_band = rendered.confidence_band
                parsed.warnings = list(parsed.warnings) + [
                    "Job analysis answer was upgraded with deterministic evidence because the model response was too generic."
                ]

        parsed.follow_up_suggestions = self._dedupe_strings(parsed.follow_up_suggestions, limit=3)
        parsed.learned_memory_notes = [item.memory_note for item in repository.list_subscriber_ai_learned_memories(subscriber_id, limit=4)]
        combined_sources = grounding.sources[:6]
        if extra_sources:
            combined_sources.extend(extra_sources[:4])
        parsed.sources = combined_sources[:8]
        combined_warnings = list(parsed.warnings) + list(grounding.warnings)
        if extra_warnings:
            combined_warnings.extend(extra_warnings)
        parsed.warnings = self._dedupe_strings(combined_warnings, limit=8)

        memory_candidates = extract_learning_memory_candidates(prompt=user_message, locale=locale)
        if memory_candidates:
            stored_memories = persist_learning_memory_candidates(
                repository,
                subscriber_id=subscriber_id,
                candidates=memory_candidates,
                observed_at=observed_at,
            )
            parsed.learned_memory_notes = [item.memory_note for item in stored_memories[:4]]

        if not parsed.answer:
            raise LocalAiGenerationError("Grounded copilot response came back empty.")
        return parsed

    @staticmethod
    def _dedupe_strings(values: list[str], *, limit: int) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = str(value or "").strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(cleaned)
            if len(result) >= limit:
                break
        return result
