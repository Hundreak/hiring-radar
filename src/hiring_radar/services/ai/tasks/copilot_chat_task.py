from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.services.ai.contracts import CopilotChatResponse
from hiring_radar.services.ai.exceptions import LocalAiGenerationError, LocalAiStructuredOutputError
from hiring_radar.services.ai.grounding import build_copilot_grounding_bundle
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
        )
        try:
            response = self.runtime.generate_structured(request)
            parsed = CopilotChatResponse.model_validate(response.content)
        except (LocalAiGenerationError, LocalAiStructuredOutputError, ValueError) as exc:
            raise LocalAiGenerationError(f"Failed to generate grounded copilot response: {exc}") from exc

        parsed.answer = parsed.answer.strip()
        parsed.follow_up_suggestions = self._dedupe_strings(parsed.follow_up_suggestions, limit=3)
        parsed.learned_memory_notes = [item.memory_note for item in repository.list_subscriber_ai_learned_memories(subscriber_id, limit=4)]
        parsed.sources = grounding.sources[:6]
        parsed.warnings = self._dedupe_strings(parsed.warnings + grounding.warnings, limit=6)

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
