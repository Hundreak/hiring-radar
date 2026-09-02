import type {JobMatchExplanation} from '@/types/job';
import {buildLocalizedReasonSummary, getPrimarySkillTerms, type SupportedLocale} from '@/lib/match-ui';

export {type SupportedLocale};

export function shouldShowRecommendationSummary(params: {
  matched: boolean;
  matchScore?: number | null;
  explanation?: JobMatchExplanation | null;
  matchedKeywords: string[];
}): boolean {
  if (!params.matched) return false;
  if (params.explanation?.key_evidence_points?.length) return true;
  if (params.explanation?.top_reasons?.length) return true;
  return getPrimarySkillTerms({
    matched_keywords: params.matchedKeywords,
    explanation: params.explanation ?? null,
  }).length > 0 || (params.matchScore ?? 0) >= 70;
}

export function buildRecommendationSummary(params: {
  locale: SupportedLocale;
  matchedKeywords: string[];
  title: string;
  company: string;
  explanation?: JobMatchExplanation | null;
}): string | null {
  return buildLocalizedReasonSummary(params.locale, params.explanation ?? null);
}

export function buildJobAnalysisPrompt(params: {
  locale: SupportedLocale;
  title: string;
  company: string;
  location: string;
  matchScore?: number | null;
  matchedKeywords: string[];
  href?: string;
  explanation?: JobMatchExplanation | null;
  evidenceTerms?: string[];
  gapTerms?: string[];
}): string {
  const visibleSignals = getPrimarySkillTerms({
    matched_keywords: params.matchedKeywords,
    explanation: params.explanation ?? null,
  }).join(', ') || (params.locale === 'en' ? 'limited' : params.locale === 'de' ? 'begrenzt' : 'sınırlı');

  if (params.locale === 'tr') {
    return [
      `Bu işi profilime göre profesyonelce analiz et.`,
      `İş: ${params.title}`,
      `Şirket: ${params.company}`,
      `Konum: ${params.location}`,
      params.matchScore != null ? `Mevcut eşleşme skoru: ${params.matchScore}%` : null,
      `Şu an görünen güçlü sinyaller: ${visibleSignals}`,
      params.explanation ? `Öne çıkan neden: ${buildLocalizedReasonSummary('tr', params.explanation)}` : null,
      params.href ? `İlan linki: ${params.href}` : null,
      `Lütfen kısa ve kullanıcı odaklı şekilde şunları açıkla:`,
      `1. Bu iş neden bana yakın veya neden sınırlı yakın görünüyor?`,
      `2. Güçlü görünen alanlar neler?`,
      `3. Eksik veya riskli görünen taraflar neler?`,
      `4. Başvurmadan önce neye dikkat etmeliyim?`,
      `Veri yetersizse bunu açıkça belirt, uydurma yorum yapma.`,
    ].filter(Boolean).join('\n');
  }

  if (params.locale === 'de') {
    return [
      `Analysiere diese Stelle professionell anhand meines Profils.`,
      `Rolle: ${params.title}`,
      `Unternehmen: ${params.company}`,
      `Standort: ${params.location}`,
      params.matchScore != null ? `Aktueller Match-Score: ${params.matchScore}%` : null,
      `Sichtbare starke Signale: ${visibleSignals}`,
      params.explanation ? `Hauptgrund: ${buildLocalizedReasonSummary('de', params.explanation)}` : null,
      params.href ? `Stellenlink: ${params.href}` : null,
      `Erkläre bitte kurz und nutzerorientiert:`,
      `1. Warum passt diese Stelle zu mir oder warum nur teilweise?`,
      `2. Welche Stärken sprechen dafür?`,
      `3. Welche Lücken oder Risiken sind sichtbar?`,
      `4. Worauf sollte ich vor einer Bewerbung achten?`,
      `Wenn die Datenlage schwach ist, sag das klar und erfinde nichts.`,
    ].filter(Boolean).join('\n');
  }

  return [
    `Analyze this job against my profile in a professional, user-focused way.`,
    `Role: ${params.title}`,
    `Company: ${params.company}`,
    `Location: ${params.location}`,
    params.matchScore != null ? `Current match score: ${params.matchScore}%` : null,
    `Visible strong signals: ${visibleSignals}`,
    params.explanation ? `Primary reason: ${buildLocalizedReasonSummary('en', params.explanation)}` : null,
    params.href ? `Job link: ${params.href}` : null,
    `Please explain briefly:`,
    `1. Why this role looks aligned or only partially aligned.`,
    `2. What the strongest signals are.`,
    `3. What looks weak, missing, or risky.`,
    `4. What I should pay attention to before applying.`,
    `If the current data is limited, say that clearly and do not invent details.`,
  ].filter(Boolean).join('\n');
}
