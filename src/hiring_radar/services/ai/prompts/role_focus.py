from __future__ import annotations

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiChatMessage, AiStructuredGenerationRequest


def _compact_list(values: list[str], *, limit: int = 8) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
        if len(result) >= limit:
            break
    return result


def _profile_projection(profile: CandidateProfileAggregate) -> dict[str, object]:
    experiences = []
    for item in profile.experiences[:4]:
        experiences.append(
            {
                "title": item.title,
                "company_name": item.company_name,
                "description": item.description,
                "skills_used": item.skills_used[:8],
                "is_current": item.is_current,
            }
        )

    education = []
    for item in profile.education[:3]:
        education.append(
            {
                "institution": item.institution,
                "degree": item.degree,
                "field_of_study": item.field_of_study,
            }
        )

    skills = _compact_list([item.skill_name for item in profile.skills], limit=16)
    target_roles = _compact_list(profile.preferences.target_roles, limit=8)
    preferred_locations = _compact_list(profile.preferences.preferred_locations, limit=6)
    work_modes = [str(value.value if hasattr(value, "value") else value) for value in profile.preferences.work_modes[:4]]

    return {
        "full_name": profile.full_name.value,
        "headline": profile.headline.value,
        "summary": profile.summary.value,
        "target_roles": target_roles,
        "preferred_locations": preferred_locations,
        "work_modes": work_modes,
        "skills": skills,
        "experiences": experiences,
        "education": education,
        "languages": [item.language_name for item in profile.languages[:6]],
        "completeness_score": profile.completeness.score,
    }


def build_role_focus_request(
    *,
    profile: CandidateProfileAggregate,
    config: LocalAiRuntimeConfig,
    locale: str = "tr",
    suggestion_count: int = 4,
    grounding_context: str | None = None,
) -> AiStructuredGenerationRequest:
    locale_normalized = (locale or "tr").strip().lower()
    projection = _profile_projection(profile)
    system_prompt = (
        "You are CoreSift's local role-focus assistant. "
        "Infer realistic career role directions from the candidate profile. "
        "Do not invent experience, certifications, industries, tools, or achievements. "
        "Use only the provided profile data. "
        "Return valid JSON only."
    )
    user_prompt = (
        f"Language: {locale_normalized}.\n"
        f"Role suggestions requested: {suggestion_count}.\n"
        "Task: Recommend the most credible role focuses for this candidate. "
        "Each role suggestion must include a short fit reason, 0-3 missing signals, and a priority where 1 is most relevant. "
        "Prefer role names the candidate could honestly pursue now or with modest profile strengthening.\n"
        f"Candidate profile projection: {projection}"
    )
    if grounding_context:
        user_prompt += f"\n\nRetrieved evidence:\n{grounding_context}"
    schema = {
        "type": "object",
        "properties": {
            "role_suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role_name": {"type": "string"},
                        "fit_reason": {"type": "string"},
                        "missing_signals": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                    },
                    "required": ["role_name", "fit_reason", "missing_signals", "priority"],
                    "additionalProperties": False,
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["role_suggestions", "warnings"],
        "additionalProperties": False,
    }
    return AiStructuredGenerationRequest(
        model=config.default_model,
        messages=[
            AiChatMessage(role="system", content=system_prompt),
            AiChatMessage(role="user", content=user_prompt),
        ],
        output_json_schema=schema,
        temperature=0.15,
        max_retries=config.max_retries,
    )
