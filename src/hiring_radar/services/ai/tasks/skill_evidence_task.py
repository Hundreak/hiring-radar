from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.services.ai.contracts import SkillEvidenceSuggestionResponse
from hiring_radar.services.ai.exceptions import LocalAiGenerationError, LocalAiStructuredOutputError
from hiring_radar.services.ai.prompts.skill_evidence import build_skill_evidence_request
from hiring_radar.services.ai.runtime import LocalAiRuntimeService


@dataclass(slots=True)
class SkillEvidenceSuggestionTask:
    runtime: LocalAiRuntimeService

    def run(
        self,
        *,
        profile: CandidateProfileAggregate,
        locale: str = "tr",
        skill_name: str,
        category: str | None = None,
        existing_evidence_note: str | None = None,
        grounding_context: str | None = None,
    ) -> SkillEvidenceSuggestionResponse:
        request = build_skill_evidence_request(
            profile=profile,
            config=self.runtime.config,
            locale=locale,
            skill_name=skill_name,
            category=category,
            existing_evidence_note=existing_evidence_note,
            grounding_context=grounding_context,
        )

        try:
            response = self.runtime.generate_structured(request)
            parsed = SkillEvidenceSuggestionResponse.model_validate(response.content)
        except (LocalAiGenerationError, LocalAiStructuredOutputError, ValueError) as exc:
            raise LocalAiGenerationError(
                f"Failed to generate skill evidence suggestions: {exc}"
            ) from exc

        parsed.description_suggestions = self._dedupe_strings(parsed.description_suggestions, limit=3)
        parsed.evidence_note_suggestions = self._dedupe_strings(parsed.evidence_note_suggestions, limit=3)
        parsed.proof_ideas = self._dedupe_strings(parsed.proof_ideas, limit=4)
        parsed.missing_signals = self._dedupe_strings(parsed.missing_signals, limit=4)
        if parsed.strengthening_note is not None:
            parsed.strengthening_note = parsed.strengthening_note.strip() or None

        if (
            not parsed.description_suggestions
            and not parsed.evidence_note_suggestions
            and not parsed.proof_ideas
        ):
            parsed.warnings.append("Model returned no usable skill evidence suggestions.")
            parsed.confidence_band = "low"

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
