from __future__ import annotations

from typing import Any

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiChatMessage, AiStructuredGenerationRequest


def _non_empty(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _profile_projection(profile: CandidateProfileAggregate) -> dict[str, Any]:
    experiences = [
        {
            "title": item.title,
            "company": item.company_name,
            "summary": item.description,
            "skills": item.skills_used[:6],
        }
        for item in profile.experiences[:6]
    ]
    education = [
        {
            "institution": item.institution,
            "degree": item.degree,
            "field_of_study": item.field_of_study,
        }
        for item in profile.education[:4]
    ]
    languages = [
        {
            "language": item.language_name,
            "level": item.proficiency_level,
        }
        for item in profile.languages[:6]
    ]
    skills = [item.skill_name for item in profile.skills[:16] if item.skill_name]

    return {
        "full_name": _non_empty(profile.full_name.value),
        "existing_headline": _non_empty(profile.headline.value),
        "existing_summary": _non_empty(profile.summary.value),
        "target_roles": profile.preferences.target_roles[:6],
        "preferred_locations": profile.preferences.preferred_locations[:6],
        "work_modes": [item.value if hasattr(item, "value") else str(item) for item in profile.preferences.work_modes[:4]],
        "skills": skills,
        "experiences": experiences,
        "education": education,
        "languages": languages,
    }


def build_headline_summary_request(
    *,
    profile: CandidateProfileAggregate,
    config: LocalAiRuntimeConfig,
    locale: str = "tr",
    headline_option_count: int = 3,
    summary_option_count: int = 3,
    grounding_context: str | None = None,
) -> AiStructuredGenerationRequest:
    locale_normalized = (locale or "tr").strip().lower()
    projection = _profile_projection(profile)
    system_prompt = (
        "You are CoreSift's local profile writing assistant. "
        "Generate concise, professional, truthful career-writing suggestions. "
        "Do not invent companies, technologies, dates, certificates, or achievements. "
        "Use only the information provided. "
        "Return valid JSON only."
    )
    user_prompt = (
        f"Language: {locale_normalized}.\n"
        f"Headline options requested: {headline_option_count}.\n"
        f"Summary options requested: {summary_option_count}.\n"
        "Task: Improve the candidate's profile headline and short summary. "
        "Each headline must be compact and credible. Each summary must be 2-4 sentences, user-facing, and professional. "
        "Avoid hype, fake metrics, and unsupported claims.\n"
        f"Candidate profile projection: {projection}"
    )
    if grounding_context:
        user_prompt += f"\n\nRetrieved evidence:\n{grounding_context}"
    schema = {
        "type": "object",
        "properties": {
            "headline_options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "rationale": {"type": ["string", "null"]},
                    },
                    "required": ["title"],
                    "additionalProperties": False,
                },
            },
            "summary_options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "rationale": {"type": ["string", "null"]},
                    },
                    "required": ["text"],
                    "additionalProperties": False,
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
            "confidence_band": {
                "type": "string",
                "enum": ["low", "medium", "high"],
            },
        },
        "required": ["headline_options", "summary_options", "warnings", "confidence_band"],
        "additionalProperties": False,
    }
    return AiStructuredGenerationRequest(
        model=config.default_model,
        messages=[
            AiChatMessage(role="system", content=system_prompt),
            AiChatMessage(role="user", content=user_prompt),
        ],
        output_json_schema=schema,
        temperature=0.2,
        max_retries=config.max_retries,
    )
