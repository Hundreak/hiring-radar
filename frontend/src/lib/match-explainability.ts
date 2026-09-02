import type {JobMatchExplanation, JobMatchGapItem, JobMatchScoreBreakdownItem} from '@/types/job';
import {buildLocalizedReasonSummary, type SupportedLocale} from '@/lib/match-ui';

export type MatchReadinessLevel = 'ready' | 'review' | 'stretch';
export type MatchConfidenceLevel = 'strong' | 'moderate' | 'limited';

export type MatchActionPlanItem = {
  kind: 'strengthen_gap' | 'verify_context' | 'prepare_story' | 'apply_now';
  terms: string[];
};

export type MatchExplainabilityModel = {
  readiness: {
    level: MatchReadinessLevel;
    score: number;
  };
  confidence: MatchConfidenceLevel;
  topDrivers: JobMatchScoreBreakdownItem[];
  strongestTerms: string[];
  priorityGaps: JobMatchGapItem[];
  missingTerms: string[];
  actionPlan: MatchActionPlanItem[];
};

const SEVERITY_WEIGHT: Record<JobMatchGapItem['severity'], number> = {
  high: 3,
  medium: 2,
  low: 1,
};

const IMPACT_WEIGHT: Record<JobMatchScoreBreakdownItem['impact'], number> = {
  strong: 3,
  moderate: 2,
  weak: 1,
};

function asArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function uniqueVisibleTerms(values: Array<string | null | undefined>, limit: number): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const value of values) {
    if (typeof value !== 'string') continue;
    const trimmed = value.trim();
    if (!trimmed || trimmed.length < 2) continue;
    const normalized = trimmed.toLowerCase();
    if (seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(trimmed);
    if (result.length >= limit) break;
  }

  return result;
}

function clampPercent(value: number | null | undefined): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function getConfidence(explanation: JobMatchExplanation | null | undefined): MatchConfidenceLevel {
  return explanation?.analysis_coverage?.level ?? 'limited';
}

function getTopDrivers(explanation: JobMatchExplanation | null | undefined): JobMatchScoreBreakdownItem[] {
  return asArray(explanation?.matching_score_breakdown)
    .filter((item) => item.raw_score >= 0.35 || item.impact !== 'weak')
    .sort((a, b) => {
      const impactDiff = IMPACT_WEIGHT[b.impact] - IMPACT_WEIGHT[a.impact];
      if (impactDiff !== 0) return impactDiff;
      return b.weighted_score - a.weighted_score;
    })
    .slice(0, 3);
}

function getPriorityGaps(explanation: JobMatchExplanation | null | undefined): JobMatchGapItem[] {
  return asArray(explanation?.gap_analysis)
    .filter((gap) => asArray(gap.missing_terms).length > 0 || gap.detail.trim().length > 0)
    .sort((a, b) => SEVERITY_WEIGHT[b.severity] - SEVERITY_WEIGHT[a.severity])
    .slice(0, 2);
}

function getStrongestTerms(explanation: JobMatchExplanation | null | undefined, fallbackTerms: string[]): string[] {
  const driverTerms = getTopDrivers(explanation).flatMap((driver) => asArray(driver.evidence_terms));
  const evidenceTerms = asArray(explanation?.key_evidence_points).flatMap((point) => asArray(point.supporting_terms));

  return uniqueVisibleTerms([
    ...driverTerms,
    ...asArray(explanation?.matched_skill_terms),
    ...evidenceTerms,
    ...fallbackTerms,
  ], 5);
}

function getMissingTerms(explanation: JobMatchExplanation | null | undefined): string[] {
  const gapTerms = getPriorityGaps(explanation).flatMap((gap) => asArray(gap.missing_terms));
  return uniqueVisibleTerms([
    ...gapTerms,
    ...asArray(explanation?.missing_skill_terms),
    ...getTopDrivers(explanation).flatMap((driver) => asArray(driver.missing_terms)),
  ], 5);
}

function buildReadiness(params: {
  matchScore: number;
  isScorePreview?: boolean;
  confidence: MatchConfidenceLevel;
  priorityGaps: JobMatchGapItem[];
}) {
  const score = clampPercent(params.matchScore);
  const highGapCount = params.priorityGaps.filter((gap) => gap.severity === 'high').length;

  if (!params.isScorePreview && score >= 82 && params.confidence !== 'limited' && highGapCount === 0) {
    return {level: 'ready' as const, score};
  }

  if (score >= 65 && highGapCount <= 1) {
    return {level: 'review' as const, score};
  }

  return {level: 'stretch' as const, score};
}

