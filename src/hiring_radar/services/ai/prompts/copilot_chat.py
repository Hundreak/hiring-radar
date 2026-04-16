from __future__ import annotations

from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiChatMessage, AiStructuredGenerationRequest
from hiring_radar.services.ai.grounding import CopilotGroundingBundle


def build_copilot_chat_request(
    *,
    config: LocalAiRuntimeConfig,
    locale: str,
    user_message: str,
    recent_messages: list[tuple[str, str]],
    grounding: CopilotGroundingBundle,
) -> AiStructuredGenerationRequest:
    locale_normalized = (locale or "tr").strip().lower()
    transcript = "\n".join(f"{role}: {content}" for role, content in recent_messages[-8:])
    system_prompt = (
        "You are CoreSift AI, a grounded career copilot. "
        "Answer only with the help of provided user profile, CV evidence, conversation memory, and curated career knowledge. "
        "Do not invent education, jobs, projects, dates, or measurable impact. "
        "Prefer practical, truthful, and profile-aware guidance. "
        "Use clean markdown with short headings and bullet lists when useful. "
        "Return valid JSON only."
    )
    user_prompt = (
        f"Language: {locale_normalized}.\n"
        f"Current user message: {user_message}\n\n"
        f"Recent conversation:\n{transcript or '(empty)'}\n\n"
        f"Canonical profile grounding:\n{grounding.profile_summary or '(none)'}\n\n"
        f"CV grounding:\n{grounding.cv_summary or '(none)'}\n\n"
        f"Learned memory grounding:\n{grounding.memory_summary or '(none)'}\n\n"
        f"Career knowledge grounding:\n{grounding.career_knowledge_summary or '(none)'}\n\n"
        "Task: answer as CoreSift AI. Be specific, useful, and grounded. "
        "If some profile area is missing, say that clearly and continue with the best available guidance. "
        "Provide 2-3 concise follow-up suggestions."
    )
    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "follow_up_suggestions": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
            "confidence_band": {"type": "string", "enum": ["low", "medium", "high"]},
        },
        "required": ["answer", "follow_up_suggestions", "warnings", "confidence_band"],
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
