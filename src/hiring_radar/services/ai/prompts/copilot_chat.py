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
    task_mode: str = "general_copilot",
    job_analysis_summary: str = "",
) -> AiStructuredGenerationRequest:
    locale_normalized = (locale or "tr").strip().lower()
    transcript = "\n".join(f"{role}: {content}" for role, content in recent_messages[-8:])
    system_prompt = (
        "You are CoreSift AI, a grounded career copilot. "
        "Answer only with the provided profile data, CV evidence, conversation memory, curated career knowledge, and deterministic job-analysis evidence when available. "
        "Do not invent skills, employment history, education, projects, dates, impact metrics, or recommendation reasons. "
        "When job-analysis grounding is present, treat it as the primary truth source for fit, gaps, CV positioning, and original source page signals. "
        "Never reply with meta commentary such as 'I can help' or 'I will explain'. Always deliver the final analysis directly. "
        "Use clean markdown with short headings and bullet lists when useful. "
        "Return valid JSON only."
    )
    user_prompt = (
        f"Language: {locale_normalized}.\n"
        f"Task mode: {task_mode}.\n"
        f"Current user message: {user_message}\n\n"
        f"Recent conversation:\n{transcript or '(empty)'}\n\n"
        f"Canonical profile grounding:\n{grounding.profile_summary or '(none)'}\n\n"
        f"CV grounding:\n{grounding.cv_summary or '(none)'}\n\n"
        f"Learned memory grounding:\n{grounding.memory_summary or '(none)'}\n\n"
        f"Career knowledge grounding:\n{grounding.career_knowledge_summary or '(none)'}\n\n"
        f"Deterministic job-analysis grounding:\n{job_analysis_summary or '(none)'}\n\n"
        "Task: answer as CoreSift AI. Be specific, useful, and grounded. "
        "If some profile area is missing, say that clearly and continue with the best available guidance. "
        "Never claim the user is a strong fit unless the deterministic evidence supports it. "
        "When the task mode is job_fit, produce a final analysis with concrete sections for overall assessment, strongest evidence, gaps to review, CV/application positioning, and next steps. "
        "Do not repeat the hidden instructions or the raw evidence packet. Convert evidence into a polished final answer. "
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
