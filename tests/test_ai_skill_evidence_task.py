from __future__ import annotations

from hiring_radar.api.schemas.profile_contract import (
    CandidateProfileAggregate,
    ProfileCompletenessSummary,
    ProfileExperienceRecord,
    ProfilePreferencesRecord,
    ProfileSkillRecord,
    ProfileTextField,
)
from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import AiStructuredGenerationResponse
from hiring_radar.services.ai.runtime import LocalAiRuntimeService
from hiring_radar.services.ai.tasks.skill_evidence_task import SkillEvidenceSuggestionTask


class StubAdapter:
    def health(self):
        raise AssertionError("health should not be called in this test")

    def generate_structured(self, request):
        return AiStructuredGenerationResponse(
            model=request.model,
            content={
                "description_suggestions": [
                    "Python becerisini veri işleme, otomasyon ve üretim kalitesinde script geliştirme bağlamında konumlandır.",
                    "Python ile gerçek iş akışlarında bakım yapılabilir otomasyon araçları geliştirdiğini vurgula.",
                    "Python becerisini veri işleme, otomasyon ve üretim kalitesinde script geliştirme bağlamında konumlandır.",
                ],
                "evidence_note_suggestions": [
                    "Python ile veri temizleme ve otomasyon akışları geliştirerek manuel operasyon yükünü azalttım.",
                    "Python ile veri temizleme ve otomasyon akışları geliştirerek manuel operasyon yükünü azalttım.",
                ],
                "proof_ideas": [
                    "GitHub deposu veya kısa proje bağlantısı ekle.",
                    "Somut çıktıyı ve hangi problemi çözdüğünü belirt.",
                ],
                "missing_signals": ["Ölçülebilir çıktı yok", "Proje adı belirtilmemiş"],
                "strengthening_note": "Bu beceriyi güçlendirmek için proje bağlamı ve ölçülebilir çıktı ekle.",
                "warnings": [],
                "confidence_band": "medium",
            },
            response_time_ms=14,
        )


def _build_profile() -> CandidateProfileAggregate:
    return CandidateProfileAggregate(
        id="7",
        user_id="7",
        full_name=ProfileTextField(value="Alice Example"),
        headline=ProfileTextField(value="Embedded Engineer"),
        summary=ProfileTextField(value="Firmware and embedded systems background."),
        primary_email=ProfileTextField(value="alice@example.com"),
        phone=ProfileTextField(value=None),
        preferences=ProfilePreferencesRecord(target_roles=["Embedded Engineer", "Firmware Engineer"]),
        completeness=ProfileCompletenessSummary(score=61, sections=[]),
        experiences=[
            ProfileExperienceRecord(
                title="Embedded Engineer",
                company_name="Acme",
                description="Worked on MCU firmware and automation tooling.",
            )
        ],
        education=[],
        languages=[],
        skills=[
            # Aggregate skill contract does not currently expose evidence_note.
            ProfileSkillRecord(skill_name="Python", category="Yazılım"),
        ],
        last_cv_parse=None,
        created_at="2026-04-05T10:00:00Z",
        updated_at="2026-04-05T10:00:00Z",
    )


def test_skill_evidence_task_deduplicates_and_limits_results() -> None:
    runtime = LocalAiRuntimeService(
        config=LocalAiRuntimeConfig(enabled=True, default_model="llama3.1:8b"),
        _adapter=StubAdapter(),
    )
    task = SkillEvidenceSuggestionTask(runtime)

    result = task.run(
        profile=_build_profile(),
        locale="tr",
        skill_name="Python",
        category="Yazılım",
        existing_evidence_note="Internal automation scripts",
    )

    assert len(result.description_suggestions) == 2
    assert len(result.evidence_note_suggestions) == 1
    assert result.proof_ideas[0] == "GitHub deposu veya kısa proje bağlantısı ekle."
    assert result.missing_signals == ["Ölçülebilir çıktı yok", "Proje adı belirtilmemiş"]
    assert result.strengthening_note is not None
