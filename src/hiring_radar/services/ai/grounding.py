from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.api.schemas.profile_contract import CandidateProfileAggregate
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import (
    CareerKnowledgeDocument,
    SubscriberAiLearnedMemory,
    SubscriberCvUpload,
)
from hiring_radar.services.ai.career_knowledge import (
    ensure_foundation_career_knowledge,
    search_career_knowledge,
)
from hiring_radar.services.ai.contracts import CopilotGroundingSource


@dataclass(slots=True, frozen=True)
class CopilotGroundingBundle:
    profile_summary: str
    cv_summary: str
    memory_summary: str
    career_knowledge_summary: str
    sources: list[CopilotGroundingSource]
    warnings: list[str]


def _compact_profile_summary(profile: CandidateProfileAggregate) -> str:
    lines: list[str] = []
    if profile.headline.value:
        lines.append(f"Headline: {profile.headline.value}")
    if profile.summary.value:
        lines.append(f"Summary: {profile.summary.value}")
    if profile.preferences.target_roles:
        lines.append("Target roles: " + ", ".join(profile.preferences.target_roles[:5]))
    if profile.skills:
        lines.append("Skills: " + ", ".join(item.skill_name for item in profile.skills[:10] if item.skill_name))
    if profile.experiences:
        top_roles = []
        for item in profile.experiences[:4]:
            line = item.title
            if item.company_name:
                line += f" @ {item.company_name}"
            if item.description:
                line += f" — {item.description}"
            top_roles.append(line)
        lines.append("Experiences: " + " | ".join(top_roles))
    return "\n".join(lines)


def _select_cv_excerpt(cv_upload: SubscriberCvUpload | None, query: str) -> tuple[str, str | None]:
    if cv_upload is None or not (cv_upload.extracted_text or "").strip():
        return "", None
    text = " ".join((cv_upload.extracted_text or "").split())
    excerpt = text[:800]
    lowered_text = text.lower()
    for term in {part.lower() for part in query.split() if len(part) >= 4}:
        idx = lowered_text.find(term)
        if idx >= 0:
            start = max(0, idx - 180)
            end = min(len(text), idx + 420)
            excerpt = text[start:end]
            break
    if len(excerpt) < len(text):
        excerpt = excerpt.rstrip() + "..."
    return excerpt, cv_upload.original_filename


def _memory_summary(memories: list[SubscriberAiLearnedMemory]) -> str:
    if not memories:
        return ""
    return "\n".join(f"- {item.memory_note}" for item in memories[:5])


def build_copilot_grounding_bundle(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    profile: CandidateProfileAggregate,
    query: str,
    locale: str,
) -> CopilotGroundingBundle:
    warnings: list[str] = []
    sources: list[CopilotGroundingSource] = []

    ensure_foundation_career_knowledge(repository, updated_at=profile.updated_at)

    profile_summary = _compact_profile_summary(profile)
    if profile_summary:
        sources.append(
            CopilotGroundingSource(
                label="Canonical profile",
                source_type="profile",
                title="Structured profile aggregate",
                snippet=profile_summary[:220],
                trust_level="canonical",
                freshness_label="live",
            )
        )

    latest_cv = repository.get_latest_subscriber_cv_upload(subscriber_id)
    cv_excerpt, cv_title = _select_cv_excerpt(latest_cv, query)
    if cv_excerpt:
        sources.append(
            CopilotGroundingSource(
                label="CV retrieval",
                source_type="cv",
                title=cv_title,
                snippet=cv_excerpt[:220],
                trust_level="user_document",
                freshness_label="latest_upload",
            )
        )
    else:
        warnings.append("No parsed CV text was available for grounding.")

    memories = repository.list_subscriber_ai_learned_memories(subscriber_id, limit=6)
    memory_summary = _memory_summary(memories)
    if memory_summary:
        sources.append(
            CopilotGroundingSource(
                label="Learned conversation memory",
                source_type="memory",
                title="Conversation-derived signals",
                snippet=memory_summary[:220],
                trust_level="learned",
                freshness_label="rolling",
            )
        )

    knowledge_matches = search_career_knowledge(repository, query=query, locale=locale, limit=3)
    career_knowledge_lines: list[str] = []
    for match in knowledge_matches:
        document: CareerKnowledgeDocument = match.document
        career_knowledge_lines.append(f"{document.title}: {match.snippet}")
        sources.append(
            CopilotGroundingSource(
                label="Career knowledge",
                source_type="career_knowledge",
                title=document.title,
                snippet=match.snippet,
                trust_level=document.trust_level,
                freshness_label=document.freshness_label,
            )
        )

    return CopilotGroundingBundle(
        profile_summary=profile_summary,
        cv_summary=cv_excerpt,
        memory_summary=memory_summary,
        career_knowledge_summary="\n".join(career_knowledge_lines),
        sources=sources,
        warnings=warnings,
    )
