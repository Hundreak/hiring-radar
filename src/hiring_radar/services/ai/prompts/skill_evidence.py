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


def _compact_unique(values: list[str], *, limit: int = 8) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
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


def _profile_projection(profile: CandidateProfileAggregate) -> dict[str, Any]:
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

    skills = []
    for item in profile.skills[:20]:
        skills.append(
            {
                "skill_name": item.skill_name,
                "category": item.category,
                "proficiency_hint": item.proficiency_hint,
                "years_hint": item.years_hint,
                # profile_contract skill records do not guarantee evidence_note.
                "evidence_note": _non_empty(getattr(item, "evidence_note", None)),
            }
        )

    return {
        "headline": _non_empty(profile.headline.value),
        "summary": _non_empty(profile.summary.value),
        "target_roles": _compact_unique(profile.preferences.target_roles, limit=6),
        "skills": skills,
        "recent_experiences": experiences,
    }


def build_skill_evidence_request(
    *,
    profile: CandidateProfileAggregate,
    config: LocalAiRuntimeConfig,
    locale: str = "tr",
    skill_name: str,
    category: str | None = None,
    existing_evidence_note: str | None = None,
    grounding_context: str | None = None,
) -> AiStructuredGenerationRequest:
    locale_normalized = (locale or "tr").strip().lower()
    skill_projection = {
        "skill_name": skill_name.strip(),
        "category": _non_empty(category),
        "existing_evidence_note": _non_empty(existing_evidence_note),
    }
    profile_projection = _profile_projection(profile)

    system_prompt = (
        "You are CoreSift's local skill-evidence assistant. "
        "Your job is to help a candidate describe a real skill more clearly and back it up with credible proof language. "
        "Do not invent tools, projects, employers, certifications, numbers, or achievements. "
        "Use only the provided profile and skill context. "
        "Return valid JSON only."
    )
    user_prompt = (
        f"Language: {locale_normalized}.\n"
        "Task: Improve how this skill is described for matching and recruiter review. "
        "Generate concise, truthful, user-facing suggestions. "
        "Description suggestions should sound professional but grounded. "
        "Evidence note suggestions should be directly usable inside a proof/note field. "
        "Proof ideas should explain what concrete project, output, document, or metric the candidate could add. "
        "Missing signals should call out what weakens credibility.\n"
        f"Skill context: {skill_projection}\n"
        f"Candidate profile projection: {profile_projection}"
    )
    if grounding_context:
        user_prompt += f"\n\nRetrieved evidence:\n{grounding_context}"

    schema = {
        "type": "object",
        "properties": {
            "description_suggestions": {"type": "array", "items": {"type": "string"}},
            "evidence_note_suggestions": {"type": "array", "items": {"type": "string"}},
            "proof_ideas": {"type": "array", "items": {"type": "string"}},
            "missing_signals": {"type": "array", "items": {"type": "string"}},
            "strengthening_note": {"type": ["string", "null"]},
            "warnings": {"type": "array", "items": {"type": "string"}},
            "confidence_band": {"type": "string", "enum": ["low", "medium", "high"]},
        },
        "required": [
            "description_suggestions",
            "evidence_note_suggestions",
            "proof_ideas",
            "missing_signals",
            "strengthening_note",
            "warnings",
            "confidence_band",
        ],
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