function buildActionPlan(params: {
  readiness: MatchReadinessLevel;
  confidence: MatchConfidenceLevel;
  strongestTerms: string[];
  missingTerms: string[];
}): MatchActionPlanItem[] {
  const actions: MatchActionPlanItem[] = [];

  if (params.readiness === 'ready') {
    actions.push({kind: 'apply_now', terms: params.strongestTerms.slice(0, 3)});
  }

  if (params.strongestTerms.length > 0) {
    actions.push({kind: 'prepare_story', terms: params.strongestTerms.slice(0, 3)});
  }

  if (params.missingTerms.length > 0) {
    actions.push({kind: 'strengthen_gap', terms: params.missingTerms.slice(0, 3)});
  }

  if (params.confidence === 'limited') {
    actions.push({kind: 'verify_context', terms: []});
  }

  return actions.slice(0, 3);
}

export function buildMatchExplainabilityModel(params: {
  matchScore: number;
  isScorePreview?: boolean;
  explanation?: JobMatchExplanation | null;
  fallbackTerms?: string[];
}): MatchExplainabilityModel {
  const confidence = getConfidence(params.explanation ?? null);
  const priorityGaps = getPriorityGaps(params.explanation ?? null);
  const topDrivers = getTopDrivers(params.explanation ?? null);
  const strongestTerms = getStrongestTerms(params.explanation ?? null, params.fallbackTerms ?? []);
  const missingTerms = getMissingTerms(params.explanation ?? null);
  const readiness = buildReadiness({
    matchScore: params.matchScore,
    isScorePreview: params.isScorePreview,
    confidence,
    priorityGaps,
  });

  return {
    readiness,
    confidence,
    topDrivers,
    strongestTerms,
    priorityGaps,
    missingTerms,
    actionPlan: buildActionPlan({
      readiness: readiness.level,
      confidence,
      strongestTerms,
      missingTerms,
    }),
  };
}

export function buildMatchActionPlanPrompt(params: {
  locale: SupportedLocale;
  title: string;
  company: string;
  location: string;
  matchScore: number;
  explanation?: JobMatchExplanation | null;
  model: MatchExplainabilityModel;
}) {
  const strengths = params.model.strongestTerms.join(', ') || '—';
  const gaps = params.model.missingTerms.join(', ') || '—';
  const reason = buildLocalizedReasonSummary(params.locale, params.explanation ?? null) ?? '—';
  const confidence = params.model.confidence;
  const readiness = params.model.readiness.level;

  if (params.locale === 'tr') {
    return [
      'Bu ilan için net, aksiyon odaklı bir başvuru planı çıkar.',
      `İş: ${params.title}`,
      `Şirket: ${params.company}`,
      `Konum: ${params.location}`,
      `Eşleşme skoru: ${params.matchScore}%`,
      `Başvuru hazırlığı: ${readiness}`,
      `Analiz güveni: ${confidence}`,
      `Ana neden: ${reason}`,
      `Güçlü sinyaller: ${strengths}`,
      `Eksik/riskli sinyaller: ${gaps}`,
      'Şunları kısa ve uygulanabilir yaz:',
      '1. Bu ilana başvurmalı mıyım?',
      '2. CV/profilimde hangi 3 noktayı güçlendirmeliyim?',
      '3. Ön yazı veya mesajda hangi kanıtları öne çıkarmalıyım?',
      '4. Eksik veri varsa açıkça belirt; tahmin uydurma.',
    ].join('\n');
  }

  if (params.locale === 'de') {
    return [
      'Erstelle einen klaren, handlungsorientierten Bewerbungsplan für diese Stelle.',
      `Rolle: ${params.title}`,
      `Unternehmen: ${params.company}`,
      `Standort: ${params.location}`,
      `Match-Score: ${params.matchScore}%`,
      `Bewerbungsreife: ${readiness}`,
      `Analyse-Vertrauen: ${confidence}`,
      `Hauptgrund: ${reason}`,
      `Starke Signale: ${strengths}`,
      `Lücken/Risiken: ${gaps}`,
      'Bitte kurz und praktisch beantworten:',
      '1. Sollte ich mich bewerben?',
      '2. Welche 3 Punkte sollte ich in CV/Profil verbessern?',
      '3. Welche Nachweise sollte ich in Anschreiben oder Nachricht betonen?',
      '4. Wenn Daten fehlen, sag das klar; nichts erfinden.',
    ].join('\n');
  }

  return [
    'Create a clear, action-oriented application plan for this role.',
    `Role: ${params.title}`,
    `Company: ${params.company}`,
    `Location: ${params.location}`,
    `Match score: ${params.matchScore}%`,
    `Application readiness: ${readiness}`,
    `Analysis confidence: ${confidence}`,
    `Primary reason: ${reason}`,
    `Strong signals: ${strengths}`,
    `Gaps/risks: ${gaps}`,
    'Please answer briefly and practically:',
    '1. Should I apply?',
    '2. What 3 things should I strengthen in my CV/profile?',
    '3. Which evidence should I highlight in a cover note or outreach message?',
    '4. If data is missing, say so clearly; do not invent details.',
  ].join('\n');
}
