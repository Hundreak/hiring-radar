from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from hiring_radar.services.ai.job_analysis_grounding import JobAnalysisGroundingBundle, JobAnalysisStructuredContext


_GENERIC_TOKENS = (
    "açıklayacağım",
    "analiz edeceğim",
    "yardımcı olabilirim",
    "i can help",
    "i can explain",
    "i will explain",
    "ich kann",
)


@dataclass(slots=True, frozen=True)
class RenderedJobAnalysis:
    answer: str
    follow_up_suggestions: tuple[str, ...]
    confidence_band: str


def _normalize_locale(locale: str) -> str:
    normalized = (locale or "tr").strip().lower()
    if normalized.startswith("de"):
        return "de"
    if normalized.startswith("en"):
        return "en"
    return "tr"


def _human_join(values: Iterable[str], *, locale: str) -> str:
    cleaned = [str(value).replace("_", " ").strip() for value in values if str(value).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    conjunction = {"tr": "ve", "en": "and", "de": "und"}.get(locale, "and")
    if len(cleaned) == 2:
        return f"{cleaned[0]} {conjunction} {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, {conjunction} {cleaned[-1]}"


def _fit_band(score: int, *, locale: str) -> str:
    if score >= 78:
        return {"tr": "güçlü uyum", "en": "strong fit", "de": "starke Passung"}[locale]
    if score >= 58:
        return {"tr": "kısmi ama anlamlı uyum", "en": "partial but meaningful fit", "de": "teilweise, aber sinnvolle Passung"}[locale]
    return {"tr": "temkinli değerlendirilmesi gereken uyum", "en": "fit that needs careful review", "de": "Passung, die sorgfältig geprüft werden sollte"}[locale]


def _confidence_band(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 55:
        return "medium"
    return "low"


def _compact_profile_profile_line(context: JobAnalysisStructuredContext, *, locale: str) -> str:
    role_text = _human_join(context.profile_target_roles[:3], locale=locale)
    skill_text = _human_join(context.profile_top_skills[:5], locale=locale)
    if locale == "tr":
        parts = []
        if role_text:
            parts.append(f"Hedef roller: {role_text}")
        if skill_text:
            parts.append(f"Öne çıkan beceriler: {skill_text}")
        return "; ".join(parts)
    if locale == "de":
        parts = []
        if role_text:
            parts.append(f"Zielrollen: {role_text}")
        if skill_text:
            parts.append(f"Stärkste Fähigkeiten: {skill_text}")
        return "; ".join(parts)
    parts = []
    if role_text:
        parts.append(f"Target roles: {role_text}")
    if skill_text:
        parts.append(f"Top skills: {skill_text}")
    return "; ".join(parts)


def _render_intro(context: JobAnalysisStructuredContext, *, locale: str) -> str:
    fit_band = _fit_band(context.fit_score_percent, locale=locale)
    profile_line = _compact_profile_profile_line(context, locale=locale)
    if locale == "tr":
        sentence = (
            f"**{context.job_title}** rolü için mevcut profilinle yaptığım veri temelli değerlendirme, bu ilanı **{fit_band}** bandına yerleştiriyor. "
            f"Deterministik eşleşme skoru **%{context.fit_score_percent}**, nihai sıralama skoru ise **%{context.final_score_percent}**."
        )
        if profile_line:
            sentence += f" {profile_line}."
        return sentence
    if locale == "de":
        sentence = (
            f"Die datenbasierte Bewertung für **{context.job_title}** ordnet diese Stelle mit deinem aktuellen Profil als **{fit_band}** ein. "
            f"Der deterministische Fit-Score liegt bei **{context.fit_score_percent}%**, der finale Ranking-Score bei **{context.final_score_percent}%**."
        )
        if profile_line:
            sentence += f" {profile_line}."
        return sentence
    sentence = (
        f"The data-backed review for **{context.job_title}** places this role in the **{fit_band}** band against your current profile. "
        f"The deterministic fit score is **{context.fit_score_percent}%**, and the final ranking score is **{context.final_score_percent}%**."
    )
    if profile_line:
        sentence += f" {profile_line}."
    return sentence


def _ensure_list(values: Iterable[str], fallback: str) -> list[str]:
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return cleaned if cleaned else [fallback]


def render_deterministic_job_analysis(
    *,
    locale: str,
    bundle: JobAnalysisGroundingBundle,
) -> RenderedJobAnalysis:
    normalized_locale = _normalize_locale(locale)
    context = bundle.analysis_context

    strengths: list[str] = []
    for point in context.evidence_details[:4]:
        strengths.append(point)
    if context.external_requirements:
        if normalized_locale == "tr":
            strengths.append(
                f"İlanın orijinal sayfasındaki gereksinimler arasında {_human_join(context.external_requirements[:4], locale=normalized_locale)} öne çıkıyor."
            )
        elif normalized_locale == "de":
            strengths.append(
                f"Auf der Originalseite werden besonders {_human_join(context.external_requirements[:4], locale=normalized_locale)} hervorgehoben."
            )
        else:
            strengths.append(
                f"The original source page emphasizes requirements such as {_human_join(context.external_requirements[:4], locale=normalized_locale)}."
            )
    strengths = _ensure_list(
        strengths,
        {
            "tr": "Mevcut profil sinyallerin bu rol için tamamen boş değil, ancak daha derin kanıt katmanı sınırlı.",
            "en": "Your current profile signals are not empty for this role, but the evidence layer is still limited.",
            "de": "Dein aktuelles Profil zeigt gewisse Signale für diese Rolle, die Evidenz ist aber noch begrenzt.",
        }[normalized_locale],
    )

    gaps: list[str] = list(context.gap_details[:4])
    if context.missing_skill_terms:
        joined = _human_join(context.missing_skill_terms[:5], locale=normalized_locale)
        if normalized_locale == "tr":
            gaps.append(f"Eksik veya zayıf görünen beceri sinyalleri: {joined}.")
        elif normalized_locale == "de":
            gaps.append(f"Fehlende oder schwach belegte Skill-Signale: {joined}.")
        else:
            gaps.append(f"Missing or weakly evidenced skill signals: {joined}.")
    gaps = _ensure_list(
        gaps,
        {
            "tr": "Belirgin kritik boşluk görünmüyor; yine de başvuru öncesi ilanın özgün gereksinimlerini CV üzerinde netleştirmek faydalı olur.",
            "en": "No major red flag is visible, but it is still worth aligning your CV with the original source requirements before applying.",
            "de": "Es ist kein kritischer Gap sichtbar, dennoch solltest du deinen Lebenslauf vor der Bewerbung klar auf die Originalanforderungen ausrichten.",
        }[normalized_locale],
    )

    cv_focus: list[str] = []
    if context.matched_skill_terms:
        joined = _human_join(context.matched_skill_terms[:5], locale=normalized_locale)
        if normalized_locale == "tr":
            cv_focus.append(f"CV'nde özellikle {joined} ile ilişkili deneyimlerini somut çıktılarla öne çıkar.")
        elif normalized_locale == "de":
            cv_focus.append(f"Hebe im Lebenslauf besonders Erfahrungen mit {joined} und klaren Ergebnissen hervor.")
        else:
            cv_focus.append(f"Bring experience tied to {joined} to the top of your CV with concrete outcomes.")
    if context.external_responsibilities:
        joined = _human_join(context.external_responsibilities[:3], locale=normalized_locale)
        if normalized_locale == "tr":
            cv_focus.append(f"İlanda öne çıkan sorumluluklar arasında {joined} var; benzer sorumlulukları daha görünür yaz.")
        elif normalized_locale == "de":
            cv_focus.append(f"Auf der Stelle stehen Aufgaben wie {joined} im Vordergrund; beschreibe ähnliche Verantwortungen sichtbarer.")
        else:
            cv_focus.append(f"The listing highlights responsibilities such as {joined}; make similar ownership clearer in your CV.")
    cv_focus = _ensure_list(
        cv_focus,
        {
            "tr": "Başvuru öncesi en alakalı deneyimlerini, kullandığın araçları ve ölçülebilir çıktıları daha görünür hale getir.",
            "en": "Before applying, surface the most relevant experience, tools, and measurable outcomes more clearly.",
            "de": "Mach vor der Bewerbung die relevantesten Erfahrungen, Werkzeuge und messbaren Ergebnisse klarer sichtbar.",
        }[normalized_locale],
    )

    next_steps: list[str] = []
    if context.external_requirements:
        joined = _human_join(context.external_requirements[:3], locale=normalized_locale)
        if normalized_locale == "tr":
            next_steps.append(f"Başvuru öncesi {joined} tarafında gerçek örneklerin hazır olduğundan emin ol.")
        elif normalized_locale == "de":
            next_steps.append(f"Stelle vor der Bewerbung sicher, dass du für {joined} konkrete Beispiele parat hast.")
        else:
            next_steps.append(f"Before applying, make sure you can speak concretely about {joined}.")
    if context.external_culture_clues:
        joined = _human_join(context.external_culture_clues[:3], locale=normalized_locale)
        if normalized_locale == "tr":
            next_steps.append(f"Şirket kültürü tarafında {joined} vurgusu var; motivasyon cümleni buna göre hizala.")
        elif normalized_locale == "de":
            next_steps.append(f"Auf der Kulturseite werden {joined} betont; richte deine Motivation daran aus.")
        else:
            next_steps.append(f"The company culture appears to value {joined}; align your motivation accordingly.")
    next_steps = _ensure_list(
        next_steps,
        {
            "tr": "Başvuru öncesi ilan metniyle birebir örtüşen 2-3 deneyim örneği ve kısa bir motivasyon çerçevesi hazırla.",
            "en": "Before applying, prepare 2-3 experience examples that map directly to the listing and a short motivation angle.",
            "de": "Bereite vor der Bewerbung 2-3 Erfahrungssituationen vor, die direkt zur Stelle passen, plus einen kurzen Motivationsrahmen.",
        }[normalized_locale],
    )

    headings = {
        "tr": {
            "overview": "## Genel değerlendirme",
            "strengths": "## Neden uygun görünüyor",
            "gaps": "## Dikkat edilmesi gereken boşluklar",
            "cv": "## CV'de özellikle öne çıkar",
            "next": "## Başvuru öncesi öneriler",
        },
        "en": {
            "overview": "## Overall assessment",
            "strengths": "## Strong alignment areas",
            "gaps": "## Gaps to review",
            "cv": "## What to emphasize in your CV",
            "next": "## Before you apply",
        },
        "de": {
            "overview": "## Gesamteinschätzung",
            "strengths": "## Starke Passungssignale",
            "gaps": "## Punkte zur Prüfung",
            "cv": "## Im Lebenslauf besonders hervorheben",
            "next": "## Vor der Bewerbung",
        },
    }[normalized_locale]

    parts = [
        headings["overview"],
        _render_intro(context, locale=normalized_locale),
        "",
        headings["strengths"],
        *[f"- {item}" for item in strengths],
        "",
        headings["gaps"],
        *[f"- {item}" for item in gaps],
        "",
        headings["cv"],
        *[f"- {item}" for item in cv_focus],
        "",
        headings["next"],
        *[f"- {item}" for item in next_steps],
    ]

    follow_ups = {
        "tr": (
            "Bu iş için CV özetimi birlikte yeniden yazalım.",
            "Mülakatta hangi deneyimleri öne çıkarmam gerektiğini çıkar.",
            "Bu ilana daha uygun alternatif rolleri göster.",
        ),
        "en": (
            "Rewrite my CV summary for this role.",
            "Show which experiences I should lead with in interviews.",
            "Find similar roles that may fit me even better.",
        ),
        "de": (
            "Formuliere meine CV-Zusammenfassung für diese Stelle neu.",
            "Zeige, welche Erfahrungen ich im Interview zuerst nennen sollte.",
            "Finde ähnliche Rollen, die noch besser passen könnten.",
        ),
    }[normalized_locale]

    return RenderedJobAnalysis(
        answer="\n".join(parts).strip(),
        follow_up_suggestions=follow_ups,
        confidence_band=_confidence_band(context.fit_score_percent),
    )


def answer_needs_job_analysis_fallback(answer: str, *, locale: str, bundle: JobAnalysisGroundingBundle) -> bool:
    normalized_answer = (answer or "").strip().lower()
    if not normalized_answer:
        return True
    if len(normalized_answer) < 280:
        return True
    if any(token in normalized_answer for token in _GENERIC_TOKENS):
        return True

    context = bundle.analysis_context
    required_signals = [context.job_title.lower()]
    if context.company_name:
        required_signals.append(context.company_name.lower())
    if context.matched_skill_terms:
        required_signals.append(context.matched_skill_terms[0].lower())
    if not any(signal in normalized_answer for signal in required_signals if signal):
        return True

    heading_tokens = {
        "tr": ("genel", "uyum", "cv", "başvuru"),
        "en": ("overall", "fit", "cv", "apply"),
        "de": ("gesamt", "passung", "lebenslauf", "bewerb"),
    }[_normalize_locale(locale)]
    if sum(1 for token in heading_tokens if token in normalized_answer) < 2:
        return True
    return False
