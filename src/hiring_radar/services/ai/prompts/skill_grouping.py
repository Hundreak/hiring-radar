from __future__ import annotations

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiChatMessage, AiStructuredGenerationRequest


def _normalized_skills(profile: CandidateProfileAggregate) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in profile.skills:
        name = (item.skill_name or "").strip()
        if not name:
            continue
        lowered = name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(
            {
                "skill_name": name,
                "category": item.category,
                "proficiency_hint": item.proficiency_hint,
                "years_hint": item.years_hint,
            }
        )
        if len(results) >= 24:
            break
    return results


def build_skill_grouping_request(
    *,
    profile: CandidateProfileAggregate,
    config: LocalAiRuntimeConfig,
    locale: str = "tr",
    group_limit: int = 5,
    skill_limit_per_group: int = 8,
    grounding_context: str | None = None,
) -> AiStructuredGenerationRequest:
    locale_normalized = (locale or "tr").strip().lower()
    projection = {
        "headline": profile.headline.value,
        "summary": profile.summary.value,
        "target_roles": profile.preferences.target_roles[:6],
        "skills": _normalized_skills(profile),
    }
    system_prompt = (
        "You are CoreSift's local skill-organization assistant. "
        "Group profile skills into credible, recruiter-friendly clusters. "
        "Do not invent tools, certifications, or experience. "
        "Use only the provided profile data. "
        "Return valid JSON only."
    )
    user_prompt = (
        f"Language: {locale_normalized}.\n"
        f"Maximum skill groups: {group_limit}.\n"
        f"Maximum skills per group: {skill_limit_per_group}.\n"
        "Task: Organize the candidate's skills into useful profile groups, identify likely duplicates, "
        "and suggest normalization improvements. Keep the output concise and user-facing.\n"
        f"Candidate skill projection: {projection}"
    )
    if grounding_context:
        user_prompt += f"\n\nRetrieved evidence:\n{grounding_context}"
    schema = {
        "type": "object",
        "properties": {
            "groups": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string"},
                        "skills": {"type": "array", "items": {"type": "string"}},
                        "notes": {"type": ["string", "null"]},
                    },
                    "required": ["group_name", "skills"],
                    "additionalProperties": False,
                },
            },
            "duplicates": {"type": "array", "items": {"type": "string"}},
            "normalization_suggestions": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["groups", "duplicates", "normalization_suggestions", "warnings"],
        "additionalProperties": False,
    }
    return AiStructuredGenerationRequest(
        model=config.default_model,
        messages=[
            AiChatMessage(role="system", content=system_prompt),
            AiChatMessage(role="user", content=user_prompt),
        ],
        output_json_schema=schema,
        temperature=0.1,
        max_retries=config.max_retries,
    )
